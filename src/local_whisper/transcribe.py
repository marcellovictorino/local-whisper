import os
import sys
import time
import tomllib
from pathlib import Path

import numpy as np

_CONFIG_PATH = Path.home() / ".config" / "local-whisper" / "config.toml"

DEFAULT_MODEL = "mlx-community/distil-whisper-large-v3"

_MODEL_SIZES: dict[str, str] = {
    "mlx-community/whisper-large-v3-turbo": "~1.5 GB",
    "mlx-community/distil-whisper-large-v3": "~600 MB",
}


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
    os.environ["HF_HUB_DISABLE_PROGRESS_BARS"] = "1"
    os.environ["TQDM_DISABLE"] = "1"


def warm_up(model: str = DEFAULT_MODEL) -> None:
    """Download (if needed) and pre-load model, compiling Metal shaders.

    Runs at startup in a background thread so the first keypress is instant.
    Shows download progress when model is not yet cached.

    Args:
        model: HuggingFace model ID to pre-load.
    """
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
) -> str:
    """Transcribe audio array to text using local MLX Whisper model.

    Args:
        audio: Float32 numpy array at 16kHz sample rate.
        model: HuggingFace model ID for mlx-whisper.

    Returns:
        Transcribed text string, stripped of leading/trailing whitespace.
    """
    if _model_is_cached(model):
        _suppress_progress_bars()

    import mlx_whisper  # lazy import — avoids slow startup cost

    print(f"Transcribing with {model}...", file=sys.stderr, flush=True)
    start = time.perf_counter()

    result = mlx_whisper.transcribe(audio, path_or_hf_repo=model, verbose=False)

    elapsed = time.perf_counter() - start
    print(f"Transcription done in {elapsed:.2f}s", file=sys.stderr, flush=True)

    return result["text"].strip()
