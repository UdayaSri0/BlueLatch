from __future__ import annotations

import shlex
from dataclasses import dataclass

from bluelatch.startup.autostart import AutostartManager
from bluelatch.startup.systemd import SystemdUserServiceManager
from bluelatch.util.xdg import AppPaths


@dataclass(slots=True)
class StartupChangeResult:
    enabled: bool
    mechanism: str
    detail: str


class StartupManager:
    def __init__(self, paths: AppPaths | None = None) -> None:
        self.paths = paths or AppPaths()
        self.systemd = SystemdUserServiceManager(self.paths)
        self.autostart = AutostartManager(self.paths)

    def set_start_on_login(self, enabled: bool, command: list[str]) -> StartupChangeResult:
        if enabled:
            if self.systemd.is_available():
                self.systemd.install(command)
                self.systemd.enable()
                return StartupChangeResult(
                    enabled=True,
                    mechanism="systemd",
                    detail=str(self.systemd.service_file),
                )
            self.autostart.enable(shlex.join(command))
            return StartupChangeResult(
                enabled=True,
                mechanism="autostart",
                detail=str(self.autostart.desktop_file),
            )

        if self.systemd.is_available():
            self.systemd.disable()
        self.autostart.disable()
        return StartupChangeResult(enabled=False, mechanism="disabled", detail="removed")
