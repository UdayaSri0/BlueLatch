from __future__ import annotations

import os

from bluelatch.config.manager import ConfigManager
from bluelatch.config.models import AppConfig
from bluelatch.models import PresenceMode
from bluelatch.util.xdg import AppPaths


def test_config_persistence_round_trip(tmp_path) -> None:
    paths = AppPaths(app_slug="bluelatch-test")
    manager = ConfigManager(paths=paths, config_path=tmp_path / "config.json")
    config = AppConfig()
    config.protection.mode = PresenceMode.DISCONNECT_ONLY
    config.bluetooth.trusted_device.address = "AA:BB:CC:DD:EE:FF"
    manager.save(config)

    loaded = manager.load()
    assert loaded.protection.mode is PresenceMode.DISCONNECT_ONLY
    assert loaded.bluetooth.trusted_device.address == "AA:BB:CC:DD:EE:FF"
    assert oct(os.stat(tmp_path / "config.json").st_mode & 0o777) == "0o600"
