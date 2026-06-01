"""
Chat API Pydantic schemas for multi-turn conversation and streaming.
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Request body for chat endpoint."""
    session_id: str = Field(..., description="Client-generated session ID for multi-turn context")
    query: str = Field(..., min_length=1, description="User's message")
    stream: bool = Field(True, description="Whether to stream the response via SSE")
    top_k: int = Field(5, ge=1, le=20, description="Number of context chunks to retrieve")


class ChatMessageSchema(BaseModel):
    """A single chat message in the response."""
    role: str  # "user" or "assistant"
    content: str
    timestamp: float


class ChatSessionSchema(BaseModel):
    """Chat session metadata."""
    session_id: str
    message_count: int
    created_at: float
    updated_at: float


class ChatSessionDetail(BaseModel):
    """Full session detail with messages."""
    session_id: str
    message_count: int
    created_at: float
    updated_at: float
    messages: List[ChatMessageSchema]


class ChatResponse(BaseModel):
    """Response from non-streaming chat."""
    session_id: str
    answer: str
    sources: List[Dict[str, Any]] = []
    message_count: int


class CacheStats(BaseModel):
    """Semantic cache statistics."""
    total_entries: int
    active_entries: int
    expired_entries: int
    threshold: float
    ttl_seconds: int
    max_size: int