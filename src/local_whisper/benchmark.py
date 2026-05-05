"""Benchmark transcription latency for comparison across models and backends."""

from __future__ import annotations

import time

import numpy as np

_SAMPLE_RATE = 16_000
DURATION_S = 30


def run(model: str, backend: str = "mlx-whisper", runs: int = 3) -> dict:
    """Benchmark warm-up and transcription latency.

    Args:
        model: HuggingFace model ID to benchmark.
        backend: Backend name ("mlx-whisper" or "parakeet-mlx").
        runs: Number of transcription runs (default 3).

    Returns:
        Dict with keys: model, backend, warmup_s, runs, mean_s, min_s, max_s, times_s.
    """
    from local_whisper import transcribe

    audio = np.zeros(_SAMPLE_RATE * DURATION_S, dtype="float32")

    t0 = time.perf_counter()
    transcribe.warm_up(model, backend=backend)
    warmup_s = time.perf_counter() - t0

    times: list[float] = []
    for _ in range(runs):
        t0 = time.perf_counter()
        transcribe.run(audio, model=model, backend=backend)
        times.append(time.perf_counter() - t0)

    return {
        "model": model,
        "backend": backend,
        "audio_duration_s": DURATION_S,
        "warmup_s": round(warmup_s, 3),
        "runs": runs,
        "mean_s": round(sum(times) / len(times), 3),
        "min_s": round(min(times), 3),
        "max_s": round(max(times), 3),
        "times_s": [round(t, 3) for t in times],
    }
