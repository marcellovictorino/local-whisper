---
phase: 02-hotkey-clipboard
plan: 01
subsystem: input-output
tags: [pynput, pyperclip, osascript, hotkey, clipboard, threading, apple-silicon]

requires:
  - phase: 01-core-pipeline
    provides: audio.record_until_event(), transcribe.run()
provides:
  - HotkeyListener (Right Command hold/release, debounced)
  - clipboard.write_and_paste() (pyperclip + osascript Cmd+V)
  - App orchestrator (hotkey → record → transcribe → paste loop)
  - --run CLI flag (persistent background listener)
  - audio.record_until_event() (event-based stop, added to Phase 1 module)
  - First-run model download notice in transcribe.py
affects: [03-overlay, 04-distribution]

tech-stack:
  added: []
  patterns:
    - threading.Event for record stop signal
    - daemon threads for record+process pipeline
    - lazy import app module in __main__ (avoids pynput cost on --test)
    - osascript for system-level paste (no AXUIElement needed)

key-files:
  created:
    - src/local_whisper/hotkey.py
    - src/local_whisper/clipboard.py
    - src/local_whisper/app.py
  modified:
    - src/local_whisper/audio.py
    - src/local_whisper/__main__.py
    - src/local_whisper/transcribe.py

key-decisions:
  - "Hold-to-record (not toggle): simpler state, push-to-talk ergonomic"
  - "threading.Event for stop signal: cleaner than polling bool"
  - "osascript Cmd+V for paste: works across all apps, no AX permission needed"
  - "Fallback to copy-only if osascript fails: graceful degradation"
  - "First-run download notice in transcribe.py: check HF cache dir existence"

patterns-established:
  - "App._record_and_process runs in daemon thread — main thread stays unblocked"
  - "clipboard.py: copy() for clipboard-only, write_and_paste() for full flow"
  - "hotkey._pressed flag debounces repeated key events while held"

duration: ~15min
started: 2026-04-27T00:10:00Z
completed: 2026-04-27T00:25:00Z
---

# Phase 2 Plan 1: Hotkey + Clipboard Summary

**Right Command hold-to-record → mlx-whisper transcription → osascript paste at cursor, running as a persistent background listener via `python -m local_whisper --run`. Verified end-to-end.**

## Performance

| Metric | Value |
|--------|-------|
| Duration | ~15 min |
| Completed | 2026-04-27 |
| Tasks | 3/3 auto + 1 checkpoint approved |
| Files modified | 6 (3 created, 3 modified) |

## Acceptance Criteria Results

| Criterion | Status | Notes |
|-----------|--------|-------|
| AC-1: Hold-to-record hotkey works | Pass | Right ⌘ press/release triggers record start/stop |
| AC-2: Transcription triggers on release | Pass | record_until_event() + transcribe.run() wired in App |
| AC-3: Text lands on clipboard and pastes | Pass | pyperclip + osascript Cmd+V confirmed working |
| AC-4: App runs persistently | Pass | --run flag starts listener, Ctrl+C exits cleanly |
| AC-5: Guard against re-entry | Pass | _pressed flag debounces repeated press events |

## Accomplishments

- `hotkey.py`: pynput Right Command listener, debounced, daemon thread
- `clipboard.py`: `copy()` + `write_and_paste()` with osascript fallback
- `app.py`: `App` class orchestrates full pipeline via threading.Event stop signal
- `audio.py`: `record_until_event()` added — sounddevice InputStream callback collects chunks until event set
- `__main__.py`: `--run` flag added with lazy App import
- `transcribe.py`: first-run model download notice (checks `~/.cache/huggingface/hub/`)

## Files Created/Modified

| File | Change | Purpose |
|------|--------|---------|
| `src/local_whisper/hotkey.py` | Created | Right ⌘ hold/release listener (pynput) |
| `src/local_whisper/clipboard.py` | Created | Clipboard write + osascript paste |
| `src/local_whisper/app.py` | Created | Pipeline orchestrator |
| `src/local_whisper/audio.py` | Modified | Added record_until_event() |
| `src/local_whisper/__main__.py` | Modified | Added --run flag |
| `src/local_whisper/transcribe.py` | Modified | First-run download notice |

## Decisions Made

| Decision | Rationale | Impact |
|----------|-----------|--------|
| Hold-to-record, not toggle | Simpler state machine, push-to-talk is intuitive | Phase 3 overlay follows same press/release events |
| threading.Event stop signal | Cleaner than polling; sounddevice InputStream exits context on event.wait() return | Pattern reusable for Phase 3 overlay |
| osascript for paste | Works across all macOS apps, no AXUIElement permission required | No extra permission prompt for users |
| Fallback copy-only on osascript fail | Graceful degradation — text still reachable via Cmd+V manually | Better UX than crash |

## Deviations from Plan

### Auto-fixed Issues

**1. First-run UX — model download notice**
- **Found during:** Human verification checkpoint
- **Issue:** No feedback during initial model download (~1.5GB) — user saw blank terminal
- **Fix:** Added `_model_is_cached()` check in `transcribe.py`; prints download notice + "only happens once" message before mlx_whisper call
- **Files:** `src/local_whisper/transcribe.py`
- **Verification:** Cache path check confirmed working (returns True on already-cached machine)

## Issues Encountered

| Issue | Resolution |
|-------|------------|
| No feedback during first model download | Fixed — download notice added to transcribe.py |

## Next Phase Readiness

**Ready:**
- `App._on_key_press` / `_on_key_release` are hooks Phase 3 overlay can listen to
- `threading.Event` pattern established — overlay can reuse same signal
- Full pipeline functional and user-verified

**Concerns:**
- Accessibility permission onboarding is manual — Phase 4 should include first-run setup guide
- No error recovery if recording thread crashes mid-session (restarts on next keypress, acceptable for MVP)

**Blockers:** None

---
*Phase: 02-hotkey-clipboard, Plan: 01*
*Completed: 2026-04-27*
