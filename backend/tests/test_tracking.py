import unittest

from backend.tracking import (
    build_tracking_not_found_response,
    extract_job_number,
    get_tracking_prompt,
    is_tracking_request,
)


class TrackingTests(unittest.TestCase):
    def test_extract_job_number_returns_long_numeric_value(self):
        self.assertEqual(extract_job_number("ช่วยเช็กสถานะ 1234567890 ให้หน่อย"), "1234567890")

    def test_extract_job_number_ignores_short_numbers(self):
        self.assertIsNone(extract_job_number("31+1"))
        self.assertIsNone(extract_job_number("เลขงาน 1234"))

    def test_extract_job_number_accepts_short_numeric_message_only(self):
        self.assertEqual(extract_job_number("356521"), "356521")
        self.assertEqual(extract_job_number("356521 ไปกับขนส่งอะไร"), "356521")

    def test_tracking_intent_detected_from_tracking_keywords(self):
        self.assertTrue(is_tracking_request("อยากติดตามสถานะพัสดุ"))

    def test_tracking_intent_detected_from_long_numeric_message_only(self):
        self.assertTrue(is_tracking_request("1314640315"))

    def test_tracking_intent_detected_from_short_numeric_message_only(self):
        self.assertTrue(is_tracking_request("356521"))
        self.assertTrue(is_tracking_request("356521 ไปกับขนส่งอะไร"))

    def test_tracking_intent_does_not_treat_math_as_tracking(self):
        self.assertFalse(is_tracking_request("2*5"))
        self.assertFalse(is_tracking_request("100-1"))

    def test_tracking_prompt_mentions_do_or_delivery(self):
        prompt = get_tracking_prompt()
        self.assertIn("DO", prompt)
        self.assertIn("Delivery", prompt)

    def test_tracking_not_found_response_says_unknown_and_points_to_skyfrog(self):
        response = build_tracking_not_found_response("356521")
        self.assertIn("ยังไม่ทราบ", response)
        self.assertIn("Skyfrog", response)
        self.assertIn("356521", response)


if __name__ == "__main__":
    unittest.main()
