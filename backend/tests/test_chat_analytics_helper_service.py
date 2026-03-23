import unittest

from backend.app.services.chat_analytics_helper_service import ChatAnalyticsHelperService


class _FakeAnalyticsRepository:
    def __init__(self):
        self.last_error = ""

    def fetch_chat_logs(self, **kwargs):
        return [
            {
                "id": 1,
                "session_id": "s1",
                "intent_name": "solar",
                "intent_lane": "knowledge",
                "preferred_answer_intent": "definition",
                "source": "knowledge_direct",
                "job_number": "",
                "user_message": "ธุรกิจ EM คืออะไร",
                "bot_reply": "ตอบแล้วค้าบ",
                "created_at": "2026-03-23T00:00:00+00:00",
            }
        ]

    def fetch_review_statuses(self, chat_log_ids):
        return {}

    def fetch_feedback_rows(self, **kwargs):
        self.last_error = "fetch_feedback_rows: temporary timeout"
        return []

    def fetch_recent_review_updates(self, **kwargs):
        return []

    def fetch_sheet_approval_rows(self, **kwargs):
        return []

    def fetch_handoff_rows(self, **kwargs):
        return []

    def fetch_sync_run_rows(self, **kwargs):
        return []

    def fetch_kb_rows(self):
        return []


class ChatAnalyticsHelperServiceTests(unittest.TestCase):
    def test_build_chat_overview_includes_repository_errors(self):
        service = ChatAnalyticsHelperService(repository=_FakeAnalyticsRepository())

        payload = service.build_chat_overview(
            days=7,
            fetch_limit=20,
            recent_limit=5,
        )

        self.assertEqual(payload.totals["chat_messages"], 1)
        self.assertIn("fetch_feedback_rows: temporary timeout", payload.repository_errors)


if __name__ == "__main__":
    unittest.main()
