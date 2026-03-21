from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta

from bluelatch.config.models import ProtectionConfig
from bluelatch.models import ProtectionState
from bluelatch.presence.models import LockDecision, PresenceAssessment


@dataclass(slots=True)
class ProtectionStateMachine:
    settings: ProtectionConfig
    state: ProtectionState = field(init=False, default=ProtectionState.STARTING)
    absence_started_at: datetime | None = field(init=False, default=None)
    presence_started_at: datetime | None = field(init=False, default=None)
    away_since: datetime | None = field(init=False, default=None)
    last_state_change_at: datetime | None = field(init=False, default=None)
    last_lock_at: datetime | None = field(init=False, default=None)
    last_lock_reason: str | None = field(init=False, default=None)
    manual_override_active: bool = field(init=False, default=False)
    _last_session_locked: bool = field(init=False, default=False)
    _lock_issued_for_current_absence: bool = field(init=False, default=False)

    def __post_init__(self) -> None:
        self.state = ProtectionState.STARTING

    def advance(
        self,
        *,
        assessment: PresenceAssessment,
        session_locked: bool,
    ) -> LockDecision:
        now = assessment.observed_at
        self._handle_session_transition(
            session_locked=session_locked,
            now=now,
            appears_present=assessment.appears_present,
        )

        if assessment.appears_present:
            return self._handle_present(now=now, reason=assessment.reason)
        return self._handle_absent(now=now, session_locked=session_locked, reason=assessment.reason)

    def mark_lock_success(self, *, now: datetime, reason: str) -> LockDecision:
        self.last_lock_at = now
        self.last_lock_reason = reason
        self.manual_override_active = False
        self._lock_issued_for_current_absence = True
        self._last_session_locked = True
        self._transition(ProtectionState.AWAY_LOCKED, now)
        return LockDecision(
            state=self.state,
            should_lock=False,
            manual_override_active=self.manual_override_active,
            last_reason=reason,
        )

    def restore_manual_override(self, *, now: datetime) -> None:
        self.manual_override_active = True
        self._lock_issued_for_current_absence = True
        self._transition(ProtectionState.AWAY_MANUAL_OVERRIDE, now)

    def _handle_present(self, *, now: datetime, reason: str) -> LockDecision:
        self.absence_started_at = None
        self.away_since = None
        self._lock_issued_for_current_absence = False

        if self.state in {ProtectionState.PRESENT}:
            return self._decision(reason)

        if self.presence_started_at is None:
            self.presence_started_at = now

        if self.state in {
            ProtectionState.AWAY_LOCKED,
            ProtectionState.AWAY_MANUAL_OVERRIDE,
            ProtectionState.AWAY_PENDING_LOCK,
            ProtectionState.MAYBE_AWAY,
            ProtectionState.STARTING,
            ProtectionState.RETURNING,
        }:
            if now - self.presence_started_at >= timedelta(
                seconds=self.settings.return_grace_seconds,
            ):
                self.manual_override_active = False
                self._transition(ProtectionState.PRESENT, now)
            else:
                self._transition(ProtectionState.RETURNING, now)
        return self._decision(reason)

    def _handle_absent(
        self,
        *,
        now: datetime,
        session_locked: bool,
        reason: str,
    ) -> LockDecision:
        self.presence_started_at = None
        self.away_since = self.away_since or now
        if self.absence_started_at is None:
            self.absence_started_at = now

        if self.manual_override_active:
            self._transition(ProtectionState.AWAY_MANUAL_OVERRIDE, now)
            return self._decision(reason)

        absence_duration = now - self.absence_started_at

        if self.state in {ProtectionState.STARTING, ProtectionState.PRESENT, ProtectionState.RETURNING}:
            if absence_duration < timedelta(seconds=self.settings.maybe_away_seconds):
                self._transition(ProtectionState.MAYBE_AWAY, now)
                return self._decision(reason)
            self._transition(ProtectionState.AWAY_PENDING_LOCK, now)

        if self.state is ProtectionState.MAYBE_AWAY:
            if absence_duration >= timedelta(seconds=self.settings.maybe_away_seconds):
                self._transition(ProtectionState.AWAY_PENDING_LOCK, now)
            return self._decision(reason)

        if self.state is ProtectionState.AWAY_LOCKED:
            return self._decision(reason)

        if self.state is ProtectionState.AWAY_PENDING_LOCK:
            grace_elapsed = absence_duration >= timedelta(
                seconds=self.settings.away_grace_seconds,
            )
            should_lock = (
                grace_elapsed
                and not session_locked
                and not self._lock_issued_for_current_absence
            )
            return LockDecision(
                state=self.state,
                should_lock=should_lock,
                manual_override_active=self.manual_override_active,
                last_reason=reason,
            )

        return self._decision(reason)

    def _handle_session_transition(
        self,
        *,
        session_locked: bool,
        now: datetime,
        appears_present: bool,
    ) -> None:
        if self._last_session_locked and not session_locked:
            if self.state is ProtectionState.AWAY_LOCKED and not appears_present:
                self.manual_override_active = True
                self._transition(ProtectionState.AWAY_MANUAL_OVERRIDE, now)
        self._last_session_locked = session_locked

    def _decision(self, reason: str | None = None) -> LockDecision:
        return LockDecision(
            state=self.state,
            should_lock=False,
            manual_override_active=self.manual_override_active,
            last_reason=reason or self.last_lock_reason,
        )

    def _transition(self, state: ProtectionState, when: datetime) -> None:
        if self.state != state:
            self.state = state
            self.last_state_change_at = when
