"""End-to-end tests for the validate-config command."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).parents[1] / "scripts" / "validate_config.py"


def _run_validator(home: Path) -> subprocess.CompletedProcess[str]:
    environment = os.environ | {"HOME": str(home)}
    return subprocess.run(
        [sys.executable, str(SCRIPT)],
        capture_output=True,
        check=False,
        env=environment,
        text=True,
    )


def test_accepts_missing_config(tmp_path: Path) -> None:
    result = _run_validator(tmp_path)

    assert result.returncode == 0
    assert result.stderr == ""
    assert str(tmp_path / ".config" / "local-whisper" / "config.toml") in result.stdout


def test_accepts_valid_config(tmp_path: Path) -> None:
    config = tmp_path / ".config" / "local-whisper" / "config.toml"
    config.parent.mkdir(parents=True)
    config.write_text('[whisper]\nmodel = "small"\n')

    result = _run_validator(tmp_path)

    assert result.returncode == 0
    assert result.stderr == ""
    assert str(config) in result.stdout


def test_rejects_malformed_config_with_path_and_location(tmp_path: Path) -> None:
    config = tmp_path / ".config" / "local-whisper" / "config.toml"
    config.parent.mkdir(parents=True)
    config.write_text("model = ]\n")

    result = _run_validator(tmp_path)

    assert result.returncode == 1
    assert result.stdout == ""
    assert str(config) in result.stderr
    assert "line 1" in result.stderr
    assert "column" in result.stderr
