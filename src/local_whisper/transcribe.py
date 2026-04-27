import os
import sys
import time
from pathlib import Path

import numpy as np

_MODEL_SIZE_HINT = "~1.5 GB"


def _model_is_cached(model: str) -> bool:
    """Check if the HuggingFace model snapshots exist in the local cache."""
    model_dir = "models--" + model.replace("/", "--")
    snapshots = Path.home() / ".cache" / "huggingface" / "hub" / model_dir / "snapshots"
    if not snapshots.exists():
        return False
    # At least one non-empty snapshot directory must exist
    return any(p.is_dir() and any(p.iterdir()) for p in snapshots.iterdir())


def run(
    audio: np.ndarray,
    model: str = "mlx-community/whisper-large-v3-turbo",
) -> str:
    """Transcribe audio array to text using local MLX Whisper model.

    Args:
        audio: Float32 numpy array at 16kHz sample rate.
        model: HuggingFace model ID for mlx-whisper.

    Returns:
        Transcribed text string, stripped of leading/trailing whitespace.
    """
    cached = _model_is_cached(model)

    if cached:
        # Suppress huggingface_hub and tqdm progress bars — model already local,
        # no download or verification progress needed.
        os.environ["HF_HUB_DISABLE_PROGRESS_BARS"] = "1"
        os.environ["TQDM_DISABLE"] = "1"
    else:
        print(
            f"First run: downloading model '{model}' ({_MODEL_SIZE_HINT}).\n"
            "  This only happens once — subsequent runs are instant.",
            file=sys.stderr,
            flush=True,
        )

    import mlx_whisper  # lazy import — avoids slow startup cost

    print(f"Transcribing with {model}...", file=sys.stderr, flush=True)
    start = time.perf_counter()

    result = mlx_whisper.transcribe(audio, path_or_hf_repo=model, verbose=False)

    elapsed = time.perf_counter() - start
    print(f"Transcription done in {elapsed:.2f}s", file=sys.stderr, flush=True)

    return result["text"].strip()
