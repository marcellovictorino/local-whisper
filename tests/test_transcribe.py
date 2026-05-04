"""Tests for transcribe._model_is_cached and get_model — pure filesystem logic."""

from pathlib import Path

from local_whisper.transcribe import DEFAULT_MODEL, _model_is_cached, get_model

MODEL = "mlx-community/whisper-large-v3-turbo"


def test_not_cached_when_dir_missing(tmp_path: Path, monkeypatch: object) -> None:
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    assert _model_is_cached(MODEL) is False


def test_not_cached_when_snapshots_empty(tmp_path: Path, monkeypatch: object) -> None:
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    snapshots = tmp_path / ".cache/huggingface/hub/models--mlx-community--whisper-large-v3-turbo/snapshots"
    snapshots.mkdir(parents=True)
    assert _model_is_cached(MODEL) is False


def test_cached_when_snapshot_has_weights(tmp_path: Path, monkeypatch: object) -> None:
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    snapshot_dir = tmp_path / ".cache/huggingface/hub/models--mlx-community--whisper-large-v3-turbo/snapshots/abc123"
    snapshot_dir.mkdir(parents=True)
    (snapshot_dir / "model.safetensors").write_bytes(b"")
    assert _model_is_cached(MODEL) is True


def test_not_cached_when_only_metadata_present(tmp_path: Path, monkeypatch: object) -> None:
    """Partial/interrupted download: config.json exists but no weight files."""
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    snapshot_dir = tmp_path / ".cache/huggingface/hub/models--mlx-community--whisper-large-v3-turbo/snapshots/abc123"
    snapshot_dir.mkdir(parents=True)
    (snapshot_dir / "config.json").write_text("{}")
    (snapshot_dir / "tokenizer.json").write_text("{}")
    assert _model_is_cached(MODEL) is False


def test_not_cached_when_snapshot_subdirs_are_empty(tmp_path: Path, monkeypatch: object) -> None:
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    snapshot_dir = tmp_path / ".cache/huggingface/hub/models--mlx-community--whisper-large-v3-turbo/snapshots/abc123"
    snapshot_dir.mkdir(parents=True)
    # directory exists but is empty
    assert _model_is_cached(MODEL) is False


# --- get_model() tests ---


def test_get_model_returns_default_when_no_config(tmp_path: Path) -> None:
    assert get_model(tmp_path / "nonexistent.toml") == DEFAULT_MODEL


def test_get_model_returns_default_when_section_absent(tmp_path: Path) -> None:
    config = tmp_path / "config.toml"
    config.write_text("[snippets]\nfoo = 'bar'\n")
    assert get_model(config) == DEFAULT_MODEL


def test_get_model_returns_configured_model(tmp_path: Path) -> None:
    config = tmp_path / "config.toml"
    config.write_text('[whisper]\nmodel = "mlx-community/whisper-large-v3-turbo"\n')
    assert get_model(config) == "mlx-community/whisper-large-v3-turbo"


def test_get_model_returns_default_on_corrupt_config(tmp_path: Path) -> None:
    config = tmp_path / "config.toml"
    config.write_text("not valid toml = = = !!!")
    assert get_model(config) == DEFAULT_MODEL
