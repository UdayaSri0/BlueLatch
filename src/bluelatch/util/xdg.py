from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _xdg_path(env_name: str, default: str) -> Path:
    raw = os.environ.get(env_name)
    return Path(raw).expanduser() if raw else Path(default).expanduser()


@dataclass(slots=True)
class AppPaths:
    app_name: str = "BlueLatch"
    app_slug: str = "bluelatch"

    @property
    def config_dir(self) -> Path:
        return _xdg_path("XDG_CONFIG_HOME", "~/.config") / self.app_slug

    @property
    def state_dir(self) -> Path:
        return _xdg_path("XDG_STATE_HOME", "~/.local/state") / self.app_slug

    @property
    def cache_dir(self) -> Path:
        return _xdg_path("XDG_CACHE_HOME", "~/.cache") / self.app_slug

    @property
    def runtime_dir(self) -> Path:
        base = os.environ.get("XDG_RUNTIME_DIR")
        if base:
            return Path(base) / self.app_slug
        return self.cache_dir / "runtime"

    @property
    def autostart_dir(self) -> Path:
        return _xdg_path("XDG_CONFIG_HOME", "~/.config") / "autostart"

    @property
    def systemd_user_dir(self) -> Path:
        return _xdg_path("XDG_CONFIG_HOME", "~/.config") / "systemd" / "user"

    @property
    def config_file(self) -> Path:
        return self.config_dir / "config.json"

    @property
    def status_file(self) -> Path:
        return self.state_dir / "status.json"

    @property
    def history_file(self) -> Path:
        return self.state_dir / "events.jsonl"

    @property
    def log_file(self) -> Path:
        return self.state_dir / "bluelatch.log"

    @property
    def agent_lock_file(self) -> Path:
        return self.runtime_dir / "agent.lock"

    def ensure(self) -> None:
        for directory in (
            self.config_dir,
            self.state_dir,
            self.cache_dir,
            self.runtime_dir,
            self.systemd_user_dir,
        ):
            directory.mkdir(parents=True, exist_ok=True)
