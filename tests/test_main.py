from __future__ import annotations

import importlib
from pathlib import Path

import bluelatch.main as main_module
from bluelatch.version import __version__


def test_main_version_flag_prints_version(capsys) -> None:
    assert main_module.main(["--version"]) == 0

    captured = capsys.readouterr()
    assert captured.out.strip() == __version__
    assert captured.err == ""


def test_cli_entry_points_are_importable() -> None:
    module = importlib.import_module("bluelatch.main")

    assert callable(module.main)
    assert callable(module.agent_main)


def test_ui_startup_failure_is_visible_and_non_zero(
    tmp_path: Path,
    monkeypatch,
    capsys,
) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "config"))
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path / "state"))
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path / "cache"))
    monkeypatch.setenv("XDG_RUNTIME_DIR", str(tmp_path / "runtime"))

    def boom() -> int:
        raise RuntimeError("boom")

    monkeypatch.setattr(main_module, "_run_ui", boom)

    assert main_module.main([]) == 1

    captured = capsys.readouterr()
    assert "BlueLatch failed to start the UI: RuntimeError: boom" in captured.err

    log_path = tmp_path / "state" / "bluelatch" / "bluelatch.log"
    assert log_path.exists()
    log_content = log_path.read_text(encoding="utf-8")
    assert "BlueLatch failed to start the UI: RuntimeError: boom" in log_content
    assert "RuntimeError: boom" in log_content
