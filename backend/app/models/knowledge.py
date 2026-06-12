"""
Knowledge Item Database Model — with private/shared visibility support.
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class Visibility:
    PRIVATE = "private"
    SHARED = "shared"


class KnowledgeItem(Base):
    __tablename__ = "knowledge_items"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String(255), nullable=False, index=True)
    content = Column(Text, nullable=False)
    category = Column(String(100), nullable=True, index=True)
    tags = Column(String(500), nullable=True)
    status = Column(String(20), default="draft")  # draft, published, archived
    visibility = Column(String(20), default=Visibility.PRIVATE)  # private, shared
    source = Column(String(255), nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    creator = relationship("User", backref="knowledge_items")

    def __repr__(self):
        return f"<KnowledgeItem(id={self.id}, title='{self.title}', visibility='{self.visibility}')>"