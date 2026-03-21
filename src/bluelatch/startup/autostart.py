from __future__ import annotations

from pathlib import Path

from bluelatch.util.files import atomic_write_text
from bluelatch.util.xdg import AppPaths


class AutostartManager:
    def __init__(self, paths: AppPaths | None = None) -> None:
        self.paths = paths or AppPaths()

    @property
    def desktop_file(self) -> Path:
        return self.paths.autostart_dir / "io.github.UdayaSri.BlueLatch.desktop"

    def enable(self, command: str) -> Path:
        content = "\n".join(
            [
                "[Desktop Entry]",
                "Type=Application",
                "Version=1.0",
                "Name=BlueLatch",
                "Comment=Linux Bluetooth proximity lock",
                f"Exec={command}",
                "Terminal=false",
                "OnlyShowIn=GNOME;Unity;X-Cinnamon;XFCE;KDE;",
                "X-GNOME-Autostart-enabled=true",
            ],
        )
        atomic_write_text(self.desktop_file, content + "\n", mode=0o644)
        return self.desktop_file

    def disable(self) -> None:
        self.desktop_file.unlink(missing_ok=True)
