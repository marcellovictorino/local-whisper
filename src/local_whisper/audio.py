import sys
import threading
from collections.abc import Callable

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


def record_until_event(
    stop_event: threading.Event,
    sample_rate: int = 16000,
    chunk_size: int = 512,
    on_amplitude: Callable[[float], None] | None = None,
) -> np.ndarray:
    """Record audio from default microphone until stop_event is set.

    Args:
        stop_event: Threading event — recording stops when set.
        sample_rate: Sample rate in Hz. Whisper expects 16000.
        chunk_size: Frames per callback chunk.
        on_amplitude: Optional callback fired with RMS amplitude per chunk.

    Returns:
        Float32 numpy array of shape (N,) normalised to [-1.0, 1.0].
    """
    chunks: list[np.ndarray] = []

    def _callback(
        indata: np.ndarray,
        frames: int,  # noqa: ARG001
        time_info: object,  # noqa: ARG001
        status: sounddevice.CallbackFlags,
    ) -> None:
        if status:
            print(f"[audio] {status}", file=sys.stderr)
        chunks.append(indata.copy())
        if on_amplitude is not None:
            rms = float(np.sqrt(np.mean(indata**2)))
            on_amplitude(rms)

    print("Recording...", file=sys.stderr, flush=True)
    with sounddevice.InputStream(
        samplerate=sample_rate,
        channels=1,
        dtype="float32",
        blocksize=chunk_size,
        callback=_callback,
    ):
        stop_event.wait()

    print("Done.", file=sys.stderr, flush=True)

    if not chunks:
        return np.zeros(0, dtype="float32")
    return np.concatenate(chunks).squeeze()
