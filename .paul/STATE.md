# Project State

## Project Reference

See: .paul/PROJECT.md (updated 2026-04-27 after Phase 2)

**Core value:** Mac users can transcribe speech to text instantly with a single keypress, using free local models, with zero network dependency.
**Current focus:** v0.1 MVP — Phase 3: Visual Overlay

## Current Position

Milestone: v0.1 MVP
Phase: 4 of 4 (Distribution) — Ready to plan
Plan: not started
Status: Ready for Phase 4 planning
Last activity: 2026-04-27 — Phase 3 complete, overlay verified working

Progress:
- Milestone: [███████░░░] 75%
- Phase 4: [░░░░░░░░░░] 0%

## Loop Position

Current loop state:
```
PLAN ──▶ APPLY ──▶ UNIFY
  ✓        ✓        ✓     [Phase 3 complete — ready for Phase 4 PLAN]
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

### Deferred Issues
| Issue | Origin | Effort | Revisit |
|-------|--------|--------|---------|
| Accessibility permission onboarding is manual | Phase 2 | S | Phase 4 first-run setup |
| No error recovery if record thread crashes mid-session | Phase 2 | S | Post-MVP polish |

### Blockers/Concerns
| Concern | Detail |
|---------|--------|
| Leaked semaphore warning on exit | multiprocessing/resource_tracker warning — likely pynput or sounddevice cleanup. Non-blocking. Deferred to Phase 4. |

## Session Continuity

Last session: 2026-04-27
Stopped at: Phase 3 complete — all 4 phases verified, overlay pill working
Next action: /paul:plan for Phase 4 (Distribution)
Resume file: .paul/ROADMAP.md

---
*STATE.md — Updated after every significant action*
