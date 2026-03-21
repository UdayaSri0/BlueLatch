from __future__ import annotations

import logging
import os
import subprocess
from dataclasses import dataclass

from bluelatch.models import LockMethod

try:
    from gi.repository import Gio
except ImportError as exc:  # pragma: no cover - integration-only import
    raise RuntimeError(
        "PyGObject is required for BlueLatch session integration",
    ) from exc


@dataclass(slots=True)
class LockResult:
    success: bool
    strategy: str
    message: str | None = None


class LockManager:
    def __init__(self, logger: logging.Logger) -> None:
        self.logger = logger
        self.session_bus = Gio.bus_get_sync(Gio.BusType.SESSION, None)

    def lock(self, method: LockMethod) -> LockResult:
        if method is LockMethod.AUTO:
            strategies = [
                ("gnome", self._lock_gnome),
                ("freedesktop", self._lock_freedesktop),
                ("loginctl", self._lock_loginctl),
            ]
        elif method is LockMethod.GNOME:
            strategies = [("gnome", self._lock_gnome)]
        elif method is LockMethod.FREEDESKTOP:
            strategies = [("freedesktop", self._lock_freedesktop)]
        else:
            strategies = [("loginctl", self._lock_loginctl)]

        errors: list[str] = []
        for strategy_name, strategy in strategies:
            try:
                strategy()
                return LockResult(True, strategy_name)
            except Exception as exc:
                message = f"{strategy_name} lock failed: {exc}"
                self.logger.warning(message)
                errors.append(message)
        return LockResult(False, strategies[-1][0], "; ".join(errors))

    def _lock_gnome(self) -> None:
        self.session_bus.call_sync(
            "org.gnome.ScreenSaver",
            "/org/gnome/ScreenSaver",
            "org.gnome.ScreenSaver",
            "Lock",
            None,
            None,
            Gio.DBusCallFlags.NONE,
            -1,
            None,
        )

    def _lock_freedesktop(self) -> None:
        self.session_bus.call_sync(
            "org.freedesktop.ScreenSaver",
            "/org/freedesktop/ScreenSaver",
            "org.freedesktop.ScreenSaver",
            "Lock",
            None,
            None,
            Gio.DBusCallFlags.NONE,
            -1,
            None,
        )

    def _lock_loginctl(self) -> None:
        session_id = os.environ.get("XDG_SESSION_ID")
        command = ["loginctl", "lock-session"]
        if session_id:
            command.append(session_id)
        subprocess.run(
            command,
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
        )
