from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class PresenceMode(str, Enum):
    DISCONNECT_ONLY = "disconnect_only"
    WEAK_SIGNAL_OR_DISCONNECT = "weak_signal_or_disconnect"
    HYBRID = "hybrid"


class ProtectionState(str, Enum):
    STARTING = "starting"
    PRESENT = "present"
    MAYBE_AWAY = "maybe_away"
    AWAY_PENDING_LOCK = "away_pending_lock"
    AWAY_LOCKED = "away_locked"
    AWAY_MANUAL_OVERRIDE = "away_manual_override"
    RETURNING = "returning"
    ERROR = "error"


class LockMethod(str, Enum):
    AUTO = "auto"
    GNOME = "gnome"
    FREEDESKTOP = "freedesktop"
    LOGINCTL = "loginctl"


class PackageType(str, Enum):
    APPIMAGE = "appimage"
    DEB = "deb"
    SOURCE = "source"
    UNKNOWN = "unknown"


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(slots=True)
class TrustedDevice:
    address: str | None = None
    object_path: str | None = None
    alias: str | None = None
    paired: bool = False
    trusted: bool = False
    connected: bool = False
    rssi: int | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "address": self.address,
            "object_path": self.object_path,
            "alias": self.alias,
            "paired": self.paired,
            "trusted": self.trusted,
            "connected": self.connected,
            "rssi": self.rssi,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any] | None) -> "TrustedDevice":
        payload = payload or {}
        return cls(
            address=payload.get("address"),
            object_path=payload.get("object_path"),
            alias=payload.get("alias"),
            paired=bool(payload.get("paired", False)),
            trusted=bool(payload.get("trusted", False)),
            connected=bool(payload.get("connected", False)),
            rssi=payload.get("rssi"),
        )


@dataclass(slots=True)
class EventRecord:
    timestamp: str
    level: str
    event: str
    message: str
    context: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def new(
        cls,
        level: str,
        event: str,
        message: str,
        **context: Any,
    ) -> "EventRecord":
        return cls(
            timestamp=utc_now().isoformat(),
            level=level,
            event=event,
            message=message,
            context=context,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "level": self.level,
            "event": self.event,
            "message": self.message,
            "context": self.context,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "EventRecord":
        return cls(
            timestamp=str(payload.get("timestamp")),
            level=str(payload.get("level", "INFO")),
            event=str(payload.get("event", "unknown")),
            message=str(payload.get("message", "")),
            context=dict(payload.get("context", {})),
        )


@dataclass(slots=True)
class StatusSnapshot:
    current_state: ProtectionState = ProtectionState.STARTING
    trusted_device: TrustedDevice = field(default_factory=TrustedDevice)
    protection_enabled: bool = True
    bluetooth_available: bool = False
    adapter_powered: bool = False
    connection_state: str = "unknown"
    proximity_summary: str = "Starting"
    session_locked: bool = False
    manual_override_active: bool = False
    last_lock_reason: str | None = None
    last_seen_at: str | None = None
    away_since: str | None = None
    last_state_change_at: str | None = None
    reconnect_state: str = "idle"
    last_error: str | None = None
    update_available: bool = False
    latest_version: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "current_state": self.current_state.value,
            "trusted_device": self.trusted_device.to_dict(),
            "protection_enabled": self.protection_enabled,
            "bluetooth_available": self.bluetooth_available,
            "adapter_powered": self.adapter_powered,
            "connection_state": self.connection_state,
            "proximity_summary": self.proximity_summary,
            "session_locked": self.session_locked,
            "manual_override_active": self.manual_override_active,
            "last_lock_reason": self.last_lock_reason,
            "last_seen_at": self.last_seen_at,
            "away_since": self.away_since,
            "last_state_change_at": self.last_state_change_at,
            "reconnect_state": self.reconnect_state,
            "last_error": self.last_error,
            "update_available": self.update_available,
            "latest_version": self.latest_version,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any] | None) -> "StatusSnapshot":
        payload = payload or {}
        state_value = str(payload.get("current_state", ProtectionState.STARTING.value))
        try:
            current_state = ProtectionState(state_value)
        except ValueError:
            current_state = ProtectionState.ERROR

        return cls(
            current_state=current_state,
            trusted_device=TrustedDevice.from_dict(payload.get("trusted_device")),
            protection_enabled=bool(payload.get("protection_enabled", True)),
            bluetooth_available=bool(payload.get("bluetooth_available", False)),
            adapter_powered=bool(payload.get("adapter_powered", False)),
            connection_state=str(payload.get("connection_state", "unknown")),
            proximity_summary=str(payload.get("proximity_summary", "Unknown")),
            session_locked=bool(payload.get("session_locked", False)),
            manual_override_active=bool(payload.get("manual_override_active", False)),
            last_lock_reason=payload.get("last_lock_reason"),
            last_seen_at=payload.get("last_seen_at"),
            away_since=payload.get("away_since"),
            last_state_change_at=payload.get("last_state_change_at"),
            reconnect_state=str(payload.get("reconnect_state", "idle")),
            last_error=payload.get("last_error"),
            update_available=bool(payload.get("update_available", False)),
            latest_version=payload.get("latest_version"),
        )
