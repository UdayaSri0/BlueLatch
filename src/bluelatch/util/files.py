from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import Any


def atomic_write_text(path: Path, content: str, mode: int = 0o600) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w",
        encoding="utf-8",
        dir=path.parent,
        delete=False,
    ) as handle:
        handle.write(content)
        handle.flush()
        os.fchmod(handle.fileno(), mode)
        temp_name = handle.name

    os.replace(temp_name, path)
    os.chmod(path, mode)


def atomic_write_json(path: Path, payload: dict[str, Any], mode: int = 0o600) -> None:
    atomic_write_text(path, json.dumps(payload, indent=2, sort_keys=True), mode=mode)


def load_json(path: Path, default: dict[str, Any] | None = None) -> dict[str, Any]:
    if not path.exists():
        return default.copy() if default else {}
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)
