"""
Knowledge Service - Business Logic Layer
"""
from typing import Optional, List
from sqlalchemy.orm import Session

from app.models.knowledge import KnowledgeItem
from app.schemas.knowledge import KnowledgeItemCreate, KnowledgeItemUpdate


class KnowledgeService:
    """Service layer for knowledge item operations."""

    @staticmethod
    def get_by_id(db: Session, item_id: int) -> Optional[KnowledgeItem]:
        return db.query(KnowledgeItem).filter(KnowledgeItem.id == item_id).first()

    @staticmethod
    def get_all(
        db: Session,
        skip: int = 0,
        limit: int = 20,
        category: Optional[str] = None,
        status: Optional[str] = None,
    ) -> tuple[List[KnowledgeItem], int]:
        query = db.query(KnowledgeItem)
        if category:
            query = query.filter(KnowledgeItem.category == category)
        if status:
            query = query.filter(KnowledgeItem.status == status)

        total = query.count()
        items = query.order_by(KnowledgeItem.updated_at.desc()) \
                     .offset(skip).limit(limit).all()
        return items, total

    @staticmethod
    def create(db: Session, data: KnowledgeItemCreate) -> KnowledgeItem:
        db_item = KnowledgeItem(**data.model_dump())
        db.add(db_item)
        db.commit()
        db.refresh(db_item)
        return db_item

    @staticmethod
    def update(db: Session, item_id: int, data: KnowledgeItemUpdate) -> Optional[KnowledgeItem]:
        db_item = KnowledgeService.get_by_id(db, item_id)
        if not db_item:
            return None
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_item, key, value)
        db.commit()
        db.refresh(db_item)
        return db_item

    @staticmethod
    def delete(db: Session, item_id: int) -> bool:
        db_item = KnowledgeService.get_by_id(db, item_id)
        if not db_item:
            return False
        db.delete(db_item)
        db.commit()
        return True

    @staticmethod
    def search(db: Session, query_text: str, limit: int = 10) -> List[KnowledgeItem]:
        return (
            db.query(KnowledgeItem)
            .filter(
                KnowledgeItem.title.contains(query_text)
                | KnowledgeItem.content.contains(query_text)
            )
            .order_by(KnowledgeItem.updated_at.desc())
            .limit(limit)
            .all()
        )