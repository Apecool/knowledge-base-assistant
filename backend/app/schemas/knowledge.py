"""
Knowledge Item Pydantic Schemas — with multi-tenant visibility support.
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class KnowledgeItemCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    content: str = Field(..., min_length=1)
    category: Optional[str] = None
    tags: Optional[str] = None
    source: Optional[str] = None
    visibility: str = Field("private", pattern=r"^(private|shared)$")


class KnowledgeItemUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    content: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[str] = None
    status: Optional[str] = None
    source: Optional[str] = None
    visibility: Optional[str] = Field(None, pattern=r"^(private|shared)$")


class KnowledgeItemResponse(BaseModel):
    id: int
    title: str
    content: str
    category: Optional[str] = None
    tags: Optional[str] = None
    status: str
    visibility: str
    source: Optional[str] = None
    created_by: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class KnowledgeItemList(BaseModel):
    items: List[KnowledgeItemResponse]
    total: int
    page: int
    page_size: int


class FileParseResult(BaseModel):
    """Result from parsing a file without saving it."""
    title: str
    content: str
    file_type: str
    file_size: int