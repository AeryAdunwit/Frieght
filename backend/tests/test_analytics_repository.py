import unittest
from unittest.mock import MagicMock, patch

from backend.app.repositories.analytics_repository import AnalyticsRepository, RepositoryQueryError


class AnalyticsRepositoryTests(unittest.TestCase):
    @patch("backend.app.repositories.analytics_repository.get_supabase_client")
    def test_fetch_chat_logs_raises_repository_query_error_when_required_query_fails(self, mock_get_supabase_client):
        mock_client = MagicMock()
        mock_query = MagicMock()
        mock_query.gte.return_value = mock_query
        mock_query.order.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.execute.side_effect = RuntimeError("db unavailable")
        mock_client.table.return_value.select.return_value = mock_query
        mock_get_supabase_client.return_value = mock_client

        repository = AnalyticsRepository()

        with self.assertRaises(RepositoryQueryError):
            repository.fetch_chat_logs()
        self.assertIn("fetch_chat_logs", repository.last_error)

    @patch("backend.app.repositories.analytics_repository.get_supabase_client")
    def test_insert_chat_feedback_raises_repository_query_error_on_insert_failure(self, mock_get_supabase_client):
        mock_client = MagicMock()
        mock_client.table.return_value.insert.return_value.execute.side_effect = RuntimeError("write failed")
        mock_get_supabase_client.return_value = mock_client

        repository = AnalyticsRepository()

        with self.assertRaises(RepositoryQueryError):
            repository.insert_chat_feedback({"session_id": "s"})
        self.assertIn("insert_chat_feedback", repository.last_error)


if __name__ == "__main__":
    unittest.main()
