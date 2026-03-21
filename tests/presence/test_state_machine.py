from __future__ import annotations

from datetime import datetime, timedelta, timezone

from bluelatch.config.models import ProtectionConfig
from bluelatch.models import PresenceMode, ProtectionState
from bluelatch.presence.estimator import PresenceAssessment, SignalBand
from bluelatch.presence.state_machine import ProtectionStateMachine


def assessment(*, present: bool, at: datetime) -> PresenceAssessment:
    return PresenceAssessment(
        connected=present,
        rssi=-70 if present else None,
        smoothed_rssi=-70 if present else None,
        signal_band=SignalBand.NEAR if present else SignalBand.FAR,
        appears_present=present,
        mode=PresenceMode.HYBRID,
        reason="present" if present else "away",
        observed_at=at,
    )


def test_device_disappears_long_enough_to_lock() -> None:
    machine = ProtectionStateMachine(
        settings=ProtectionConfig(away_grace_seconds=10, maybe_away_seconds=2),
    )
    base = datetime(2026, 1, 1, tzinfo=timezone.utc)

    machine.advance(assessment=assessment(present=True, at=base), session_locked=False)
    machine.advance(
        assessment=assessment(present=True, at=base + timedelta(seconds=6)),
        session_locked=False,
    )
    first_absent = machine.advance(
        assessment=assessment(present=False, at=base + timedelta(seconds=7)),
        session_locked=False,
    )
    assert first_absent.state is ProtectionState.MAYBE_AWAY

    second_absent = machine.advance(
        assessment=assessment(present=False, at=base + timedelta(seconds=9)),
        session_locked=False,
    )
    assert second_absent.state is ProtectionState.AWAY_PENDING_LOCK

    lock_decision = machine.advance(
        assessment=assessment(present=False, at=base + timedelta(seconds=18)),
        session_locked=False,
    )
    assert lock_decision.should_lock is True


def test_manual_unlock_while_phone_away_enables_override() -> None:
    machine = ProtectionStateMachine(
        settings=ProtectionConfig(away_grace_seconds=5, maybe_away_seconds=1),
    )
    base = datetime(2026, 1, 1, tzinfo=timezone.utc)
    machine.advance(assessment=assessment(present=True, at=base), session_locked=False)
    machine.advance(
        assessment=assessment(present=True, at=base + timedelta(seconds=5)),
        session_locked=False,
    )
    machine.advance(
        assessment=assessment(present=False, at=base + timedelta(seconds=6)),
        session_locked=False,
    )
    machine.advance(
        assessment=assessment(present=False, at=base + timedelta(seconds=7)),
        session_locked=False,
    )
    machine.advance(
        assessment=assessment(present=False, at=base + timedelta(seconds=12)),
        session_locked=False,
    )
    machine.mark_lock_success(now=base + timedelta(seconds=12), reason="phone away")

    unlocked = machine.advance(
        assessment=assessment(present=False, at=base + timedelta(seconds=15)),
        session_locked=False,
    )
    assert unlocked.state is ProtectionState.AWAY_MANUAL_OVERRIDE
    assert unlocked.manual_override_active is True

    later = machine.advance(
        assessment=assessment(present=False, at=base + timedelta(seconds=30)),
        session_locked=False,
    )
    assert later.should_lock is False
    assert later.state is ProtectionState.AWAY_MANUAL_OVERRIDE


def test_phone_return_clears_override_and_resumes_protection() -> None:
    machine = ProtectionStateMachine(
        settings=ProtectionConfig(
            away_grace_seconds=5,
            maybe_away_seconds=1,
            return_grace_seconds=2,
        ),
    )
    base = datetime(2026, 1, 1, tzinfo=timezone.utc)
    machine.restore_manual_override(now=base)

    returning = machine.advance(
        assessment=assessment(present=True, at=base + timedelta(seconds=1)),
        session_locked=False,
    )
    assert returning.state is ProtectionState.RETURNING

    stable = machine.advance(
        assessment=assessment(present=True, at=base + timedelta(seconds=4)),
        session_locked=False,
    )
    assert stable.state is ProtectionState.PRESENT
    assert stable.manual_override_active is False
