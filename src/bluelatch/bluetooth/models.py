from __future__ import annotations

import re
from dataclasses import dataclass


_MAC_ADDRESS_RE = re.compile(r"^(?:[0-9A-Fa-f]{2}[:\-]){5}[0-9A-Fa-f]{2}$")


@dataclass(slots=True)
class BluezDevice:
    object_path: str
    address: str
    alias: str
    name: str
    paired: bool
    trusted: bool
    connected: bool
    rssi: int | None = None

    @property
    def display_name(self) -> str:
        return choose_device_display_name(self.name, self.alias)


@dataclass(slots=True)
class AdapterState:
    object_path: str | None = None
    powered: bool = False
    discovering: bool = False


def is_mac_like(value: str | None) -> bool:
    if not value:
        return False
    return bool(_MAC_ADDRESS_RE.fullmatch(value.strip()))


def choose_device_display_name(name: str | None, alias: str | None) -> str:
    clean_name = (name or "").strip()
    clean_alias = (alias or "").strip()

    if clean_name and not is_mac_like(clean_name):
        return clean_name
    if clean_alias and not is_mac_like(clean_alias):
        return clean_alias
    return "Unnamed device"
