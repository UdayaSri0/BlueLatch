from __future__ import annotations

import logging
import os
from typing import Callable

try:
    from gi.repository import Gio, GLib
except ImportError as exc:  # pragma: no cover - integration-only import
    raise RuntimeError(
        "PyGObject is required for BlueLatch session integration",
    ) from exc


SessionCallback = Callable[[bool], None]
ResumeCallback = Callable[[], None]


class SessionMonitor:
    def __init__(self, logger: logging.Logger) -> None:
        self.logger = logger
        self.session_bus = Gio.bus_get_sync(Gio.BusType.SESSION, None)
        self.system_bus = Gio.bus_get_sync(Gio.BusType.SYSTEM, None)
        self.is_locked = False
        self.backend = "unknown"
        self._state_callbacks: list[SessionCallback] = []
        self._resume_callbacks: list[ResumeCallback] = []
        self._session_path: str | None = None

    def start(self) -> None:
        self._subscribe_gnome()
        self._session_path = self._resolve_logind_session_path()
        if self._session_path:
            self._subscribe_logind_session(self._session_path)
        self._subscribe_prepare_for_sleep()
        self.refresh()
        GLib.timeout_add_seconds(2, self._poll_state)

    def on_state_change(self, callback: SessionCallback) -> None:
        self._state_callbacks.append(callback)

    def on_resume(self, callback: ResumeCallback) -> None:
        self._resume_callbacks.append(callback)

    def refresh(self) -> None:
        locked = self._query_gnome_locked()
        if locked is not None:
            self._set_locked(locked, backend="gnome")
            return
        locked = self._query_logind_locked()
        if locked is not None:
            self._set_locked(locked, backend="logind")

    def _subscribe_gnome(self) -> None:
        self.session_bus.signal_subscribe(
            "org.gnome.ScreenSaver",
            "org.gnome.ScreenSaver",
            "ActiveChanged",
            "/org/gnome/ScreenSaver",
            None,
            Gio.DBusSignalFlags.NONE,
            self._on_gnome_active_changed,
        )

    def _subscribe_logind_session(self, session_path: str) -> None:
        self.system_bus.signal_subscribe(
            "org.freedesktop.login1",
            "org.freedesktop.login1.Session",
            "Lock",
            session_path,
            None,
            Gio.DBusSignalFlags.NONE,
            self._on_logind_lock,
        )
        self.system_bus.signal_subscribe(
            "org.freedesktop.login1",
            "org.freedesktop.login1.Session",
            "Unlock",
            session_path,
            None,
            Gio.DBusSignalFlags.NONE,
            self._on_logind_unlock,
        )

    def _subscribe_prepare_for_sleep(self) -> None:
        self.system_bus.signal_subscribe(
            "org.freedesktop.login1",
            "org.freedesktop.login1.Manager",
            "PrepareForSleep",
            "/org/freedesktop/login1",
            None,
            Gio.DBusSignalFlags.NONE,
            self._on_prepare_for_sleep,
        )

    def _query_gnome_locked(self) -> bool | None:
        try:
            response = self.session_bus.call_sync(
                "org.gnome.ScreenSaver",
                "/org/gnome/ScreenSaver",
                "org.gnome.ScreenSaver",
                "GetActive",
                None,
                GLib.VariantType("(b)"),
                Gio.DBusCallFlags.NONE,
                2000,
                None,
            )
        except Exception:
            return None
        return bool(response.unpack()[0])

    def _query_logind_locked(self) -> bool | None:
        if not self._session_path:
            return None
        try:
            response = self.system_bus.call_sync(
                "org.freedesktop.login1",
                self._session_path,
                "org.freedesktop.DBus.Properties",
                "Get",
                GLib.Variant("(ss)", ("org.freedesktop.login1.Session", "LockedHint")),
                GLib.VariantType("(v)"),
                Gio.DBusCallFlags.NONE,
                2000,
                None,
            )
        except Exception:
            return None
        return bool(response.unpack()[0])

    def _resolve_logind_session_path(self) -> str | None:
        session_id = os.environ.get("XDG_SESSION_ID")
        method = "GetSession" if session_id else "GetSessionByPID"
        args = GLib.Variant("(s)", (session_id,)) if session_id else GLib.Variant("(u)", (os.getpid(),))
        try:
            response = self.system_bus.call_sync(
                "org.freedesktop.login1",
                "/org/freedesktop/login1",
                "org.freedesktop.login1.Manager",
                method,
                args,
                GLib.VariantType("(o)"),
                Gio.DBusCallFlags.NONE,
                2000,
                None,
            )
        except Exception:
            self.logger.exception("Failed to resolve current login1 session")
            return None
        return str(response.unpack()[0])

    def _poll_state(self) -> bool:
        self.refresh()
        return True

    def _set_locked(self, locked: bool, *, backend: str) -> None:
        self.backend = backend
        if self.is_locked == locked:
            return
        self.is_locked = locked
        for callback in self._state_callbacks:
            callback(locked)

    def _on_gnome_active_changed(
        self,
        _connection: Gio.DBusConnection,
        _sender_name: str,
        _object_path: str,
        _interface_name: str,
        _signal_name: str,
        parameters: GLib.Variant,
    ) -> None:
        self._set_locked(bool(parameters.unpack()[0]), backend="gnome")

    def _on_logind_lock(self, *_args: object) -> None:
        self._set_locked(True, backend="logind")

    def _on_logind_unlock(self, *_args: object) -> None:
        self._set_locked(False, backend="logind")

    def _on_prepare_for_sleep(
        self,
        _connection: Gio.DBusConnection,
        _sender_name: str,
        _object_path: str,
        _interface_name: str,
        _signal_name: str,
        parameters: GLib.Variant,
    ) -> None:
        preparing = bool(parameters.unpack()[0])
        if not preparing:
            for callback in self._resume_callbacks:
                callback()
