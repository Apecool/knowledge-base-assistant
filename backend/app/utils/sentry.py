"""
Sentry Error Tracking — optional, only initializes if SENTRY_DSN is set.
"""
import logging
from app.config import settings

logger = logging.getLogger("kb_assistant")


def init_sentry():
    """Initialize Sentry SDK if SENTRY_DSN is configured."""
    dsn = settings.SENTRY_DSN
    if not dsn:
        logger.info("Sentry not configured (SENTRY_DSN is empty)")
        return

    try:
        import sentry_sdk
        from sentry_sdk.integrations.fastapi import FastApiIntegration
        from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
        from sentry_sdk.integrations.logging import LoggingIntegration

        sentry_sdk.init(
            dsn=dsn,
            integrations=[
                FastApiIntegration(),
                SqlalchemyIntegration(),
                LoggingIntegration(event_level=logging.WARNING),
            ],
            traces_sample_rate=0.1,  # Sample 10% in production
            environment="production" if not settings.DEBUG else "development",
            send_default_pii=False,
        )
        logger.info("Sentry initialized")
    except ImportError:
        logger.warning("sentry-sdk not installed, skipping Sentry init")