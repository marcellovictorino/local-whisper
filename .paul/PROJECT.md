# local-whisper

## What This Is

A macOS application that transcribes speech to text locally and offline, triggered by a keyboard shortcut. Leverages free models such as Nvidia Parakeet running on Apple Silicon (M-family chips). Shows a visual overlay while recording, then places transcribed text on the clipboard and pastes it at the current cursor position — no cloud, no subscription.

## Core Value

Mac users can transcribe speech to text instantly with a single keypress, using free local models, with zero network dependency.

## Current State

| Attribute | Value |
|-----------|-------|
| Version | 0.1.0-dev |
| Status | Prototype |
| Last Updated | 2026-04-27 |

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

### Active (In Progress)

- [ ] Visual recording indicator overlay — Phase 3

### Planned (Next)

**Phase 3 (Overlay UI):**
- [ ] Small visual overlay/bubble indicating recording in progress
- [ ] Auto-dismiss on transcription complete

**Phase 4 (Distribution):**
- [ ] macOS app packaging (.app or launchd service)
- [ ] First-run setup (permissions guide, model download)

**v0.2 Enhancements (future):**
- [ ] Snippet expansion — spoken keywords map to predefined text (e.g. "calendly link" → URL)
- [ ] Personal dictionary — learns corrections to avoid repeating manual fixes
- [ ] Command mode — apply spoken prompt over currently selected text

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
| Overlay UI | TBD (Phase 3) | tkinter / rumps / PyObjC |
| Clipboard | pyperclip + osascript | Write + paste at cursor |

---
*PROJECT.md — Updated when requirements or context change*
*Last updated: 2026-04-27 after Phase 2 (Hotkey + Clipboard)*
