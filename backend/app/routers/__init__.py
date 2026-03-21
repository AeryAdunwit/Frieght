from .analytics import router as analytics_router
from .chat import router as chat_router
from .handoff import router as handoff_router
from .health import router as health_router
from .knowledge import router as knowledge_router
from .tracking import router as tracking_router

__all__ = [
    "analytics_router",
    "chat_router",
    "handoff_router",
    "health_router",
    "knowledge_router",
    "tracking_router",
]
