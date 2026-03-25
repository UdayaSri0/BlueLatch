from __future__ import annotations

import sys

from bluelatch.config.manager import ConfigManager
from bluelatch.config.models import AppConfig
from bluelatch.models import LockMethod, PresenceMode
from bluelatch.startup import StartupManager

try:
    import gi

    gi.require_version("Adw", "1")
    gi.require_version("Gtk", "4.0")
    from gi.repository import Adw, Gtk
except ImportError as exc:  # pragma: no cover - UI-only import
    raise RuntimeError("PyGObject with GTK4/libadwaita is required for the UI") from exc


PRESENCE_MODES = [
    ("Disconnect only", PresenceMode.DISCONNECT_ONLY),
    ("Weak signal or disconnect", PresenceMode.WEAK_SIGNAL_OR_DISCONNECT),
    ("Hybrid", PresenceMode.HYBRID),
]

LOCK_METHODS = [
    ("Auto", LockMethod.AUTO),
    ("GNOME", LockMethod.GNOME),
    ("Freedesktop", LockMethod.FREEDESKTOP),
    ("loginctl", LockMethod.LOGINCTL),
]


class SettingsPage(Gtk.Box):
    def __init__(self, config_manager: ConfigManager, startup_manager: StartupManager) -> None:
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.config_manager = config_manager
        self.startup_manager = startup_manager
        self.set_margin_top(0)
        self.set_margin_bottom(0)
        self.set_margin_start(0)
        self.set_margin_end(0)

        scrolled = Gtk.ScrolledWindow()
        scrolled.set_vexpand(True)
        scrolled.set_hscrollbar_policy(Gtk.PolicyType.NEVER)

        clamp = Adw.Clamp(maximum_size=860, tightening_threshold=640)
        clamp.set_margin_top(18)
        clamp.set_margin_bottom(18)
        clamp.set_margin_start(18)
        clamp.set_margin_end(30)

        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=18)

        title = Gtk.Label(label="Protection Settings")
        title.add_css_class("title-2")
        title.set_xalign(0)
        content.append(title)

        self.status_label = Gtk.Label(label="")
        self.status_label.set_xalign(0)
        self.status_label.set_wrap(True)
        content.append(self.status_label)

        self.protection_group = Adw.PreferencesGroup(title="Protection")
        self.enable_switch = self._switch_row(self.protection_group, "Enable protection")
        self.auto_reconnect_switch = self._switch_row(self.protection_group, "Reconnect automatically")
        self.start_on_login_switch = self._switch_row(self.protection_group, "Start on login")
        self.notifications_switch = self._switch_row(self.protection_group, "Notifications")
        self.debug_switch = self._switch_row(self.protection_group, "Debug logging")
        self.check_updates_switch = self._switch_row(self.protection_group, "Check for updates on startup")
        self.mode_dropdown = self._dropdown_row(self.protection_group, "Presence mode", [label for label, _ in PRESENCE_MODES])
        self.lock_dropdown = self._dropdown_row(self.protection_group, "Lock method", [label for label, _ in LOCK_METHODS])
        self.away_spin = self._spin_row(self.protection_group, "Away grace (seconds)", 1, 3600, 1)
        self.maybe_away_spin = self._spin_row(self.protection_group, "Initial debounce (seconds)", 0, 120, 1)
        self.return_spin = self._spin_row(self.protection_group, "Return stability (seconds)", 0, 120, 1)
        self.near_spin = self._spin_row(self.protection_group, "Near RSSI threshold", -100, -20, 1)
        self.far_spin = self._spin_row(self.protection_group, "Far RSSI threshold", -120, -20, 1)
        self.window_spin = self._spin_row(self.protection_group, "Smoothing window", 1, 20, 1)
        content.append(self.protection_group)

        save_button = Gtk.Button(label="Save Settings")
        save_button.connect("clicked", self._save)
        content.append(save_button)

        clamp.set_child(content)
        scrolled.set_child(clamp)
        self.append(scrolled)

        self.reload()

    def reload(self) -> None:
        config = self.config_manager.load()
        self.enable_switch.set_active(config.protection.enabled)
        self.auto_reconnect_switch.set_active(config.bluetooth.auto_reconnect)
        self.start_on_login_switch.set_active(config.startup.start_on_login)
        self.notifications_switch.set_active(config.session.notifications_enabled)
        self.debug_switch.set_active(config.logging.debug_enabled)
        self.check_updates_switch.set_active(config.updates.check_on_startup)
        self.mode_dropdown.set_selected(self._enum_index(PRESENCE_MODES, config.protection.mode))
        self.lock_dropdown.set_selected(self._enum_index(LOCK_METHODS, config.session.lock_method))
        self.away_spin.set_value(config.protection.away_grace_seconds)
        self.maybe_away_spin.set_value(config.protection.maybe_away_seconds)
        self.return_spin.set_value(config.protection.return_grace_seconds)
        self.near_spin.set_value(config.protection.near_threshold)
        self.far_spin.set_value(config.protection.far_threshold)
        self.window_spin.set_value(config.protection.signal_smoothing_window)
        self.status_label.set_text("")

    def _save(self, *_args: object) -> None:
        config = self.config_manager.load()
        config.protection.enabled = self.enable_switch.get_active()
        config.bluetooth.auto_reconnect = self.auto_reconnect_switch.get_active()
        config.startup.start_on_login = self.start_on_login_switch.get_active()
        config.session.notifications_enabled = self.notifications_switch.get_active()
        config.logging.debug_enabled = self.debug_switch.get_active()
        config.updates.check_on_startup = self.check_updates_switch.get_active()
        config.protection.mode = PRESENCE_MODES[self.mode_dropdown.get_selected()][1]
        config.session.lock_method = LOCK_METHODS[self.lock_dropdown.get_selected()][1]
        config.protection.away_grace_seconds = int(self.away_spin.get_value())
        config.protection.maybe_away_seconds = int(self.maybe_away_spin.get_value())
        config.protection.return_grace_seconds = int(self.return_spin.get_value())
        config.protection.near_threshold = int(self.near_spin.get_value())
        config.protection.far_threshold = int(self.far_spin.get_value())
        config.protection.signal_smoothing_window = int(self.window_spin.get_value())
        self.config_manager.save(config)

        try:
            self.startup_manager.set_start_on_login(
                config.startup.start_on_login,
                [sys.executable, "-m", "bluelatch.main", "--agent"],
            )
            self.status_label.set_text("Settings saved.")
        except Exception as exc:
            self.status_label.set_text(f"Settings saved, but startup update failed: {exc}")

    @staticmethod
    def _enum_index(options, value) -> int:
        for index, (_label, enum_value) in enumerate(options):
            if enum_value == value:
                return index
        return 0

    @staticmethod
    def _switch_row(group: Adw.PreferencesGroup, title: str) -> Gtk.Switch:
        row = Adw.ActionRow(title=title)
        widget = Gtk.Switch()
        widget.set_valign(Gtk.Align.CENTER)
        row.add_suffix(widget)
        row.set_activatable_widget(widget)
        group.add(row)
        return widget

    @staticmethod
    def _dropdown_row(group: Adw.PreferencesGroup, title: str, items: list[str]) -> Gtk.DropDown:
        row = Adw.ActionRow(title=title)
        widget = Gtk.DropDown.new_from_strings(items)
        widget.set_valign(Gtk.Align.CENTER)
        widget.set_size_request(160, -1)
        row.add_suffix(widget)
        group.add(row)
        return widget

    @staticmethod
    def _spin_row(
        group: Adw.PreferencesGroup,
        title: str,
        minimum: int,
        maximum: int,
        step: int,
    ) -> Gtk.SpinButton:
        row = Adw.ActionRow(title=title)
        adjustment = Gtk.Adjustment(
            value=minimum,
            lower=minimum,
            upper=maximum,
            step_increment=step,
            page_increment=step * 10,
        )
        widget = Gtk.SpinButton(adjustment=adjustment)
        widget.set_valign(Gtk.Align.CENTER)
        widget.set_width_chars(6)
        row.add_suffix(widget)
        group.add(row)
        return widget
