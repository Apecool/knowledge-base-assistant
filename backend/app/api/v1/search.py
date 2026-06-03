"""
Search API Routes — Full-text and semantic (RAG) search
"""
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.knowledge import KnowledgeItem
from app.schemas.knowledge import KnowledgeItemResponse
from app.schemas.search import (
    SemanticSearchResponse,
    ChunkResult,
    ReindexResponse,
)
from app.services.langchain_rag import LangChainRAGService
from app.config import settings

router = APIRouter()


@router.get("/", response_model=List[KnowledgeItemResponse])
async def search_knowledge(
    q: str = Query(..., min_length=1, description="Search query"),
    category: Optional[str] = None,
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
):
    """Full-text search across knowledge items (SQL LIKE)."""
    query = db.query(KnowledgeItem).filter(
        KnowledgeItem.title.contains(q)
        | KnowledgeItem.content.contains(q)
    )

    if category:
        query = query.filter(KnowledgeItem.category == category)

    results = query.order_by(KnowledgeItem.updated_at.desc()).limit(limit).all()
    return results


@router.get("/semantic", response_model=SemanticSearchResponse)
async def semantic_search(
    q: str = Query(..., min_length=1, description="Query text for semantic search"),
    top_k: int = Query(5, ge=1, le=50, description="Number of top results"),
):
    """
    Semantic search using sentence-transformers + ChromaDB.
    Returns chunks most semantically similar to the query.
    """
    try:
        rag = LangChainRAGService(
            persist_dir=settings.CHROMA_PERSIST_DIR,
            enable_reranker=True,
            enable_cache=True,
        )
        results = rag.search(query=q, top_k=top_k, rerank=True)

        chunk_results = [
            ChunkResult(
                id=r.get("id", f"chunk_{i}"),
                document=r.get("document", ""),
                metadata=r.get("metadata", {}),
                score=r.get("score", 0),
            )
            for i, r in enumerate(results)
        ]

        return SemanticSearchResponse(
            query=q,
            results=chunk_results,
            total=len(chunk_results),
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Semantic search failed: {str(e)}",
        )


@router.post("/reindex", response_model=ReindexResponse)
async def reindex_all(db: Session = Depends(get_db)):
    """
    Re-index all knowledge items into the vector store.
    Useful after initial setup or if vector store is out of sync.
    """
    try:
        rag = LangChainRAGService(
            persist_dir=settings.CHROMA_PERSIST_DIR,
            enable_reranker=True,
            enable_cache=True,
        )
        result = rag.reindex_all(db)
        return ReindexResponse(
            items_indexed=result["items_indexed"],
            chunks_created=result["chunks_created"],
            message=f"Re-indexed {result['items_indexed']} items into {result['chunks_created']} chunks",
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Re-indexing failed: {str(e)}",
        )


@router.post("/reindex/{item_id}", response_model=ReindexResponse)
async def reindex_single(item_id: int, db: Session = Depends(get_db)):
    """Re-index a single knowledge item by ID."""
    item = db.query(KnowledgeItem).filter(KnowledgeItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Knowledge item not found")

    try:
        rag = LangChainRAGService(
            persist_dir=settings.CHROMA_PERSIST_DIR,
            enable_reranker=True,
            enable_cache=True,
        )
        chunks = rag.index_knowledge(
            knowledge_id=item.id,
            title=item.title,
            content=item.content,
            category=item.category,
        )
        return ReindexResponse(
            items_indexed=1,
            chunks_created=chunks,
            message=f"Re-indexed item {item_id} into {chunks} chunks",
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Re-indexing failed: {str(e)}",
        )