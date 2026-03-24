import os
import unittest
from unittest.mock import AsyncMock, Mock, patch

from fastapi import Request
from fastapi.responses import StreamingResponse

from backend.app.models.chat import PublicChatPayload
from backend.app.services.chat_service import ChatService


def _build_request() -> Request:
    return Request(
        {
            "type": "http",
            "asgi": {"version": "3.0"},
            "method": "POST",
            "path": "/chat",
            "headers": [],
            "client": ("127.0.0.1", 5000),
            "server": ("testserver", 80),
            "scheme": "http",
            "query_string": b"",
        }
    )


async def _read_stream(response: StreamingResponse) -> str:
    chunks: list[str] = []
    async for chunk in response.body_iterator:
        if isinstance(chunk, bytes):
            chunks.append(chunk.decode("utf-8"))
        else:
            chunks.append(str(chunk))
    return "".join(chunks)


class ChatServiceTests(unittest.IsolatedAsyncioTestCase):
    async def test_unknown_carrier_question_returns_unknown_and_skyfrog(self):
        service = ChatService()
        request = _build_request()
        body = PublicChatPayload(message="356521 ไปกับขนส่งอะไร", history=[], session_id="sess-1")

        with (
            patch.dict(os.environ, {"GEMINI_API_KEY": "test-key"}, clear=False),
            patch("backend.app.services.chat_service.lookup_tracking", new=AsyncMock(return_value=None)),
            patch(
                "backend.app.services.chat_service.enqueue_tracking_resolution_request",
                new=Mock(return_value=True),
            ) as queue_mock,
        ):
            response = await service.handle_chat(request, body)

        self.assertIsInstance(response, StreamingResponse)
        payload = await _read_stream(response)
        self.assertIn("ยังไม่ทราบ", payload)
        self.assertIn("Skyfrog", payload)
        self.assertNotIn("Kerry Express", payload)
        queue_mock.assert_called_once_with(
            job_number="356521",
            user_message="356521 ไปกับขนส่งอะไร",
            session_id="sess-1",
            source="tracking_not_found",
        )


if __name__ == "__main__":
    unittest.main()
