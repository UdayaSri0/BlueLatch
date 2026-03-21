from __future__ import annotations

import logging
from typing import Callable

from bluelatch.bluetooth.models import AdapterState, BluezDevice
from bluelatch.models import TrustedDevice

try:
    from gi.repository import Gio, GLib
except ImportError as exc:  # pragma: no cover - integration-only import
    raise RuntimeError(
        "PyGObject is required for BlueLatch Bluetooth integration",
    ) from exc


BluezCallback = Callable[[], None]


class BluezClient:
    BLUEZ_BUS = "org.bluez"

    def __init__(self, logger: logging.Logger) -> None:
        self.logger = logger
        self.system_bus = Gio.bus_get_sync(Gio.BusType.SYSTEM, None)
        self._device_callbacks: list[BluezCallback] = []
        self._adapter_callbacks: list[BluezCallback] = []
        self._dirty = True
        self._managed_objects: dict[str, dict[str, dict[str, object]]] = {}
        self.adapter = AdapterState()

    @property
    def available(self) -> bool:
        return bool(self._managed_objects)

    def start(self) -> None:
        self.refresh()
        self.system_bus.signal_subscribe(
            self.BLUEZ_BUS,
            "org.freedesktop.DBus.ObjectManager",
            "InterfacesAdded",
            None,
            None,
            Gio.DBusSignalFlags.NONE,
            self._on_objects_changed,
        )
        self.system_bus.signal_subscribe(
            self.BLUEZ_BUS,
            "org.freedesktop.DBus.ObjectManager",
            "InterfacesRemoved",
            None,
            None,
            Gio.DBusSignalFlags.NONE,
            self._on_objects_changed,
        )
        self.system_bus.signal_subscribe(
            self.BLUEZ_BUS,
            "org.freedesktop.DBus.Properties",
            "PropertiesChanged",
            None,
            None,
            Gio.DBusSignalFlags.NONE,
            self._on_properties_changed,
        )

    def on_device_change(self, callback: BluezCallback) -> None:
        self._device_callbacks.append(callback)

    def on_adapter_change(self, callback: BluezCallback) -> None:
        self._adapter_callbacks.append(callback)

    def refresh(self) -> None:
        try:
            response = self.system_bus.call_sync(
                self.BLUEZ_BUS,
                "/",
                "org.freedesktop.DBus.ObjectManager",
                "GetManagedObjects",
                None,
                GLib.VariantType("(a{oa{sa{sv}}})"),
                Gio.DBusCallFlags.NONE,
                -1,
                None,
            )
        except Exception:
            self.logger.exception("Failed to query BlueZ managed objects")
            self._managed_objects = {}
            self.adapter = AdapterState()
            return
        self._managed_objects = response.unpack()[0]
        self._dirty = False
        self._refresh_adapter_state()

    def maybe_refresh(self) -> None:
        if self._dirty:
            self.refresh()

    def list_devices(self) -> list[BluezDevice]:
        self.maybe_refresh()
        devices: list[BluezDevice] = []
        for object_path, interfaces in self._managed_objects.items():
            device_props = interfaces.get("org.bluez.Device1")
            if not device_props:
                continue
            devices.append(
                BluezDevice(
                    object_path=object_path,
                    address=str(device_props.get("Address", "")),
                    alias=str(
                        device_props.get("Alias")
                        or device_props.get("Name")
                        or device_props.get("Address")
                    ),
                    paired=bool(device_props.get("Paired", False)),
                    trusted=bool(device_props.get("Trusted", False)),
                    connected=bool(device_props.get("Connected", False)),
                    rssi=self._coerce_optional_int(device_props.get("RSSI")),
                ),
            )
        devices.sort(key=lambda item: (not item.connected, item.alias.lower()))
        return devices

    def resolve_trusted_device(self, trusted_device: TrustedDevice) -> BluezDevice | None:
        self.maybe_refresh()
        if trusted_device.object_path:
            for device in self.list_devices():
                if device.object_path == trusted_device.object_path:
                    return device
        if trusted_device.address:
            normalized = trusted_device.address.upper()
            for device in self.list_devices():
                if device.address.upper() == normalized:
                    return device
        return None

    def start_discovery(self) -> None:
        if not self.adapter.object_path:
            self.refresh()
        if not self.adapter.object_path:
            raise RuntimeError("No Bluetooth adapter found")
        self._call_method(self.adapter.object_path, "org.bluez.Adapter1", "StartDiscovery")
        self._dirty = True

    def stop_discovery(self) -> None:
        if self.adapter.object_path:
            self._call_method(self.adapter.object_path, "org.bluez.Adapter1", "StopDiscovery")
            self._dirty = True

    def pair_device(self, object_path: str) -> None:
        self._call_method(object_path, "org.bluez.Device1", "Pair")
        self._dirty = True

    def trust_device(self, object_path: str, trusted: bool = True) -> None:
        self.system_bus.call_sync(
            self.BLUEZ_BUS,
            object_path,
            "org.freedesktop.DBus.Properties",
            "Set",
            GLib.Variant(
                "(ssv)",
                ("org.bluez.Device1", "Trusted", GLib.Variant("b", trusted)),
            ),
            None,
            Gio.DBusCallFlags.NONE,
            -1,
            None,
        )
        self._dirty = True

    def connect_device(self, object_path: str) -> None:
        self._call_method(object_path, "org.bluez.Device1", "Connect")
        self._dirty = True

    def disconnect_device(self, object_path: str) -> None:
        self._call_method(object_path, "org.bluez.Device1", "Disconnect")
        self._dirty = True

    def _call_method(self, object_path: str, interface: str, method: str) -> None:
        self.system_bus.call_sync(
            self.BLUEZ_BUS,
            object_path,
            interface,
            method,
            None,
            None,
            Gio.DBusCallFlags.NONE,
            -1,
            None,
        )

    def _refresh_adapter_state(self) -> None:
        adapter = AdapterState()
        for object_path, interfaces in self._managed_objects.items():
            adapter_props = interfaces.get("org.bluez.Adapter1")
            if not adapter_props:
                continue
            adapter = AdapterState(
                object_path=object_path,
                powered=bool(adapter_props.get("Powered", False)),
                discovering=bool(adapter_props.get("Discovering", False)),
            )
            break
        self.adapter = adapter

    def _on_objects_changed(
        self,
        *_args: object,
    ) -> None:
        self._dirty = True
        for callback in self._device_callbacks:
            callback()
        for callback in self._adapter_callbacks:
            callback()

    def _on_properties_changed(
        self,
        _connection: Gio.DBusConnection,
        _sender_name: str,
        object_path: str,
        _interface_name: str,
        _signal_name: str,
        parameters: GLib.Variant,
    ) -> None:
        changed_interface, _changed_props, _invalidated = parameters.unpack()
        if changed_interface in {"org.bluez.Device1", "org.bluez.Adapter1"}:
            self._dirty = True
            if changed_interface == "org.bluez.Device1":
                for callback in self._device_callbacks:
                    callback()
            if changed_interface == "org.bluez.Adapter1":
                self.logger.debug("Bluetooth adapter properties changed", extra={"context": {"path": object_path}})
                for callback in self._adapter_callbacks:
                    callback()

    @staticmethod
    def _coerce_optional_int(value: object) -> int | None:
        if value is None:
            return None
        try:
            return int(value)
        except (TypeError, ValueError):
            return None
