# Research: pywhispercpp (whisper.cpp Python bindings)

## Summary

**Verdict: NOT VIABLE for the speed goal.**

Pre-built arm64 wheels exist (Metal GPU enabled). However the PyPI wheel does NOT include
CoreML/ANE — that requires building from source with `WHISPER_COREML=1`, which violates
the zero-compilation constraint. Metal-only performance is similar to or slower than
mlx-whisper, providing no speed improvement.

---

## 1. Pre-built arm64 Wheels

- `pywhispercpp 1.4.1` ships arm64 wheels for Python 3.9–3.14 built on `macos-14` runner.
- `pip install pywhispercpp` works on macOS arm64 without Xcode/cmake.
- Metal GPU is enabled by default (`GGML_METAL_DEFAULT=ON` in the CI build).
- **CoreML/ANE is NOT included** — requires `WHISPER_COREML=1 pip install git+...` from source.

---

## 2. Model Format

- GGML `.bin` format (distinct from GGUF used by llama.cpp)
- Repo: `ggerganov/whisper.cpp` on HuggingFace
- Auto-downloads by name on first use; or pass local file path

Key model sizes:
| Model | Size |
|---|---|
| `large-v3` | 3.1 GB |
| `large-v3-turbo` | 1.62 GB |
| `large-v3-turbo-q5_0` | 574 MB |

---

## 3. Python Inference API

```python
from pywhispercpp.model import Model
import numpy as np

model = Model('large-v3-turbo', n_threads=4)
# Accepts float32 numpy array at 16kHz OR file path
segments = model.transcribe(audio_data)
for seg in segments:
    print(seg.text)
```

Return type: `List[Segment]` with `.t0`, `.t1`, `.text`, `.probability`.

---

## 4. Latency (PyPI wheel — Metal GPU, no ANE)

| Implementation | Latency |
|---|---|
| mlx-whisper | ~1.02s |
| whisper.cpp + CoreML (from source) | ~1.23s |
| pywhispercpp PyPI (Metal only) | ~1.5–2s (estimated, slower than CoreML build) |

Metal-only is likely slower than, or equal to, mlx-whisper for 30s audio.
Quantized models (q5_0) may be slower on Metal due to whisper.cpp issue #2241.

---

## 5. Key Risks / Gotchas

| Risk | Detail |
|---|---|
| No CoreML/ANE in PyPI wheel | CoreML build requires Xcode CLT + cmake — violates zero-compilation constraint |
| Metal ≠ ANE | Metal uses GPU cores; ANE requires CoreML path |
| Performance | PyPI wheel likely no faster than mlx-whisper; CoreML path not available without compilation |
| GGML model management | Separate model format from HuggingFace mlx models; parallel download ecosystem |

---

## Conclusion

pywhispercpp PyPI wheel is a dead end for speed improvement. ANE path requires compilation.
Skip this option.

Sources:
- https://pypi.org/project/pywhispercpp/
- https://github.com/absadiki/pywhispercpp
- https://huggingface.co/ggerganov/whisper.cpp
- https://github.com/anvanvan/mac-whisper-speedtest
