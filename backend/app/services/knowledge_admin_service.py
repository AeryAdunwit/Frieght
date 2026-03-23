from __future__ import annotations

from fastapi import Request
from fastapi.responses import JSONResponse

from ..config import AppSettings
from ..models.analytics import SheetApprovalPayload
from .analytics_service import AnalyticsService
from .security_service import SecurityService


class KnowledgeAdminService:
    def __init__(
        self,
        analytics_service: AnalyticsService | None = None,
        security_service: SecurityService | None = None,
    ) -> None:
        self.analytics_service = analytics_service or AnalyticsService()
        self.security_service = security_service or SecurityService(AppSettings())

    def _auth(self, request: Request) -> None:
        self.security_service.ensure_admin_api_key(request)

    async def trigger_sync(self, request: Request) -> JSONResponse:
        self._auth(request)
        return await self.analytics_service.trigger_knowledge_sync()

    async def approve_to_sheet(self, request: Request, body: SheetApprovalPayload) -> JSONResponse:
        self._auth(request)
        return await self.analytics_service.approve_to_sheet(body)

    def get_sheet_tab_link(self, request: Request, topic: str = "") -> JSONResponse:
        self._auth(request)
        return self.analytics_service.get_sheet_tab_link(topic)
