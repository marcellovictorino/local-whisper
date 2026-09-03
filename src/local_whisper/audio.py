import logging
import math
import threading
import time
from collections.abc import Callable

import numpy as np
import sounddevice

logger = logging.getLogger("local_whisper")

SAMPLE_RATE_HZ = 16_000  # Whisper expects 16 kHz input
_POLL_INTERVAL_S = 0.2  # how often record_until_event checks the silence timeout


def record(duration: float, sample_rate: int = SAMPLE_RATE_HZ) -> np.ndarray:
    """Record audio from default microphone.

    Args:
        duration: Recording length in seconds.
        sample_rate: Sample rate in Hz. Whisper expects 16000.

    Returns:
        Float32 numpy array of shape (N,) normalised to [-1.0, 1.0].
    """
    logger.info("Recording...")
    audio = sounddevice.rec(
        int(duration * sample_rate),
        samplerate=sample_rate,
        channels=1,
        dtype="float32",
    )
    sounddevice.wait()
    logger.info("Done.")
    return audio.squeeze()


def record_until_event(
    stop_event: threading.Event,
    sample_rate: int = SAMPLE_RATE_HZ,
    chunk_size: int = 512,
    on_amplitude: Callable[[float], None] | None = None,
    silence_timeout_s: float | None = None,
    silence_rms_threshold: float = 0.01,
) -> np.ndarray:
    """Record audio from default microphone until stop_event is set.

    Args:
        stop_event: Threading event — recording stops when set.
        sample_rate: Sample rate in Hz. Whisper expects 16000.
        chunk_size: Frames per callback chunk.
        on_amplitude: Optional callback fired with RMS amplitude per chunk.
        silence_timeout_s: If given, recording auto-stops after this many
            seconds with no chunk above silence_rms_threshold. Also the grace
            period before any speech is detected. This is the backstop for a
            stop_event that never arrives — e.g. a lost key-release event —
            so a stuck session can't record forever with nobody talking.
        silence_rms_threshold: RMS level above which a chunk counts as speech.

    Returns:
        Float32 numpy array of shape (N,) normalised to [-1.0, 1.0].
    """
    chunks: list[np.ndarray] = []
    last_voice_at = time.monotonic()
    need_rms = on_amplitude is not None or silence_timeout_s is not None

    def _callback(
        indata: np.ndarray,
        frames: int,  # noqa: ARG001
        time_info: object,  # noqa: ARG001
        status: sounddevice.CallbackFlags,
    ) -> None:
        nonlocal last_voice_at
        if status:
            logger.warning("[audio] %s", status)
        chunks.append(indata.copy())
        if need_rms:
            flat = indata[:, 0]
            rms = math.sqrt(float(np.dot(flat, flat)) / len(flat))
            if silence_timeout_s is not None and rms >= silence_rms_threshold:
                last_voice_at = time.monotonic()
            if on_amplitude is not None:
                on_amplitude(rms)

    logger.info("Recording...")
    with sounddevice.InputStream(
        samplerate=sample_rate,
        channels=1,
        dtype="float32",
        blocksize=chunk_size,
        callback=_callback,
    ):
        poll_timeout = min(_POLL_INTERVAL_S, silence_timeout_s) if silence_timeout_s is not None else None
        while not stop_event.wait(timeout=poll_timeout):
            if silence_timeout_s is not None and time.monotonic() - last_voice_at >= silence_timeout_s:
                logger.info("Silence timeout — auto-stopping.")
                break

    logger.info("Done.")

    if not chunks:
        return np.zeros(0, dtype="float32")
    return np.concatenate(chunks).squeeze()
