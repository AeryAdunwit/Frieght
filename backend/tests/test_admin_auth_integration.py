import os
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from backend.app.config import AppSettings
from backend.app.dependencies import (
    get_analytics_service,
    get_handoff_service,
    get_knowledge_admin_service,
    get_security_service,
    get_settings,
)
from backend.app.main import create_app


class _FakeAnalyticsService:
    def get_chat_overview(self, **kwargs):
        return {"ok": True, "filters": kwargs}


class _FakeHandoffService:
    def update_request(self, request, body):
        return {"ok": True, "handoff_id": body.handoff_id}


class _FakeKnowledgeAdminService:
    async def trigger_sync(self, request):
        return {"ok": True, "status": "queued", "run_id": 1}


class AdminAuthIntegrationTests(unittest.TestCase):
    def setUp(self):
        get_settings.cache_clear()
        get_security_service.cache_clear()
        get_analytics_service.cache_clear()
        get_handoff_service.cache_clear()
        get_knowledge_admin_service.cache_clear()

    def tearDown(self):
        get_settings.cache_clear()
        get_security_service.cache_clear()
        get_analytics_service.cache_clear()
        get_handoff_service.cache_clear()
        get_knowledge_admin_service.cache_clear()

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

    def test_handoff_update_requires_admin_key(self):
        with patch.dict(os.environ, {"ADMIN_API_KEY": "secret-123"}, clear=False):
            app = create_app(AppSettings())
            app.dependency_overrides[get_handoff_service] = lambda: _FakeHandoffService()
            client = TestClient(app)

            response = client.post("/analytics/handoff-update", json={"handoff_id": 1, "status": "closed"})

        self.assertEqual(response.status_code, 401)

    def test_knowledge_sync_accepts_valid_admin_key(self):
        with patch.dict(os.environ, {"ADMIN_API_KEY": "secret-123"}, clear=False):
            app = create_app(AppSettings())
            app.dependency_overrides[get_knowledge_admin_service] = lambda: _FakeKnowledgeAdminService()
            client = TestClient(app)

            response = client.post("/analytics/knowledge-sync", headers={"X-Admin-Key": "secret-123"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["ok"], True)


if __name__ == "__main__":
    unittest.main()
