import unittest

from backend import intent_router, sanitizer, sheets_loader, sync_vectors, tracking, vector_search
from backend.app.middleware import sanitizer as sanitizer_core
from backend.app.services import (
    intent_router_core,
    knowledge_sync_core,
    sheets_core,
    tracking_core,
    vector_search_core,
)


class RootWrapperTests(unittest.TestCase):
    def test_intent_router_wrapper_points_to_app_core(self):
        self.assertIs(intent_router.ChatIntent, intent_router_core.ChatIntent)
        self.assertIs(intent_router.classify_intent, intent_router_core.classify_intent)

    def test_sanitizer_wrapper_points_to_app_core(self):
        self.assertIs(sanitizer.validate_message, sanitizer_core.validate_message)
        self.assertIs(sanitizer.sanitize_sheet_content, sanitizer_core.sanitize_sheet_content)

    def test_vector_search_wrapper_points_to_app_core(self):
        self.assertIs(vector_search.get_supabase_client, vector_search_core.get_supabase_client)
        self.assertIs(vector_search.search_knowledge, vector_search_core.search_knowledge)
        self.assertIs(vector_search.load_topic_rows, vector_search_core.load_topic_rows)
        self.assertIs(vector_search.invalidate_knowledge_caches, vector_search_core.invalidate_knowledge_caches)

    def test_tracking_wrapper_points_to_app_core(self):
        self.assertIs(tracking.extract_job_number, tracking_core.extract_job_number)
        self.assertIs(tracking.lookup_tracking, tracking_core.lookup_tracking)
        self.assertIs(tracking.format_tracking_response, tracking_core.format_tracking_response)

    def test_sheets_wrapper_points_to_app_core(self):
        self.assertIs(sheets_loader.get_sheets_service, sheets_core.get_sheets_service)
        self.assertIs(sheets_loader.append_knowledge_row, sheets_core.append_knowledge_row)
        self.assertIs(sheets_loader.load_knowledge_rows, sheets_core.load_knowledge_rows)

    def test_sync_wrapper_points_to_app_core(self):
        self.assertIs(sync_vectors.embed_text, knowledge_sync_core.embed_text)
        self.assertIs(sync_vectors.sync, knowledge_sync_core.sync)


if __name__ == "__main__":
    unittest.main()
