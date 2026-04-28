# local-whisper

## What This Is

A macOS application that transcribes speech to text locally and offline, triggered by a keyboard shortcut. Leverages free models such as Nvidia Parakeet running on Apple Silicon (M-family chips). Shows a visual overlay while recording, then places transcribed text on the clipboard and pastes it at the current cursor position — no cloud, no subscription.

## Core Value

Mac users can transcribe speech to text instantly with a single keypress, using free local models, with zero network dependency.

## Current State

| Attribute | Value |
|-----------|-------|
| Version | 0.3.0 |
| Status | Active |
| Last Updated | 2026-04-28 |

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

### Planned (Next)

**v0.3+ ideas:**
- [ ] LLM-based cleanup — higher quality transcript polish (1-2s overhead, OpenAI-compatible)

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
| ASR Model | whisper-large-v3-turbo | ~1.5GB, downloaded once to ~/.cache/huggingface |
| Inference | mlx-whisper | Apple Silicon native via MLX (ANE/GPU) |
| Audio Capture | sounddevice | NumPy-native, 16kHz float32 |
| Global Hotkey | pynput | Requires macOS Accessibility permission |
| Overlay UI | PyObjC (NSPanel + NSVisualEffectView) | Frosted-glass pill, always-on-top, no dock icon |
| Clipboard | pyperclip + osascript | Write + paste at cursor |

---
*PROJECT.md — Updated when requirements or context change*
*Last updated: 2026-04-28 after Phase 8 (Auto-Cleanup) — v0.3.0*
