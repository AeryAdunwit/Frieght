from __future__ import annotations

from fastapi import Request

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
        self.security_service = security_service or SecurityService()

    def _auth(self, request: Request):
        return self.security_service.require_admin_api_key(request)

    async def trigger_sync(self, request: Request):
        auth_error = self._auth(request)
        if auth_error:
            return auth_error
        return await self.analytics_service.trigger_knowledge_sync()

    async def approve_to_sheet(self, request: Request, body: SheetApprovalPayload):
        auth_error = self._auth(request)
        if auth_error:
            return auth_error
        return await self.analytics_service.approve_to_sheet(body)

    def get_sheet_tab_link(self, request: Request, topic: str = ""):
        auth_error = self._auth(request)
        if auth_error:
            return auth_error
        return self.analytics_service.get_sheet_tab_link(topic)
