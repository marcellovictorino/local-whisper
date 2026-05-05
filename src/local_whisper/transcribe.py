import os
import sys
import tempfile
import time
import tomllib
from enum import StrEnum
from pathlib import Path
from typing import Any

import numpy as np

_CONFIG_PATH = Path.home() / ".config" / "local-whisper" / "config.toml"


class KnownModel(StrEnum):
    """Supported model IDs with known backend assignments.

    Add new models here to register them. Unknown IDs fall back to mlx-whisper.
    """

    DISTIL_WHISPER = "mlx-community/distil-whisper-large-v3"  # default; fast English
    WHISPER_TURBO = "mlx-community/whisper-large-v3-turbo"  # multilingual, accurate
    PARAKEET_V2 = "mlx-community/parakeet-tdt-0.6b-v2"  # fastest; English only


class Backend(StrEnum):
    """Inference backend names. Backend is auto-inferred from model ID via get_backend()."""

    MLX_WHISPER = "mlx-whisper"
    PARAKEET = "parakeet-mlx"


DEFAULT_MODEL = KnownModel.DISTIL_WHISPER
DEFAULT_BACKEND = Backend.MLX_WHISPER

_MODEL_SIZES: dict[str, str] = {
    KnownModel.WHISPER_TURBO: "~1.5 GB",
    KnownModel.DISTIL_WHISPER: "~600 MB",
    KnownModel.PARAKEET_V2: "~600 MB",
}

_BACKEND_MAP: dict[str, Backend] = {
    KnownModel.DISTIL_WHISPER: Backend.MLX_WHISPER,
    KnownModel.WHISPER_TURBO: Backend.MLX_WHISPER,
    KnownModel.PARAKEET_V2: Backend.PARAKEET,
}

# Parakeet model instance cached at warm_up time so from_pretrained() runs once per session.
_parakeet_cache: dict[str, Any] = {}


def get_backend(model: str) -> Backend:
    """Infer backend from model ID. Unknown IDs default to mlx-whisper.

    Args:
        model: HuggingFace model ID (from get_model() or KnownModel).

    Returns:
        Backend enum value.
    """
    return _BACKEND_MAP.get(model, DEFAULT_BACKEND)


def get_model(path: Path = _CONFIG_PATH) -> str:
    """Read model ID from config.toml, falling back to DEFAULT_MODEL.

    Args:
        path: Path to config.toml file.

    Returns:
        HuggingFace model ID string.
    """
    try:
        with open(path, "rb") as f:
            data = tomllib.load(f)
        return data.get("whisper", {}).get("model", DEFAULT_MODEL)
    except FileNotFoundError:
        return DEFAULT_MODEL
    except Exception as exc:
        print(f"[local-whisper] whisper config error: {exc}", file=sys.stderr)
        return DEFAULT_MODEL


def _model_is_cached(model: str) -> bool:
    """Check if the HuggingFace model snapshots exist in the local cache."""
    model_dir = "models--" + model.replace("/", "--")
    snapshots = Path.home() / ".cache" / "huggingface" / "hub" / model_dir / "snapshots"
    if not snapshots.exists():
        return False
    # Require at least one .safetensors weight file — partial/interrupted downloads
    # may leave only metadata (config.json etc.) which passes an any(iterdir()) check.
    return any(p.is_dir() and any(p.glob("*.safetensors")) for p in snapshots.iterdir())


def _suppress_progress_bars() -> None:
    import logging

    os.environ["HF_HUB_DISABLE_PROGRESS_BARS"] = "1"
    os.environ["TQDM_DISABLE"] = "1"
    os.environ["HF_HUB_OFFLINE"] = "1"  # model cached — skip HF network check
    logging.getLogger("huggingface_hub").setLevel(logging.ERROR)


def _run_mlx_whisper(audio: np.ndarray, model: str) -> str:
    import mlx.core as mx
    import mlx_whisper

    # MLX Metal streams are thread-local; warm_up runs on a different thread than
    # each keypress transcription thread, so we create a fresh stream here.
    with mx.stream(mx.gpu):
        result = mlx_whisper.transcribe(audio, path_or_hf_repo=model, verbose=False)
    return result["text"].strip()


def _run_parakeet(audio: np.ndarray, model: str) -> str:
    # Spike findings (Task 1):
    # - from_pretrained(hf_id_or_path) → BaseParakeet
    # - model.transcribe(path: Path|str) → AlignedResult — takes file path, not numpy array
    #   Uses ffmpeg internally to load audio; requires ffmpeg in PATH
    # - AlignedResult.text: str attribute (not dict subscript)
    # - Write audio to temp WAV via soundfile (float32, 16 kHz), pass path, then clean up
    try:
        import parakeet_mlx
    except ImportError:
        print(
            "[local-whisper] parakeet-mlx not installed. Run: uv sync --extra parakeet\nFalling back to mlx-whisper.",
            file=sys.stderr,
        )
        return _run_mlx_whisper(audio, model)

    import soundfile as sf

    if model not in _parakeet_cache:
        _parakeet_cache[model] = parakeet_mlx.from_pretrained(model)
    parakeet_model = _parakeet_cache[model]

    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp_path = tmp.name
        sf.write(tmp_path, audio, 16000, subtype="PCM_16")
        result = parakeet_model.transcribe(tmp_path)
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)
    return result.text.strip()


def warm_up(model: str = DEFAULT_MODEL, backend: str = DEFAULT_BACKEND) -> None:
    """Download (if needed) and pre-load model, compiling Metal shaders.

    Runs at startup in a background thread so the first keypress is instant.
    Shows download progress when model is not yet cached.

    Args:
        model: HuggingFace model ID to pre-load.
        backend: Backend name ("mlx-whisper" or "parakeet-mlx").
    """
    if backend == Backend.PARAKEET:
        try:
            import parakeet_mlx
        except ImportError:
            return
        try:
            _parakeet_cache[model] = parakeet_mlx.from_pretrained(model)
            print("[local-whisper] Model ready.", file=sys.stderr, flush=True)
        except Exception as exc:
            print(f"[local-whisper] Warm-up failed (non-fatal): {exc}", file=sys.stderr, flush=True)
        return

    if not _model_is_cached(model):
        print(
            f"[local-whisper] Downloading model '{model}' ({_MODEL_SIZES.get(model, 'unknown size')})...",
            file=sys.stderr,
            flush=True,
        )
    else:
        _suppress_progress_bars()

    import mlx_whisper

    silence = np.zeros(int(0.5 * 16000), dtype="float32")
    try:
        mlx_whisper.transcribe(silence, path_or_hf_repo=model, verbose=False)
        print("[local-whisper] Model ready.", file=sys.stderr, flush=True)
    except Exception as exc:
        print(f"[local-whisper] Warm-up failed (non-fatal): {exc}", file=sys.stderr, flush=True)


def run(
    audio: np.ndarray,
    model: str = DEFAULT_MODEL,
    backend: str = DEFAULT_BACKEND,
) -> str:
    """Transcribe audio array to text using local MLX Whisper model.

    Args:
        audio: Float32 numpy array at 16kHz sample rate.
        model: HuggingFace model ID.
        backend: Backend name ("mlx-whisper" or "parakeet-mlx").

    Returns:
        Transcribed text string, stripped of leading/trailing whitespace.
    """
    if _model_is_cached(model):
        _suppress_progress_bars()

    print(f"Transcribing with {model} ({backend})...", file=sys.stderr, flush=True)
    start = time.perf_counter()

    if backend == Backend.PARAKEET:
        text = _run_parakeet(audio, model)
    else:
        text = _run_mlx_whisper(audio, model)

    elapsed = time.perf_counter() - start
    print(f"Transcription done in {elapsed:.2f}s", file=sys.stderr, flush=True)

    return text
