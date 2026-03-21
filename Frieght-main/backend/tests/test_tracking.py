import unittest

from backend.tracking import extract_job_number, get_tracking_prompt, is_tracking_request


class TrackingTests(unittest.TestCase):
    def test_extract_job_number(self):
        self.assertEqual(extract_job_number("ช่วยเช็คสถานะ 1234567890 ให้หน่อย"), "1234567890")

    def test_tracking_intent_without_number(self):
        self.assertTrue(is_tracking_request("ต้องการติดตามพัสดุ"))
        self.assertIn("10 หลัก", get_tracking_prompt())


if __name__ == "__main__":
    unittest.main()
