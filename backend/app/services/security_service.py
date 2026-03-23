from __future__ import annotations

import hmac

from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse

from ..config import AppSettings
from ..logging_utils import get_logger
from ..models.responses import PublicConfigResponse

logger = get_logger(__name__)


class SecurityService:
    def __init__(self, settings: AppSettings):
        self.settings = settings

    def _get_cookie_security(self, request: Request) -> tuple[bool, str]:
        forwarded_proto = (request.headers.get("x-forwarded-proto", "") or "").split(",")[0].strip().lower()
        is_secure = request.url.scheme == "https" or forwarded_proto == "https"
        same_site = "none" if is_secure else "lax"
        return is_secure, same_site

    def _get_request_admin_key(self, request: Request) -> str:
        header_key = request.headers.get("X-Admin-Key", "").strip()
        if header_key:
            return header_key
        return (request.cookies.get(self.settings.admin_session_cookie_name, "") or "").strip()

    def is_valid_admin_api_key(self, provided_key: str) -> bool:
        expected_key = self.settings.admin_api_key
        normalized_key = (provided_key or "").strip()
        return bool(normalized_key and expected_key and hmac.compare_digest(normalized_key, expected_key))

    def get_public_config(self) -> dict[str, str | bool]:
        return PublicConfigResponse(
            admin_auth_enabled=bool(self.settings.admin_api_key),
            scg_recaptcha_site_key=self.settings.scg_recaptcha_site_key,
        ).model_dump()

    def admin_auth_error(self) -> JSONResponse:
        return JSONResponse(status_code=401, content={"error": "admin authorization required"})

    def ensure_admin_api_key(self, request: Request) -> None:
        if not self.settings.admin_api_key:
            return
        provided_key = self._get_request_admin_key(request)
        if self.is_valid_admin_api_key(provided_key):
            return
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="admin authorization required")

    def create_admin_session(self, request: Request, provided_key: str) -> JSONResponse:
        if self.settings.admin_api_key and not self.is_valid_admin_api_key(provided_key):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="admin authorization required")

        response = JSONResponse(status_code=200, content={"ok": True, "authenticated": True})
        secure, same_site = self._get_cookie_security(request)
        response.set_cookie(
            key=self.settings.admin_session_cookie_name,
            value=(provided_key or "").strip(),
            max_age=max(300, int(self.settings.admin_session_max_age_seconds or 28800)),
            httponly=True,
            secure=secure,
            samesite=same_site,
            path="/",
        )
        return response

    def clear_admin_session(self, request: Request) -> JSONResponse:
        response = JSONResponse(status_code=200, content={"ok": True, "authenticated": False})
        secure, same_site = self._get_cookie_security(request)
        response.delete_cookie(
            key=self.settings.admin_session_cookie_name,
            path="/",
            secure=secure,
            samesite=same_site,
        )
        return response

    def require_admin_api_key(self, request: Request) -> JSONResponse | None:
        try:
            self.ensure_admin_api_key(request)
            return None
        except HTTPException:
            return self.admin_auth_error()

    def log_server_error(self, label: str, exc: Exception) -> None:
        logger.error("%s: %s", label, exc)

    def safe_error_response(self, message: str, status_code: int = 500) -> JSONResponse:
        return JSONResponse(status_code=status_code, content={"error": message})
