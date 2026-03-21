from __future__ import annotations

import json
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any

from bluelatch.util.xdg import AppPaths


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        extra = getattr(record, "context", None)
        if isinstance(extra, dict):
            payload["context"] = extra
        return json.dumps(payload, sort_keys=True)


def configure_logging(
    *,
    debug: bool = False,
    logger_name: str = "bluelatch",
    paths: AppPaths | None = None,
) -> logging.Logger:
    paths = paths or AppPaths()
    paths.ensure()
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.DEBUG if debug else logging.INFO)
    if logger.handlers:
        return logger

    formatter = JsonFormatter()
    log_path: Path = paths.log_file
    file_handler = RotatingFileHandler(
        log_path,
        maxBytes=2_000_000,
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.DEBUG if debug else logging.INFO)
    logger.addHandler(file_handler)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    stream_handler.setLevel(logging.DEBUG if debug else logging.INFO)
    logger.addHandler(stream_handler)
    return logger
