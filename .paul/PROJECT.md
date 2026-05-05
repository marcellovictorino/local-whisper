# local-whisper

## What This Is

A macOS application that transcribes speech to text locally and offline, triggered by a keyboard shortcut. Leverages free models such as Nvidia Parakeet running on Apple Silicon (M-family chips). Shows a visual overlay while recording, then places transcribed text on the clipboard and pastes it at the current cursor position — no cloud, no subscription.

## Core Value

Mac users can transcribe speech to text instantly with a single keypress, using free local models, with zero network dependency.

## Current State

| Attribute | Value |
|-----------|-------|
| Version | 0.7.0 |
| Status | Active |
| Last Updated | 2026-05-05 |

## Requirements

### Validated (Shipped)

- [x] Python package with uv + pyproject.toml — Phase 1
- [x] Microphone audio capture at 16kHz (sounddevice → float32 numpy) — Phase 1
- [x] Local offline transcription on Apple Silicon (mlx-whisper, whisper-large-v3-turbo) — Phase 1
- [x] CLI smoke test: `python -m local_whisper --test` records and prints transcript — Phase 1
- [x] Global keyboard shortcut listener (Right Command hold-to-record, debounced) — Phase 2
- [x] Clipboard write + paste at active cursor via osascript — Phase 2
- [x] Persistent background listener: `python -m local_whisper --run` — Phase 2
- [x] First-run model download notice — Phase 2

- [x] Visual recording indicator overlay (NSPanel frosted-glass pill, top-center, no dock icon) — Phase 3
- [x] Accessibility permission check on startup with actionable error — Phase 4
- [x] launchd user agent: auto-starts on login via `bash setup.sh` — Phase 4
- [x] Model pre-download at install time (snapshot_download, ~1.5GB, once) — Phase 4
- [x] `justfile` day-to-day ops: install/uninstall/start/stop/status/run/logs — Phase 4

- [x] Auto-cleanup: filler word removal + immediate repetition collapse (opt-out via config) — Phase 8
- [x] Auto-adapt: app-aware LLM text reshaping with per-app prompts + built-in Slack/Mail presets (opt-in via config) — Phase 9

- [x] Configurable Whisper model via `[whisper] model` in config.toml — Phase 10
- [x] Default model switched to `distil-whisper-large-v3` (~2× faster, ~600 MB) — Phase 10
- [x] Benchmark module: warm-up + transcription timing, JSON output, `just benchmark` recipe — Phase 10

- [x] `KnownModel` StrEnum: single source of truth for all supported model IDs + backend assignment — Phase 11
- [x] `get_backend(model)` — pure lookup; backend auto-inferred from model ID, no second config key — Phase 11
- [x] parakeet-mlx backend wired through `run()`, `warm_up()`, `App`, `__main__`, benchmark — Phase 11
- [x] parakeet-mlx optional extra (`uv sync --extra parakeet`); graceful ImportError fallback to mlx-whisper — Phase 11
- [x] `_parakeet_cache` module-level dict: parakeet model loaded once at `warm_up()`, reused per keypress — Phase 12
- [x] `warm_up()` parakeet branch: now actually pre-loads model (eliminates ~5s from_pretrained() at first keypress) — Phase 12

- [~] SFSpeechRecognizer (PyObjC) evaluated as sub-second ASR backend — Phase 14 (benchmarked and dropped)
  - Benchmark: 57.1% WER vs 12.2% for distil-whisper; on-device Siri model quality unacceptable for dictation
  - Additional concern: macOS shows "sends voice to Apple" permission dialog regardless of `requiresOnDeviceRecognition=True`
  - Decision: reverted; distil-whisper-large-v3 remains default; no net code change from v0.6

### Planned (Next)

**v0.4+ ideas:**
- [ ] LLM-based cleanup — higher quality transcript polish (1-2s overhead, OpenAI-compatible)
- [ ] User-configurable filler list (deferred from Phase 8)

### Out of Scope
- Cloud-based transcription — must run fully offline
- Windows / Linux support (initially)

## Target Users

**Primary:** Mac users (Apple Silicon) who want fast, private, free speech-to-text
- Want keyboard-driven workflow
- Privacy-conscious (no audio sent to cloud)
- Frustrated with paid solutions like Wispr Flow

## Context

**Business Context:**
Inspired by Wispr Flow (wisprflow.ai). Aims to replicate core value for free using open-source local models.

**Technical Context:**
Apple Silicon M-family chips enable fast on-device inference. Using mlx-whisper (whisper-large-v3-turbo) — runs via MLX, uses ANE/GPU, no cloud. Global hotkey via pynput (macOS Accessibility API). Clipboard paste via pyperclip + AppleScript osascript.

## Constraints

### Technical Constraints
- Must run on macOS with Apple Silicon (M1/M2/M3/M4+)
- Model must run fully offline — no network calls for transcription
- Must paste at active cursor position across all apps

### Business Constraints
- Free and open source — no paid model APIs

## Key Decisions

| Decision | Rationale | Date | Status |
|----------|-----------|------|--------|
| Target Apple Silicon first | Best local inference performance, largest target market for this use case | 2026-04-27 | Active |
| mlx-whisper + whisper-large-v3-turbo | Free, Apple Silicon native via MLX (ANE/GPU), high accuracy | 2026-04-27 | Active |
| sounddevice for audio capture | NumPy-native, no disk I/O, simple API, no PortAudio compile issues | 2026-04-27 | Active |
| Lazy import mlx_whisper | Avoids 2-3s import cost — cold start penalty paid once per session | 2026-04-27 | Active |
| stdout=transcript, stderr=progress | Clean Unix tool behaviour, allows piping output | 2026-04-27 | Active |
| Hold-to-record (not toggle) | Simpler state, push-to-talk ergonomic, less edge cases | 2026-04-27 | Active |
| osascript for paste | Works across all apps, no AXUIElement permission needed | 2026-04-27 | Active |
| PyObjC for overlay (not tkinter) | Native macOS frosted-glass NSPanel, no dock icon, AppKit-native | 2026-04-27 | Active |
| Skip applicationDidFinishLaunching_ delegate | pynput consumes notification before delegate attaches — build panel directly in run() | 2026-04-27 | Active |
| orderFrontRegardless() + setHidesOnDeactivate_(False) | Accessory apps never become "active"; standard window show methods are no-ops | 2026-04-27 | Active |
| setup.sh + justfile (not Makefile) | setup.sh for git-clone pipe install pattern; justfile for day-to-day ops | 2026-04-27 | Active |
| AXIsProcessTrusted() via ctypes for Accessibility check | No new deps (stdlib ctypes); early exit before pynput/AppKit init | 2026-04-27 | Active |
| No KeepAlive in launchd plist | Prevents restart loop when Accessibility not yet granted to uv binary | 2026-04-27 | Active |
| auto_adapt opt-in (enabled = false default) | Reshaping changes output significantly — user must explicitly enable | 2026-04-28 | Active |
| App captured at press time (not process time) | Focus may change during recording; correct app is the one at key press | 2026-04-28 | Active |
| openai module-level import (try/except) | Lazy import inside function is not patchable via unittest.mock.patch | 2026-04-28 | Active |
| Default model → distil-whisper-large-v3 | ~2× faster than turbo at runtime, ~600 MB vs 1.5 GB, <1% WER delta on English | 2026-05-04 | Active |
| get_model() takes explicit path param | Enables direct test isolation without monkeypatching Path.home() | 2026-05-04 | Active |
| Config read once at startup, not per keypress | Model load is heavyweight; config change requires restart (consistent with expectations) | 2026-05-04 | Active |
| KnownModel StrEnum + _BACKEND_MAP for backend dispatch | Single source of truth; adding future models = one line; unknown IDs fall back to mlx-whisper | 2026-05-04 | Active |
| parakeet-mlx transcribe() takes file path, not numpy array | API spike finding: uses ffmpeg internally; _run_parakeet() writes temp WAV via soundfile | 2026-05-04 | Active |
| parakeet-mlx optional extra; never required | Users install with `uv sync --extra parakeet`; default distil-whisper path unchanged | 2026-05-04 | Active |
| _parakeet_cache module-level dict in transcribe.py | warm_up() pre-loads model once; _run_parakeet() uses cache — eliminates 5s reload per keypress | 2026-05-04 | Active |
| CoreML/ANE Python backend deferred | No pip-installable Python CoreML Whisper package exists (whisperkittools is dev-only, not PyPI) | 2026-05-04 | Deferred |
| SFSpeechRecognizer chosen for sub-second ASR | 200–700ms warm latency, zero install, ~0% WER on clear English, PyObjC already dep; whisper.cpp skipped | 2026-05-05 | Active |
| addsPunctuation=True default for SFSpeech | Natural output; +100–200ms overhead acceptable vs. unformatted transcript | 2026-05-05 | Active |
| SFSpeechURLRecognitionRequest (file path API) | Simpler than buffer API; reuses temp-WAV pattern from parakeet; no CMSampleBuffer conversion needed | 2026-05-05 | Active |
| threading.Event for SFSpeech sync (not NSRunLoop) | SFSpeech delivers callbacks on internal queue, not caller's run loop; threading.Event correct for background threads | 2026-05-05 | Active |
| SFSpeech opt-in via config, not new default | Benchmark comparison needed before promoting to default; distil-whisper-large-v3 remains default | 2026-05-05 | Active |

## Success Metrics

| Metric | Target | Current | Status |
|--------|--------|---------|--------|
| Transcription accuracy | >95% on clear speech | - | Not measured |
| Latency (keypress → paste) | <3s for 30s audio | - | Not measured |
| Works offline | 100% | - | Not tested |

## Tech Stack

| Layer | Technology | Notes |
|-------|------------|-------|
| Language | Python 3.13 | via uv, pyproject.toml |
| Package Manager | uv | Fast, modern, lockfile |
| ASR Model | distil-whisper-large-v3 (default) | ~600 MB; turbo for multilingual; parakeet for fastest English; sfspeech for sub-second |
| Inference | mlx-whisper (default) / parakeet-mlx (optional) / SFSpeechRecognizer (opt-in) | Backend auto-inferred from model ID; all backends cached at startup; SFSpeech: 200–700ms warm |
| Audio Capture | sounddevice | NumPy-native, 16kHz float32 |
| Global Hotkey | pynput | Requires macOS Accessibility permission |
| Overlay UI | PyObjC (NSPanel + NSVisualEffectView) | Frosted-glass pill, always-on-top, no dock icon |
| Clipboard | pyperclip + osascript | Write + paste at cursor |

---
*PROJECT.md — Updated when requirements or context change*
*Last updated: 2026-05-05 after Phase 14 (SFSpeech Implementation) — v0.7 complete*
