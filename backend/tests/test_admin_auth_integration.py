import os
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from backend.app.config import AppSettings
from backend.app.dependencies import get_analytics_service, get_security_service, get_settings
from backend.app.main import create_app


class _FakeAnalyticsService:
    def get_chat_overview(self, **kwargs):
        return {"ok": True, "filters": kwargs}


class AdminAuthIntegrationTests(unittest.TestCase):
    def setUp(self):
        get_settings.cache_clear()
        get_security_service.cache_clear()
        get_analytics_service.cache_clear()

    def tearDown(self):
        get_settings.cache_clear()
        get_security_service.cache_clear()
        get_analytics_service.cache_clear()

    def test_chat_overview_requires_admin_key(self):
        with patch.dict(os.environ, {"ADMIN_API_KEY": "secret-123"}, clear=False):
            app = create_app(AppSettings())
            client = TestClient(app)

            response = client.get("/analytics/chat-overview")

        self.assertEqual(response.status_code, 401)

    def test_chat_overview_accepts_valid_admin_key(self):
        with patch.dict(os.environ, {"ADMIN_API_KEY": "secret-123"}, clear=False):
            app = create_app(AppSettings())
            app.dependency_overrides[get_analytics_service] = lambda: _FakeAnalyticsService()
            client = TestClient(app)

            response = client.get("/analytics/chat-overview", headers={"X-Admin-Key": "secret-123"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["ok"], True)


if __name__ == "__main__":
    unittest.main()
