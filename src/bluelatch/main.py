from __future__ import annotations

import argparse
import sys

from bluelatch.version import __version__


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="BlueLatch Linux proximity lock")
    parser.add_argument("--agent", action="store_true", help="Run the background monitoring agent")
    parser.add_argument("--version", action="store_true", help="Print the application version")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.version:
        print(__version__)
        return 0
    if args.agent:
        from bluelatch.agent import run_agent

        return run_agent()
    from bluelatch.app import run_ui

    return run_ui()


def agent_main() -> int:
    from bluelatch.agent import run_agent

    return run_agent()


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
