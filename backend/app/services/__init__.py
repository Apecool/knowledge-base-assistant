# Service imports - keep lazy to avoid triggering heavy imports (torch, chromadb)
# Use direct imports in your code: from app.services.knowledge_service import KnowledgeService

from app.services.knowledge_service import KnowledgeService

__all__ = [
    "KnowledgeService",
]