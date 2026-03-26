from __future__ import annotations

import argparse
import logging
import sys
from typing import Callable

from bluelatch.util.logging import configure_logging
from bluelatch.util.xdg import AppPaths
from bluelatch.version import __version__


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="BlueLatch Linux proximity lock")
    parser.add_argument("--agent", action="store_true", help="Run the background monitoring agent")
    parser.add_argument("--version", action="store_true", help="Print the application version")
    return parser


def _load_config_debug_flag(paths: AppPaths) -> bool:
    try:
        from bluelatch.config.manager import ConfigManager

        return ConfigManager(paths=paths).load().logging.debug_enabled
    except Exception:
        return False


def _configure_startup_logger(logger_name: str) -> tuple[logging.Logger | None, AppPaths | None]:
    try:
        paths = AppPaths()
        debug = _load_config_debug_flag(paths)
        logger = configure_logging(
            debug=debug,
            logger_name=logger_name,
            paths=paths,
        )
        return logger, paths
    except Exception:
        return None, None


def _format_startup_error(target: str, exc: Exception) -> str:
    return f"BlueLatch failed to start {target}: {type(exc).__name__}: {exc}"


def _report_startup_failure(
    target: str,
    exc: Exception,
    *,
    logger: logging.Logger | None,
    paths: AppPaths | None,
) -> int:
    message = _format_startup_error(target, exc)
    print(message, file=sys.stderr)
    if paths is not None:
        print(f"BlueLatch log file: {paths.log_file}", file=sys.stderr)
    if logger is not None:
        logger.exception(message)
    return 1


def _run_ui() -> int:
    from bluelatch.app import run_ui

    return run_ui()


def _run_agent() -> int:
    from bluelatch.agent import run_agent

    return run_agent()


def _run_with_startup_diagnostics(
    target: str,
    *,
    logger_name: str,
    runner: Callable[[], int],
) -> int:
    logger, paths = _configure_startup_logger(logger_name)
    try:
        return runner()
    except Exception as exc:
        return _report_startup_failure(
            target,
            exc,
            logger=logger,
            paths=paths,
        )


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.version:
        print(__version__)
        return 0
    if args.agent:
        return _run_with_startup_diagnostics(
            "the background agent",
            logger_name="bluelatch",
            runner=_run_agent,
        )
    return _run_with_startup_diagnostics(
        "the UI",
        logger_name="bluelatch.ui",
        runner=_run_ui,
    )


def agent_main() -> int:
    return _run_with_startup_diagnostics(
        "the background agent",
        logger_name="bluelatch",
        runner=_run_agent,
    )


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
