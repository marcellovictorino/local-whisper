"""Tests for transcribe._model_is_cached, get_model, KnownModel, get_backend, parakeet caching."""

import sys
import threading
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

import local_whisper.transcribe as _tr
from local_whisper.transcribe import (
    DEFAULT_MODEL,
    Backend,
    KnownModel,
    _keepalive_loop,
    _model_is_cached,
    _parakeet_cache,
    _run_mlx_whisper,
    _run_parakeet,
    get_backend,
    get_model,
    start_keepalive,
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
        (KnownModel.WHISPER_SMALL_EN, "mlx-whisper"),
        (KnownModel.DISTIL_WHISPER, "mlx-whisper"),
        (KnownModel.WHISPER_TURBO, "mlx-whisper"),
        (KnownModel.PARAKEET_V2, "parakeet-mlx"),
        ("unknown/custom-model", "mlx-whisper"),
    ],
)
def test_get_backend(model: str, expected_backend: str) -> None:
    assert get_backend(model) == expected_backend


def test_default_model_is_whisper_small_en() -> None:
    """Parakeet is opt-in only — default stays whisper until it earns a benchmark row."""
    assert DEFAULT_MODEL == KnownModel.WHISPER_SMALL_EN
    assert _tr.DEFAULT_BACKEND == Backend.MLX_WHISPER


# --- parakeet model caching ---


def test_warm_up_parakeet_caches_model_instance_and_runs_dummy_inference() -> None:
    mock_parakeet = MagicMock()
    mock_instance = MagicMock()
    mock_parakeet.from_pretrained.return_value = mock_instance
    _parakeet_cache.clear()
    try:
        with (
            patch.dict(sys.modules, {"parakeet_mlx": mock_parakeet}),
            patch("local_whisper.transcribe._parakeet_unavailable_reason", return_value=None),
            patch("local_whisper.transcribe._run_parakeet") as mock_run,
        ):
            _tr.warm_up(KnownModel.PARAKEET_V2, backend="parakeet-mlx")
        mock_parakeet.from_pretrained.assert_called_once_with(KnownModel.PARAKEET_V2)
        assert _parakeet_cache[KnownModel.PARAKEET_V2] is mock_instance
        # Dummy inference pre-pays Metal shader compilation before the first keypress.
        mock_run.assert_called_once()
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
        with (
            patch.dict(sys.modules, {"parakeet_mlx": mock_parakeet, "soundfile": mock_sf}),
            patch("local_whisper.transcribe._parakeet_unavailable_reason", return_value=None),
        ):
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
    mock_mlx.assert_called_once_with(audio, KnownModel.WHISPER_SMALL_EN)
    assert result == "fallback text"


def test_run_parakeet_falls_back_when_ffmpeg_missing() -> None:
    """A user without ffmpeg must still get a transcription, not a dead session."""
    import numpy as np

    audio = np.zeros(8000, dtype="float32")
    with (
        patch.dict(sys.modules, {"parakeet_mlx": MagicMock()}),
        patch("local_whisper.transcribe._has_ffmpeg", return_value=False),
        patch("local_whisper.transcribe._run_mlx_whisper", return_value="fallback text") as mock_mlx,
    ):
        result = _run_parakeet(audio, "mlx-community/parakeet-tdt-0.6b-v2")
    mock_mlx.assert_called_once_with(audio, KnownModel.WHISPER_SMALL_EN)
    assert result == "fallback text"


def test_warm_up_warms_whisper_fallback_when_parakeet_unavailable() -> None:
    """Broken parakeet install must not mean a cold (or mid-dictation-download) first session."""
    mock_mlx = MagicMock()
    with (
        patch("local_whisper.transcribe._parakeet_unavailable_reason", return_value="ffmpeg not found"),
        patch("local_whisper.transcribe._model_is_cached", return_value=True),
        patch.dict(sys.modules, {"mlx_whisper": mock_mlx}),
    ):
        _tr.warm_up(KnownModel.PARAKEET_V2, backend="parakeet-mlx")
    mock_mlx.transcribe.assert_called_once()
    assert mock_mlx.transcribe.call_args.kwargs["path_or_hf_repo"] == KnownModel.WHISPER_SMALL_EN


# --- _metal_lock serialization ---


def test_metal_lock_serializes_concurrent_mlx_whisper_calls() -> None:
    """Two threads calling _run_mlx_whisper concurrently must never overlap.

    Proves the lock, not just its presence: the mocked transcribe call sleeps
    briefly with a shared in-critical-section counter, and the test fails if
    that counter is ever seen above 1.
    """
    audio = np.zeros(8000, dtype="float32")
    concurrent_count = 0
    max_concurrent = 0
    lock = threading.Lock()

    def fake_transcribe(*_a, **_kw):
        nonlocal concurrent_count, max_concurrent
        with lock:
            concurrent_count += 1
            max_concurrent = max(max_concurrent, concurrent_count)
        time.sleep(0.05)
        with lock:
            concurrent_count -= 1
        return {"text": "hi"}

    mock_mlx_whisper = MagicMock()
    mock_mlx_whisper.transcribe.side_effect = fake_transcribe

    mock_mlx = MagicMock()
    # mx.stream(...) is used as a context manager around the transcribe call.
    mock_mlx.core.stream.return_value.__enter__ = lambda self: None
    mock_mlx.core.stream.return_value.__exit__ = lambda self, *a: None

    with patch.dict(sys.modules, {
        "mlx_whisper": mock_mlx_whisper,
        "mlx": mock_mlx,
        "mlx.core": mock_mlx.core,
    }):
        threads = [threading.Thread(target=_run_mlx_whisper, args=(audio, DEFAULT_MODEL)) for _ in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=5)

    assert max_concurrent == 1


def test_metal_lock_acquire_is_bounded_by_a_timeout() -> None:
    """A holder that never releases must not lock out every future MLX/Metal call forever.

    Exercises _metal_guard directly rather than through _run_mlx_whisper, so the
    test doesn't depend on the real MLX/Metal runtime.
    """
    with patch("local_whisper.transcribe._METAL_LOCK_TIMEOUT_S", 0.05), _tr._metal_lock:
        with pytest.raises(TimeoutError), _tr._metal_guard():
            pass


# --- keepalive ---


@pytest.mark.parametrize("backend", [Backend.MLX_WHISPER, Backend.PARAKEET])
def test_start_keepalive_spawns_daemon_thread(backend: Backend) -> None:
    with patch("local_whisper.transcribe.threading.Thread") as mock_thread:
        start_keepalive(model=DEFAULT_MODEL, backend=backend, interval_s=1)
    mock_thread.assert_called_once()
    _, kwargs = mock_thread.call_args
    assert kwargs.get("daemon") is True
    assert kwargs["args"][2] == backend


def test_keepalive_loop_calls_mlx_whisper_each_iteration() -> None:
    with (
        patch("local_whisper.transcribe.wait_warmed"),
        patch("local_whisper.transcribe._run_mlx_whisper") as mock_mlx,
        patch("local_whisper.transcribe.time.sleep", side_effect=[None, StopIteration]),
    ):
        with pytest.raises(StopIteration):
            _keepalive_loop("some/whisper-model", interval_s=1, backend=Backend.MLX_WHISPER)

    mock_mlx.assert_called_once()
    assert mock_mlx.call_args.args[1] == "some/whisper-model"


def test_keepalive_loop_calls_parakeet_for_parakeet_backend() -> None:
    with (
        patch("local_whisper.transcribe.wait_warmed"),
        patch("local_whisper.transcribe._run_parakeet") as mock_parakeet,
        patch("local_whisper.transcribe._run_mlx_whisper") as mock_mlx,
        patch("local_whisper.transcribe.time.sleep", side_effect=[None, StopIteration]),
    ):
        with pytest.raises(StopIteration):
            _keepalive_loop(DEFAULT_MODEL, interval_s=1, backend=Backend.PARAKEET)

    mock_parakeet.assert_called_once()
    mock_mlx.assert_not_called()
    assert mock_parakeet.call_args.args[1] == DEFAULT_MODEL


def test_keepalive_ping_swallows_backend_errors() -> None:
    """A failed ping must never crash the daemon — keepalive is best-effort."""
    with patch("local_whisper.transcribe._run_backend", side_effect=RuntimeError("boom")):
        _tr._keepalive_ping(DEFAULT_MODEL, Backend.MLX_WHISPER)  # must not raise


# --- wake re-warm ---


def test_rewarm_on_wake_pings_configured_backend() -> None:
    """On wake we re-page the exact model/backend the watcher was started with."""
    with (
        patch("local_whisper.transcribe._wake_target", ("some/whisper-model", Backend.MLX_WHISPER)),
        patch("local_whisper.transcribe._run_backend") as mock_run,
    ):
        _tr._rewarm_on_wake()
    mock_run.assert_called_once()
    assert mock_run.call_args.args[1] == "some/whisper-model"
    assert mock_run.call_args.args[2] == Backend.MLX_WHISPER


def test_rewarm_on_wake_noop_without_target() -> None:
    with (
        patch("local_whisper.transcribe._wake_target", None),
        patch("local_whisper.transcribe._run_backend") as mock_run,
    ):
        _tr._rewarm_on_wake()
    mock_run.assert_not_called()


def test_start_wake_watcher_degrades_when_appkit_unavailable() -> None:
    """No AppKit (e.g. headless) → no-op, no crash; keepalive still covers idle."""
    with (
        patch("local_whisper.transcribe._wake_observer", None),
        patch.dict("sys.modules", {"AppKit": None}),
    ):
        _tr.start_wake_watcher()  # must not raise
        assert _tr._wake_observer is None
