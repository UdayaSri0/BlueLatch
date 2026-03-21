from __future__ import annotations

import random
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(slots=True)
class ReconnectBackoff:
    initial_seconds: int = 5
    max_seconds: int = 300
    jitter_ratio: float = 0.2
    factor: float = 2.0
    _current_seconds: float = field(init=False, default=0.0)

    def reset(self) -> None:
        self._current_seconds = 0.0

    def next_delay_seconds(self) -> float:
        if self._current_seconds == 0.0:
            base = float(self.initial_seconds)
        else:
            base = min(float(self.max_seconds), self._current_seconds * self.factor)
        self._current_seconds = base
        jitter_span = base * self.jitter_ratio
        if jitter_span <= 0:
            return base
        return max(0.0, base + random.uniform(-jitter_span, jitter_span))


@dataclass(slots=True)
class ReconnectController:
    backoff: ReconnectBackoff
    next_attempt_at: datetime | None = None

    def mark_success(self) -> None:
        self.backoff.reset()
        self.next_attempt_at = None

    def mark_failure(self, now: datetime | None = None) -> datetime:
        now = now or utc_now()
        delay = self.backoff.next_delay_seconds()
        self.next_attempt_at = now + timedelta(seconds=delay)
        return self.next_attempt_at

    def should_attempt(self, now: datetime | None = None) -> bool:
        now = now or utc_now()
        return self.next_attempt_at is None or now >= self.next_attempt_at
