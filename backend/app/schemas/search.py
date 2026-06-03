"""
Search-related Pydantic schemas for RAG and semantic search.
"""
from typing import List, Any, Dict
from pydantic import BaseModel, Field


class SemanticSearchQuery(BaseModel):
    """Query parameters for semantic search."""
    q: str = Field(..., min_length=1, description="Search query text")
    top_k: int = Field(5, ge=1, le=50, description="Number of top results")


class ChunkResult(BaseModel):
    """A single chunk result from semantic search."""
    id: str
    document: str
    metadata: Dict[str, Any]
    score: float

    class Config:
        from_attributes = True


class SemanticSearchResponse(BaseModel):
    """Response from semantic search."""
    query: str
    results: List[ChunkResult]
    total: int


class ReindexResponse(BaseModel):
    """Response from re-indexing operation."""
    items_indexed: int
    chunks_created: int
    message: str = "Re-indexing completed successfully"