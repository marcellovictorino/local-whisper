# Project State

## Project Reference

See: .paul/PROJECT.md (updated 2026-04-28 after Phase 8)

**Core value:** Mac users can transcribe speech to text instantly with a single keypress, using free local models, with zero network dependency.
**Current focus:** v0.3 Polish — COMPLETE

## Current Position

Milestone: v0.3 Polish — ✅ COMPLETE
Phase: 8 of 8 (Auto-Cleanup) — Complete
Plan: 08-01 — Complete
Status: Milestone complete — v0.3.0 shipped
Last activity: 2026-04-28 — Phase 8 complete, v0.3.0 shipped

Progress:
- Milestone: [██████████] 100%
- Phase 8: [██████████] 100%

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
| setup.sh + justfile (not Makefile) | Phase 4 | setup.sh for one-shot git-clone install, justfile for day-to-day ops |
| Single config.toml for snippets + corrections | Phase 5/6 | ~/.config/local-whisper/config.toml with [snippets] and [corrections] sections |
| Env vars for command mode API config | Phase 7 | API keys unsuitable for config files; LOCAL_WHISPER_OPENAI_API_KEY, LOCAL_WHISPER_OPENAI_BASE_URL, LOCAL_WHISPER_COMMAND_MODEL |
| Right ⌘ auto-detects mode via NSPasteboard.changeCount | Phase 7 | Selection → command mode (⚡); no selection → dictation (⏺) |
| auto_cleanup config read per call (no App state) | Phase 8 | Consistent with snippets; changes take effect immediately |
| Conservative filler set: um/uh/er/ah/hmm/you know | Phase 8 | Avoids false positives on "like"/"so"/"right" |

### Deferred Issues
| Issue | Origin | Effort | Revisit |
|-------|--------|--------|---------|
| Accessibility permission onboarding is manual | Phase 2 | S | Future polish |
| No error recovery if record thread crashes mid-session | Phase 2 | S | Future polish |
| Filler list not user-configurable | Phase 8 | S | v0.4+ |
| LLM-based cleanup (higher quality, ~1s overhead) | Phase 8 | M | v0.4+ |

### Blockers/Concerns
| Concern | Detail |
|---------|--------|
| Leaked semaphore warning on exit | Suppressed via PYTHONWARNINGS in launchd plist. Still visible in --run foreground mode. Non-blocking. |

## Session Continuity

Last session: 2026-04-28
Stopped at: v0.3 Polish complete — all phases shipped and verified
Next action: Start v0.4 milestone (/paul:discuss or /paul:plan) or pause
Resume file: .paul/ROADMAP.md

---
*STATE.md — Updated after every significant action*
