import unittest
from unittest.mock import patch

from backend.app.services.chat_support_service import direct_topic_intent_rows, rows_for_preferred_answer_intent
from backend.app.services.intent_router_core import ChatIntent


class ChatSupportServiceTests(unittest.TestCase):
    def test_rows_for_preferred_answer_intent_accepts_weigh_alias(self):
        intent = ChatIntent(
            name="solar",
            lane="longform",
            knowledge_query="",
            top_k=3,
            threshold=0.5,
            system_hint="",
            preferred_answer_intent="weight",
        )
        rows = [
            {"topic": "solar", "intent": "definition", "answer": "definition"},
            {"topic": "solar", "intent": "weigh", "answer": "weight answer"},
        ]

        filtered = rows_for_preferred_answer_intent(intent, rows)

        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0]["answer"], "weight answer")

    def test_direct_topic_intent_rows_accepts_weigh_alias(self):
        intent = ChatIntent(
            name="solar",
            lane="longform",
            knowledge_query="",
            top_k=3,
            threshold=0.5,
            system_hint="",
            preferred_answer_intent="weight",
        )
        rows = [
            {
                "topic": "solar",
                "question": "Solar หนักเท่าไหร่",
                "keywords": "หนัก กี่กิโล กี่ตัน",
                "intent": "weigh",
                "answer": "ประมาณ 1.2 ตันต่อเลท",
            }
        ]

        with patch("backend.app.services.chat_support_service.load_topic_rows", return_value=rows):
            matched = direct_topic_intent_rows(intent, "Solar หนักเท่าไหร่")

        self.assertEqual(len(matched), 1)
        self.assertEqual(matched[0]["answer"], "ประมาณ 1.2 ตันต่อเลท")


if __name__ == "__main__":
    unittest.main()
