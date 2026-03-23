from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Callable, TypeVar


T = TypeVar("T")


class CircuitBreakerOpenError(RuntimeError):
    """Raised when a guarded operation is attempted while the breaker is open."""


@dataclass
class CircuitBreaker:
    name: str
    failure_threshold: int = 3
    recovery_timeout_seconds: int = 30
    failure_count: int = 0
    opened_at: datetime | None = None
    last_error: str = ""
    _utcnow: Callable[[], datetime] = field(default=lambda: datetime.now(timezone.utc), repr=False)

    def is_open(self) -> bool:
        if self.opened_at is None:
            return False
        return self._utcnow() < self.opened_at + timedelta(seconds=self.recovery_timeout_seconds)

    def is_half_open(self) -> bool:
        return self.opened_at is not None and not self.is_open()

    def can_attempt(self) -> bool:
        return not self.is_open()

    def record_success(self) -> None:
        self.failure_count = 0
        self.opened_at = None
        self.last_error = ""

    def record_failure(self, exc: Exception) -> None:
        self.failure_count += 1
        self.last_error = str(exc)
        if self.failure_count >= self.failure_threshold:
            self.opened_at = self._utcnow()

    def call(self, fn: Callable[[], T]) -> T:
        if self.is_open():
            raise CircuitBreakerOpenError(f"{self.name} circuit is open")
        try:
            result = fn()
        except Exception as exc:
            self.record_failure(exc)
            raise
        self.record_success()
        return result
