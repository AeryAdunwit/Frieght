import unittest
from unittest.mock import MagicMock, patch

from backend import vector_search


class VectorSearchCacheTests(unittest.TestCase):
    def setUp(self):
        vector_search.invalidate_knowledge_caches()

    def tearDown(self):
        vector_search.invalidate_knowledge_caches()

    @patch("backend.vector_search.genai.embed_content")
    @patch("backend.vector_search.genai.configure")
    def test_embed_query_uses_cache_for_same_input(self, mock_configure, mock_embed_content):
        mock_embed_content.return_value = {"embedding": [0.1, 0.2, 0.3]}

        first = vector_search.embed_query("ส่ง solar ไป ขอนแก่น")
        second = vector_search.embed_query("ส่ง   solar   ไป   ขอนแก่น")

        self.assertEqual(first, second)
        self.assertEqual(mock_embed_content.call_count, 1)
        self.assertEqual(mock_configure.call_count, 1)

    @patch("backend.vector_search.get_supabase_client")
    @patch("backend.vector_search.embed_query")
    def test_search_knowledge_uses_cache_for_same_query(self, mock_embed_query, mock_get_supabase_client):
        mock_embed_query.return_value = [0.1, 0.2, 0.3]
        mock_client = MagicMock()
        mock_execute = MagicMock()
        mock_execute.data = [{"question": "Q1", "answer": "A1", "intent": "pricing"}]
        mock_client.rpc.return_value.execute.return_value = mock_execute
        mock_get_supabase_client.return_value = mock_client

        first = vector_search.search_knowledge("ส่ง solar ไป ขอนแก่น", top_k=3, threshold=0.6)
        second = vector_search.search_knowledge("ส่ง   solar   ไป   ขอนแก่น", top_k=3, threshold=0.6)

        self.assertEqual(first, second)
        self.assertEqual(mock_client.rpc.call_count, 1)

    @patch("backend.vector_search.get_supabase_client")
    def test_load_topic_rows_uses_cache_for_same_topic(self, mock_get_supabase_client):
        mock_client = MagicMock()
        mock_execute = MagicMock()
        mock_execute.data = [{"topic": "solar", "question": "Q1", "answer": "A1", "intent": "definition"}]
        mock_client.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.return_value = mock_execute
        mock_get_supabase_client.return_value = mock_client

        first = vector_search.load_topic_rows("solar", limit=50)
        second = vector_search.load_topic_rows(" solar ", limit=50)

        self.assertEqual(first, second)
        self.assertEqual(
            mock_client.table.return_value.select.return_value.eq.return_value.limit.return_value.execute.call_count,
            1,
        )


if __name__ == "__main__":
    unittest.main()
