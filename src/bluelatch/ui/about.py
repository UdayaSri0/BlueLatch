from __future__ import annotations

from bluelatch.version import __version__

try:
    import gi

    gi.require_version("Adw", "1")
    gi.require_version("Gtk", "4.0")
    from gi.repository import Adw, Gtk
except ImportError as exc:  # pragma: no cover - UI-only import
    raise RuntimeError("PyGObject with GTK4/libadwaita is required for the UI") from exc


def show_about_dialog(parent: Gtk.Window) -> None:
    about = Adw.AboutWindow(transient_for=parent, modal=True)
    about.set_application_name("BlueLatch")
    about.set_application_icon("io.github.UdayaSri.BlueLatch")
    about.set_version(__version__)
    about.set_developer_name("Udaya Sri")
    about.set_license_type(Gtk.License.MIT_X11)
    about.set_comments("Linux Bluetooth proximity lock")
    about.set_website("https://github.com/UdayaSri0/BlueLatch")
    about.set_issue_url("https://github.com/UdayaSri0/BlueLatch/issues")
    about.set_developers(["Udaya Sri"])
    about.set_copyright("Copyright (c) 2026 Udaya Sri")
    about.set_release_notes(
        "BlueLatch auto-locks a GNOME session when the trusted phone goes away and never auto-unlocks it."
    )
    about.add_link("GitHub", "https://github.com/UdayaSri0")
    about.add_link("Project Repository", "https://github.com/UdayaSri0/BlueLatch")
    about.add_link("Issue Tracker", "https://github.com/UdayaSri0/BlueLatch/issues")
    about.set_release_notes_version(__version__)
    about.present()
