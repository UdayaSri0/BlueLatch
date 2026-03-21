from __future__ import annotations

import fcntl
from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class SingleInstanceLock:
    path: Path
    _handle: object | None = None

    def acquire(self) -> bool:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._handle = self.path.open("w", encoding="utf-8")
        try:
            fcntl.flock(self._handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            self._handle.close()
            self._handle = None
            return False
        self._handle.write(str(self.path))
        self._handle.flush()
        return True

    def release(self) -> None:
        if self._handle is None:
            return
        fcntl.flock(self._handle.fileno(), fcntl.LOCK_UN)
        self._handle.close()
        self._handle = None
