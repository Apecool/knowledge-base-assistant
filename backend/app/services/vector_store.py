"""
Vector Store Service — ChromaDB wrapper for persistent vector storage.
Handles CRUD operations on document embeddings.
"""
from typing import List, Optional, Dict, Any
import chromadb
from chromadb.config import Settings


class VectorStore:
    """ChromaDB-based vector store for knowledge document chunks."""

    def __init__(self, persist_dir: str = "./chroma_db"):
        self.persist_dir = persist_dir
        self.collection_name = "knowledge_chunks"
        self._client = None
        self._collection = None

    def _get_client(self):
        if self._client is None:
            self._client = chromadb.PersistentClient(
                path=self.persist_dir,
                settings=Settings(anonymized_telemetry=False),
            )
        return self._client

    def _get_collection(self):
        if self._collection is None:
            client = self._get_client()
            try:
                self._collection = client.get_collection(self.collection_name)
            except (ValueError, chromadb.errors.NotFoundError):
                self._collection = client.create_collection(
                    name=self.collection_name,
                    metadata={"hnsw:space": "cosine"},
                )
        return self._collection

    def add_chunks(
        self,
        knowledge_id: int,
        chunk_texts: List[str],
        embeddings: List[List[float]],
        metadatas: Optional[List[Dict[str, Any]]] = None,
    ) -> int:
        """
        Add document chunks to the vector store.

        Args:
            knowledge_id: The parent knowledge item ID.
            chunk_texts: List of chunk text strings.
            embeddings: List of embedding vectors for each chunk.
            metadatas: Optional list of metadata dicts per chunk.

        Returns:
            Number of chunks added.
        """
        if not chunk_texts:
            return 0

        if metadatas is None:
            metadatas = [{"knowledge_id": knowledge_id, "chunk_index": i}
                         for i in range(len(chunk_texts))]

        ids = [f"kb_{knowledge_id}_chunk_{i}" for i in range(len(chunk_texts))]

        collection = self._get_collection()
        collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=chunk_texts,
            metadatas=metadatas,
        )
        return len(chunk_texts)

    def search(
        self,
        query_embedding: List[float],
        top_k: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Search for the most similar chunks given a query embedding.

        Args:
            query_embedding: The embedding vector of the query.
            top_k: Number of top results to return.

        Returns:
            List of result dicts with keys: id, document, metadata, distance.
        """
        collection = self._get_collection()
        # If collection is empty, return empty
        if collection.count() == 0:
            return []
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=min(top_k, 100),
            include=["documents", "metadatas", "distances"],
        )

        formatted = []
        if results["ids"] and results["ids"][0]:
            for i in range(len(results["ids"][0])):
                formatted.append({
                    "id": results["ids"][0][i],
                    "document": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i],
                    "score": 1 - results["distances"][0][i],  # cosine → similarity
                })
        return formatted

    def delete_by_knowledge_id(self, knowledge_id: int) -> int:
        """
        Delete all chunks belonging to a specific knowledge item.

        Args:
            knowledge_id: The knowledge item ID to delete.

        Returns:
            Number of chunks deleted.
        """
        collection = self._get_collection()
        # Get all chunk IDs for this knowledge_id
        results = collection.get(
            where={"knowledge_id": knowledge_id},
        )
        ids = results.get("ids", [])
        if ids:
            collection.delete(ids=ids)
        return len(ids)

    def count_chunks(self, knowledge_id: Optional[int] = None) -> int:
        """Count chunks, optionally filtered by knowledge_id."""
        collection = self._get_collection()
        if knowledge_id is not None:
            results = collection.get(where={"knowledge_id": knowledge_id})
            return len(results.get("ids", []))
        return collection.count()

    def get_all_knowledge_ids(self) -> List[int]:
        """Get all unique knowledge_ids stored in the vector store."""
        collection = self._get_collection()
        results = collection.get()
        ids = set()
        for meta in results.get("metadatas", []):
            kid = meta.get("knowledge_id")
            if kid is not None:
                ids.add(kid)
        return sorted(ids)