from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from typing import Callable

from bluelatch.config.models import AppConfig, SCHEMA_VERSION
from bluelatch.util.files import atomic_write_json, load_json
from bluelatch.util.xdg import AppPaths


def migrate_config(config: AppConfig) -> AppConfig:
    if config.schema_version < SCHEMA_VERSION:
        return replace(config, schema_version=SCHEMA_VERSION)
    return config


class ConfigManager:
    def __init__(self, paths: AppPaths | None = None, config_path: Path | None = None) -> None:
        self.paths = paths or AppPaths()
        self.paths.ensure()
        self.config_path = config_path or self.paths.config_file
        self._last_mtime: float | None = None

    def load(self) -> AppConfig:
        raw = load_json(self.config_path, default=AppConfig().to_dict())
        config = migrate_config(AppConfig.from_dict(raw))
        if not self.config_path.exists():
            self.save(config)
        self._remember_mtime()
        return config

    def save(self, config: AppConfig) -> None:
        atomic_write_json(self.config_path, migrate_config(config).to_dict())
        self._remember_mtime()

    def update(self, mutator: Callable[[AppConfig], AppConfig]) -> AppConfig:
        config = self.load()
        updated = mutator(config)
        self.save(updated)
        return updated

    def has_external_change(self) -> bool:
        if not self.config_path.exists():
            return False
        current_mtime = self.config_path.stat().st_mtime
        if self._last_mtime is None:
            self._last_mtime = current_mtime
            return False
        if current_mtime > self._last_mtime:
            self._last_mtime = current_mtime
            return True
        return False

    def _remember_mtime(self) -> None:
        if self.config_path.exists():
            self._last_mtime = self.config_path.stat().st_mtime
