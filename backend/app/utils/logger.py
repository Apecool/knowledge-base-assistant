"""
Structured logging with trace ID support for request tracing.
"""
import logging
import time
from contextvars import ContextVar
from typing import Optional

trace_id_var: ContextVar[str] = ContextVar('trace_id', default='')

# Custom formatter that includes trace_id
class TraceFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        trace_id = trace_id_var.get('')
        if trace_id:
            record.msg = f"[{trace_id}] {record.msg}"
        return super().format(record)

# Configure root logger
_handler = logging.StreamHandler()
_handler.setFormatter(TraceFormatter(
    '%(asctime)s | %(levelname)s | %(message)s'
))
logging.basicConfig(level=logging.INFO, handlers=[_handler])

logger = logging.getLogger("kb_assistant")


class TraceLogger:
    """Logger that automatically includes the current trace_id."""

    @staticmethod
    def get_trace_id() -> str:
        return trace_id_var.get('')

    @staticmethod
    def set_trace_id(trace_id: str):
        trace_id_var.set(trace_id)

    @staticmethod
    def info(msg: str, **kwargs):
        logger.info(msg, extra=kwargs)

    @staticmethod
    def error(msg: str, **kwargs):
        logger.error(msg, extra=kwargs)

    @staticmethod
    def warn(msg: str, **kwargs):
        logger.warning(msg, extra=kwargs)

    @staticmethod
    def duration(step_name: str, duration_ms: float, **kwargs):
        """Log a step duration for performance tracing."""
        logger.info(
            f"DURATION | {step_name}={duration_ms:.1f}ms",
            extra={"duration_ms": duration_ms, **kwargs},
        )

    @staticmethod
    def trace_rag(step: str, duration_ms: float, details: Optional[dict] = None):
        """Log RAG pipeline step timing."""
        extra = details or {}
        extra["rag_step"] = step
        extra["duration_ms"] = duration_ms
        logger.info(f"RAG | {step} | {duration_ms:.1f}ms", extra=extra)