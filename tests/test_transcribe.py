"""Tests for transcribe._model_is_cached, get_model, KnownModel, get_backend."""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import local_whisper.transcribe as _tr
from local_whisper.transcribe import (
    DEFAULT_MODEL,
    KnownModel,
    _model_is_cached,
    _parakeet_cache,
    _run_parakeet,
    get_backend,
    get_model,
)

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


# --- KnownModel + get_backend() tests ---


def test_known_model_values_match_hf_ids() -> None:
    for member in KnownModel:
        assert isinstance(member.value, str)
        assert member.value.startswith("mlx-community/")


def test_get_backend_returns_mlx_whisper_for_distil() -> None:
    assert get_backend(KnownModel.DISTIL_WHISPER) == "mlx-whisper"


def test_get_backend_returns_parakeet_for_parakeet_v2() -> None:
    assert get_backend(KnownModel.PARAKEET_V2) == "parakeet-mlx"


def test_get_backend_returns_mlx_whisper_for_unknown_model() -> None:
    assert get_backend("unknown/custom-model") == "mlx-whisper"


# --- parakeet model caching tests ---


def test_warm_up_parakeet_caches_model_instance() -> None:
    mock_parakeet = MagicMock()
    mock_instance = MagicMock()
    mock_parakeet.from_pretrained.return_value = mock_instance

    _parakeet_cache.clear()
    try:
        with patch.dict(sys.modules, {"parakeet_mlx": mock_parakeet}):
            _tr.warm_up(KnownModel.PARAKEET_V2, backend="parakeet-mlx")
        mock_parakeet.from_pretrained.assert_called_once_with(KnownModel.PARAKEET_V2)
        assert _parakeet_cache[KnownModel.PARAKEET_V2] is mock_instance
    finally:
        _parakeet_cache.clear()


def test_run_parakeet_skips_from_pretrained_when_cached() -> None:
    import numpy as np

    mock_parakeet = MagicMock()
    mock_model = MagicMock()
    mock_result = MagicMock()
    mock_result.text = "hello"
    mock_model.transcribe.return_value = mock_result
    mock_sf = MagicMock()

    audio = np.zeros(8000, dtype="float32")
    _parakeet_cache[KnownModel.PARAKEET_V2] = mock_model
    try:
        with patch.dict(sys.modules, {"parakeet_mlx": mock_parakeet, "soundfile": mock_sf}):
            result = _run_parakeet(audio, KnownModel.PARAKEET_V2)
        mock_parakeet.from_pretrained.assert_not_called()
        assert result == "hello"
    finally:
        _parakeet_cache.clear()


def test_run_parakeet_falls_back_on_import_error() -> None:
    import numpy as np

    audio = np.zeros(8000, dtype="float32")
    with (
        patch.dict(sys.modules, {"parakeet_mlx": None}),
        patch("local_whisper.transcribe._run_mlx_whisper", return_value="fallback text") as mock_mlx,
    ):
        result = _run_parakeet(audio, "mlx-community/parakeet-tdt-0.6b-v2")

    mock_mlx.assert_called_once_with(audio, DEFAULT_MODEL)
    assert result == "fallback text"
