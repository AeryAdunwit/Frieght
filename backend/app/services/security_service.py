from __future__ import annotations

from fastapi import Request
from fastapi.responses import JSONResponse

from ..config import AppSettings
from ..logging_utils import get_logger
from ..models.responses import PublicConfigResponse

logger = get_logger(__name__)


class SecurityService:
    def __init__(self, settings: AppSettings):
        self.settings = settings

    def get_public_config(self) -> PublicConfigResponse:
        return PublicConfigResponse(
            admin_auth_enabled=bool(self.settings.admin_api_key),
            scg_recaptcha_site_key=self.settings.scg_recaptcha_site_key,
        )

    def admin_auth_error(self) -> JSONResponse:
        return JSONResponse(status_code=401, content={"error": "admin authorization required"})

    def require_admin_api_key(self, request: Request) -> JSONResponse | None:
        if not self.settings.admin_api_key:
            return None
        provided_key = request.headers.get("X-Admin-Key", "").strip()
        if provided_key == self.settings.admin_api_key:
            return None
        return self.admin_auth_error()

    def log_server_error(self, label: str, exc: Exception) -> None:
        logger.error("%s: %s", label, exc)

    def safe_error_response(self, message: str, status_code: int = 500) -> JSONResponse:
        return JSONResponse(status_code=status_code, content={"error": message})
