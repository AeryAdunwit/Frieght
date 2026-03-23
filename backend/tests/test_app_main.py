import os
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from backend.app.config import AppSettings
from backend.app.main import build_allowed_origins, create_app


class AppMainTests(unittest.TestCase):
    def test_build_allowed_origins_uses_frontend_and_additional_origins(self):
        with patch.dict(
            os.environ,
            {
                "FRONTEND_URL": "https://example.com",
                "ADDITIONAL_CORS_ORIGINS": "https://admin.example.com, https://ops.example.com",
            },
            clear=False,
        ):
            settings = AppSettings()
            origins = build_allowed_origins(settings)

        self.assertEqual(
            origins,
            [
                "https://example.com",
                "https://admin.example.com",
                "https://ops.example.com",
            ],
        )

    def test_create_app_registers_limiter_and_routes(self):
        app = create_app(AppSettings())

        self.assertTrue(hasattr(app.state, "limiter"))
        routes = {route.path for route in app.routes}
        self.assertIn("/health", routes)
        self.assertIn("/chat", routes)
        self.assertIn("/analytics/chat-overview", routes)

    def test_create_app_blocks_unsafe_cross_origin_requests(self):
        app = create_app(AppSettings())
        client = TestClient(app)

        response = client.post(
            "/analytics/chat-feedback",
            json={"user_message": "x", "bot_reply": "y", "feedback_value": "helpful", "session_id": "s"},
            headers={"Origin": "https://evil.example.com"},
        )

        self.assertEqual(response.status_code, 403)


if __name__ == "__main__":
    unittest.main()
