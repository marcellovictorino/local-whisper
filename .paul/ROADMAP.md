# Roadmap: local-whisper

## Overview

Build a macOS speech-to-text tool running fully offline on Apple Silicon. Start with a working transcription pipeline (Phase 1), add the keyboard trigger and clipboard paste (Phase 2), then add a visual recording indicator (Phase 3). Phase 4 covers distribution and packaging for real-world use. v0.2 adds power-user features: snippets, corrections, and command mode.

## Current Milestone

**v0.5 Model Selection** (v0.5.0)
Status: 🔄 In progress
Phases: 0 of 1 complete

---

**v0.4 Auto-Adapt** (v0.4.0)
Status: ✅ Complete
Phases: 1 of 1 complete

---

**v0.3 Polish** (v0.3.0)
Status: ✅ Complete
Phases: 1 of 1 complete

---

**v0.2 Enhancements** (v0.2.0)
Status: ✅ Complete
Phases: 3 of 3 complete

---

**v0.1 MVP** (v0.1.0)
Status: ✅ Complete
Phases: 4 of 4 complete

## Phases

### v0.5 Model Selection

| Phase | Name | Plans | Status | GitHub Issue | Completed |
|-------|------|-------|--------|--------------|-----------|
| 10 | Model Selection | 1 | 🔄 Planning | - | - |

### v0.4 Auto-Adapt

| Phase | Name | Plans | Status | GitHub Issue | Completed |
|-------|------|-------|--------|--------------|-----------|
| 9 | Auto-Adapt | 1 | ✅ Complete | - | 2026-04-28 |

### v0.3 Polish

| Phase | Name | Plans | Status | GitHub Issue | Completed |
|-------|------|-------|--------|--------------|-----------|
| 8 | Auto-Cleanup | 1 | ✅ Complete | - | 2026-04-28 |

### v0.2 Enhancements

| Phase | Name | Plans | Status | GitHub Issue | Completed |
|-------|------|-------|--------|--------------|-----------|
| 5 | Snippet Expansion | 1 | ✅ Complete | #4 | 2026-04-27 |
| 6 | Personal Corrections | 1 | ✅ Complete | #2 | 2026-04-27 |
| 7 | Command Mode | 1 | ✅ Complete | #3 | 2026-04-27 |

### v0.1 MVP

| Phase | Name | Plans | Status | Completed |
|-------|------|-------|--------|-----------|
| 1 | Core Pipeline | 1/1 | ✅ Complete | 2026-04-27 |
| 2 | Hotkey + Clipboard | 1/1 | ✅ Complete | 2026-04-27 |
| 3 | Visual Overlay | 1/1 | ✅ Complete | 2026-04-27 |
| 4 | Distribution | 1/1 | ✅ Complete | 2026-04-27 |

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
- [x] 03-01: Recording indicator overlay

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

### Phase 9: Auto-Adapt

**Goal:** Detect the frontmost macOS app at key press time and automatically reshape the transcription via LLM using a per-app prompt before pasting. Opt-in via config; command mode takes full priority.
**Depends on:** Phase 7 (command mode / OpenAI client established)
**Research:** Unlikely (NSWorkspace already available via PyObjC, reuses existing LLM infra)

**Scope:**
- App detection: `NSWorkspace.sharedWorkspace().frontmostApplication().localizedName()` at press time
- Config: `[auto_adapt]` section with `enabled = false` default + per-app sub-sections (`[auto_adapt.email]`, `[auto_adapt.slack]`)
- Two built-in presets: email (formal) + Slack (casual, emojis, bullets)
- Pipeline: after `auto_cleanup`, before `corrections` + `snippets` — replaces text when rule matches
- Command mode (text selected) takes full priority — auto-adapt skipped
- Fallback: unrecognised app → passthrough
- README: latency/cost note, config examples

**Plans:**
- [ ] 09-01: auto_adapt module + config + pipeline integration + README

### Phase 8: Auto-Cleanup

**Goal:** Post-process every transcription to remove filler words and immediate repetitions before paste. Always-on by default, opt-out via config.
**Depends on:** Phase 7 (pipeline established)
**Research:** Unlikely (rule-based, no new deps)

**Scope:**
- Filler word removal (`um`, `uh`, `like`, `you know`, etc.)
- Immediate repetition collapse (`I I need` → `I need`)
- Config: `[auto_cleanup] enabled = true` in `config.toml`
- Pipeline position: transcribe → auto-cleanup → snippets → corrections → paste

**Plans:**
- [ ] 08-01: Auto-cleanup module + config integration

### Phase 10: Model Selection

**Goal:** Make `mlx-community/distil-whisper-large-v3` the default model (~2× faster than turbo at runtime, same ~1.5 GB download, <1% WER on English). Allow users to override via `[whisper] model` in config.toml. Document `mlx-community/whisper-large-v3-turbo` as the switch for multilingual support or higher accuracy.
**Depends on:** Phase 1 (transcribe module)
**Research:** Not needed (mlx-whisper already accepts any HF model ID)

**Scope:**
- Change default model to `mlx-community/distil-whisper-large-v3`
- `transcribe.get_model()` reads `[whisper] model` from config, falls back to default
- Dynamic size hint per model in first-run download message
- `App` and `__main__` resolve model once at startup, pass through to `warm_up()` and `run()`
- 4 new unit tests for `get_model()`

**Plans:**
- [ ] 10-01: get_model() + default change + App wiring + tests

---
*Roadmap created: 2026-04-27*
*Last updated: 2026-05-04 — v0.5 milestone started; Phase 10 (Model Selection) added*
