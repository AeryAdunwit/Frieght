from __future__ import annotations

from functools import lru_cache

from .config import AppSettings
from .repositories.analytics_repository import AnalyticsRepository
from .repositories.supabase_repository import SupabaseRepository
from .services.analytics_service import AnalyticsService
from .services.chat_analytics_helper_service import ChatAnalyticsHelperService
from .services.chat_service import ChatService
from .services.gemini_service import GeminiService
from .services.handoff_service import HandoffService
from .services.health_service import HealthService
from .services.intent_router import IntentRouterService
from .services.knowledge_admin_service import KnowledgeAdminService
from .services.knowledge_service import KnowledgeService
from .services.security_service import SecurityService
from .services.sheets_service import SheetsService
from .services.tracking_service import TrackingService


@lru_cache(maxsize=1)
def get_analytics_service() -> AnalyticsService:
    return AnalyticsService()


@lru_cache(maxsize=1)
def get_chat_analytics_helper_service() -> ChatAnalyticsHelperService:
    return ChatAnalyticsHelperService()


@lru_cache(maxsize=1)
def get_chat_service() -> ChatService:
    return ChatService()


@lru_cache(maxsize=1)
def get_settings() -> AppSettings:
    return AppSettings()


@lru_cache(maxsize=1)
def get_security_service() -> SecurityService:
    return SecurityService(get_settings())


@lru_cache(maxsize=1)
def get_supabase_repository() -> SupabaseRepository:
    return SupabaseRepository()


@lru_cache(maxsize=1)
def get_analytics_repository() -> AnalyticsRepository:
    return AnalyticsRepository()


@lru_cache(maxsize=1)
def get_handoff_service() -> HandoffService:
    return HandoffService(get_analytics_service(), get_security_service())


@lru_cache(maxsize=1)
def get_intent_router_service() -> IntentRouterService:
    return IntentRouterService()


@lru_cache(maxsize=1)
def get_tracking_service() -> TrackingService:
    return TrackingService()


@lru_cache(maxsize=1)
def get_sheets_service() -> SheetsService:
    return SheetsService()


@lru_cache(maxsize=1)
def get_knowledge_service() -> KnowledgeService:
    return KnowledgeService()


@lru_cache(maxsize=1)
def get_knowledge_admin_service() -> KnowledgeAdminService:
    return KnowledgeAdminService(get_analytics_service(), get_security_service())


@lru_cache(maxsize=1)
def get_gemini_service() -> GeminiService:
    return GeminiService()


@lru_cache(maxsize=1)
def get_health_service() -> HealthService:
    return HealthService()
