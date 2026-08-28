import contextlib
import logging
import os
import shutil
import tempfile
import threading
import time
from enum import StrEnum
from pathlib import Path
from typing import Any

import numpy as np

from local_whisper import config
from local_whisper.audio import SAMPLE_RATE_HZ

logger = logging.getLogger("local_whisper")


class KnownModel(StrEnum):
    """Supported model IDs with known backend assignments.

    Add new models here to register them. Unknown IDs fall back to mlx-whisper.
    """

    WHISPER_SMALL_EN = "mlx-community/whisper-small.en-mlx"  # default; best latency/accuracy; English only; ~250 MB
    DISTIL_WHISPER = "mlx-community/distil-whisper-large-v3"  # high accuracy; English only; ~600 MB
    WHISPER_TURBO = "mlx-community/whisper-large-v3-turbo"  # multilingual, accurate; ~1.5 GB
    PARAKEET_V2 = "mlx-community/parakeet-tdt-0.6b-v2"  # fastest; English only; requires --extra parakeet + ffmpeg


class Backend(StrEnum):
    """Inference backend names. Backend is auto-inferred from model ID via get_backend()."""

    MLX_WHISPER = "mlx-whisper"
    PARAKEET = "parakeet-mlx"


DEFAULT_MODEL = KnownModel.WHISPER_SMALL_EN
DEFAULT_BACKEND = Backend.MLX_WHISPER

_MODEL_SIZES: dict[str, str] = {
    KnownModel.WHISPER_TURBO: "~1.5 GB",
    KnownModel.DISTIL_WHISPER: "~600 MB",
    KnownModel.PARAKEET_V2: "~600 MB",
    KnownModel.WHISPER_SMALL_EN: "~250 MB",
}

_BACKEND_MAP: dict[str, Backend] = {
    KnownModel.DISTIL_WHISPER: Backend.MLX_WHISPER,
    KnownModel.WHISPER_TURBO: Backend.MLX_WHISPER,
    KnownModel.PARAKEET_V2: Backend.PARAKEET,
}

# Parakeet model instance cached at warm_up time so from_pretrained() runs once per session.
_parakeet_cache: dict[str, Any] = {}

# ffmpeg presence doesn't change mid-session; cache so the hot path skips the PATH scan.
_ffmpeg_available: bool | None = None


def _has_ffmpeg() -> bool:
    global _ffmpeg_available
    if _ffmpeg_available is None:
        _ffmpeg_available = shutil.which("ffmpeg") is not None
    return _ffmpeg_available


def _parakeet_unavailable_reason() -> str | None:
    """None when the parakeet backend can run; otherwise why it can't."""
    try:
        import parakeet_mlx  # noqa: F401
    except ImportError:
        return "parakeet-mlx not installed (run: uv sync --extra parakeet)"
    if not _has_ffmpeg():
        return "ffmpeg not found (run: brew install ffmpeg)"
    return None


def _silence(duration_s: float = 0.5) -> np.ndarray:
    return np.zeros(int(duration_s * SAMPLE_RATE_HZ), dtype="float32")


# Set by warm_up() when the warm-up attempt completes (success or failure).
_warmed = threading.Event()

# Serializes all MLX/Metal calls (dictation, keepalive ping, wake re-warm, warm_up)
# — MLX Metal command queues are not safe for concurrent access from multiple
# threads, and a collision can hang the native call with no Python exception.
_metal_lock = threading.Lock()

_progress_bars_suppressed = False


def get_backend(model: str) -> Backend:
    """Infer backend from model ID. Unknown IDs are assumed whisper-compatible.

    Args:
        model: HuggingFace model ID (from get_model() or KnownModel).

    Returns:
        Backend enum value.
    """
    return _BACKEND_MAP.get(model, Backend.MLX_WHISPER)


def supports_vocab_prompt(backend: str) -> bool:
    """Only whisper backends accept initial_prompt vocabulary seeding."""
    return backend == Backend.MLX_WHISPER


def get_model(path: Path = config.CONFIG_PATH) -> str:
    """Read model ID from config.toml, falling back to DEFAULT_MODEL.

    Args:
        path: Path to config.toml file.

    Returns:
        HuggingFace model ID string.
    """
    value = config.get_whisper_model(path)
    return value if isinstance(value, str) else DEFAULT_MODEL


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
    global _progress_bars_suppressed
    if _progress_bars_suppressed:
        return
    os.environ["HF_HUB_DISABLE_PROGRESS_BARS"] = "1"
    os.environ["TQDM_DISABLE"] = "1"
    logging.getLogger("huggingface_hub").setLevel(logging.ERROR)
    _progress_bars_suppressed = True


def _run_mlx_whisper(audio: np.ndarray, model: str, initial_prompt: str | None = None) -> str:
    import mlx.core as mx
    import mlx_whisper

    # MLX Metal streams are thread-local; warm_up runs on a different thread than
    # each keypress transcription thread, so we create a fresh stream here.
    # _metal_lock serializes this against keepalive/wake-rewarm/warm_up calls —
    # concurrent Metal command-queue access from multiple threads can hang the
    # native call with no Python exception raised.
    with _metal_lock, mx.stream(mx.gpu):
        result = mlx_whisper.transcribe(
            audio,
            path_or_hf_repo=model,
            verbose=False,
            initial_prompt=initial_prompt,
            # Single greedy pass. mlx-whisper's default temperature is a 6-value
            # fallback tuple (0.0..1.0) that re-decodes each 30s window at every
            # higher temperature whenever the compression-ratio / logprob
            # thresholds trip — up to 6x decode work on exactly the hard audio
            # where latency hurts most. Pinning 0.0 trades that fallback for
            # consistent low latency; validated to not regress WER (td-255e47).
            temperature=0.0,
        )
    return result["text"].strip()


def _run_parakeet(audio: np.ndarray, model: str) -> str:
    reason = _parakeet_unavailable_reason()
    if reason:
        logger.warning("Parakeet unavailable — %s. Falling back to mlx-whisper.", reason)
        return _run_mlx_whisper(audio, KnownModel.WHISPER_SMALL_EN)

    import parakeet_mlx
    import soundfile as sf

    with _metal_lock:
        if model not in _parakeet_cache:
            _parakeet_cache[model] = parakeet_mlx.from_pretrained(model)
        parakeet_model = _parakeet_cache[model]

        tmp_path = None
        try:
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                tmp_path = tmp.name
            sf.write(tmp_path, audio, SAMPLE_RATE_HZ, subtype="PCM_16")
            result = parakeet_model.transcribe(tmp_path)
        finally:
            if tmp_path:
                with contextlib.suppress(OSError):
                    Path(tmp_path).unlink(missing_ok=True)
    return result.text.strip()


def warm_up(model: str = DEFAULT_MODEL, backend: str = DEFAULT_BACKEND) -> None:
    """Download (if needed) and pre-load model, compiling Metal shaders.

    Runs at startup in a background thread so the first keypress is instant.
    Shows download progress when model is not yet cached.

    Args:
        model: HuggingFace model ID to pre-load.
        backend: Backend name ("mlx-whisper" or "parakeet-mlx").
    """
    try:
        if backend == Backend.PARAKEET:
            reason = _parakeet_unavailable_reason()
            if reason:
                # Warm the whisper model sessions will actually fall back to,
                # so a broken parakeet install doesn't mean a cold first dictation.
                logger.warning(
                    "Parakeet unavailable — %s. Sessions will fall back to %s.",
                    reason,
                    KnownModel.WHISPER_SMALL_EN,
                )
                model = KnownModel.WHISPER_SMALL_EN
            else:
                import parakeet_mlx

                try:
                    _parakeet_cache[model] = parakeet_mlx.from_pretrained(model)
                    # Dummy inference pre-pays Metal shader compilation and the ffmpeg
                    # audio-loading path, same as the whisper branch below.
                    _run_parakeet(_silence(), model)
                    logger.info("Model ready.")
                except Exception as exc:
                    logger.warning("Warm-up failed (non-fatal): %s", exc)
                return

        if not _model_is_cached(model):
            logger.info(
                "Downloading model '%s' (%s)...",
                model,
                _MODEL_SIZES.get(model, "unknown size"),
            )
        else:
            _suppress_progress_bars()

        import mlx_whisper

        try:
            with _metal_lock:
                mlx_whisper.transcribe(_silence(), path_or_hf_repo=model, verbose=False)
            logger.info("Model ready.")
        except Exception as exc:
            logger.warning("Warm-up failed (non-fatal): %s", exc)
    finally:
        _warmed.set()


def _run_backend(audio: np.ndarray, model: str, backend: str, initial_prompt: str | None = None) -> str:
    """Dispatch transcription to the backend for this model.

    initial_prompt is silently dropped for backends without vocabulary
    seeding (see supports_vocab_prompt); the app logs that once at startup.
    """
    if backend == Backend.PARAKEET:
        return _run_parakeet(audio, model)
    return _run_mlx_whisper(audio, model, initial_prompt=initial_prompt)


_KEEPALIVE_INTERVAL_S = 20 * 60  # 20 minutes — keeps model pages active before macOS compresses them


def _keepalive_ping(model: str, backend: str) -> None:
    """Run one silent transcription to re-page the model's Metal memory."""
    try:
        _run_backend(_silence(), model, backend)
        logger.debug("Keepalive: model warm.")
    except Exception as exc:  # noqa: BLE001 — keepalive is best-effort
        logger.debug("Keepalive ping failed (non-fatal): %s", exc)


def _keepalive_loop(model: str, interval_s: int, backend: str) -> None:
    wait_warmed(timeout=None)  # wait indefinitely — model download may exceed 60s
    while True:
        time.sleep(interval_s)
        _keepalive_ping(model, backend)


def start_keepalive(
    model: str = DEFAULT_MODEL, backend: str = DEFAULT_BACKEND, interval_s: int = _KEEPALIVE_INTERVAL_S
) -> None:
    """Spawn daemon thread that runs silent transcription every interval_s to prevent GPU memory eviction.

    Both MLX backends keep weights in Metal unified memory, so both need
    periodic touches to stop macOS from compressing idle pages.

    Covers active-idle only: during system sleep this thread is frozen and its
    timer can't fire, so pair it with start_wake_watcher() to re-warm on wake.
    """
    t = threading.Thread(target=_keepalive_loop, args=(model, interval_s, backend), daemon=True)
    t.start()
    logger.debug("Keepalive started (interval: %ds).", interval_s)


# Kept alive for the process lifetime so the ObjC observer isn't collected.
_wake_observer: Any = None
_wake_target: tuple[str, str] | None = None


def _rewarm_on_wake() -> None:
    if _wake_target is not None:
        _keepalive_ping(*_wake_target)


def start_wake_watcher(model: str = DEFAULT_MODEL, backend: str = DEFAULT_BACKEND) -> None:
    """Re-warm the model immediately when the Mac wakes from sleep.

    System sleep evicts the weights from Metal unified memory *and* freezes the
    keepalive timer, so the first post-wake dictation would otherwise be cold
    (full reload + Metal shader recompile). NSWorkspaceDidWakeNotification fires
    on real user wake (not the periodic maintenance DarkWakes), letting us
    re-page the weights in the background before the user dictates.

    Requires the AppKit run loop that overlay.run() provides; degrades to a
    no-op (keepalive still covers active-idle) if AppKit is unavailable.
    """
    global _wake_observer, _wake_target
    if _wake_observer is not None:
        return
    try:
        from AppKit import NSWorkspace
        from Foundation import NSObject
    except Exception as exc:  # noqa: BLE001 — wake re-warm is an optimisation
        logger.debug("Wake watcher unavailable (AppKit import failed): %s", exc)
        return

    class _WakeHandler(NSObject):
        def handleWake_(self, _note: Any) -> None:
            threading.Thread(target=_rewarm_on_wake, daemon=True).start()

    _wake_target = (model, backend)
    _wake_observer = _WakeHandler.alloc().init()
    NSWorkspace.sharedWorkspace().notificationCenter().addObserver_selector_name_object_(
        _wake_observer, "handleWake:", "NSWorkspaceDidWakeNotification", None
    )
    logger.debug("Wake watcher registered (re-warm on wake).")


def wait_warmed(timeout: float | None = 60) -> bool:
    """Block until warm_up() has completed (success or failure).

    Args:
        timeout: Seconds to wait. None = wait forever. 0 = non-blocking check.

    Returns:
        True if warm-up finished within timeout; False if timeout elapsed first.
    """
    return _warmed.wait(timeout=timeout)


def run(
    audio: np.ndarray,
    model: str = DEFAULT_MODEL,
    backend: str = DEFAULT_BACKEND,
    initial_prompt: str | None = None,
) -> str:
    """Transcribe audio array to text using local MLX Whisper model.

    Args:
        audio: Float32 numpy array at 16kHz sample rate.
        model: HuggingFace model ID.
        backend: Backend name ("mlx-whisper" or "parakeet-mlx").
        initial_prompt: Optional text to seed Whisper's decoder. Biases token
            probabilities toward terms in the prompt (e.g. personal vocabulary).
            Ignored for Parakeet backend. ~224-token limit.

    Returns:
        Transcribed text string, stripped of leading/trailing whitespace.
    """
    _suppress_progress_bars()

    logger.debug("Transcribing with %s (%s)...", model, backend)
    start = time.perf_counter()

    text = _run_backend(audio, model, backend, initial_prompt=initial_prompt)

    elapsed = time.perf_counter() - start
    logger.debug("Transcription done in %.2fs", elapsed)

    return text
