import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from backend.app.main import app as app_scaffold
from backend.app.models.chat import PublicChatPayload
from backend.main import app as legacy_app
from backend.main import chat as legacy_chat


class MainCompatTests(unittest.IsolatedAsyncioTestCase):
    def test_legacy_entrypoint_reuses_app_scaffold(self):
        self.assertIs(legacy_app, app_scaffold)

    async def test_legacy_chat_wrapper_delegates_to_chat_service(self):
        request = SimpleNamespace()
        body = PublicChatPayload(message="สวัสดี", history=[], session_id="", response_mode="quick")
        expected_response = object()
        mock_service = AsyncMock()
        mock_service.handle_chat.return_value = expected_response

        with patch("backend.app.dependencies.get_chat_service", return_value=mock_service):
            response = await legacy_chat(request, body)

        mock_service.handle_chat.assert_awaited_once_with(request, body)
        self.assertIs(response, expected_response)


if __name__ == "__main__":
    unittest.main()
