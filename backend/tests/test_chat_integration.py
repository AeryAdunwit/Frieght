import os
import unittest
from unittest.mock import patch

from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient

from backend.app.config import AppSettings
from backend.app.dependencies import get_chat_service, get_security_service, get_settings
from backend.app.main import create_app


class _FakeChatService:
    async def handle_chat(self, request, body):
        return JSONResponse(
            status_code=200,
            content={
                "ok": True,
                "message": body.message,
                "session_id": body.session_id,
                "response_mode": body.response_mode,
            },
        )


class ChatIntegrationTests(unittest.TestCase):
    def setUp(self):
        get_settings.cache_clear()
        get_security_service.cache_clear()
        get_chat_service.cache_clear()

    def tearDown(self):
        get_settings.cache_clear()
        get_security_service.cache_clear()
        get_chat_service.cache_clear()

    def test_chat_route_accepts_payload_and_uses_dependency_override(self):
        with patch.dict(os.environ, {"ADMIN_API_KEY": ""}, clear=False):
            app = create_app(AppSettings())
            app.dependency_overrides[get_chat_service] = lambda: _FakeChatService()
            client = TestClient(app)

            response = client.post(
                "/chat",
                json={
                    "message": "สวัสดี",
                    "history": [{"role": "user", "content": "ก่อนหน้า"}],
                    "session_id": "chat-session-1",
                    "response_mode": "detail",
                },
            )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload["ok"])
        self.assertEqual(payload["message"], "สวัสดี")
        self.assertEqual(payload["session_id"], "chat-session-1")
        self.assertEqual(payload["response_mode"], "detail")

    def test_chat_route_rejects_invalid_payload(self):
        with patch.dict(os.environ, {"ADMIN_API_KEY": ""}, clear=False):
            app = create_app(AppSettings())
            app.dependency_overrides[get_chat_service] = lambda: _FakeChatService()
            client = TestClient(app)

            response = client.post("/chat", json={"history": []})

        self.assertEqual(response.status_code, 422)


if __name__ == "__main__":
    unittest.main()
