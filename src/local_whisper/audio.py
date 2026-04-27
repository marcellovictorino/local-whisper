import sys

import numpy as np
import sounddevice


def record(duration: float, sample_rate: int = 16000) -> np.ndarray:
    """Record audio from default microphone.

    Args:
        duration: Recording length in seconds.
        sample_rate: Sample rate in Hz. Whisper expects 16000.

    Returns:
        Float32 numpy array of shape (N,) normalised to [-1.0, 1.0].
    """
    print("Recording...", file=sys.stderr, flush=True)
    audio = sounddevice.rec(
        int(duration * sample_rate),
        samplerate=sample_rate,
        channels=1,
        dtype="float32",
    )
    sounddevice.wait()
    print("Done.", file=sys.stderr, flush=True)
    return audio.squeeze()
