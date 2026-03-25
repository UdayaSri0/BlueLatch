from __future__ import annotations

from bluelatch.bluetooth.models import BluezDevice, choose_device_display_name
from bluelatch.models import TrustedDevice


def test_choose_display_name_prefers_real_name_over_mac_alias() -> None:
    assert choose_device_display_name("Galaxy S24", "30:9A:1B:93:FC:A5") == "Galaxy S24"


def test_choose_display_name_skips_mac_like_alias() -> None:
    assert choose_device_display_name("", "30:9A:1B:93:FC:A5") == "Unnamed device"


def test_choose_display_name_falls_back_to_alias_when_human_readable() -> None:
    assert choose_device_display_name("", "Work Phone") == "Work Phone"


def test_bluez_device_exposes_friendly_display_name() -> None:
    device = BluezDevice(
        object_path="/org/bluez/hci0/dev_30_9A_1B_93_FC_A5",
        address="30:9A:1B:93:FC:A5",
        alias="30:9A:1B:93:FC:A5",
        name="Galaxy S24",
        paired=False,
        trusted=False,
        connected=False,
    )
    assert device.display_name == "Galaxy S24"


def test_trusted_device_persistence_keeps_identity_fields() -> None:
    trusted = TrustedDevice(
        address="30:9A:1B:93:FC:A5",
        object_path="/org/bluez/hci0/dev_30_9A_1B_93_FC_A5",
        alias="Galaxy S24",
        name="Galaxy S24",
        paired=True,
        trusted=True,
        connected=True,
        rssi=-61,
    )
    restored = TrustedDevice.from_dict(trusted.to_dict())
    assert restored.address == trusted.address
    assert restored.object_path == trusted.object_path
    assert restored.alias == trusted.alias
    assert restored.name == trusted.name
