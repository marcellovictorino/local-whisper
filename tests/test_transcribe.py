"""Tests for transcribe._model_is_cached — pure filesystem logic."""
from pathlib import Path

from local_whisper.transcribe import _model_is_cached

MODEL = "mlx-community/whisper-large-v3-turbo"


def test_not_cached_when_dir_missing(tmp_path: Path, monkeypatch: object) -> None:
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    assert _model_is_cached(MODEL) is False


def test_not_cached_when_snapshots_empty(tmp_path: Path, monkeypatch: object) -> None:
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    snapshots = tmp_path / ".cache/huggingface/hub/models--mlx-community--whisper-large-v3-turbo/snapshots"
    snapshots.mkdir(parents=True)
    assert _model_is_cached(MODEL) is False


def test_cached_when_snapshot_has_files(tmp_path: Path, monkeypatch: object) -> None:
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    snapshot_dir = (
        tmp_path
        / ".cache/huggingface/hub/models--mlx-community--whisper-large-v3-turbo/snapshots/abc123"
    )
    snapshot_dir.mkdir(parents=True)
    (snapshot_dir / "config.json").write_text("{}")
    assert _model_is_cached(MODEL) is True


def test_not_cached_when_snapshot_subdirs_are_empty(tmp_path: Path, monkeypatch: object) -> None:
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    snapshot_dir = (
        tmp_path
        / ".cache/huggingface/hub/models--mlx-community--whisper-large-v3-turbo/snapshots/abc123"
    )
    snapshot_dir.mkdir(parents=True)
    # directory exists but is empty
    assert _model_is_cached(MODEL) is False
