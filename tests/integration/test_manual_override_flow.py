from __future__ import annotations

from datetime import datetime, timedelta, timezone

from bluelatch.config.models import ProtectionConfig
from bluelatch.models import PresenceMode, ProtectionState
from bluelatch.presence.estimator import PresenceAssessment, SignalBand
from bluelatch.presence.state_machine import ProtectionStateMachine


def snapshot(*, present: bool, at: datetime, reason: str) -> PresenceAssessment:
    return PresenceAssessment(
        connected=present,
        rssi=-68 if present else None,
        smoothed_rssi=-68 if present else None,
        signal_band=SignalBand.NEAR if present else SignalBand.FAR,
        appears_present=present,
        mode=PresenceMode.HYBRID,
        reason=reason,
        observed_at=at,
    )


def test_manual_override_only_clears_after_phone_returns() -> None:
    machine = ProtectionStateMachine(
        settings=ProtectionConfig(
            away_grace_seconds=8,
            maybe_away_seconds=2,
            return_grace_seconds=3,
        ),
    )
    base = datetime(2026, 3, 1, tzinfo=timezone.utc)

    machine.advance(assessment=snapshot(present=True, at=base, reason="initial"), session_locked=False)
    machine.advance(
        assessment=snapshot(
            present=True,
            at=base + timedelta(seconds=4),
            reason="stable present",
        ),
        session_locked=False,
    )
    machine.advance(
        assessment=snapshot(
            present=False,
            at=base + timedelta(seconds=5),
            reason="disconnect starts",
        ),
        session_locked=False,
    )
    machine.advance(
        assessment=snapshot(
            present=False,
            at=base + timedelta(seconds=7),
            reason="still away",
        ),
        session_locked=False,
    )
    decision = machine.advance(
        assessment=snapshot(
            present=False,
            at=base + timedelta(seconds=15),
            reason="grace expired",
        ),
        session_locked=False,
    )
    assert decision.should_lock is True
    machine.mark_lock_success(now=base + timedelta(seconds=15), reason="trusted phone absent")

    override = machine.advance(
        assessment=snapshot(
            present=False,
            at=base + timedelta(seconds=19),
            reason="manual unlock",
        ),
        session_locked=False,
    )
    assert override.state is ProtectionState.AWAY_MANUAL_OVERRIDE

    still_suppressed = machine.advance(
        assessment=snapshot(
            present=False,
            at=base + timedelta(seconds=60),
            reason="still away",
        ),
        session_locked=False,
    )
    assert still_suppressed.should_lock is False

    machine.advance(
        assessment=snapshot(
            present=True,
            at=base + timedelta(seconds=62),
            reason="phone returns",
        ),
        session_locked=False,
    )
    resumed = machine.advance(
        assessment=snapshot(
            present=True,
            at=base + timedelta(seconds=66),
            reason="stable again",
        ),
        session_locked=False,
    )
    assert resumed.state is ProtectionState.PRESENT
    assert resumed.manual_override_active is False
