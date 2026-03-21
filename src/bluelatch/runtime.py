from __future__ import annotations

import json
from pathlib import Path

from bluelatch.models import EventRecord, StatusSnapshot
from bluelatch.util.files import atomic_write_json
from bluelatch.util.xdg import AppPaths


class RuntimeStore:
    def __init__(self, paths: AppPaths | None = None) -> None:
        self.paths = paths or AppPaths()
        self.paths.ensure()

    def load_status(self) -> StatusSnapshot:
        if not self.paths.status_file.exists():
            return StatusSnapshot()
        with self.paths.status_file.open("r", encoding="utf-8") as handle:
            return StatusSnapshot.from_dict(json.load(handle))

    def save_status(self, status: StatusSnapshot) -> None:
        atomic_write_json(self.paths.status_file, status.to_dict())

    def append_event(self, record: EventRecord) -> None:
        self.paths.state_dir.mkdir(parents=True, exist_ok=True)
        with self.paths.history_file.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record.to_dict(), sort_keys=True) + "\n")

    def load_events(self, limit: int = 200) -> list[EventRecord]:
        if not self.paths.history_file.exists():
            return []
        with self.paths.history_file.open("r", encoding="utf-8") as handle:
            lines = handle.readlines()
        events: list[EventRecord] = []
        for line in lines[-limit:]:
            line = line.strip()
            if not line:
                continue
            events.append(EventRecord.from_dict(json.loads(line)))
        return events

    def clear_events(self) -> None:
        self.paths.history_file.unlink(missing_ok=True)
