"""
Semantic Cache — Cache LLM responses based on query embedding similarity.
Reuses cached responses for semantically similar queries (threshold > 0.95).
"""
import time
import hashlib
from typing import List, Optional, Dict, Any
from app.services.embedding_service import LocalEmbeddingService


def cosine_similarity(a: List[float], b: List[float]) -> float:
    """Compute cosine similarity between two vectors."""
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = sum(x * x for x in a) ** 0.5
    norm_b = sum(x * x for x in b) ** 0.5
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


class SemanticCache:
    """
    Semantic cache that uses embedding similarity to detect cache hits.

    Cache entries expire after TTL. The cache is stored in-memory.
    For production, consider Redis or a persistent DB backend.

    Args:
        threshold: Cosine similarity threshold for cache hit (0.0-1.0).
        ttl_seconds: Time-to-live for cache entries in seconds.
        max_size: Maximum number of cache entries.
    """

    def __init__(
        self,
        threshold: float = 0.95,
        ttl_seconds: int = 3600,
        max_size: int = 1000,
    ):
        self.threshold = threshold
        self.ttl = ttl_seconds
        self.max_size = max_size
        self._cache: List[Dict[str, Any]] = []
        self._embedder = LocalEmbeddingService()

    def get(self, query: str) -> Optional[str]:
        """
        Look up a query in the semantic cache.

        Args:
            query: The search query text.

        Returns:
            Cached response string if found, None otherwise.
        """
        if not self._cache:
            return None

        query_emb = self._embedder.embed_query(query)
        now = time.time()

        for entry in self._cache:
            # Check expiry
            if now - entry["timestamp"] > self.ttl:
                continue

            sim = cosine_similarity(query_emb, entry["embedding"])
            if sim >= self.threshold:
                return entry["response"]

        return None

    def set(self, query: str, response: str):
        """
        Store a query-response pair in the cache.

        Args:
            query: The original query text.
            response: The response to cache.
        """
        # Evict if at capacity
        if len(self._cache) >= self.max_size:
            self._cache.pop(0)

        embedding = self._embedder.embed_query(query)
        self._cache.append({
            "embedding": embedding,
            "query": query,
            "response": response,
            "timestamp": time.time(),
        })

    def clear(self):
        """Clear the entire cache."""
        self._cache.clear()

    @property
    def size(self) -> int:
        """Current number of cache entries."""
        return len(self._cache)

    def get_stats(self) -> dict:
        """Get cache statistics."""
        now = time.time()
        active = sum(1 for e in self._cache if now - e["timestamp"] <= self.ttl)
        expired = self.size - active
        return {
            "total_entries": self.size,
            "active_entries": active,
            "expired_entries": expired,
            "threshold": self.threshold,
            "ttl_seconds": self.ttl,
            "max_size": self.max_size,
        }