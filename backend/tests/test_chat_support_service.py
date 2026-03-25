import unittest
from unittest.mock import patch

from backend.app.services.chat_support_service import direct_topic_intent_rows, rows_for_preferred_answer_intent
from backend.app.services.intent_router_core import ChatIntent


class ChatSupportServiceTests(unittest.TestCase):
    def _build_intent(self, preferred_answer_intent: str, name: str = "solar") -> ChatIntent:
        return ChatIntent(
            name=name,
            lane="longform",
            knowledge_query="",
            top_k=3,
            threshold=0.5,
            system_hint="",
            preferred_answer_intent=preferred_answer_intent,
        )

    def test_rows_for_preferred_answer_intent_accepts_pricing_family_alias(self):
        intent = self._build_intent("pricing")
        rows = [
            {"topic": "solar", "intent": "definition", "answer": "definition"},
            {"topic": "solar", "intent": "pricing_policy", "answer": "pricing answer"},
        ]

        filtered = rows_for_preferred_answer_intent(intent, rows)

        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0]["answer"], "pricing answer")

    def test_rows_for_preferred_answer_intent_accepts_weigh_alias(self):
        intent = self._build_intent("weight")
        rows = [
            {"topic": "solar", "intent": "definition", "answer": "definition"},
            {"topic": "solar", "intent": "weigh", "answer": "weight answer"},
        ]

        filtered = rows_for_preferred_answer_intent(intent, rows)

        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0]["answer"], "weight answer")

    def test_direct_topic_intent_rows_accepts_weigh_alias(self):
        intent = self._build_intent("weight")
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

    def test_direct_topic_intent_rows_accepts_weight_suffix_alias(self):
        intent = self._build_intent("weight")
        rows = [
            {
                "topic": "solar",
                "question": "Solar หนักเท่าไหร่",
                "keywords": "หนัก กี่กิโล กี่ตัน",
                "intent": "solar_weight_detail",
                "answer": "ประมาณ 1.2 ตันต่อเลท",
            }
        ]

        with patch("backend.app.services.chat_support_service.load_topic_rows", return_value=rows):
            matched = direct_topic_intent_rows(intent, "Solar หนักเท่าไหร่")

        self.assertEqual(len(matched), 1)
        self.assertEqual(matched[0]["answer"], "ประมาณ 1.2 ตันต่อเลท")

    def test_rows_for_preferred_answer_intent_accepts_booking_family_alias(self):
        intent = self._build_intent("booking_step", name="booking")
        rows = [
            {"topic": "booking", "intent": "booking_input", "answer": "input answer"},
            {"topic": "booking", "intent": "booking_process_detail", "answer": "step answer"},
        ]

        filtered = rows_for_preferred_answer_intent(intent, rows)

        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0]["answer"], "step answer")

    def test_rows_for_preferred_answer_intent_accepts_claim_family_alias(self):
        intent = self._build_intent("claim_evidence", name="claim")
        rows = [
            {"topic": "claim", "intent": "claim_step", "answer": "step answer"},
            {"topic": "claim", "intent": "claim_proof_detail", "answer": "proof answer"},
        ]

        filtered = rows_for_preferred_answer_intent(intent, rows)

        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0]["answer"], "proof answer")

    def test_rows_for_preferred_answer_intent_accepts_coverage_family_alias(self):
        intent = self._build_intent("check_area", name="coverage")
        rows = [
            {"topic": "coverage", "intent": "nationwide", "answer": "nationwide answer"},
            {"topic": "coverage", "intent": "coverage_check_detail", "answer": "check answer"},
        ]

        filtered = rows_for_preferred_answer_intent(intent, rows)

        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0]["answer"], "check answer")

    def test_rows_for_preferred_answer_intent_accepts_timeline_family_alias(self):
        intent = self._build_intent("cutoff", name="timeline")
        rows = [
            {"topic": "timeline", "intent": "transit_time", "answer": "transit answer"},
            {"topic": "timeline", "intent": "timeline_cutoff_policy", "answer": "cutoff answer"},
        ]

        filtered = rows_for_preferred_answer_intent(intent, rows)

        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0]["answer"], "cutoff answer")

    def test_rows_for_preferred_answer_intent_accepts_general_family_alias(self):
        intent = self._build_intent("service_overview", name="general_chat")
        rows = [
            {"topic": "general", "intent": "handoff", "answer": "handoff answer"},
            {"topic": "general", "intent": "service_intro_detail", "answer": "overview answer"},
        ]

        filtered = rows_for_preferred_answer_intent(intent, rows)

        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0]["answer"], "overview answer")


if __name__ == "__main__":
    unittest.main()
