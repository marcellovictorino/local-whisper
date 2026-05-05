# Phase 12: CoreML Backend — Research Summary

**Date:** 2026-05-04
**Unknowns researched:** 3

---

## Decision: whisperkittools is the only viable Python CoreML path

| Approach | Verdict | Reason |
|---|---|---|
| `whisperkittools` + coremltools | ✅ **RECOMMENDED** | Pre-built arm64 wheels, full ASR pipeline, 200–500ms |
| `pywhispercpp` (PyPI wheel) | ❌ Skip | Metal GPU only, no ANE/CoreML, same speed as mlx-whisper |
| `whisperkit-cli` subprocess | ❌ Skip | 1–5s model reload per keypress, no persistent server in Homebrew bottle |

---

## 1. coremltools + whisperkittools

**Key finding:** `pip install whisperkittools` works on macOS arm64 (no Xcode/compilation).
Uses `argmaxinc/whisperkit-coreml` pre-compiled CoreML models from HuggingFace.

**Realistic latency:** 200–500ms end-to-end from Python on M1/M2/M3 (vs ~1s mlx-whisper).

**Critical constraint — first-run ANE compilation:** 4+ minutes on first model load.
Must run in `warm_up()` at startup (same pattern as current mlx warm_up).

**API pattern:**
```python
from whisperkittools import WhisperKit
pipe = WhisperKit("distil-whisper_distil-large-v3_turbo_600MB")
result = pipe.transcribe("audio.wav")  # or numpy via temp WAV
text = result["text"]
```

**Target model:** `distil-whisper_distil-large-v3_turbo_600MB` — 600MB, consistent with current default.

**Constraints:**
- Pin `numpy<2` in pyproject.toml (coremltools incompatible with numpy 2.x)
- encoder → `CPU_AND_NE` (ANE), decoder → `CPU_AND_GPU`
- macOS only (no Linux inference)

Details: [coremltools.md](research/coremltools.md)

---

## 2. pywhispercpp — ELIMINATED

Pre-built arm64 PyPI wheel uses Metal GPU (not ANE). CoreML/ANE requires compilation
from source (`WHISPER_COREML=1`), violating zero-compilation constraint. Metal-only
speed ≈ mlx-whisper — no benefit.

Details: [pywhispercpp.md](research/pywhispercpp.md)

---

## 3. WhisperKit CLI subprocess — ELIMINATED

`brew install whisperkit-cli` works (arm64, no Xcode). But every subprocess invocation
restarts the process and reloads CoreML models (1–5s). No persistent server in
Homebrew bottle (`serve` requires `BUILD_ALL=1` from source). Latency would be
**worse** than current mlx-whisper baseline for dictation.

Details: [whisperkit-cli.md](research/whisperkit-cli.md)

---

## Phase 12 Implementation Plan Inputs

Based on research, Phase 12 should:

1. **Add `whisperkittools` as optional extra** (`--extra coreml`)
2. **Register `KnownModel.DISTIL_WHISPER_COREML`** with backend `"whisperkittools"`
3. **Implement `_run_whisperkittools(audio, model)`** — temp WAV → `WhisperKit.transcribe()`
4. **Update `warm_up()`** — pre-download + trigger ANE compilation at startup
5. **Pin `numpy<2`** in pyproject.toml for whisperkittools installs
6. **Benchmark** coreml vs mlx-whisper in `benchmark_compare.py`

Key open questions for planning:
- Does `WhisperKit(...).transcribe()` accept numpy directly or only file paths?
- Is there a `precompile()` / `warm_up()` method, or does first transcription trigger compilation?
- Does `whisperkittools` PyPI package export a stable `WhisperKit` class API?
- What is the exact HuggingFace model ID format expected by whisperkittools?
