from __future__ import annotations

from dataclasses import replace

from bluelatch.bluetooth.bluez import BluezClient
from bluelatch.bluetooth.models import BluezDevice
from bluelatch.config.manager import ConfigManager
from bluelatch.models import TrustedDevice

try:
    import gi

    gi.require_version("Adw", "1")
    gi.require_version("Gtk", "4.0")
    from gi.repository import Adw, GLib, Gtk
except ImportError as exc:  # pragma: no cover - UI-only import
    raise RuntimeError("PyGObject with GTK4/libadwaita is required for the UI") from exc


class DevicesPage(Gtk.Box):
    def __init__(self, config_manager: ConfigManager, bluez: BluezClient) -> None:
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self.config_manager = config_manager
        self.bluez = bluez
        self.selected_device: BluezDevice | None = None
        self.set_margin_top(18)
        self.set_margin_bottom(18)
        self.set_margin_start(18)
        self.set_margin_end(18)

        header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        title = Gtk.Label(label="Trusted Device")
        title.add_css_class("title-2")
        title.set_xalign(0)
        title.set_hexpand(True)

        scan_button = Gtk.Button(label="Scan")
        scan_button.connect("clicked", self._on_scan_clicked)
        refresh_button = Gtk.Button(label="Refresh")
        refresh_button.connect("clicked", lambda *_args: self.refresh())
        pair_button = Gtk.Button(label="Pair")
        pair_button.connect("clicked", self._pair_selected)
        trust_button = Gtk.Button(label="Trust")
        trust_button.connect("clicked", self._trust_selected)
        select_button = Gtk.Button(label="Use Selected")
        select_button.connect("clicked", self._select_selected)
        for button in (scan_button, refresh_button, pair_button, trust_button, select_button):
            header.append(button)

        header.prepend(title)

        self.status_label = Gtk.Label(label="Choose one trusted phone device.")
        self.status_label.set_xalign(0)
        self.status_label.set_wrap(True)

        self.listbox = Gtk.ListBox()
        self.listbox.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.listbox.connect("row-selected", self._on_row_selected)

        scroll = Gtk.ScrolledWindow()
        scroll.set_vexpand(True)
        scroll.set_child(self.listbox)

        self.append(header)
        self.append(self.status_label)
        self.append(scroll)

        self.refresh()

    def refresh(self) -> None:
        try:
            self.bluez.refresh()
            devices = self.bluez.list_devices()
        except Exception as exc:
            self.status_label.set_text(f"Bluetooth scan failed: {exc}")
            return
        self._rebuild_list(devices)
        self.status_label.set_text(f"Found {len(devices)} Bluetooth devices.")

    def _rebuild_list(self, devices: list[BluezDevice]) -> None:
        child = self.listbox.get_first_child()
        while child is not None:
            next_child = child.get_next_sibling()
            self.listbox.remove(child)
            child = next_child

        trusted_address = self.config_manager.load().bluetooth.trusted_device.address
        for device in devices:
            row = Adw.ActionRow(
                title=device.alias or device.address,
                subtitle=(
                    f"{device.address} | "
                    f"{'Connected' if device.connected else 'Disconnected'} | "
                    f"{'Trusted' if device.trusted else 'Untrusted'} | "
                    f"{'Paired' if device.paired else 'Unpaired'}"
                ),
            )
            row.device = device  # type: ignore[attr-defined]
            if trusted_address and trusted_address.upper() == device.address.upper():
                badge = Gtk.Label(label="Trusted")
                badge.add_css_class("accent")
                row.add_suffix(badge)
            self.listbox.append(row)

    def _on_row_selected(self, _listbox: Gtk.ListBox, row: Gtk.ListBoxRow | None) -> None:
        if row is None:
            self.selected_device = None
            return
        self.selected_device = getattr(row, "device", None)

    def _on_scan_clicked(self, *_args: object) -> None:
        try:
            self.bluez.start_discovery()
            self.status_label.set_text("Discovery started for 10 seconds...")
            GLib.timeout_add_seconds(10, self._stop_scan)
        except Exception as exc:
            self.status_label.set_text(f"Could not start discovery: {exc}")

    def _stop_scan(self) -> bool:
        try:
            self.bluez.stop_discovery()
        except Exception:
            pass
        self.refresh()
        return False

    def _pair_selected(self, *_args: object) -> None:
        if not self.selected_device:
            self.status_label.set_text("Select a device to pair.")
            return
        try:
            self.bluez.pair_device(self.selected_device.object_path)
            self.status_label.set_text(f"Pairing started with {self.selected_device.alias}.")
            self.refresh()
        except Exception as exc:
            self.status_label.set_text(f"Pairing failed: {exc}")

    def _trust_selected(self, *_args: object) -> None:
        if not self.selected_device:
            self.status_label.set_text("Select a device to trust.")
            return
        try:
            self.bluez.trust_device(self.selected_device.object_path, True)
            self.status_label.set_text(f"{self.selected_device.alias} marked as trusted.")
            self.refresh()
        except Exception as exc:
            self.status_label.set_text(f"Could not mark device as trusted: {exc}")

    def _select_selected(self, *_args: object) -> None:
        if not self.selected_device:
            self.status_label.set_text("Select a device first.")
            return

        device = self.selected_device

        def mutator(config):
            config.bluetooth.trusted_device = TrustedDevice(
                address=device.address,
                object_path=device.object_path,
                alias=device.alias,
                paired=device.paired,
                trusted=device.trusted,
                connected=device.connected,
                rssi=device.rssi,
            )
            return config

        self.config_manager.update(mutator)
        self.status_label.set_text(f"{device.alias} is now the trusted phone.")
        self.refresh()
