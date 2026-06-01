"""
Knowledge Item Database Model
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Enum as SAEnum
from app.database import Base
import enum


class KnowledgeStatus(str, enum.Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class KnowledgeItem(Base):
    __tablename__ = "knowledge_items"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String(255), nullable=False, index=True)
    content = Column(Text, nullable=False)
    category = Column(String(100), nullable=True, index=True)
    tags = Column(String(500), nullable=True)  # Comma-separated tags
    status = Column(SAEnum(KnowledgeStatus), default=KnowledgeStatus.DRAFT)
    source = Column(String(255), nullable=True)
    created_by = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<KnowledgeItem(id={self.id}, title='{self.title}')>"