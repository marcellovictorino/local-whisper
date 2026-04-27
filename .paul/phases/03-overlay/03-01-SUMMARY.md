---
phase: 03-overlay
plan: 01
subsystem: ui
tags: [pyobjc, appkit, nspanel, nsvisualeffectview, macos, overlay]

requires:
  - phase: 02-hotkey-clipboard
    provides: App._on_key_press/_on_key_release hooks for show/hide triggers

provides:
  - Native macOS frosted-glass pill overlay (NSPanel + NSVisualEffectView)
  - Thread-safe queue-driven show/hide from any thread
  - RecordingOverlay class with run() owning AppKit main thread

affects: 04-distribution

tech-stack:
  added: []  # pyobjc already present as pynput dependency
  patterns:
    - Queue-drain via NSTimer (50ms poll) for AppKit thread safety
    - Lazy panel build on first show (NSScreen reliable only after app.run())
    - orderFrontRegardless() for accessory apps (never "active")
    - setHidesOnDeactivate_(False) to prevent auto-hide in background apps
    - sizeToFit() + manual centering instead of NSTextField alignment

key-files:
  created: [src/local_whisper/overlay.py]
  modified: [src/local_whisper/app.py, src/local_whisper/__main__.py]

key-decisions:
  - "PyObjC over tkinter: native macOS look, frosted glass, no dock icon"
  - "Skip applicationDidFinishLaunching_ delegate: pynput consumes it before delegate attaches"
  - "Lazy panel build: NSScreen.mainScreen() unreliable before app.run()"
  - "orderFrontRegardless() not orderFront_(): accessory apps never become active"
  - "sizeToFit() + manual x/y: NSTextField alignment unreliable for single-line labels"

patterns-established:
  - "Accessory app windows: always setHidesOnDeactivate_(False) + orderFrontRegardless()"
  - "AppKit UI from background threads: queue.Queue + NSTimer poll on main thread"

duration: ~3h (debugging)
started: 2026-04-27T10:00:00Z
completed: 2026-04-27T14:00:00Z
---

# Phase 3 Plan 01: Native macOS Recording Overlay — Summary

**NSPanel frosted-glass pill overlay at top-center of screen, shown on Right ⌘ press, hidden after paste, no dock icon, thread-safe.**

## Performance

| Metric | Value |
|--------|-------|
| Duration | ~3h |
| Started | 2026-04-27 |
| Completed | 2026-04-27 |
| Tasks | 3 auto + 1 human-verify |
| Files modified | 3 |

## Acceptance Criteria Results

| Criterion | Status | Notes |
|-----------|--------|-------|
| AC-1: Overlay appears on keypress | Pass | Frosted pill appears top-center on Right ⌘ |
| AC-2: Overlay stays visible during transcription | Pass | hide() called only in finally block after paste |
| AC-3: Overlay fades out after paste | Pass | setAlphaValue_(0.0) + orderOut_() on hide |
| AC-4: Thread safety | Pass | All AppKit calls on main thread via NSTimer queue poll |
| AC-5: Clean exit | Pass | SIGINT → app.terminate_(None) |

## Accomplishments

- NSPanel with NSVisualEffectView (HUD material, dark frosted) positioned top-center below menu bar
- Thread-safe command queue drained every 50ms by NSTimer on main thread
- No dock icon via NSApplicationActivationPolicyAccessory
- Pill shape: 80×24pt, cornerRadius=12, dark border, white "⏺ ..." label
- Label pixel-perfect centered: sizeToFit() for natural dimensions, manual x/y calculation

## Files Created/Modified

| File | Change | Purpose |
|------|--------|---------|
| `src/local_whisper/overlay.py` | Created | RecordingOverlay + _OverlayController (NSPanel, NSTimer, queue) |
| `src/local_whisper/app.py` | Modified | overlay param, start()/stop() methods, show/hide hooks |
| `src/local_whisper/__main__.py` | Modified | overlay.run() owns main thread, app.start() in daemon thread |

## Decisions Made

| Decision | Rationale | Impact |
|----------|-----------|--------|
| Skip delegate/applicationDidFinishLaunching_ | pynput initializes NSApplication early, consuming the notification before delegate attaches — delegate never fires | Build panel + timer directly in run() before app.run() |
| Lazy panel build (first show, not at startup) | NSScreen.mainScreen() returns None before app.run() starts | _build_panel() called inside _fade_in() on first "show" command |
| orderFrontRegardless() over orderFront_() | Accessory apps (NSApplicationActivationPolicyAccessory) are never "active" — orderFront_(None) is a silent no-op | Panel actually appears |
| setHidesOnDeactivate_(False) | NSPanel default hides on app deactivation; accessory apps are always "deactivated" | Panel stays visible during transcription |
| sizeToFit() + manual centering | NSTextField.setAlignment_ unreliable for single-line labels (labelWithString_ defaults to alignment=4/natural) | Pixel-perfect centered label |

## Deviations from Plan

| Type | Count | Impact |
|------|-------|--------|
| Auto-fixed | 5 | All root causes in PyObjC/AppKit accessory app behavior |
| Deferred | 1 | Sound wave animation (v0.2) |

### Auto-fixed Issues

**1. applicationDidFinishLaunching_ never fires**
- Found during: Task 1 (initial implementation)
- Issue: pynput keyboard listener initializes NSApplication (PyObjC-based), consuming the launch notification before our delegate is attached
- Fix: Removed delegate approach entirely; build panel + schedule timer directly in RecordingOverlay.run() before app.run()

**2. Ctrl+C broken**
- Found during: Task 3 testing
- Issue: app.run() blocks in C code, never yields to Python's SIGINT handler
- Fix: signal.signal(SIGINT, lambda: app.terminate_(None))

**3. Panel not visible — orderFront_ no-op**
- Found during: human-verify checkpoint
- Issue: NSApplicationActivationPolicyAccessory apps are never "active"; orderFront_(None) requires app to be active
- Fix: orderFrontRegardless()

**4. Panel auto-hides immediately**
- Found during: human-verify (visible only for instant)
- Issue: NSPanel.hidesOnDeactivate = YES by default; accessory apps always "deactivated"
- Fix: panel.setHidesOnDeactivate_(False)

**5. Label not centered**
- Found during: human-verify (text appeared right-aligned)
- Issue: NSTextField.labelWithString_() defaults alignment=4 (natural/LTR); setAlignment_(2) didn't reliably reflow single-line labels
- Fix: sizeToFit() to get natural pixel dimensions, manually compute lx/ly for center position

### Deferred Items

- v0.2: Sound wave amplitude bars — pipe RMS from record_until_event() callback float queue → CALayer bar heights in pollQueue_. Architecture: add `on_rms: Callable[[float], None]` param to record_until_event(), call overlay.update_amplitude(rms) from audio thread, drain via same NSTimer.

## Issues Encountered

| Issue | Resolution |
|-------|------------|
| Leaked semaphore warning on exit | Not yet fixed — likely pynput or sounddevice cleanup; non-blocking warning, deferred to Phase 4 |

## Next Phase Readiness

**Ready:**
- Full hotkey → record → transcribe → paste → overlay flow working end-to-end
- PyObjC patterns established for any future AppKit UI additions
- Clean thread model: daemon threads for audio/pynput, main thread for AppKit

**Concerns:**
- Leaked semaphore warning on process exit (cosmetic, non-blocking)

**Blockers:**
- None

---
*Phase: 03-overlay, Plan: 01*
*Completed: 2026-04-27*
