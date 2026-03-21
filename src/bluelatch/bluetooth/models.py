from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class BluezDevice:
    object_path: str
    address: str
    alias: str
    paired: bool
    trusted: bool
    connected: bool
    rssi: int | None = None


@dataclass(slots=True)
class AdapterState:
    object_path: str | None = None
    powered: bool = False
    discovering: bool = False
