from __future__ import annotations

from bluelatch.runtime import RuntimeStore

try:
    import gi

    gi.require_version("Gtk", "4.0")
    from gi.repository import GLib, Gtk
except ImportError as exc:  # pragma: no cover - UI-only import
    raise RuntimeError("PyGObject with GTK4/libadwaita is required for the UI") from exc


class LogsPage(Gtk.Box):
    def __init__(self, runtime_store: RuntimeStore) -> None:
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self.runtime_store = runtime_store
        self.set_margin_top(18)
        self.set_margin_bottom(18)
        self.set_margin_start(18)
        self.set_margin_end(18)

        header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        title = Gtk.Label(label="Event History")
        title.add_css_class("title-2")
        title.set_xalign(0)
        title.set_hexpand(True)
        refresh_button = Gtk.Button(label="Refresh")
        refresh_button.connect("clicked", lambda *_args: self.refresh())
        header.append(title)
        header.append(refresh_button)

        self.text_view = Gtk.TextView()
        self.text_view.set_editable(False)
        self.text_view.set_cursor_visible(False)
        self.text_view.set_monospace(True)
        self.text_view.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)

        scroll = Gtk.ScrolledWindow()
        scroll.set_vexpand(True)
        scroll.set_child(self.text_view)

        self.append(header)
        self.append(scroll)

        GLib.timeout_add_seconds(5, self._poll)
        self.refresh()

    def refresh(self) -> None:
        events = self.runtime_store.load_events(limit=200)
        lines = []
        for record in events:
            lines.append(
                f"{record.timestamp} [{record.level}] {record.event}: {record.message}"
            )
        if not lines:
            lines = ["No events recorded yet."]
        buffer = self.text_view.get_buffer()
        buffer.set_text("\n".join(lines))

    def _poll(self) -> bool:
        self.refresh()
        return True
