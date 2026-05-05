# Project State

## Project Reference

See: .paul/PROJECT.md (updated 2026-05-04 after Phase 12)

**Core value:** Mac users can transcribe speech to text instantly with a single keypress, using free local models, with zero network dependency.
**Current focus:** v0.6 Speed — complete. Next milestone TBD.

## Current Position

Milestone: v0.6 Speed — ✅ Complete
Phase: 12 (CoreML Backend / Parakeet Caching) — ✅ Complete
Plan: 12-01 — UNIFY complete
Status: Milestone complete
Last activity: 2026-05-04 — Phase 12 UNIFY complete; v0.6 Speed milestone done

Progress:
- v0.5 Model Selection: [██████████] 100% (complete)
- v0.6 Speed: [██████████] 100% (complete)

## Loop Position

Current loop state:
```
PLAN ──▶ APPLY ──▶ UNIFY
  ✓        ✓        ✓     [Loop closed — milestone complete]
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
| Default model → distil-whisper-large-v3 | Phase 10 | ~2× faster than turbo, ~600 MB; turbo still available via config |
| get_model() reads config once at startup | Phase 10 | Model flows: config.toml → get_model() → warm_up() + App._model → run() |
| KnownModel StrEnum + _BACKEND_MAP for backend dispatch | Phase 11 | Single source of truth; backend inferred from model ID; unknown IDs → mlx-whisper |
| parakeet-mlx transcribe() requires file path + ffmpeg | Phase 11 | API discovery: writes numpy to temp WAV via soundfile, then cleans up |
| parakeet-mlx as optional extra (--extra parakeet) | Phase 11 | Never required; graceful ImportError fallback to mlx-whisper |
| Phase 12 pivot: parakeet caching over CoreML | Phase 12 | whisperkittools not on PyPI; coremltools too low-level; pivot to module-level parakeet instance cache in transcribe.py |
| _parakeet_cache module-level dict in transcribe.py | Phase 12 | warm_up() pre-loads model once; _run_parakeet() uses cache — eliminates 5s reload per keypress |
| CoreML/ANE Python backend deferred | Phase 12 | No pip-installable Python CoreML Whisper package exists as of 2026-05-04 |

### Deferred Issues
| Issue | Origin | Effort | Revisit |
|-------|--------|--------|---------|
| Accessibility permission onboarding is manual | Phase 2 | S | Future polish |
| No error recovery if record thread crashes mid-session | Phase 2 | S | Future polish |
| Filler list not user-configurable | Phase 8 | S | v0.7+ |
| LLM-based cleanup (higher quality, ~1s overhead) | Phase 8 | M | v0.7+ |
| auto_adapt uses same COMMAND_MODEL env var as command mode | Phase 9 | S | v0.7+ |
| CoreML/ANE Python inference: no pip-installable package exists | Phase 12 | L | Revisit when argmaxinc publishes proper PyPI package |

### Blockers/Concerns
| Concern | Detail |
|---------|--------|
| Leaked semaphore warning on exit | Suppressed via PYTHONWARNINGS in launchd plist. Still visible in --run foreground mode. Non-blocking. |

## Session Continuity

Last session: 2026-05-04
Stopped at: v0.6 Speed milestone complete (Phase 12 UNIFY done)
Next action: Define next milestone (v0.7) or start ad-hoc work
Resume file: .paul/ROADMAP.md

---
*STATE.md — Updated after every significant action*
