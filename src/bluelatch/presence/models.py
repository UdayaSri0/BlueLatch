from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from bluelatch.models import PresenceMode, ProtectionState


class SignalBand(str, Enum):
    UNKNOWN = "unknown"
    NEAR = "near"
    MID = "mid"
    FAR = "far"


@dataclass(slots=True)
class PresenceAssessment:
    connected: bool
    rssi: int | None
    smoothed_rssi: float | None
    signal_band: SignalBand
    appears_present: bool
    mode: PresenceMode
    reason: str
    observed_at: datetime


@dataclass(slots=True)
class LockDecision:
    state: ProtectionState
    should_lock: bool = False
    manual_override_active: bool = False
    last_reason: str | None = None
