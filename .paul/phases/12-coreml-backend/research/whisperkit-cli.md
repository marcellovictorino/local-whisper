# Research: WhisperKit CLI binary via Python subprocess

## Summary

**Verdict: NOT VIABLE for dictation use case.**

`brew install whisperkit-cli` works cleanly (arm64, no Xcode). CLI interface is clean.
However, per-invocation model reload costs 1–5s per keypress — fatal for dictation. No
persistent server mode in Homebrew bottle (requires `BUILD_ALL=1` from source).

---

## 1. Distribution & Installation

```bash
brew install whisperkit-cli
```

- Version: 1.0.0 (released May 1, 2026)
- Pre-built bottles: `arm64_sonoma`, `arm64_sequoia`, `arm64_tahoe`
- Xcode required at **build time only** — not needed at runtime for end users
- macOS 13.0+ required

For `setup.sh`: one-liner install works. Adds `brew` as a dependency.

---

## 2. CLI Interface

```bash
# Transcribe a file (plain text output to stdout):
whisperkit-cli transcribe \
  --model-path ~/Documents/huggingface/models/argmaxinc/whisperkit-coreml/distil-whisper_distil-large-v3_594MB \
  --audio-path audio.wav

# Or with auto-download (first run):
whisperkit-cli transcribe \
  --model-prefix distil \
  --model distil-large-v3_594MB \
  --audio-path audio.wav
```

Key flags:
| Flag | Default | Notes |
|---|---|---|
| `--audio-path` | — | WAV, MP3, M4A, FLAC, AIFF, AAC |
| `--model-path` | — | Path to pre-downloaded CoreML model dir |
| `--model` | — | Name for auto-download |
| `--model-prefix` | `openai` | Use `distil` for distil-whisper models |
| `--verbose` | false | Do NOT set — pollutes stdout |
| `--report` | false | Writes JSON to disk if structured output needed |

Without `--verbose`: stdout is **clean plain text** — subprocess-friendly.

---

## 3. Models

Cache location: `~/Documents/huggingface/models/argmaxinc/whisperkit-coreml/`
(non-standard, differs from Python HF default `~/.cache/huggingface`)

Available distil models:
- `distil-whisper_distil-large-v3`
- `distil-whisper_distil-large-v3_594MB`
- `distil-whisper_distil-large-v3_turbo`
- `distil-whisper_distil-large-v3_turbo_600MB`

Pre-compiled CoreML `.mlmodelc` — no compilation by user needed.

---

## 4. Latency (the fatal issue)

**Per-invocation model reload:**
- Every `subprocess.run(['whisperkit-cli', ...])` starts a new process.
- CoreML model loading (`.mlmodelc` → device-specific code): **1–5 seconds** per call.
- No warm/persistent mode in Homebrew bottle (server mode requires `BUILD_ALL=1` build).

Benchmark (M4, large model):
- mlx-whisper in-process: ~1.02s
- WhisperKit CLI subprocess (full large): ~2.22s + model reload overhead

For dictation: every keypress pays 1–5s overhead before transcription starts.
This is worse than the current mlx-whisper baseline.

Mitigation exists (`argmax-cli serve --port 8080` HTTP server) but requires from-source
build with `BUILD_ALL=1` — violates zero-compilation constraint.

---

## 5. Risks

| Risk | Severity |
|---|---|
| Per-invocation model reload | **HIGH** — makes dictation unusable |
| No persistent server in Homebrew bottle | **HIGH** |
| Brew dependency for setup.sh | Medium |
| Non-standard model cache path | Low |

---

## Conclusion

WhisperKit CLI is technically sound but architecturally wrong for this use case.
In-process Python (whisperkittools) is the correct CoreML approach.

Sources:
- https://formulae.brew.sh/formula/whisperkit-cli
- https://github.com/argmaxinc/WhisperKit
- https://huggingface.co/argmaxinc/whisperkit-coreml
- https://arxiv.org/html/2507.10860v1
- https://github.com/anvanvan/mac-whisper-speedtest
