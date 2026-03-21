from __future__ import annotations

try:
    import gi

    gi.require_version("Gtk", "4.0")
    from gi.repository import Gtk
except ImportError as exc:  # pragma: no cover - UI-only import
    raise RuntimeError("PyGObject with GTK4/libadwaita is required for the UI") from exc


class OnboardingPage(Gtk.Box):
    def __init__(self, open_devices_callback, open_settings_callback) -> None:
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=18)
        self.set_margin_top(24)
        self.set_margin_bottom(24)
        self.set_margin_start(24)
        self.set_margin_end(24)

        title = Gtk.Label(label="Welcome to BlueLatch")
        title.add_css_class("title-1")
        title.set_xalign(0)

        intro = Gtk.Label(
            label=(
                "BlueLatch locks your Linux session when a trusted phone is no longer nearby. "
                "It never auto-unlocks the machine."
            )
        )
        intro.set_xalign(0)
        intro.set_wrap(True)
        self.append(title)
        self.append(intro)

        steps = [
            "1. Scan for your phone on the Trusted Device page.",
            "2. Pair and mark it as trusted if BlueZ allows it.",
            "3. Select it as the one trusted phone for BlueLatch.",
            "4. Review grace periods and startup behavior before enabling protection.",
            "5. If you manually unlock while the phone is still away, BlueLatch suppresses re-locking until the phone comes back.",
        ]
        for line in steps:
            label = Gtk.Label(label=line)
            label.set_xalign(0)
            label.set_wrap(True)
            self.append(label)

        buttons = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        devices_button = Gtk.Button(label="Open Trusted Device Setup")
        devices_button.connect("clicked", lambda *_args: open_devices_callback())
        settings_button = Gtk.Button(label="Open Settings")
        settings_button.connect("clicked", lambda *_args: open_settings_callback())
        buttons.append(devices_button)
        buttons.append(settings_button)

        self.append(buttons)
