# Project State

## Project Reference

See: .paul/PROJECT.md (updated 2026-04-27 after Phase 2)

**Core value:** Mac users can transcribe speech to text instantly with a single keypress, using free local models, with zero network dependency.
**Current focus:** v0.2 Enhancements — COMPLETE

## Current Position

Milestone: v0.3 Polish — 🔄 In progress
Phase: 8 of 8 (Animated Waveform Overlay) — In progress
Plan: 08-01 — Applying
Status: Implementation complete, awaiting verification
Last activity: 2026-04-27 — Phase 8 waveform animation implemented

Progress:
- Milestone: [░░░░░░░░░░] 0% (phase in progress)
- Phase 8: [████████░░] 80%

## Loop Position

Current loop state:
```
PLAN ──▶ APPLY ──▶ UNIFY
  ✓        ✓        ○     [Applied, needs verification]
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
| Single config.toml for snippets + corrections | Phase 5/6 | ~/.config/local-whisper/config.toml with [snippets] and [corrections] sections |
| Env vars for command mode API config | Phase 7 | API keys unsuitable for config files; LOCAL_WHISPER_OPENAI_API_KEY, LOCAL_WHISPER_OPENAI_BASE_URL, LOCAL_WHISPER_COMMAND_MODEL |
| Right ⌘ auto-detects mode via NSPasteboard.changeCount | Phase 7 → post-7 fix | Selection detected → command mode (⚡); no selection → dictation (⏺). Replaced Right ⌥ separate key to avoid hotkey conflicts. |

### Deferred Issues
| Issue | Origin | Effort | Revisit |
|-------|--------|--------|---------|
| Accessibility permission onboarding is manual | Phase 2 | S | Future polish |
| No error recovery if record thread crashes mid-session | Phase 2 | S | Future polish |

### Blockers/Concerns
| Concern | Detail |
|---------|--------|
| Leaked semaphore warning on exit | Suppressed via PYTHONWARNINGS in launchd plist. Still visible in --run foreground mode. Non-blocking. |

## Session Continuity

Last session: 2026-04-27
Stopped at: Phase 8 implementation applied — needs live testing
Next action: Test overlay animation with `just run`, verify bars animate with voice
Resume file: .paul/phases/08-animated-overlay/08-01-PLAN.md

---
*STATE.md — Updated after every significant action*
