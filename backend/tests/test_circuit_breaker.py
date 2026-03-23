import unittest
from datetime import datetime, timedelta, timezone

from backend.app.services.circuit_breaker import CircuitBreaker, CircuitBreakerOpenError


class CircuitBreakerTests(unittest.TestCase):
    def test_opens_after_threshold_failures(self):
        now = datetime(2026, 3, 23, tzinfo=timezone.utc)
        breaker = CircuitBreaker(
            name="gemini",
            failure_threshold=2,
            recovery_timeout_seconds=30,
            _utcnow=lambda: now,
        )

        with self.assertRaises(RuntimeError):
            breaker.call(lambda: (_ for _ in ()).throw(RuntimeError("boom-1")))
        self.assertFalse(breaker.is_open())

        with self.assertRaises(RuntimeError):
            breaker.call(lambda: (_ for _ in ()).throw(RuntimeError("boom-2")))
        self.assertTrue(breaker.is_open())

    def test_rejects_calls_while_open(self):
        now = datetime(2026, 3, 23, tzinfo=timezone.utc)
        breaker = CircuitBreaker(
            name="sheets",
            failure_threshold=1,
            recovery_timeout_seconds=30,
            _utcnow=lambda: now,
        )

        with self.assertRaises(RuntimeError):
            breaker.call(lambda: (_ for _ in ()).throw(RuntimeError("down")))

        with self.assertRaises(CircuitBreakerOpenError):
            breaker.call(lambda: "ok")

    def test_allows_retry_after_recovery_window_and_resets_on_success(self):
        now = datetime(2026, 3, 23, tzinfo=timezone.utc)
        breaker = CircuitBreaker(
            name="tracking",
            failure_threshold=1,
            recovery_timeout_seconds=30,
            _utcnow=lambda: now,
        )

        with self.assertRaises(RuntimeError):
            breaker.call(lambda: (_ for _ in ()).throw(RuntimeError("down")))

        later = now + timedelta(seconds=31)
        breaker._utcnow = lambda: later

        self.assertTrue(breaker.is_half_open())
        self.assertEqual(breaker.call(lambda: "ok"), "ok")
        self.assertFalse(breaker.is_open())
        self.assertEqual(breaker.failure_count, 0)


if __name__ == "__main__":
    unittest.main()
