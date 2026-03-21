import unittest

from backend.intent_router import classify_intent


class IntentRouterTests(unittest.TestCase):
    def test_classify_solar_limitations(self):
        intent = classify_intent("ข้อจำกัด solar hub มีอะไรบ้าง")
        self.assertEqual(intent.name, "solar")
        self.assertEqual(intent.preferred_answer_intent, "limitations")

    def test_classify_pricing_quote_input(self):
        intent = classify_intent("ขอ quotation ต้องส่งข้อมูลอะไรบ้าง")
        self.assertEqual(intent.name, "pricing")
        self.assertEqual(intent.preferred_answer_intent, "quote_input")

    def test_classify_document_pod(self):
        intent = classify_intent("ต้องใช้ POD หรือไม่")
        self.assertEqual(intent.name, "document")
        self.assertEqual(intent.preferred_answer_intent, "pod")

    def test_classify_timeline_cutoff(self):
        intent = classify_intent("ตัดรอบกี่โมง")
        self.assertEqual(intent.name, "timeline")
        self.assertEqual(intent.preferred_answer_intent, "cutoff")

    def test_classify_greeting_rule_response(self):
        intent = classify_intent("สวัสดี")
        self.assertEqual(intent.name, "greeting")
        self.assertEqual(intent.lane, "rule")
        self.assertTrue(intent.canned_response)

    def test_classify_general_chat_fallback(self):
        intent = classify_intent("หิว")
        self.assertEqual(intent.name, "general_chat")
        self.assertEqual(intent.lane, "general")


if __name__ == "__main__":
    unittest.main()
