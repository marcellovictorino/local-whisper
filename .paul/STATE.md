# Project State

## Project Reference

See: .paul/PROJECT.md (updated 2026-04-28 after Phase 9)

**Core value:** Mac users can transcribe speech to text instantly with a single keypress, using free local models, with zero network dependency.
**Current focus:** v0.5 Model Selection — Phase 10 planning complete

## Current Position

Milestone: v0.5 Model Selection — In progress
Phase: 10 (Model Selection) — Planning complete
Plan: 10-01 approved, ready for APPLY
Status: Plan ready — awaiting execution
Last activity: 2026-05-04 — Phases 10 (planned), 11 (planned), 12 (research-required) added

Progress:
- v0.5 Model Selection: [░░░░░░░░░░] 0% (plan approved)
- Phase 10: [██░░░░░░░░] 20% (PLAN done, APPLY pending)

## Loop Position

Current loop state:
```
PLAN ──▶ APPLY ──▶ UNIFY
  ✓        ○        ○     [Phase 10 — ready to execute]
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
| setup.sh + justfile (not Makefile) | Phase 4 | setup.sh for one-shot git-clone install, justfile for day-to-day ops |
| Single config.toml for snippets + corrections | Phase 5/6 | ~/.config/local-whisper/config.toml with [snippets] and [corrections] sections |
| Env vars for command mode API config | Phase 7 | API keys unsuitable for config files; LOCAL_WHISPER_OPENAI_API_KEY, LOCAL_WHISPER_OPENAI_BASE_URL, LOCAL_WHISPER_COMMAND_MODEL |
| Right ⌘ auto-detects mode via NSPasteboard.changeCount | Phase 7 | Selection → command mode (⚡); no selection → dictation (⏺) |
| auto_cleanup config read per call (no App state) | Phase 8 | Consistent with snippets; changes take effect immediately |
| Conservative filler set: um/uh/er/ah/hmm/you know | Phase 8 | Avoids false positives on "like"/"so"/"right" |
| auto_adapt opt-in (enabled = false default) | Phase 9 | Reshaping changes output significantly — user must explicitly enable |
| App captured at press time in _on_key_press | Phase 9 | Focus may change during recording; correct app is the one at key press |
| openai module-level import (try/except) | Phase 9 | Lazy import inside function is not patchable via unittest.mock.patch |

### Deferred Issues
| Issue | Origin | Effort | Revisit |
|-------|--------|--------|---------|
| Accessibility permission onboarding is manual | Phase 2 | S | Future polish |
| No error recovery if record thread crashes mid-session | Phase 2 | S | Future polish |
| Filler list not user-configurable | Phase 8 | S | v0.5+ |
| LLM-based cleanup (higher quality, ~1s overhead) | Phase 8 | M | v0.5+ |
| auto_adapt uses same COMMAND_MODEL env var as command mode | Phase 9 | S | v0.5+ |

### Blockers/Concerns
| Concern | Detail |
|---------|--------|
| Leaked semaphore warning on exit | Suppressed via PYTHONWARNINGS in launchd plist. Still visible in --run foreground mode. Non-blocking. |

## Session Continuity

Last session: 2026-05-04
Stopped at: Phase 10 plan approved; Phases 11 (parakeet-mlx) and 12 (CoreML, research required) planned
Next action: Run `/paul:apply .paul/phases/10-model-selection/10-01-PLAN.md`
Resume file: .paul/phases/10-model-selection/10-01-PLAN.md

---
*STATE.md — Updated after every significant action*
