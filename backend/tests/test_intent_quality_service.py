import unittest

from backend.app.services.intent_quality_service import normalize_intent_message


class IntentQualityServiceTests(unittest.TestCase):
    def test_normalize_intent_message_replaces_common_variants(self):
        normalized = normalize_intent_message("ส่ง โซล่า ผ่าน ฮับ แล้วใช้ พอด ไหม")
        self.assertIn("โซลาร์", normalized)
        self.assertIn("hub", normalized)
        self.assertIn("pod", normalized)

    def test_normalize_intent_message_collapses_whitespace(self):
        normalized = normalize_intent_message("   quotation    solar   hub   ")
        self.assertEqual(normalized, "quotation solar hub")


if __name__ == "__main__":
    unittest.main()
