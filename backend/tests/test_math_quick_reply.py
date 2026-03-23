import unittest

from backend.app.services.chat_support_service import build_basic_math_reply as _build_basic_math_reply


class MathQuickReplyTests(unittest.TestCase):
    def test_addition_reply(self):
        reply = _build_basic_math_reply("31+1")
        self.assertIsNotNone(reply)
        self.assertIn("32", reply)

    def test_division_reply(self):
        reply = _build_basic_math_reply("1/2")
        self.assertIsNotNone(reply)
        self.assertIn("0.5", reply)

    def test_parentheses_reply(self):
        reply = _build_basic_math_reply("(2+3)*4")
        self.assertIsNotNone(reply)
        self.assertIn("20", reply)

    def test_non_math_reply_is_none(self):
        self.assertIsNone(_build_basic_math_reply("ส่งของไปขอนแก่น"))
        self.assertIsNone(_build_basic_math_reply("1314640315"))


if __name__ == "__main__":
    unittest.main()
