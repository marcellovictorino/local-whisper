import os
import sys
import tempfile
import time
import tomllib
from enum import StrEnum
from pathlib import Path
from typing import Any

import numpy as np
import objc
from Foundation import NSURL, NSLocale

_CONFIG_PATH = Path.home() / ".config" / "local-whisper" / "config.toml"

objc.loadBundle(
    "Speech",
    globals(),
    bundle_path="/System/Library/Frameworks/Speech.framework",
)

# PyObjC cannot infer block signature from framework metadata for this selector.
# Without this registration, recognitionTaskWithRequest:resultHandler: silently
# fails to call the Python block.
objc.registerMetaDataForSelector(
    b"SFSpeechRecognizer",
    b"recognitionTaskWithRequest:resultHandler:",
    {
        "arguments": {
            3: {
                "callable": {
                    "retval": {"type": b"v"},
                    "arguments": {
                        0: {"type": b"^v"},
                        1: {"type": b"@"},
                        2: {"type": b"@"},
                    },
                }
            }
        }
    },
)


class KnownModel(StrEnum):
    """Supported model IDs with known backend assignments.

    Add new models here to register them. Unknown IDs fall back to mlx-whisper.
    """

    DISTIL_WHISPER = "mlx-community/distil-whisper-large-v3"  # default; fast English
    WHISPER_TURBO = "mlx-community/whisper-large-v3-turbo"  # multilingual, accurate
    PARAKEET_V2 = "mlx-community/parakeet-tdt-0.6b-v2"  # fastest; English only
    SFSPEECH_EN = "macos/sfspeech-en-us"  # macOS SFSpeechRecognizer; synthetic ID, not a HF repo


class Backend(StrEnum):
    """Inference backend names. Backend is auto-inferred from model ID via get_backend()."""

    MLX_WHISPER = "mlx-whisper"
    PARAKEET = "parakeet-mlx"
    SFSPEECH = "sfspeech"


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
    KnownModel.SFSPEECH_EN: Backend.SFSPEECH,
}

# Parakeet model instance cached at warm_up time so from_pretrained() runs once per session.
_parakeet_cache: dict[str, Any] = {}

# SFSpeechRecognizer instance cached at warm_up time; recognizer creation is lightweight
# but reusing the same instance avoids repeated alloc/init overhead per keypress.
_sfspeech_recognizer_cache: dict[str, Any] = {}


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
        value = data.get("whisper", {}).get("model", DEFAULT_MODEL)
        return value if isinstance(value, str) else DEFAULT_MODEL
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
        return _run_mlx_whisper(audio, DEFAULT_MODEL)

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


def _run_sfspeech(audio: np.ndarray, model: str) -> str:
    """Transcribe audio via macOS SFSpeechRecognizer (on-device, zero install).

    WAV overhead is ~1–5ms for typical clips (5s = ~160KB PCM16); not the bottleneck.
    Uses threading.Event rather than NSRunLoop — safe from any thread, including the
    background thread used by the hotkey handler.

    Args:
        audio: Float32 numpy array at 16kHz.
        model: Model ID (used as cache key; only "macos/sfspeech-en-us" supported).

    Returns:
        Transcribed text string.
    """
    import threading

    import soundfile as sf

    if model not in _sfspeech_recognizer_cache:
        locale = NSLocale.alloc().initWithLocaleIdentifier_("en-US")
        _sfspeech_recognizer_cache[model] = SFSpeechRecognizer.alloc().initWithLocale_(locale)  # noqa: F821
    recognizer = _sfspeech_recognizer_cache[model]

    tmp_path = None
    transcript = ""
    try:
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp_path = tmp.name
        sf.write(tmp_path, audio, 16000, subtype="PCM_16")

        url = NSURL.fileURLWithPath_(tmp_path)
        request = SFSpeechURLRecognitionRequest.alloc().initWithURL_(url)  # noqa: F821
        request.setRequiresOnDeviceRecognition_(True)
        request.setAddsPunctuation_(True)

        done = threading.Event()
        result_holder: list[str | None] = [None]

        def handler(result, error):
            if result is not None and result.isFinal():
                result_holder[0] = result.bestTranscription().formattedString()
                done.set()
            elif error is not None:
                done.set()

        recognizer.recognitionTaskWithRequest_resultHandler_(request, handler)
        done.wait(timeout=5.0)
        transcript = result_holder[0] or ""
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)

    return transcript.strip()


def warm_up(model: str = DEFAULT_MODEL, backend: str = DEFAULT_BACKEND) -> None:
    """Download (if needed) and pre-load model, compiling Metal shaders.

    Runs at startup in a background thread so the first keypress is instant.
    Shows download progress when model is not yet cached.

    Args:
        model: HuggingFace model ID to pre-load.
        backend: Backend name ("mlx-whisper" or "parakeet-mlx").
    """
    if backend == Backend.SFSPEECH:
        try:
            locale = NSLocale.alloc().initWithLocaleIdentifier_("en-US")
            _sfspeech_recognizer_cache[model] = SFSpeechRecognizer.alloc().initWithLocale_(locale)  # noqa: F821
            print("[local-whisper] SFSpeech recognizer ready.", file=sys.stderr, flush=True)
        except Exception as exc:
            print(f"[local-whisper] SFSpeech warm-up failed (non-fatal): {exc}", file=sys.stderr, flush=True)
        return

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

    if backend == Backend.SFSPEECH:
        try:
            text = _run_sfspeech(audio, model)
        except Exception as exc:
            print(
                f"[local-whisper] SFSpeech failed, falling back to mlx-whisper: {exc}",
                file=sys.stderr,
            )
            text = _run_mlx_whisper(audio, KnownModel.DISTIL_WHISPER)
    elif backend == Backend.PARAKEET:
        text = _run_parakeet(audio, model)
    else:
        text = _run_mlx_whisper(audio, model)

    elapsed = time.perf_counter() - start
    print(f"Transcription done in {elapsed:.2f}s", file=sys.stderr, flush=True)

    return text
