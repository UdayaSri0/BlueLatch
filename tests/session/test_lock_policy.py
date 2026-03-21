from __future__ import annotations

from bluelatch.models import LockMethod


def test_lock_method_enum_values_are_stable() -> None:
    assert LockMethod.AUTO.value == "auto"
    assert LockMethod.GNOME.value == "gnome"
    assert LockMethod.LOGINCTL.value == "loginctl"
