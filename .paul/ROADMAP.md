# Roadmap: local-whisper

## Overview

Build a macOS speech-to-text tool running fully offline on Apple Silicon. Start with a working transcription pipeline (Phase 1), add the keyboard trigger and clipboard paste (Phase 2), then add a visual recording indicator (Phase 3). Phase 4 covers distribution and packaging for real-world use.

## Current Milestone

**v0.1 MVP** (v0.1.0)
Status: In progress
Phases: 2 of 4 complete

## Phases

| Phase | Name | Plans | Status | Completed |
|-------|------|-------|--------|-----------|
| 1 | Core Pipeline | 1/1 | ✅ Complete | 2026-04-27 |
| 2 | Hotkey + Clipboard | 1/1 | ✅ Complete | 2026-04-27 |
| 3 | Visual Overlay | 1 | Not started | - |
| 4 | Distribution | 1 | Not started | - |

## Phase Details

### Phase 1: Core Pipeline

**Goal:** Record audio from microphone and transcribe it to text via a local model — no UI, no hotkey yet. Validate the full audio → text path works on Apple Silicon.
**Depends on:** Nothing (first phase)
**Research:** Unlikely (using mlx-whisper, established on Apple Silicon)

**Scope:**
- Python project setup (uv, pyproject.toml, src layout)
- Audio capture module (sounddevice → numpy array)
- Transcription module (mlx-whisper, lazy model load)
- CLI smoke test: `python -m local_whisper --test` records 5s → prints transcript

**Plans:**
- [ ] 01-01: Project setup, audio capture, transcription pipeline

### Phase 2: Hotkey + Clipboard

**Goal:** Trigger recording via a global keyboard shortcut (Right Command), transcribe, write result to clipboard, and paste at active cursor position.
**Depends on:** Phase 1 (transcription module)
**Research:** Unlikely (pynput for hotkey, pyperclip + AppleScript for paste)

**Scope:**
- Global hotkey listener (pynput, requires Accessibility permission)
- Toggle-mode recording (press to start, press to stop)
- Clipboard write + `osascript` paste at cursor

**Plans:**
- [ ] 02-01: Hotkey listener + clipboard paste integration

### Phase 3: Visual Overlay

**Goal:** Show a small always-on-top bubble/indicator while recording is active. Auto-dismiss when transcription completes.
**Depends on:** Phase 2 (application loop exists)
**Research:** Unlikely (tkinter or rumps for macOS menubar/overlay)

**Scope:**
- Small floating window (recording indicator)
- Show on hotkey press, hide on transcription complete
- Non-blocking — runs in separate thread

**Plans:**
- [ ] 03-01: Recording indicator overlay

### Phase 4: Distribution

**Goal:** Package as a launchable macOS app or background service users can install and run at login.
**Depends on:** Phase 3 (feature complete)
**Research:** Likely (py2app vs PyInstaller vs Swift wrapper)

**Scope:**
- Packaging as `.app` or `launchd` service
- First-run setup (permissions, model download)
- README with install instructions

**Plans:**
- [ ] 04-01: macOS distribution packaging

---
*Roadmap created: 2026-04-27*
*Last updated: 2026-04-27*
