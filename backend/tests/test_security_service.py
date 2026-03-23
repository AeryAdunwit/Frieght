import os
import unittest
from unittest.mock import patch

from fastapi import HTTPException
from fastapi import Request

from backend.app.config import AppSettings
from backend.app.services.security_service import SecurityService


def _build_request(headers: dict[str, str] | None = None) -> Request:
    raw_headers = []
    for key, value in (headers or {}).items():
        raw_headers.append((key.lower().encode("latin-1"), value.encode("latin-1")))
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/analytics/chat-overview",
        "headers": raw_headers,
        "query_string": b"",
    }
    return Request(scope)


class SecurityServiceTests(unittest.TestCase):
    def test_public_config_defaults_to_admin_disabled(self):
        with patch.dict(os.environ, {}, clear=False):
            service = SecurityService(AppSettings())
            config = service.get_public_config()
        self.assertIn("admin_auth_enabled", config)
        self.assertIn("scg_recaptcha_site_key", config)

    def test_require_admin_key_returns_none_when_auth_disabled(self):
        with patch.dict(os.environ, {"ADMIN_API_KEY": ""}, clear=False):
            service = SecurityService(AppSettings())
            result = service.require_admin_api_key(_build_request())
        self.assertIsNone(result)

    def test_require_admin_key_rejects_missing_header(self):
        with patch.dict(os.environ, {"ADMIN_API_KEY": "secret-123"}, clear=False):
            service = SecurityService(AppSettings())
            response = service.require_admin_api_key(_build_request())
        self.assertIsNotNone(response)
        self.assertEqual(response.status_code, 401)

    def test_require_admin_key_accepts_correct_header(self):
        with patch.dict(os.environ, {"ADMIN_API_KEY": "secret-123"}, clear=False):
            service = SecurityService(AppSettings())
            response = service.require_admin_api_key(_build_request({"X-Admin-Key": "secret-123"}))
        self.assertIsNone(response)

    def test_require_admin_key_accepts_cookie_session(self):
        with patch.dict(
            os.environ,
            {"ADMIN_API_KEY": "secret-123", "ADMIN_SESSION_COOKIE_NAME": "frieght_admin_session"},
            clear=False,
        ):
            service = SecurityService(AppSettings())
            response = service.require_admin_api_key(_build_request({"Cookie": "frieght_admin_session=secret-123"}))
        self.assertIsNone(response)

    def test_ensure_admin_key_rejects_missing_header(self):
        with patch.dict(os.environ, {"ADMIN_API_KEY": "secret-123"}, clear=False):
            service = SecurityService(AppSettings())
            with self.assertRaises(HTTPException):
                service.ensure_admin_api_key(_build_request())

    def test_ensure_admin_key_accepts_compare_digest_path(self):
        with patch.dict(os.environ, {"ADMIN_API_KEY": "secret-123"}, clear=False):
            service = SecurityService(AppSettings())
            self.assertIsNone(service.ensure_admin_api_key(_build_request({"X-Admin-Key": "secret-123"})))

    def test_create_admin_session_sets_httponly_cookie(self):
        with patch.dict(
            os.environ,
            {"ADMIN_API_KEY": "secret-123", "ADMIN_SESSION_COOKIE_NAME": "frieght_admin_session"},
            clear=False,
        ):
            service = SecurityService(AppSettings())
            response = service.create_admin_session(_build_request(), "secret-123")

        self.assertEqual(response.status_code, 200)
        self.assertIn("HttpOnly", response.headers.get("set-cookie", ""))


if __name__ == "__main__":
    unittest.main()
