# Project State

## Project Reference

See: .paul/PROJECT.md (updated 2026-04-27 after Phase 2)

**Core value:** Mac users can transcribe speech to text instantly with a single keypress, using free local models, with zero network dependency.
**Current focus:** v0.1 MVP — Phase 3: Visual Overlay

## Current Position

Milestone: v0.1 MVP
Phase: 3 of 4 (Visual Overlay) — Ready to plan
Plan: Not started
Status: Ready to plan
Last activity: 2026-04-27 — Phase 2 complete, transitioned to Phase 3

Progress:
- Milestone: [████░░░░░░] 50%
- Phase 3: [░░░░░░░░░░] 0%

## Loop Position

Current loop state:
```
PLAN ──▶ APPLY ──▶ UNIFY
  ✓        ✓        ✓     [Loop complete - ready for next PLAN]
```

## Accumulated Context

### Decisions
| Decision | Phase | Impact |
|----------|-------|--------|
| mlx-whisper + whisper-large-v3-turbo | Phase 1 | Apple Silicon native ASR, ~1-3s latency |
| sounddevice + record_until_event() | Phase 1/2 | Event-based stop, no disk I/O |
| Hold-to-record (not toggle) | Phase 2 | Phase 3 overlay hooks same press/release events |
| osascript for paste | Phase 2 | Works across all apps, no extra permission |
| threading.Event stop signal | Phase 2 | Pattern reusable for Phase 3 overlay visibility |

### Deferred Issues
| Issue | Origin | Effort | Revisit |
|-------|--------|--------|---------|
| Accessibility permission onboarding is manual | Phase 2 | S | Phase 4 first-run setup |
| No error recovery if record thread crashes mid-session | Phase 2 | S | Post-MVP polish |

### Blockers/Concerns
None.

## Session Continuity

Last session: 2026-04-27
Stopped at: Phase 2 complete — full hotkey→transcribe→paste flow verified
Next action: /paul:plan for Phase 3 (Visual Overlay)
Resume file: .paul/ROADMAP.md

---
*STATE.md — Updated after every significant action*
