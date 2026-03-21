from __future__ import annotations

import logging
import sys

from bluelatch.ui.window import BlueLatchWindow

try:
    import gi

    gi.require_version("Adw", "1")
    gi.require_version("Gtk", "4.0")
    from gi.repository import Adw
except ImportError as exc:  # pragma: no cover - UI-only import
    raise RuntimeError("PyGObject with GTK4/libadwaita is required for the UI") from exc


class BlueLatchApplication(Adw.Application):
    def __init__(self) -> None:
        super().__init__(application_id="io.github.UdayaSri.BlueLatch")
        self.window: BlueLatchWindow | None = None
        self.logger = logging.getLogger("bluelatch.ui")

    def do_activate(self) -> None:
        if self.window is None:
            self.window = BlueLatchWindow(self)
        self.window.present()


def run_ui() -> int:
    app = BlueLatchApplication()
    return app.run(sys.argv)
