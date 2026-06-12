"""
Database Configuration and Session Management
Supports SQLite (dev) and PostgreSQL (production/Render/Supabase).
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from app.config import settings

# Determine connect_args based on database type
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}
elif settings.DATABASE_URL.startswith("postgresql"):
    connect_args = {}
    # For async PostgreSQL, add asyncpg driver prefix
    if "+asyncpg" not in settings.DATABASE_URL and "render" in settings.DATABASE_URL:
        pass  # Render provides sync URL
else:
    connect_args = {}

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True,  # Verify connections before using
    pool_size=5,         # Connection pool for PostgreSQL
    max_overflow=10,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """Dependency that provides a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Create all tables (idempotent — only creates missing tables)."""
    Base.metadata.create_all(bind=engine)

    # Migration: add missing columns for existing SQLite databases
    if settings.DATABASE_URL.startswith("sqlite"):
        from sqlalchemy import text
        with engine.connect() as conn:
            # Ensure visibility column exists on knowledge_items
            try:
                conn.execute(text("ALTER TABLE knowledge_items ADD COLUMN visibility VARCHAR(20) DEFAULT 'private'"))
                conn.commit()
            except Exception:
                pass  # Column already exists
            # Ensure created_by column exists on knowledge_items
            try:
                conn.execute(text("ALTER TABLE knowledge_items ADD COLUMN created_by INTEGER REFERENCES users(id)"))
                conn.commit()
            except Exception:
                pass  # Column already exists
