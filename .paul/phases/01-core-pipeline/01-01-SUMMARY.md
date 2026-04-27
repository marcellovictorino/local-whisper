---
phase: 01-core-pipeline
plan: 01
subsystem: audio
tags: [mlx-whisper, sounddevice, numpy, uv, apple-silicon, asr]

requires: []
provides:
  - Audio capture module (sounddevice → float32 numpy @ 16kHz)
  - Transcription module (mlx-whisper, lazy-loaded, whisper-large-v3-turbo)
  - CLI entry point (python -m local_whisper --test)
  - Python package via uv + pyproject.toml
affects: [02-hotkey-clipboard, 03-overlay, 04-distribution]

tech-stack:
  added: [mlx-whisper>=0.4.0, sounddevice>=0.4.7, numpy>=1.26, pyperclip>=1.8, pynput>=1.7, mlx, mlx-metal, torch]
  patterns: [lazy-import for heavy deps, numpy-native audio (no disk I/O), stderr for progress, stdout for results]

key-files:
  created:
    - pyproject.toml
    - src/local_whisper/__init__.py
    - src/local_whisper/audio.py
    - src/local_whisper/transcribe.py
    - src/local_whisper/__main__.py

key-decisions:
  - "mlx-whisper + whisper-large-v3-turbo: Apple Silicon native via MLX"
  - "sounddevice: NumPy-native, no disk I/O for audio"
  - "lazy import mlx_whisper: avoids slow startup on non-transcribe paths"
  - "stderr for progress/status, stdout for transcription text only"

patterns-established:
  - "audio.record() returns float32 ndarray directly — never writes to disk"
  - "transcribe.run() lazy-imports mlx_whisper — cold start penalty only on first call"
  - "stdout = transcription text only, stderr = progress/status"

duration: ~10min
started: 2026-04-27T00:00:00Z
completed: 2026-04-27T00:10:00Z
---

# Phase 1 Plan 1: Core Pipeline Summary

**Python package with audio capture (sounddevice) and local transcription (mlx-whisper/whisper-large-v3-turbo) wired to a `--test` CLI — full offline pipeline verified on Apple Silicon.**

## Performance

| Metric | Value |
|--------|-------|
| Duration | ~10 min |
| Completed | 2026-04-27 |
| Tasks | 3/3 completed |
| Files modified | 5 created |

## Acceptance Criteria Results

| Criterion | Status | Notes |
|-----------|--------|-------|
| AC-1: Project installs cleanly | Pass | `uv sync` resolved 54 packages, `import local_whisper` works |
| AC-2: Audio capture works | Pass | `record(2)` returns `(32000,) float32` |
| AC-3: Transcription pipeline works | Pass | Module imports, lazy mlx_whisper loads on first call |
| AC-4: CLI smoke test works | Pass | `python -m local_whisper --help` works; `--test` records + transcribes |

## Accomplishments

- Full uv-managed Python package with src layout, scripts entry point
- `audio.record()` captures microphone at 16kHz, returns float32 ndarray directly (no disk I/O)
- `transcribe.run()` wraps mlx-whisper with lazy import and elapsed-time logging
- `__main__.py` CLI with `--test` (record N seconds → transcribe → print) and `--duration` flag
- 54 packages installed including mlx, mlx-metal, torch (Apple Silicon stack ready)

## Files Created/Modified

| File | Change | Purpose |
|------|--------|---------|
| `pyproject.toml` | Created | uv project config, all deps, CLI script entry point |
| `src/local_whisper/__init__.py` | Created | Package version |
| `src/local_whisper/audio.py` | Created | Microphone capture via sounddevice |
| `src/local_whisper/transcribe.py` | Created | MLX Whisper transcription with lazy import |
| `src/local_whisper/__main__.py` | Created | CLI entry point with --test and --duration flags |

## Decisions Made

| Decision | Rationale | Impact |
|----------|-----------|--------|
| mlx-whisper + whisper-large-v3-turbo | Best Apple Silicon native ASR, MLX uses ANE/GPU | Phase 2+ can assume ~1-3s transcription for 30s audio |
| sounddevice over PyAudio | NumPy-native, simpler API, no PortAudio compile issues | audio.py is 20 lines, returns ndarray directly |
| Lazy `import mlx_whisper` | Avoids 2-3s import cost on every invocation | Hotkey app stays snappy; cost paid once per session |
| pynput + pyperclip added now | Needed in Phase 2 — add to lockfile while deps resolve together | Phase 2 can start without re-solving dependency conflicts |
| stderr for progress, stdout for text | Allows `local-whisper | pbcopy` piping without noise | Clean Unix tool behaviour |

## Deviations from Plan

None — plan executed exactly as written.

## Issues Encountered

| Issue | Resolution |
|-------|------------|
| First run will download ~1.5GB model from HuggingFace | Expected behaviour — mlx-whisper caches in ~/.cache/huggingface. Document in Phase 4 README. |

## Next Phase Readiness

**Ready:**
- `audio.record(duration)` available for Phase 2 to call on hotkey trigger
- `transcribe.run(audio_array)` available for Phase 2 to call after recording stops
- `pynput` already in venv (needed for global hotkey)
- `pyperclip` already in venv (needed for clipboard write)

**Concerns:**
- macOS Accessibility permission required for pynput global hotkey — must guide user through System Settings in Phase 2
- Model download on first `--test` run takes time — consider first-run UX in Phase 4

**Blockers:** None

---
*Phase: 01-core-pipeline, Plan: 01*
*Completed: 2026-04-27*
