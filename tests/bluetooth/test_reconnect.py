from __future__ import annotations

from datetime import datetime, timezone

from bluelatch.bluetooth.reconnect import ReconnectBackoff, ReconnectController


def test_backoff_grows_until_maximum() -> None:
    backoff = ReconnectBackoff(initial_seconds=5, max_seconds=20, jitter_ratio=0.0)
    assert backoff.next_delay_seconds() == 5
    assert backoff.next_delay_seconds() == 10
    assert backoff.next_delay_seconds() == 20
    assert backoff.next_delay_seconds() == 20


def test_controller_marks_success_and_failure() -> None:
    controller = ReconnectController(
        backoff=ReconnectBackoff(initial_seconds=5, max_seconds=20, jitter_ratio=0.0),
    )
    now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    next_attempt = controller.mark_failure(now=now)
    assert next_attempt > now
    assert controller.should_attempt(now=now) is False
    controller.mark_success()
    assert controller.should_attempt(now=now) is True
