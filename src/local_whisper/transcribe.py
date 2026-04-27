import sys
import time

import numpy as np


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
    import mlx_whisper  # lazy import — avoids slow startup cost

    print(f"Transcribing with {model}...", file=sys.stderr, flush=True)
    start = time.perf_counter()

    result = mlx_whisper.transcribe(audio, path_or_hf_repo=model)

    elapsed = time.perf_counter() - start
    print(f"Transcription done in {elapsed:.2f}s", file=sys.stderr, flush=True)

    return result["text"].strip()
