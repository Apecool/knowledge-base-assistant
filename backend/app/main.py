"""
FastAPI Application Entry Point
"""
import time
import uuid
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.api.v1 import knowledge, search, auth, chat
from app.utils.logger import TraceLogger, trace_id_var
from app.utils.sentry import init_sentry
from app.database import init_db

import sentry_sdk

sentry_sdk.init(
    dsn=settings.SENTRY_DSN,
    # Add data like request headers and IP for users,
    # see https://docs.sentry.io/platforms/python/data-management/data-collected/ for more info
    send_default_pii=True,
    # Enable sending logs to Sentry
    enable_logs=True,
    # Set traces_sample_rate to 1.0 to capture 100%
    # of transactions for tracing.
    traces_sample_rate=1.0,
    # Set profile_session_sample_rate to 1.0 to profile 100%
    # of profile sessions.
    profile_session_sample_rate=1.0,
)

app = FastAPI(
    title="知识库助手 API",
    description="Knowledge Base Assistant Backend with RAG",
    version="2.0.0",
)

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    """Initialize services on application startup."""
    # Initialize Sentry (only if SENTRY_DSN configured)
    init_sentry()
    # Create database tables
    init_db()
    TraceLogger.info(f"App started: {settings.APP_NAME}, DB={settings.DATABASE_URL[:30]}...")


@app.middleware("http")
async def trace_middleware(request: Request, call_next):
    """
    Request tracing middleware.
    - Assigns/forwards trace_id from X-Trace-Id header
    - Logs request start/end with duration
    - Adds X-Trace-Id to response headers
    """
    trace_id = request.headers.get("X-Trace-Id", str(uuid.uuid4())[:8])
    trace_id_var.set(trace_id)

    start = time.time()
    TraceLogger.info(f"→ {request.method} {request.url.path}")

    try:
        response: Response = await call_next(request)
    except Exception as e:
        duration_ms = (time.time() - start) * 1000
        TraceLogger.error(f"✗ {request.method} {request.url.path} | error={str(e)} | {duration_ms:.1f}ms")
        raise

    duration_ms = (time.time() - start) * 1000
    TraceLogger.info(
        f"← {request.method} {request.url.path} | "
        f"status={response.status_code} | {duration_ms:.1f}ms"
    )
    response.headers["X-Trace-Id"] = trace_id
    response.headers["X-Duration-Ms"] = str(int(duration_ms))

    return response


# Register routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(knowledge.router, prefix="/api/v1/knowledge", tags=["Knowledge"])
app.include_router(search.router, prefix="/api/v1/search", tags=["Search"])
app.include_router(chat.router, prefix="/api/v1/chat", tags=["Chat"])


@app.get("/")
async def root():
    return {"message": "Knowledge Base Assistant API is running", "version": "2.0.0"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}