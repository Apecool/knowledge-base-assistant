"""
LangChain-based RAG Service
Integrated pipeline: document parsing → chunking → embedding → retrieval → reranking
Uses LangChain components with local sentence-transformers and ChromaDB.
"""
from typing import List, Dict, Any, Optional, AsyncGenerator
from sqlalchemy.orm import Session

from app.config import settings
from app.services.reranker import Reranker
from app.services.semantic_cache import SemanticCache
from app.services.document_parser import chunk_with_structure
from app.utils.logger import TraceLogger

# Use only our local TF-IDF embedding — zero downloads
from app.services.embedding_service import LocalEmbeddingService
from app.services.vector_store import VectorStore


class LangChainRAGService:
    """
    RAG service using LangChain components.

    Features:
    - LangChain Chroma vector store (persistent)
    - LangChain text splitters with markdown-aware chunking
    - Cross-encoder reranker for improved retrieval
    - Semantic cache for similar query detection
    - Optional LLM-based answer generation (requires API key)
    - Optional streaming support
    """

    def __init__(
        self,
        persist_dir: Optional[str] = None,
        enable_reranker: bool = True,
        enable_cache: bool = True,
    ):
        self.persist_dir = persist_dir or settings.CHROMA_PERSIST_DIR
        # Local TF-IDF embedder — zero network, zero download
        self.embedder = LocalEmbeddingService()
        self.vector_store = VectorStore(persist_dir=self.persist_dir)

        # Optional components
        self.reranker = Reranker() if enable_reranker else None
        self.cache = SemanticCache() if enable_cache else None

    def index_knowledge(
        self,
        knowledge_id: int,
        title: str,
        content: str,
        category: Optional[str] = None,
    ) -> int:
        """
        Index a knowledge item: parse → chunk → embed → store.
        - Uses document_parser for heading/table-aware chunking
        - Uses local TF-IDF embedding (no downloads)
        - Batch embeds all chunks, then single ChromaDB write
        """
        import time
        t0 = time.time()

        full_text = f"# {title}\n\n{content}"
        structured_chunks = chunk_with_structure(full_text)

        if not structured_chunks:
            return 0

        # Collect all texts and metadata
        texts = []
        metadatas = []
        for i, chunk in enumerate(structured_chunks):
            chunk_text = chunk["text"]
            if not chunk_text.strip():
                continue
            texts.append(chunk_text)
            metadatas.append({
                "knowledge_id": knowledge_id,
                "chunk_index": i,
                "heading": chunk["heading"],
                "level": chunk["level"],
                "contains_table": chunk.get("contains_table", False),
                "contains_code": chunk.get("contains_code", False),
                "title": title,
                "category": category or "",
            })

        if not texts:
            return 0

        # Batch embed all texts at once
        embeddings = self.embedder.embed_batch(texts)

        # Delete old chunks, then write all at once
        self.vector_store.delete_by_knowledge_id(knowledge_id)
        self.vector_store.add_chunks(
            knowledge_id=knowledge_id,
            chunk_texts=texts,
            embeddings=embeddings,
            metadatas=metadatas,
        )

        TraceLogger.duration("index_knowledge", (time.time() - t0) * 1000,
                             knowledge_id=knowledge_id, chunks=len(texts))
        return len(texts)

    def remove_knowledge(self, knowledge_id: int) -> int:
        """Remove all chunks for a knowledge item."""
        return self.vector_store.delete_by_knowledge_id(knowledge_id)

    def search(
        self,
        query: str,
        top_k: int = 5,
        rerank: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Semantic search: local TF-IDF → ChromaDB → optional rerank.
        Pipeline:
        1. Check semantic cache
        2. Embed query (local TF-IDF)
        3. Retrieve Top-20 from ChromaDB
        4. Cross-encoder re-ranking to Top-5
        5. Cache the top result
        """
        import time

        # Step 0: Check cache
        if self.cache:
            t0 = time.time()
            cached = self.cache.get(query)
            TraceLogger.trace_rag("cache_check", (time.time() - t0) * 1000,
                                  {"hit": cached is not None})
            if cached:
                return [{"document": cached, "score": 1.0, "from_cache": True}]

        # Step 1: Embed query
        t1 = time.time()
        query_embedding = self.embedder.embed_query(query)

        # Step 2: Search ChromaDB (get top 20 if reranking)
        k = 20 if (rerank and self.reranker) else top_k
        results = self.vector_store.search(query_embedding, top_k=k)
        TraceLogger.trace_rag("retrieval", (time.time() - t1) * 1000,
                              {"results": len(results)})

        # Step 3: Rerank
        if rerank and self.reranker and results:
            t2 = time.time()
            results = self.reranker.rerank(query, results, top_k=top_k)
            TraceLogger.trace_rag("rerank", (time.time() - t2) * 1000,
                                  {"reranked": len(results)})

        # Step 4: Cache the top result
        if self.cache and results:
            self.cache.set(query, results[0]["document"])

        return results[:top_k]

    def reindex_all(self, db: Session) -> dict:
        """Re-index all knowledge items from the database."""
        from app.models.knowledge import KnowledgeItem
        items = db.query(KnowledgeItem).all()
        total_chunks = 0
        for item in items:
            chunks_count = self.index_knowledge(
                knowledge_id=item.id,
                title=item.title,
                content=item.content,
                category=item.category,
            )
            total_chunks += chunks_count
        return {"items_indexed": len(items), "chunks_created": total_chunks}