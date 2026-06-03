"""
Chat API — Multi-turn conversation with RAG context, streaming SSE support.
"""
import json
import asyncio
from typing import AsyncGenerator
from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.chat import (
    ChatRequest,
    ChatResponse,
    ChatSessionDetail,
    CacheStats,
)
from app.services.langchain_rag import LangChainRAGService
from app.services.chat_memory import session_manager
from app.services.semantic_cache import SemanticCache
from app.config import settings
from app.utils.logger import TraceLogger, trace_id_var

router = APIRouter()


def get_rag() -> LangChainRAGService:
    """Dependency to get RAG service instance."""
    return LangChainRAGService(
        persist_dir=settings.CHROMA_PERSIST_DIR,
        enable_reranker=False,  # off by default — reranker needs CrossEncoder download
        enable_cache=True,
    )


async def _generate_context(rag: LangChainRAGService, query: str,
                            top_k: int = 5) -> tuple:
    """
    Retrieve relevant context for a query.

    Returns:
        Tuple of (context_text, sources_list).
    """
    results = rag.search(query, top_k=top_k, rerank=True)
    contexts = []
    sources = []

    for r in results:
        doc = r.get("document", "")
        meta = r.get("metadata", {})
        score = r.get("score", 0)
        contexts.append(doc)
        sources.append({
            "document": doc[:200] + "..." if len(doc) > 200 else doc,
            "score": round(score, 4),
            "heading": meta.get("heading", ""),
            "title": meta.get("title", ""),
            "knowledge_id": meta.get("knowledge_id"),
        })

    context_text = "\n\n---\n\n".join(contexts) if contexts else ""
    return context_text, sources


def _build_prompt(query: str, context: str, history: str) -> str:
    """
    Build a prompt for the LLM with context and chat history.
    """
    if context:
        prompt = f"""你是一个知识库助手。请基于以下参考文档回答问题。
如果参考文档中不包含相关信息，请如实说明你不知道。

参考文档：
{context}

"""
        if history:
            prompt += f"""对话历史：
{history}

"""
        prompt += f"""用户问题：{query}

请用中文回答。"""
    else:
        prompt = f"""用户问题：{query}

(未在知识库中找到相关参考文档)"""
    return prompt


def _get_llm_client():
    """Get LLM client based on configured provider."""
    import openai

    if settings.LLM_PROVIDER == "deepseek":
        api_key = settings.DEEPSEEK_API_KEY
        base_url = settings.DEEPSEEK_API_BASE
        model = settings.DEEPSEEK_MODEL
    else:
        api_key = settings.OPENAI_API_KEY
        base_url = settings.OPENAI_API_BASE
        model = settings.OPENAI_MODEL

    client = openai.OpenAI(api_key=api_key, base_url=base_url)
    return client, model


async def _stream_response(
    request_id: str, query: str, context: str,
    history: str, sources: list, session_id: str,
) -> AsyncGenerator[str, None]:
    """
    SSE streaming generator.
    Supports OpenAI and DeepSeek (via LLM_PROVIDER setting).
    When no API key is configured, returns structured knowledge results
    instead of the raw prompt text.
    """
    api_key = settings.OPENAI_API_KEY if settings.LLM_PROVIDER == "openai" else settings.DEEPSEEK_API_KEY

    if not api_key:
        # No LLM configured — return structured knowledge retrieval results
        if not sources:
            answer = "未在知识库中找到与问题相关的信息。"
            yield f"data: {json.dumps({'type': 'token', 'content': answer})}\n\n"
            yield f"data: {json.dumps({'type': 'done', 'full_content': answer})}\n\n"
            return

        yield "data: " + json.dumps({"type": "token", "content": "📄 在知识库中找到以下相关条目：\n\n"}) + "\n\n"
        for i, src in enumerate(sources):
            line = f"**{i+1}. {src.get('title', '未知')}** (相似度: {src.get('score', 0)*100:.0f}%)\n"
            if src.get('heading'):
                line += f"   章节: {src['heading']}\n"
            line += f"   {src.get('document', '')}\n\n"
            yield "data: " + json.dumps({"type": "token", "content": line}) + "\n\n"
            await asyncio.sleep(0.005)

        answer = "\n💡 配置 LLM API Key (DeepSeek/OpenAI) 后可获得智能生成的回答。"
        yield "data: " + json.dumps({"type": "token", "content": answer}) + "\n\n"
        yield f"data: {json.dumps({'type': 'done', 'full_content': '知识库检索结果'})}\n\n"
        return

    try:
        client, model = _get_llm_client()

        messages = [{"role": "system", "content": "你是一个知识库助手。"}]
        if history:
            for line in history.split("\n"):
                if line.startswith("用户: "):
                    messages.append({"role": "user", "content": line[4:]})
                elif line.startswith("助手: "):
                    messages.append({"role": "assistant", "content": line[4:]})

        messages.append({"role": "user", "content": _build_prompt(query, context, "")})

        stream = client.chat.completions.create(
            model=model,
            messages=messages,
            stream=True,
            temperature=0.3,
        )

        full_content = ""
        for chunk in stream:
            if chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                full_content += content
                yield f"data: {json.dumps({'type': 'token', 'content': content})}\n\n"

        yield f"data: {json.dumps({'type': 'done', 'full_content': full_content})}\n\n"

    except Exception as e:
        yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"


@router.post("/stream")
async def chat_stream(
    request: ChatRequest,
    rag_request: Request,
    db: Session = Depends(get_db),
):
    """
    Multi-turn chat with SSE streaming.

    Request body:
    {
        "session_id": "abc-123",
        "query": "什么是微服务架构?",
        "stream": true,
        "top_k": 5
    }

    Returns SSE stream with events:
    - {"type": "token", "content": "..."} — text tokens
    - {"type": "sources", "sources": [...]} — retrieved sources
    - {"type": "done", "full_content": "..."} — completion signal
    """
    trace_id = trace_id_var.get() or request.session_id[:8]
    TraceLogger.info(f"Chat request: session={request.session_id[:8]} query={request.query[:50]}")

    rag = get_rag()

    # Retrieve context
    context, sources = await _generate_context(rag, request.query, request.top_k)

    # Get chat history
    history = session_manager.get_history(request.session_id, limit=10)

    # Save user message
    session_manager.add_user_message(request.session_id, request.query)

    async def event_stream():
        # Send sources first
        yield f"data: {json.dumps({'type': 'sources', 'sources': sources})}\n\n"

        # Stream response
        async for event in _stream_response(
            request_id=trace_id,
            query=request.query,
            context=context,
            sources=sources,
            history=history,
            session_id=request.session_id,
        ):
            yield event

        # Save AI response (extract from done event)
        # Note: In a real implementation, we'd capture the full response here

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
            "X-Trace-Id": trace_id,
        },
    )


@router.post("/", response_model=ChatResponse)
async def chat_sync(
    request: ChatRequest,
    db: Session = Depends(get_db),
):
    """
    Non-streaming chat endpoint.
    Returns complete answer with sources.
    """
    rag = get_rag()

    # Retrieve context
    context, sources = await _generate_context(rag, request.query, request.top_k)

    # Get chat history
    history = session_manager.get_history(request.session_id, limit=10)

    # Save messages
    session_manager.add_user_message(request.session_id, request.query)

    # Generate answer using configured LLM
    api_key = settings.OPENAI_API_KEY if settings.LLM_PROVIDER == "openai" else settings.DEEPSEEK_API_KEY

    if api_key:
        try:
            client, model = _get_llm_client()
            prompt = _build_prompt(request.query, context, history)

            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
            )
            answer = response.choices[0].message.content
        except Exception as e:
            answer = f"抱歉，生成回答时出错: {str(e)}"
    else:
        # No API key — return structured knowledge retrieval results
        if not sources:
            answer = "未在知识库中找到与问题相关的信息。"
        else:
            answer = "📄 在知识库中找到以下相关条目：\n\n"
            for i, src in enumerate(sources):
                answer += f"{i+1}. **{src.get('title', '未知')}** (相似度: {src.get('score', 0)*100:.0f}%)\n"
                if src.get('heading'):
                    answer += f"   章节: {src['heading']}\n"
                answer += f"   {src.get('document', '')}\n\n"
            answer += "\n💡 配置 LLM API Key (DeepSeek/OpenAI) 后可获得智能生成的回答。"

    # Save AI response
    session_manager.add_ai_message(request.session_id, answer)

    session = session_manager.get_or_create(request.session_id)
    return ChatResponse(
        session_id=request.session_id,
        answer=answer,
        sources=sources,
        message_count=len(session.messages),
    )


@router.get("/sessions", response_model=list)
async def list_sessions():
    """List all chat sessions."""
    return session_manager.list_sessions()


@router.get("/sessions/{session_id}", response_model=ChatSessionDetail)
async def get_session(session_id: str):
    """Get a specific session with full message history."""
    session = session_manager.get_or_create(session_id)
    return ChatSessionDetail(
        session_id=session.session_id,
        message_count=len(session.messages),
        created_at=session.created_at,
        updated_at=session.updated_at,
        messages=[{"role": m.role, "content": m.content, "timestamp": m.timestamp}
                  for m in session.messages],
    )


@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    """Delete a chat session."""
    session_manager.delete_session(session_id)
    return {"message": "Session deleted"}


@router.get("/cache/stats", response_model=CacheStats)
async def cache_stats():
    """Get semantic cache statistics."""
    cache = SemanticCache()
    return CacheStats(**cache.get_stats())


@router.post("/cache/clear")
async def clear_cache():
    """Clear the semantic cache."""
    cache = SemanticCache()
    cache.clear()
    return {"message": "Cache cleared"}