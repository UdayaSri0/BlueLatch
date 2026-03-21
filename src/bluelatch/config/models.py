from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from bluelatch.models import LockMethod, PresenceMode, TrustedDevice


SCHEMA_VERSION = 1


def _coerce_int(value: Any, default: int, minimum: int | None = None) -> int:
    try:
        result = int(value)
    except (TypeError, ValueError):
        result = default
    if minimum is not None:
        result = max(minimum, result)
    return result


def _coerce_float(value: Any, default: float, minimum: float | None = None) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError):
        result = default
    if minimum is not None:
        result = max(minimum, result)
    return result


@dataclass(slots=True)
class ProtectionConfig:
    enabled: bool = True
    mode: PresenceMode = PresenceMode.HYBRID
    away_grace_seconds: int = 20
    maybe_away_seconds: int = 4
    return_grace_seconds: int = 5
    near_threshold: int = -70
    far_threshold: int = -82
    signal_smoothing_window: int = 5

    def to_dict(self) -> dict[str, Any]:
        return {
            "enabled": self.enabled,
            "mode": self.mode.value,
            "away_grace_seconds": self.away_grace_seconds,
            "maybe_away_seconds": self.maybe_away_seconds,
            "return_grace_seconds": self.return_grace_seconds,
            "near_threshold": self.near_threshold,
            "far_threshold": self.far_threshold,
            "signal_smoothing_window": self.signal_smoothing_window,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any] | None) -> "ProtectionConfig":
        payload = payload or {}
        mode_name = str(payload.get("mode", PresenceMode.HYBRID.value))
        try:
            mode = PresenceMode(mode_name)
        except ValueError:
            mode = PresenceMode.HYBRID
        return cls(
            enabled=bool(payload.get("enabled", True)),
            mode=mode,
            away_grace_seconds=_coerce_int(payload.get("away_grace_seconds"), 20, 1),
            maybe_away_seconds=_coerce_int(payload.get("maybe_away_seconds"), 4, 0),
            return_grace_seconds=_coerce_int(payload.get("return_grace_seconds"), 5, 0),
            near_threshold=_coerce_int(payload.get("near_threshold"), -70),
            far_threshold=_coerce_int(payload.get("far_threshold"), -82),
            signal_smoothing_window=_coerce_int(
                payload.get("signal_smoothing_window"),
                5,
                1,
            ),
        )


@dataclass(slots=True)
class BluetoothConfig:
    trusted_device: TrustedDevice = field(default_factory=TrustedDevice)
    auto_reconnect: bool = True
    reconnect_initial_seconds: int = 5
    reconnect_max_seconds: int = 300
    reconnect_jitter_ratio: float = 0.2

    def to_dict(self) -> dict[str, Any]:
        return {
            "trusted_device": self.trusted_device.to_dict(),
            "auto_reconnect": self.auto_reconnect,
            "reconnect_initial_seconds": self.reconnect_initial_seconds,
            "reconnect_max_seconds": self.reconnect_max_seconds,
            "reconnect_jitter_ratio": self.reconnect_jitter_ratio,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any] | None) -> "BluetoothConfig":
        payload = payload or {}
        return cls(
            trusted_device=TrustedDevice.from_dict(payload.get("trusted_device")),
            auto_reconnect=bool(payload.get("auto_reconnect", True)),
            reconnect_initial_seconds=_coerce_int(
                payload.get("reconnect_initial_seconds"),
                5,
                1,
            ),
            reconnect_max_seconds=_coerce_int(
                payload.get("reconnect_max_seconds"),
                300,
                5,
            ),
            reconnect_jitter_ratio=_coerce_float(
                payload.get("reconnect_jitter_ratio"),
                0.2,
                0.0,
            ),
        )


@dataclass(slots=True)
class SessionConfig:
    lock_method: LockMethod = LockMethod.AUTO
    notifications_enabled: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "lock_method": self.lock_method.value,
            "notifications_enabled": self.notifications_enabled,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any] | None) -> "SessionConfig":
        payload = payload or {}
        method_name = str(payload.get("lock_method", LockMethod.AUTO.value))
        try:
            lock_method = LockMethod(method_name)
        except ValueError:
            lock_method = LockMethod.AUTO
        return cls(
            lock_method=lock_method,
            notifications_enabled=bool(payload.get("notifications_enabled", True)),
        )


@dataclass(slots=True)
class StartupConfig:
    start_on_login: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "start_on_login": self.start_on_login,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any] | None) -> "StartupConfig":
        payload = payload or {}
        return cls(start_on_login=bool(payload.get("start_on_login", True)))


@dataclass(slots=True)
class UpdateConfig:
    check_on_startup: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "check_on_startup": self.check_on_startup,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any] | None) -> "UpdateConfig":
        payload = payload or {}
        return cls(check_on_startup=bool(payload.get("check_on_startup", True)))


@dataclass(slots=True)
class LoggingConfig:
    debug_enabled: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {"debug_enabled": self.debug_enabled}

    @classmethod
    def from_dict(cls, payload: dict[str, Any] | None) -> "LoggingConfig":
        payload = payload or {}
        return cls(debug_enabled=bool(payload.get("debug_enabled", False)))


@dataclass(slots=True)
class AppConfig:
    schema_version: int = SCHEMA_VERSION
    protection: ProtectionConfig = field(default_factory=ProtectionConfig)
    bluetooth: BluetoothConfig = field(default_factory=BluetoothConfig)
    session: SessionConfig = field(default_factory=SessionConfig)
    startup: StartupConfig = field(default_factory=StartupConfig)
    updates: UpdateConfig = field(default_factory=UpdateConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "protection": self.protection.to_dict(),
            "bluetooth": self.bluetooth.to_dict(),
            "session": self.session.to_dict(),
            "startup": self.startup.to_dict(),
            "updates": self.updates.to_dict(),
            "logging": self.logging.to_dict(),
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any] | None) -> "AppConfig":
        payload = payload or {}
        return cls(
            schema_version=_coerce_int(payload.get("schema_version"), SCHEMA_VERSION, 1),
            protection=ProtectionConfig.from_dict(payload.get("protection")),
            bluetooth=BluetoothConfig.from_dict(payload.get("bluetooth")),
            session=SessionConfig.from_dict(payload.get("session")),
            startup=StartupConfig.from_dict(payload.get("startup")),
            updates=UpdateConfig.from_dict(payload.get("updates")),
            logging=LoggingConfig.from_dict(payload.get("logging")),
        )
