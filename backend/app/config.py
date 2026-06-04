"""
Application Configuration
Reads from backend/.env automatically via pydantic-settings.
Only template with defaults — real values go in .env (gitignored).
"""
from pydantic_settings import BaseSettings
from typing import List, Union
from pydantic import field_validator


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "知识库助手"
    DEBUG: bool = False

    # Database — SQLite (dev) or PostgreSQL (production)
    DATABASE_URL: str = "sqlite:///./knowledge_base.db"
    # Supabase/PostgreSQL examples:
    # DATABASE_URL: str = "postgresql+psycopg2://user:password@host:5432/knowledge_base"
    # DATABASE_URL: str = "postgresql://postgres:password@db.xxxxx.supabase.co:5432/postgres"

    # CORS — add your Vercel/Netlify domain in production
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "https://kb-assistant.vercel.app",
        "https://knowledge-base-assistant-sandy.vercel.app"
    ]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        # If it comes in from the environment as a plain string, split it by commas
        if isinstance(v, str):
            # Handle JSON array format just in case
            if v.startswith("[") and v.endswith("]"):
                import json
                return json.loads(v)
            return [item.strip() for item in v.split(",") if item.strip()]
        return v
    # JWT Authentication
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # LLM Provider — "openai" or "deepseek"
    LLM_PROVIDER: str = "openai"

    # OpenAI
    OPENAI_API_KEY: str = ""
    OPENAI_API_BASE: str = "https://api.openai.com/v1"
    OPENAI_MODEL: str = "gpt-4o-mini"

    # DeepSeek
    DEEPSEEK_API_KEY: str = ""
    DEEPSEEK_API_BASE: str = "https://api.deepseek.com/v1"
    DEEPSEEK_MODEL: str = "deepseek-chat"

    # Vector DB (ChromaDB)
    CHROMA_PERSIST_DIR: str = "./chroma_db"

    # Monitoring
    SENTRY_DSN: str = ""           # https://sentry.io — error tracking
    LOGTAIL_TOKEN: str = ""        # https://betterstack.com/logtail — log management

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()