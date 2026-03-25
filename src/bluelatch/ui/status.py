from __future__ import annotations

from bluelatch.models import StatusSnapshot
from bluelatch.runtime import RuntimeStore

try:
    import gi

    gi.require_version("Adw", "1")
    gi.require_version("Gtk", "4.0")
    from gi.repository import Adw, GLib, Gtk
except ImportError as exc:  # pragma: no cover - UI-only import
    raise RuntimeError("PyGObject with GTK4/libadwaita is required for the UI") from exc


class StatusPage(Gtk.Box):
    def __init__(self, runtime_store: RuntimeStore) -> None:
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=18)
        self.runtime_store = runtime_store
        self.set_margin_top(18)
        self.set_margin_bottom(18)
        self.set_margin_start(18)
        self.set_margin_end(18)

        title = Gtk.Label(label="Live Status")
        title.add_css_class("title-2")
        title.set_xalign(0)
        self.append(title)

        self.group = Adw.PreferencesGroup()
        self.device_row = Adw.ActionRow(title="Trusted Device")
        self.bluetooth_row = Adw.ActionRow(title="Bluetooth")
        self.connection_row = Adw.ActionRow(title="Connection")
        self.state_row = Adw.ActionRow(title="Protection State")
        self.lock_row = Adw.ActionRow(title="Last Lock Reason")
        self.last_seen_row = Adw.ActionRow(title="Last Seen")
        self.override_row = Adw.ActionRow(title="Manual Override")
        self.reconnect_row = Adw.ActionRow(title="Reconnect")
        for row in (
            self.device_row,
            self.bluetooth_row,
            self.connection_row,
            self.state_row,
            self.lock_row,
            self.last_seen_row,
            self.override_row,
            self.reconnect_row,
        ):
            self.group.add(row)
        self.append(self.group)

        GLib.timeout_add_seconds(2, self._poll)
        self.refresh()

    def refresh(self) -> None:
        status = self.runtime_store.load_status()
        self._apply_status(status)

    def _poll(self) -> bool:
        self.refresh()
        return True

    def _apply_status(self, status: StatusSnapshot) -> None:
        device_name = status.trusted_device.alias or status.trusted_device.name or status.trusted_device.address or "Not configured"
        self.device_row.set_subtitle(device_name)
        self.bluetooth_row.set_subtitle(
            f"{'Available' if status.bluetooth_available else 'Unavailable'} / "
            f"{'Powered' if status.adapter_powered else 'Off'}"
        )
        self.connection_row.set_subtitle(status.connection_state)
        self.state_row.set_subtitle(status.current_state.value)
        self.lock_row.set_subtitle(status.last_lock_reason or "No automatic lock recorded")
        self.last_seen_row.set_subtitle(status.last_seen_at or "Never")
        self.override_row.set_subtitle("Active" if status.manual_override_active else "Inactive")
        self.reconnect_row.set_subtitle(status.reconnect_state)
