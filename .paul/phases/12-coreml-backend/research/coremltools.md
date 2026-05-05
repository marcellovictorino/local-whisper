# Research: coremltools + whisperkittools for Python CoreML inference

## Summary

**Verdict: VIABLE — recommended path for Phase 12.**

`whisperkittools` (wraps coremltools + argmaxinc CoreML models) provides a pure-Python,
pre-built-wheel CoreML inference path. Realistic 200–500ms end-to-end for 30s audio on
M1/M2/M3, vs ~1s with mlx-whisper.

---

## 1. Pre-built arm64 Wheels

- `coremltools>=8.2` ships genuine pre-built arm64 wheels on PyPI (added in late 2024).
  No Xcode or compilation required: `pip install coremltools` works on macOS arm64.
- `whisperkittools` depends on coremltools and also ships arm64 wheels.
  `pip install whisperkittools` installs cleanly without Xcode/cmake.

---

## 2. Pre-converted Models on HuggingFace

Repo: `argmaxinc/whisperkit-coreml`

Key models (CoreML `.mlpackage` / `.mlmodelc`):
- `distil-whisper_distil-large-v3_594MB` — best match for current project default
- `distil-whisper_distil-large-v3_turbo_600MB` — recommended (speed + accuracy)
- `openai_whisper-large-v3-v20240930_626MB` — multilingual, accurate

---

## 3. Python Inference API (whisperkittools)

```python
from whisperkittools import WhisperKit

# Load model (downloads + compiles on first call, then cached)
pipe = WhisperKit("distil-whisper_distil-large-v3_turbo_600MB")

# Transcribe from file path (float32 numpy requires writing to WAV first)
result = pipe.transcribe("audio.wav")
print(result["text"])
```

whisperkittools handles: log-mel spectrogram, encoder (ANE), decoder (GPU), tokenizer,
beam search. No manual ASR pipeline needed.

---

## 4. Realistic Latency

Source: mac-whisper-speedtest (M4 Mac, large models)

| Implementation | Latency |
|---|---|
| FluidAudio / Parakeet CoreML (native) | ~0.19s |
| mlx-whisper | ~1.02s |
| whisper.cpp + CoreML | ~1.23s |
| WhisperKit (full large) | ~2.22s |

Python overhead adds ~100–200ms vs native Swift. Expected range from Python via
whisperkittools: **200–500ms** for distil/turbo models on M1/M2/M3 — 2–5x over mlx-whisper.

---

## 5. Key Risks / Gotchas

| Risk | Detail |
|---|---|
| First-run ANE compilation | 4+ min on first model load (CoreML compiles to device-specific code). Must trigger during `warm_up()` at startup, not at first keypress. |
| numpy<2 required | coremltools does not support numpy 2.x. Pin `numpy<2` in pyproject.toml. |
| torch dependency | whisperkittools expects `torch~=2.1.x` for stable conversion workflows. |
| Encoder on ANE, decoder on GPU | Most ops dispatch correctly; some quantized models may route decoder to CPU. Set `compute_units=CPU_AND_NE` for encoder. |
| No Linux inference | `coremltools.MLModel.predict()` macOS only — acceptable for this project. |
| wisperkittools is a wrapper, not official | argmaxinc repo is actively maintained but not an Apple product. |

---

## Recommended Approach for Phase 12

1. `uv add whisperkittools` (optional extra: `--extra coreml`)
2. Pre-download + compile model in `warm_up()` using `WhisperKit(...).precompile()`
3. Cache compiled model path for subsequent calls
4. Target model: `distil-whisper_distil-large-v3_turbo_600MB` (~600MB, matches current default)
5. Pin `numpy<2` in pyproject.toml

Sources:
- https://pypi.org/project/coremltools/
- https://github.com/argmaxinc/whisperkittools
- https://huggingface.co/argmaxinc/whisperkit-coreml
- https://apple.github.io/coremltools/docs-guides/source/installing-coremltools.html
- https://github.com/anvanvan/mac-whisper-speedtest
