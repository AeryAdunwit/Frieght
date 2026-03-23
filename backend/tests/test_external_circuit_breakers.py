import os
import unittest
from unittest.mock import patch

from backend.app.services.circuit_breaker import (
    CircuitBreakerOpenError,
    get_or_create_circuit_breaker,
    reset_circuit_breakers,
)
from backend.app.services.chat_runtime_service import stream_model_response
from backend.app.services.intent_router_core import ChatIntent
from backend.app.services.sheets_core import _run_sheets_call
from backend.app.services.vector_search_core import embed_query


class ExternalCircuitBreakerIntegrationTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        reset_circuit_breakers()

    def tearDown(self):
        reset_circuit_breakers()

    async def test_stream_model_response_short_circuits_when_gemini_breaker_is_open(self):
        with patch.dict(
            os.environ,
            {
                "ENABLE_EXTERNAL_CIRCUIT_BREAKERS": "1",
                "GEMINI_CIRCUIT_FAILURE_THRESHOLD": "1",
                "GEMINI_CIRCUIT_RECOVERY_SECONDS": "60",
            },
            clear=False,
        ), patch("backend.app.services.chat_runtime_service.log_chat_interaction"):
            breaker = get_or_create_circuit_breaker(
                "gemini",
                failure_threshold=1,
                recovery_timeout_seconds=60,
            )
            breaker.record_failure(RuntimeError("gemini down"))

            intent = ChatIntent(
                name="general",
                lane="general",
                knowledge_query="",
                top_k=0,
                threshold=0.0,
                system_hint="",
            )
            payload = b""
            async for chunk in stream_model_response(
                "สวัสดี",
                [],
                "system prompt",
                session_id="session-1",
                intent=intent,
            ):
                payload += chunk

        self.assertIn("ตอนนี้ระบบตอบกลับมีสะดุดนิดหน่อยค้าบ", payload.decode("utf-8"))

    def test_embed_query_returns_empty_when_gemini_breaker_is_open(self):
        with patch.dict(
            os.environ,
            {
                "ENABLE_EXTERNAL_CIRCUIT_BREAKERS": "1",
                "GEMINI_CIRCUIT_FAILURE_THRESHOLD": "1",
                "GEMINI_CIRCUIT_RECOVERY_SECONDS": "60",
            },
            clear=False,
        ):
            breaker = get_or_create_circuit_breaker(
                "gemini",
                failure_threshold=1,
                recovery_timeout_seconds=60,
            )
            breaker.record_failure(RuntimeError("gemini down"))

            self.assertEqual(embed_query("ธุรกิจ EM คืออะไร"), [])

    def test_run_sheets_call_raises_when_sheets_breaker_is_open(self):
        with patch.dict(
            os.environ,
            {
                "ENABLE_EXTERNAL_CIRCUIT_BREAKERS": "1",
                "SHEETS_CIRCUIT_FAILURE_THRESHOLD": "1",
                "SHEETS_CIRCUIT_RECOVERY_SECONDS": "60",
            },
            clear=False,
        ):
            breaker = get_or_create_circuit_breaker(
                "sheets",
                failure_threshold=1,
                recovery_timeout_seconds=60,
            )
            breaker.record_failure(RuntimeError("sheets down"))

            with self.assertRaises(CircuitBreakerOpenError):
                _run_sheets_call("test", lambda: {"ok": True})


if __name__ == "__main__":
    unittest.main()
