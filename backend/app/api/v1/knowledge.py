"""
Knowledge CRUD API Routes — with private/shared visibility.
Users see their own items + all shared items. Only the creator can delete.
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, File, UploadFile, Form
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.database import get_db
from app.models.knowledge import KnowledgeItem, Visibility
from app.models.user import User
from app.schemas.knowledge import (
    KnowledgeItemCreate,
    KnowledgeItemUpdate,
    KnowledgeItemResponse,
    KnowledgeItemList,
    FileParseResult,
)
from app.services.langchain_rag import LangChainRAGService
from app.services.file_parser import FileParser
from app.config import settings
from app.api.v1.auth import get_current_user

router = APIRouter()


def get_rag() -> LangChainRAGService:
    """Dependency to get LangChainRAGService instance."""
    return LangChainRAGService(
        persist_dir=settings.CHROMA_PERSIST_DIR,
        enable_reranker=True,
        enable_cache=True,
    )


def _visibility_filter(user_id: int):
    """Return SQLAlchemy filter for items visible to a user."""
    return or_(
        KnowledgeItem.created_by == user_id,
        KnowledgeItem.visibility == Visibility.SHARED,
    )


@router.get("/", response_model=KnowledgeItemList)
async def list_knowledge(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    category: Optional[str] = None,
    status: Optional[str] = None,
    search: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get a paginated list of knowledge items visible to the current user."""
    query = db.query(KnowledgeItem).filter(
        _visibility_filter(current_user.id)
    )

    if category:
        query = query.filter(KnowledgeItem.category == category)
    if status:
        query = query.filter(KnowledgeItem.status == status)
    if search:
        query = query.filter(
            KnowledgeItem.title.contains(search)
            | KnowledgeItem.content.contains(search)
        )

    total = query.count()
    items = query.order_by(KnowledgeItem.updated_at.desc()) \
                 .offset((page - 1) * page_size) \
                 .limit(page_size) \
                 .all()

    return KnowledgeItemList(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{item_id}", response_model=KnowledgeItemResponse)
async def get_knowledge(
    item_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get a single knowledge item by ID (must be visible to user)."""
    item = db.query(KnowledgeItem).filter(
        KnowledgeItem.id == item_id,
        _visibility_filter(current_user.id),
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="Knowledge item not found")
    return item


@router.post("/", response_model=KnowledgeItemResponse, status_code=201)
async def create_knowledge(
    item: KnowledgeItemCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new knowledge item. Indexing runs in background."""
    db_item = KnowledgeItem(
        **item.model_dump(),
        created_by=current_user.id,
    )
    db.add(db_item)
    db.commit()
    db.refresh(db_item)

    # Background indexing — don't block the response
    import threading
    def _bg_index(item_id: int):
        try:
            rag = get_rag()
            rag.index_knowledge(
                knowledge_id=item_id,
                title=db_item.title,
                content=db_item.content,
                category=db_item.category,
            )
        except Exception:
            pass
    threading.Thread(target=_bg_index, args=(db_item.id,), daemon=True).start()

    return db_item


@router.put("/{item_id}", response_model=KnowledgeItemResponse)
async def update_knowledge(
    item_id: int,
    item: KnowledgeItemUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update an existing knowledge item (creator or shared) and re-index it."""
    db_item = db.query(KnowledgeItem).filter(
        KnowledgeItem.id == item_id,
        _visibility_filter(current_user.id),
    ).first()
    if not db_item:
        raise HTTPException(status_code=404, detail="Knowledge item not found")

    # Only the creator can change visibility or delete
    update_data = item.model_dump(exclude_unset=True)

    # Only creator can change visibility
    if "visibility" in update_data and db_item.created_by != current_user.id:
        raise HTTPException(status_code=403, detail="Only the creator can change visibility")

    for key, value in update_data.items():
        setattr(db_item, key, value)

    db.commit()
    db.refresh(db_item)

    try:
        rag = get_rag()
        rag.index_knowledge(
            knowledge_id=db_item.id,
            title=db_item.title,
            content=db_item.content,
            category=db_item.category,
        )
    except Exception:
        pass

    return db_item


@router.post("/parse-file", response_model=FileParseResult, status_code=200)
async def parse_file(
    file: UploadFile = File(...),
):
    """
    Parse an uploaded file (.txt, .md, .pdf, .docx) and return the extracted content.
    Does NOT save to the database — the user can preview and then click Save to persist.
    """
    if not FileParser.is_supported(file.filename or ""):
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type. Supported: {FileParser.SUPPORTED_EXTENSIONS}",
        )

    content_bytes = await file.read()
    if not content_bytes:
        raise HTTPException(status_code=400, detail="Empty file")

    try:
        parsed = FileParser.parse(file.filename or "upload", content_bytes)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"File parsing failed: {str(e)}")

    return FileParseResult(
        title=parsed["title"],
        content=parsed["content"],
        file_type=parsed["file_type"],
        file_size=parsed["file_size"],
    )


@router.post("/upload", response_model=KnowledgeItemResponse, status_code=201)
async def upload_knowledge(
    file: UploadFile = File(...),
    category: Optional[str] = Form(None),
    tags: Optional[str] = Form(None),
    source: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Upload a file and create a knowledge item directly.
    """
    if not FileParser.is_supported(file.filename or ""):
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type. Supported: {FileParser.SUPPORTED_EXTENSIONS}",
        )

    content_bytes = await file.read()
    if not content_bytes:
        raise HTTPException(status_code=400, detail="Empty file")

    try:
        parsed = FileParser.parse(file.filename or "upload", content_bytes)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"File parsing failed: {str(e)}")

    db_item = KnowledgeItem(
        title=parsed["title"],
        content=parsed["content"],
        category=category,
        tags=tags,
        source=source or file.filename,
        created_by=current_user.id,
    )
    db.add(db_item)
    db.commit()
    db.refresh(db_item)

    _id, _title, _content, _category = db_item.id, db_item.title, db_item.content, db_item.category
    def _bg_index():
        try:
            rag = get_rag()
            rag.index_knowledge(_id, _title, _content, _category)
        except Exception:
            pass
    import threading
    threading.Thread(target=_bg_index, daemon=True).start()

    return db_item


@router.delete("/{item_id}", status_code=204)
async def delete_knowledge(
    item_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a knowledge item — only the creator can delete it."""
    db_item = db.query(KnowledgeItem).filter(
        KnowledgeItem.id == item_id,
        KnowledgeItem.created_by == current_user.id,
    ).first()
    if not db_item:
        raise HTTPException(status_code=404, detail="Knowledge item not found or not owned by you")

    try:
        rag = get_rag()
        rag.remove_knowledge(knowledge_id=item_id)
    except Exception:
        pass

    db.delete(db_item)
    db.commit()
    return None