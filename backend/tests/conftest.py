"""
Pytest configuration and fixtures for backend tests.
"""
from typing import Generator, Any
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.database import Base, get_db

# Use SQLite file for tests (not in-memory to avoid issues)
TEST_DATABASE_URL = "sqlite:///./test_knowledge_base.db"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db() -> Generator[Session, None, None]:
    """Override the get_db dependency for testing."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(autouse=True)
def setup_database():
    """Create tables before each test, drop after."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db() -> Generator[Session, None, None]:
    """Provide a database session for tests."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="session")
def app():
    """Lazy-load FastAPI app to avoid importing sentence-transformers at collection time."""
    from app.main import app as _app
    return _app


@pytest.fixture
def client(app: Any) -> Generator[TestClient, None, None]:
    """Provide a FastAPI TestClient with overridden DB dependency."""
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def sample_knowledge_data() -> dict:
    """Sample data for creating a knowledge item."""
    return {
        "title": "什么是微服务架构",
        "content": (
            "微服务架构是一种将应用程序构建为独立可部署服务集合的架构风格。"
            "每个服务运行在自己的进程中，并通过轻量级通信机制（通常是HTTP API）进行交互。"
            "微服务架构的优点包括：独立部署、技术多样性、可扩展性、故障隔离等。"
        ),
        "category": "技术",
        "tags": "微服务,架构,后端",
        "source": "https://example.com/microservices",
    }


@pytest.fixture
def sample_knowledge(db: Session, sample_knowledge_data: dict) -> Any:
    """Create and return a sample knowledge item in the database."""
    from app.models.knowledge import KnowledgeItem
    item = KnowledgeItem(**sample_knowledge_data)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@pytest.fixture
def sample_user_data() -> dict:
    """Sample data for creating a user."""
    return {
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpass123",
        "full_name": "Test User",
    }