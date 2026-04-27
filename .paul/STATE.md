# Project State

## Project Reference

See: .paul/PROJECT.md (updated 2026-04-27 after Phase 1)

**Core value:** Mac users can transcribe speech to text instantly with a single keypress, using free local models, with zero network dependency.
**Current focus:** v0.1 MVP — Phase 2: Hotkey + Clipboard

## Current Position

Milestone: v0.1 MVP
Phase: 2 of 4 (Hotkey + Clipboard) — Ready to plan
Plan: Not started
Status: Ready to plan
Last activity: 2026-04-27 — Phase 1 complete, transitioned to Phase 2

Progress:
- Milestone: [██░░░░░░░░] 25%
- Phase 2: [░░░░░░░░░░] 0%

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
| mlx-whisper + whisper-large-v3-turbo | Phase 1 | Apple Silicon native ASR, ~1-3s latency for 30s audio |
| sounddevice for audio capture | Phase 1 | NumPy-native, no disk I/O, 16kHz float32 |
| Lazy import mlx_whisper | Phase 1 | Cold start once per session, stays snappy |
| stdout=transcript, stderr=progress | Phase 1 | Clean Unix piping behaviour |
| pynput + pyperclip already in lockfile | Phase 1 | Phase 2 can start without dependency re-solve |

### Deferred Issues
| Issue | Origin | Effort | Revisit |
|-------|--------|--------|---------|
| First run downloads ~1.5GB model | Phase 1 | S | Phase 4 (first-run UX) |
| macOS Accessibility permission required for pynput | Phase 1 | S | Phase 2 (must guide user) |

### Blockers/Concerns
None.

## Session Continuity

Last session: 2026-04-27
Stopped at: Phase 1 complete — core pipeline verified, UNIFY closed
Next action: /paul:plan for Phase 2 (Hotkey + Clipboard)
Resume file: .paul/ROADMAP.md

---
*STATE.md — Updated after every significant action*
