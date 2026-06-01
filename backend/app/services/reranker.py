"""
Cross-encoder Reranker — Improves RAG retrieval quality by re-ranking
the top-N results from the bi-encoder (sentence-transformers) using
a more powerful cross-encoder model.
"""
from typing import List, Dict, Any, Optional


class Reranker:
    """
    Cross-encoder based reranker for improving retrieval quality.

    Uses BAAI/bge-reranker-v2-m3 for Chinese/English mixed content.
    Falls back to a smaller model if the primary is not available.

    The cross-encoder evaluates query-document pairs directly,
    producing more accurate relevance scores than bi-encoder cosine similarity.
    """

    # Default model: good for Chinese + English
    DEFAULT_MODEL = "BAAI/bge-reranker-v2-m3"
    # Fallback: smaller, faster
    FALLBACK_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"

    def __init__(self, model_name: Optional[str] = None):
        self.model_name = model_name or self.DEFAULT_MODEL
        self._model = None
        self._load_error = None

    def _get_model(self):
        """Lazy-load the cross-encoder model."""
        if self._model is not None:
            return self._model

        try:
            from sentence_transformers import CrossEncoder
            self._model = CrossEncoder(self.model_name)
        except Exception as e:
            self._load_error = str(e)
            # Try fallback model
            try:
                from sentence_transformers import CrossEncoder
                print(f"Reranker: fallback to {self.FALLBACK_MODEL}")
                self._model = CrossEncoder(self.FALLBACK_MODEL)
            except Exception as e2:
                raise RuntimeError(
                    f"Failed to load reranker model: {e}. "
                    f"Fallback also failed: {e2}. "
                    "Reranking will be disabled."
                )
        return self._model

    def rerank(
        self,
        query: str,
        results: List[Dict[str, Any]],
        top_k: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Re-rank search results using cross-encoder.

        Args:
            query: The original search query.
            results: List of result dicts, each must have 'document' key.
            top_k: Number of top results to return after re-ranking.

        Returns:
            Re-ranked results list (sorted by score descending),
            with updated 'score' field from cross-encoder.
        """
        if not results:
            return []

        model = self._get_model()
        documents = [
            r.get("document", r.get("text", "")) for r in results
        ]

        # Create query-document pairs
        pairs = [[query, doc] for doc in documents]

        # Get cross-encoder scores
        scores = model.predict(pairs)

        # Attach scores and sort
        for i, result in enumerate(results):
            result["score"] = float(scores[i])
            result["rerank_score"] = float(scores[i])

        # Sort by score descending
        reranked = sorted(results, key=lambda x: x["score"], reverse=True)

        return reranked[:top_k]

    @property
    def is_available(self) -> bool:
        """Check if the reranker model loaded successfully."""
        try:
            self._get_model()
            return True
        except Exception:
            return False