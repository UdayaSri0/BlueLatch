from __future__ import annotations

import shlex
import shutil
import subprocess
from pathlib import Path

from bluelatch.util.files import atomic_write_text
from bluelatch.util.xdg import AppPaths


class SystemdUserServiceManager:
    SERVICE_NAME = "bluelatch-agent.service"

    def __init__(self, paths: AppPaths | None = None) -> None:
        self.paths = paths or AppPaths()

    @property
    def service_file(self) -> Path:
        return self.paths.systemd_user_dir / self.SERVICE_NAME

    def is_available(self) -> bool:
        return shutil.which("systemctl") is not None

    def install(self, command: list[str]) -> Path:
        exec_line = shlex.join(command)
        content = "\n".join(
            [
                "[Unit]",
                "Description=BlueLatch background proximity lock agent",
                "After=graphical-session.target bluetooth.target",
                "PartOf=graphical-session.target",
                "",
                "[Service]",
                "Type=simple",
                f"ExecStart={exec_line}",
                "Restart=on-failure",
                "RestartSec=5",
                "",
                "[Install]",
                "WantedBy=default.target",
            ],
        )
        atomic_write_text(self.service_file, content + "\n", mode=0o644)
        return self.service_file

    def enable(self) -> None:
        subprocess.run(["systemctl", "--user", "daemon-reload"], check=True)
        subprocess.run(
            ["systemctl", "--user", "enable", "--now", self.SERVICE_NAME],
            check=True,
        )

    def disable(self) -> None:
        subprocess.run(
            ["systemctl", "--user", "disable", "--now", self.SERVICE_NAME],
            check=False,
        )
        self.service_file.unlink(missing_ok=True)
        subprocess.run(["systemctl", "--user", "daemon-reload"], check=False)
