# Project State

## Project Reference

See: .paul/PROJECT.md (updated 2026-04-27 after Phase 2)

**Core value:** Mac users can transcribe speech to text instantly with a single keypress, using free local models, with zero network dependency.
**Current focus:** v0.1 MVP — COMPLETE

## Current Position

Milestone: v0.1 MVP — ✅ COMPLETE
Phase: 4 of 4 (Distribution) — Complete
Plan: 04-01 — Complete
Status: Milestone complete — all 4 phases shipped
Last activity: 2026-04-27 — Phase 4 complete, v0.1.0 MVP shipped

Progress:
- Milestone: [██████████] 100%
- Phase 4: [██████████] 100%

## Loop Position

Current loop state:
```
PLAN ──▶ APPLY ──▶ UNIFY
  ✓        ✓        ✓     [Milestone complete]
```

## Accumulated Context

### Decisions
| Decision | Phase | Impact |
|----------|-------|--------|
| mlx-whisper + whisper-large-v3-turbo | Phase 1 | Apple Silicon native ASR, ~1-3s latency |
| sounddevice + record_until_event() | Phase 1/2 | Event-based stop, no disk I/O |
| Hold-to-record (not toggle) | Phase 2 | Phase 3 overlay hooks same press/release events |
| osascript for paste | Phase 2 | Works across all apps, no extra permission |
| PyObjC NSPanel for overlay | Phase 3 | Native frosted-glass, no dock icon |
| orderFrontRegardless() + setHidesOnDeactivate_(False) | Phase 3 | Required for NSApplicationActivationPolicyAccessory apps |
| Lazy panel build in _fade_in | Phase 3 | NSScreen.mainScreen() unreliable before app.run() |
| setup.sh + justfile (not Makefile) | Phase 4 | setup.sh for one-shot git-clone install, justfile for day-to-day ops |
| AXIsProcessTrusted() via ctypes | Phase 4 | No new deps; exits cleanly before pynput init if permission missing |
| No KeepAlive in launchd plist | Phase 4 | Prevents restart loop when Accessibility not yet granted |

### Deferred Issues
| Issue | Origin | Effort | Revisit |
|-------|--------|--------|---------|
| Accessibility permission onboarding is manual | Phase 2 | S | Phase 4 first-run setup |
| No error recovery if record thread crashes mid-session | Phase 2 | S | Post-MVP polish |

### Blockers/Concerns
| Concern | Detail |
|---------|--------|
| Leaked semaphore warning on exit | Suppressed via PYTHONWARNINGS in launchd plist. Still visible in --run foreground mode. Non-blocking. |

## Session Continuity

Last session: 2026-04-27
Stopped at: v0.1 MVP complete — all 4 phases shipped and verified
Next action: Start v0.2 milestone (/paul:plan) or pause
Resume file: .paul/ROADMAP.md

---
*STATE.md — Updated after every significant action*
