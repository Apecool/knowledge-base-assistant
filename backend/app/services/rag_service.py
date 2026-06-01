"""
RAG (Retrieval-Augmented Generation) Service
Orchestrates: document chunking → embedding → vector search
Uses local sentence-transformers (no API key required).
"""
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from app.services.embedding_service import LocalEmbeddingService
from app.services.vector_store import VectorStore
from app.services.chunk_service import chunk_document, chunk_metadata
from app.config import settings


class RAGService:
    """
    RAG service that indexes knowledge items and enables semantic search.

    Flow:
    1. index_knowledge():  chunk → embed → store in ChromaDB
    2. search():           embed query → ChromaDB similarity search → return results
    """

    def __init__(self, persist_dir: Optional[str] = None):
        self.embedder = LocalEmbeddingService()
        self.vector_store = VectorStore(
            persist_dir=persist_dir or settings.CHROMA_PERSIST_DIR,
        )

    def index_knowledge(
        self,
        knowledge_id: int,
        title: str,
        content: str,
        category: Optional[str] = None,
    ) -> int:
        """
        Index a knowledge item: chunk + embed + store.

        Args:
            knowledge_id: The knowledge item's database ID.
            title: The item's title.
            content: The item's content body.
            category: Optional category string.

        Returns:
            Number of chunks indexed.
        """
        # Step 1: Build full text from title + content
        full_text = f"{title}\n{content}"

        # Step 2: Chunk the document
        chunks = chunk_document(full_text, chunk_size=500, overlap=50)
        if not chunks:
            return 0

        # Step 3: Generate embeddings
        embeddings = self.embedder.embed_batch(chunks)

        # Step 4: Build metadata
        metadatas = chunk_metadata(knowledge_id, chunks)
        for meta in metadatas:
            meta["title"] = title
            meta["category"] = category or ""

        # Step 5: Remove old chunks for this knowledge_id (re-index)
        self.vector_store.delete_by_knowledge_id(knowledge_id)

        # Step 6: Store new chunks
        self.vector_store.add_chunks(
            knowledge_id=knowledge_id,
            chunk_texts=chunks,
            embeddings=embeddings,
            metadatas=metadatas,
        )
        return len(chunks)

    def remove_knowledge(self, knowledge_id: int) -> int:
        """
        Remove all chunks for a knowledge item from the vector store.

        Args:
            knowledge_id: The knowledge item's database ID.

        Returns:
            Number of chunks removed.
        """
        return self.vector_store.delete_by_knowledge_id(knowledge_id)

    def search(
        self,
        query: str,
        top_k: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Semantic search: embed query → retrieve similar chunks.

        Args:
            query: The search query text.
            top_k: Number of top results.

        Returns:
            List of result dicts with keys: id, document, metadata, score.
        """
        # Step 1: Embed the query
        query_embedding = self.embedder.embed_query(query)

        # Step 2: Search vector store
        results = self.vector_store.search(query_embedding, top_k=top_k)

        return results

    def reindex_all(self, db: Session) -> dict:
        """
        Re-index all knowledge items from the database.
        Used for bulk re-indexing or initial setup.

        Args:
            db: SQLAlchemy database session.

        Returns:
            Dict with total indexed count.
        """
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

        return {
            "items_indexed": len(items),
            "chunks_created": total_chunks,
        }