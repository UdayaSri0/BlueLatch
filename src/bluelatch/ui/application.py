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
        self.startup_error: Exception | None = None

    def do_activate(self) -> None:
        try:
            if self.window is None:
                self.window = BlueLatchWindow(self)
            self.window.present()
        except Exception as exc:
            self.startup_error = exc
            self.quit()


def run_ui() -> int:
    app = BlueLatchApplication()
    exit_code = app.run(sys.argv)
    if app.startup_error is not None:
        raise app.startup_error
    return exit_code
