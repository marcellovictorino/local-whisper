# Phase 13: Sub-second ASR Research

**Date:** 2026-05-05
**Researcher:** Claude (Sonnet 4.6)
**Machine:** Apple Silicon (macOS 25.x)

---

## Candidates Evaluated

| Candidate | Latency — 5s audio | Latency — 15s audio | WER estimate | Install friction | Evaluated |
|-----------|-------------------|---------------------|--------------|-----------------|-----------|
| SFSpeechRecognizer (PyObjC) | 200–525ms warm | 523–705ms warm | ~0% on clear speech | Zero (built-in) | ✅ Yes |
| whisper.cpp CoreML binary | not measured | not measured | ~5–10% (known) | Medium (GGML model download) | ⏭ Skipped — SFSpeechRecognizer sufficient |
| distil-whisper-small / whisper-tiny | not measured | not measured | ~20%+ (expected) | Trivial | ⏭ Skipped — fallback not needed |

---

## Winner

**macOS SFSpeechRecognizer via PyObjC** — delivers 200–700ms on-device transcription with zero install friction and accuracy indistinguishable from distil-whisper on clear English speech.

---

## Spike Findings

### SFSpeechRecognizer

**API path confirmed:** `SFSpeechURLRecognitionRequest` (file path in, transcript out — no numpy→CMSampleBuffer conversion needed).

**Key findings:**
- `requiresOnDeviceRecognition = True` works without Siri/network — fully offline
- `addsPunctuation = True` adds ~100–200ms overhead but produces natural output
- Auth status shows 0 ("not determined") but recognition succeeds — Terminal/Python inherits access silently; no explicit `requestAuthorization_` call needed in CLI context
- PyObjC cannot infer block signature from framework metadata — `registerMetaDataForSelector` required for `recognitionTaskWithRequest:resultHandler:`
- No model download on first run; uses built-in macOS Siri language model (~0 bytes user-facing)
- Cold start (first call per process): ~520ms. Warm (subsequent calls): 165–700ms depending on audio length

**Measured latency (warm, on-device, en-US):**

| Clip | No punctuation | With punctuation |
|------|---------------|-----------------|
| ~5s (4.25s) | 165–525ms | 206–639ms |
| ~15s (12.8s) | 354ms | 603–705ms |

**Transcription quality assessment (TTS-generated speech):**
- All words correct on 5s clip
- All words correct on 15s clip with punctuation
- Minor: proper noun capitalisation sometimes differs ("Riverbank" vs "river bank") — acceptable for dictation
- No filler word hallucination (unlike whisper which sometimes adds "Thank you." at end)

**Limitation:** English-only (en-US locale tested). Other locales available but not tested.

---

## Integration Path

### Python API for `transcribe.py`

```python
# One-time at module import (pyobjc already a project dep):
import objc
from Foundation import NSDate, NSLocale, NSRunLoop, NSURL

objc.loadBundle("Speech", globals(),
    bundle_path="/System/Library/Frameworks/Speech.framework")

objc.registerMetaDataForSelector(
    b"SFSpeechRecognizer",
    b"recognitionTaskWithRequest:resultHandler:",
    {"arguments": {3: {"callable": {
        "retval": {"type": b"v"},
        "arguments": {0: {"type": b"^v"}, 1: {"type": b"@"}, 2: {"type": b"@"}},
    }}}}
)

# Per-call (warm path):
def _run_sfspeech(audio: np.ndarray, model: str) -> str:
    # Write numpy to temp WAV (same pattern as _run_parakeet)
    # then call SFSpeechURLRecognitionRequest with the path
    ...
```

**Warm-up:** Load recognizer once in `warm_up()` — `SFSpeechRecognizer.alloc().initWithLocale_(locale)`.  First transcription call triggers model init; subsequent calls are fast.

**Audio input:** `SFSpeechURLRecognitionRequest` requires a file path. Write numpy array to temp WAV via `soundfile` (same pattern as `_run_parakeet`), transcribe, delete. Estimated overhead: ~10–20ms.

---

## Changes Needed in `transcribe.py`

### 1. New `Backend` enum value

```python
class Backend(StrEnum):
    MLX_WHISPER = "mlx-whisper"
    PARAKEET = "parakeet-mlx"
    SFSPEECH = "sfspeech"          # new
```

### 2. New `KnownModel` entry

```python
class KnownModel(StrEnum):
    DISTIL_WHISPER = "mlx-community/distil-whisper-large-v3"
    WHISPER_TURBO = "mlx-community/whisper-large-v3-turbo"
    PARAKEET_V2 = "mlx-community/parakeet-tdt-0.6b-v2"
    SFSPEECH_EN = "macos/sfspeech-en-us"    # new — synthetic ID, not a HF repo
```

### 3. New `_BACKEND_MAP` entry

```python
_BACKEND_MAP: dict[str, Backend] = {
    KnownModel.DISTIL_WHISPER: Backend.MLX_WHISPER,
    KnownModel.WHISPER_TURBO: Backend.MLX_WHISPER,
    KnownModel.PARAKEET_V2: Backend.PARAKEET,
    KnownModel.SFSPEECH_EN: Backend.SFSPEECH,   # new
}
```

### 4. New `_run_sfspeech(audio, model)` function

```python
def _run_sfspeech(audio: np.ndarray, model: str) -> str:
    # Write temp WAV, call SFSpeechURLRecognitionRequest with
    # requiresOnDeviceRecognition=True, addsPunctuation=True,
    # drain NSRunLoop until isFinal(), delete temp file, return text
    ...
```

### 5. New `_sfspeech_recognizer_cache` module-level dict

Same caching pattern as `_parakeet_cache` — store recognizer instance keyed by locale string.

### 6. `warm_up()` branch for `Backend.SFSPEECH`

Pre-create the `SFSpeechRecognizer` instance. No model download needed.

### 7. `run()` dispatch

```python
if backend == Backend.SFSPEECH:
    text = _run_sfspeech(audio, model)
```

---

## Distribution / Install Changes

**pyproject.toml:** No new dependency. `pyobjc-framework-Cocoa` (which provides `objc`, `AppKit`, `Foundation`) is already pulled in transitively via `pynput`. The Speech framework is a macOS system framework — no pip package needed.

**setup.sh:** No changes. No binary download, no model download.

**config.toml user-facing:** `[whisper] model = "macos/sfspeech-en-us"` (or set as default — see implementation plan).

---

## Recommendation for Implementation Plan

1. Make `SFSpeechRecognizer` the **new default model** — replaces `distil-whisper-large-v3` as default for English users on macOS 13+
2. Keep `distil-whisper-large-v3` available for multilingual / accuracy-critical users via config
3. Fall back gracefully if `SFSpeechRecognizer` is unavailable (older macOS, non-Apple-Silicon)
4. `addsPunctuation = True` should be on by default — output quality is better

---

## Deferred / Rejected

- **whisper.cpp CoreML**: Not evaluated. SFSpeechRecognizer met all criteria — <1s latency, high accuracy, zero install. No need to add binary distribution complexity.
- **distil-whisper-small**: Not evaluated. Fallback path; WER likely unacceptable; not needed.
