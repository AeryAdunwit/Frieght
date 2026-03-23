from __future__ import annotations

from ..config import AppSettings
from ..logging_utils import get_logger

logger = get_logger(__name__)
_monitoring_initialized = False


def init_monitoring(settings: AppSettings) -> bool:
    global _monitoring_initialized

    if _monitoring_initialized or not settings.sentry_dsn:
        return False

    try:
        import sentry_sdk
    except ImportError:
        logger.warning("Sentry SDK not installed; monitoring scaffold is inactive")
        return False

    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        environment=settings.sentry_environment,
        traces_sample_rate=max(0.0, min(settings.sentry_traces_sample_rate, 1.0)),
    )
    _monitoring_initialized = True
    logger.info("Sentry monitoring initialized")
    return True
