"""Tests for transcribe._model_is_cached, get_model, KnownModel, get_backend, parakeet caching."""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

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


# --- _model_is_cached ---


def test_not_cached_when_dir_missing(tmp_path: Path, monkeypatch: object) -> None:
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    assert _model_is_cached(MODEL) is False


@pytest.mark.parametrize(
    "setup",
    [
        "empty_snapshots",
        "empty_snapshot_subdir",
        "only_metadata",
    ],
)
def test_not_cached_without_weights(tmp_path: Path, monkeypatch: object, setup: str) -> None:
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    snapshots = tmp_path / ".cache/huggingface/hub/models--mlx-community--whisper-large-v3-turbo/snapshots"
    snapshots.mkdir(parents=True)
    if setup == "only_metadata":
        snapshot_dir = snapshots / "abc123"
        snapshot_dir.mkdir()
        (snapshot_dir / "config.json").write_text("{}")
    elif setup == "empty_snapshot_subdir":
        (snapshots / "abc123").mkdir()
    # "empty_snapshots": no subdirs — nothing to create
    assert _model_is_cached(MODEL) is False


def test_cached_when_snapshot_has_weights(tmp_path: Path, monkeypatch: object) -> None:
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    snapshot_dir = tmp_path / ".cache/huggingface/hub/models--mlx-community--whisper-large-v3-turbo/snapshots/abc123"
    snapshot_dir.mkdir(parents=True)
    (snapshot_dir / "model.safetensors").write_bytes(b"")
    assert _model_is_cached(MODEL) is True


# --- get_model ---


@pytest.mark.parametrize(
    "toml",
    [
        None,  # file missing
        "[snippets]\nfoo = 'bar'\n",  # section absent
        "not valid toml = = = !!!",  # corrupt
    ],
)
def test_get_model_returns_default(tmp_path: Path, toml: str | None) -> None:
    if toml is None:
        path = tmp_path / "nonexistent.toml"
    else:
        path = tmp_path / "config.toml"
        path.write_text(toml)
    assert get_model(path) == DEFAULT_MODEL


def test_get_model_returns_configured_model(tmp_path: Path) -> None:
    config = tmp_path / "config.toml"
    config.write_text('[whisper]\nmodel = "mlx-community/whisper-large-v3-turbo"\n')
    assert get_model(config) == "mlx-community/whisper-large-v3-turbo"


# --- KnownModel + get_backend ---


def test_known_model_members_are_valid_hf_ids() -> None:
    for member in KnownModel:
        assert isinstance(member.value, str)
        assert member.value.startswith("mlx-community/")


@pytest.mark.parametrize(
    "model,expected_backend",
    [
        (KnownModel.DISTIL_WHISPER, "mlx-whisper"),
        (KnownModel.WHISPER_TURBO, "mlx-whisper"),
        (KnownModel.PARAKEET_V2, "parakeet-mlx"),
        ("unknown/custom-model", "mlx-whisper"),
    ],
)
def test_get_backend(model: str, expected_backend: str) -> None:
    assert get_backend(model) == expected_backend


def test_default_model_is_whisper_small_en() -> None:
    assert DEFAULT_MODEL == KnownModel.WHISPER_SMALL_EN


# --- parakeet model caching ---


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
    mock_model.transcribe.return_value = MagicMock(text="hello")
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
