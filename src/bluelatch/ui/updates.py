from __future__ import annotations

import subprocess
import threading

from bluelatch.updates import UpdateCheckResult, UpdateService
from bluelatch.version import __version__

try:
    import gi

    gi.require_version("Adw", "1")
    gi.require_version("Gtk", "4.0")
    from gi.repository import Adw, GLib, Gtk
except ImportError as exc:  # pragma: no cover - UI-only import
    raise RuntimeError("PyGObject with GTK4/libadwaita is required for the UI") from exc


class UpdateDialog(Adw.Window):
    def __init__(self, parent: Gtk.Window, update_service: UpdateService | None = None) -> None:
        super().__init__(transient_for=parent, modal=True)
        self.set_title("BlueLatch Updates")
        self.set_default_size(560, 360)
        self.update_service = update_service or UpdateService()
        self.result: UpdateCheckResult | None = None

        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=18)
        root.set_margin_top(24)
        root.set_margin_bottom(24)
        root.set_margin_start(24)
        root.set_margin_end(24)

        title = Gtk.Label(label="Check for Updates")
        title.add_css_class("title-2")
        title.set_xalign(0)

        self.summary_label = Gtk.Label(label="Ready to check GitHub Releases.")
        self.summary_label.set_xalign(0)
        self.summary_label.set_wrap(True)

        self.guidance_label = Gtk.Label(label="")
        self.guidance_label.set_xalign(0)
        self.guidance_label.set_wrap(True)
        self.guidance_label.add_css_class("dim-label")

        self.notes_view = Gtk.TextView()
        self.notes_view.set_editable(False)
        self.notes_view.set_cursor_visible(False)
        self.notes_view.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        self.notes_view.set_monospace(False)
        notes_scroll = Gtk.ScrolledWindow()
        notes_scroll.set_vexpand(True)
        notes_scroll.set_child(self.notes_view)

        actions = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        self.check_button = Gtk.Button(label="Check Now")
        self.check_button.connect("clicked", self._on_check_clicked)
        self.open_button = Gtk.Button(label="Open Release")
        self.open_button.set_sensitive(False)
        self.open_button.connect("clicked", self._open_release)
        close_button = Gtk.Button(label="Close")
        close_button.connect("clicked", lambda *_args: self.close())
        actions.append(self.check_button)
        actions.append(self.open_button)
        actions.append(close_button)

        root.append(title)
        root.append(self.summary_label)
        root.append(self.guidance_label)
        root.append(notes_scroll)
        root.append(actions)
        self.set_child(root)

    def present_and_check(self) -> None:
        self.present()
        self._start_check()

    def _on_check_clicked(self, *_args: object) -> None:
        self._start_check()

    def _start_check(self) -> None:
        self.check_button.set_sensitive(False)
        self.summary_label.set_text("Checking GitHub Releases...")
        thread = threading.Thread(target=self._worker, daemon=True)
        thread.start()

    def _worker(self) -> None:
        result = self.update_service.check_for_updates(__version__)
        GLib.idle_add(self._apply_result, result)

    def _apply_result(self, result: UpdateCheckResult) -> bool:
        self.result = result
        self.check_button.set_sensitive(True)
        if result.error:
            self.summary_label.set_text(f"Update check failed: {result.error}")
            self.guidance_label.set_text(result.guidance)
            self._set_notes("")
            return False

        if result.update_available:
            self.summary_label.set_text(
                f"Update available: {result.current_version} -> {result.latest_version}"
            )
        else:
            self.summary_label.set_text(
                f"BlueLatch is up to date at {result.current_version}"
            )
        self.guidance_label.set_text(result.guidance)
        self._set_notes(result.notes or "")
        self.open_button.set_sensitive(bool(result.release_url))
        return False

    def _set_notes(self, text: str) -> None:
        buffer = self.notes_view.get_buffer()
        buffer.set_text(text)

    def _open_release(self, *_args: object) -> None:
        if not self.result or not self.result.release_url:
            return
        subprocess.run(["xdg-open", self.result.release_url], check=False)
