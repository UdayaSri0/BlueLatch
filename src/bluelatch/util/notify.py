from __future__ import annotations

import shutil
import subprocess


def send_notification(summary: str, body: str) -> None:
    notify_send = shutil.which("notify-send")
    if not notify_send:
        return
    subprocess.run(
        [notify_send, "--app-name=BlueLatch", summary, body],
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
