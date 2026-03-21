from __future__ import annotations

from bluelatch.agent import spawn_background_agent
from bluelatch.bluetooth.bluez import BluezClient
from bluelatch.config.manager import ConfigManager
from bluelatch.runtime import RuntimeStore
from bluelatch.startup import StartupManager
from bluelatch.ui.about import show_about_dialog
from bluelatch.ui.devices import DevicesPage
from bluelatch.ui.logs import LogsPage
from bluelatch.ui.onboarding import OnboardingPage
from bluelatch.ui.settings import SettingsPage
from bluelatch.ui.status import StatusPage
from bluelatch.ui.updates import UpdateDialog

try:
    import gi

    gi.require_version("Adw", "1")
    gi.require_version("Gtk", "4.0")
    from gi.repository import Adw, Gtk
except ImportError as exc:  # pragma: no cover - UI-only import
    raise RuntimeError("PyGObject with GTK4/libadwaita is required for the UI") from exc


class BlueLatchWindow(Adw.ApplicationWindow):
    def __init__(self, application) -> None:
        super().__init__(application=application)
        self.set_title("BlueLatch")
        self.set_default_size(1080, 760)

        spawn_background_agent()

        self.config_manager = ConfigManager()
        self.runtime_store = RuntimeStore()
        self.startup_manager = StartupManager()
        self.bluez = BluezClient(application.logger)

        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        header = Gtk.HeaderBar()
        header.set_title_widget(Gtk.Label(label="BlueLatch"))
        updates_button = Gtk.Button(label="Updates")
        updates_button.connect("clicked", self._show_updates)
        about_button = Gtk.Button(label="About")
        about_button.connect("clicked", lambda *_args: show_about_dialog(self))
        header.pack_end(about_button)
        header.pack_end(updates_button)

        content = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        self.stack = Gtk.Stack()
        self.stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT_RIGHT)
        self.stack.set_hexpand(True)
        self.stack.set_vexpand(True)

        sidebar = Gtk.StackSidebar()
        sidebar.set_stack(self.stack)
        sidebar.set_vexpand(True)
        sidebar.set_size_request(220, -1)

        self.onboarding_page = OnboardingPage(
            open_devices_callback=lambda: self.stack.set_visible_child_name("devices"),
            open_settings_callback=lambda: self.stack.set_visible_child_name("settings"),
        )
        self.devices_page = DevicesPage(self.config_manager, self.bluez)
        self.settings_page = SettingsPage(self.config_manager, self.startup_manager)
        self.status_page = StatusPage(self.runtime_store)
        self.logs_page = LogsPage(self.runtime_store)

        self.stack.add_titled(self.onboarding_page, "welcome", "Welcome")
        self.stack.add_titled(self.devices_page, "devices", "Trusted Device")
        self.stack.add_titled(self.settings_page, "settings", "Settings")
        self.stack.add_titled(self.status_page, "status", "Status")
        self.stack.add_titled(self.logs_page, "logs", "Logs")

        content.append(sidebar)
        content.append(self.stack)
        root.append(header)
        root.append(content)
        self.set_content(root)

        if self.config_manager.load().bluetooth.trusted_device.address:
            self.stack.set_visible_child_name("status")
        else:
            self.stack.set_visible_child_name("welcome")

    def _show_updates(self, *_args: object) -> None:
        dialog = UpdateDialog(self)
        dialog.present_and_check()
