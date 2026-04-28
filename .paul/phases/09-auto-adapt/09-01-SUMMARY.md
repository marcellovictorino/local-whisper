---
phase: 09-auto-adapt
plan: 01
subsystem: transcription
tags: [auto_adapt, app-detection, llm, openai, nsworkspace, config, python]

requires:
  - phase: 07-command-mode
    provides: openai client pattern + env var config (API key, base URL, model)
  - phase: 08-auto-cleanup
    provides: established pipeline (transcribe → auto_cleanup → corrections → snippets → paste)

provides:
  - auto_adapt module with NSWorkspace app detection + per-app LLM reshaping
  - built-in presets: Slack (casual/emoji) + Mail (formal email)
  - config opt-in via [auto_adapt] enabled = true + per-app sub-sections
  - pipeline integration: after auto_cleanup, before corrections + snippets
  - active app captured at press time (not process time)

affects: future LLM-pipeline phases (module-level openai import pattern established)

tech-stack:
  added: []
  patterns: [module-level try/except openai import for patchability, opt-in config gate (default false)]

key-files:
  created: [src/local_whisper/auto_adapt.py, tests/test_auto_adapt.py]
  modified: [src/local_whisper/app.py]

key-decisions:
  - "openai imported at module level (try/except) — enables patch() in tests without HAS_OPENAI flag"
  - "Opt-in default (enabled = false) — auto_adapt unlike auto_cleanup which is opt-out"
  - "App captured at _on_key_press not _record_and_process — preserves correct app even if focus changes during recording"
  - "Command mode excluded — voice instructions must reach LLM verbatim"

patterns-established:
  - "module-level openai import with try/except + `if openai is None:` guard — patchable in tests"
  - "_get_prompt(app_name, section) — config sub-section iteration then built-in fallback"

duration: ~20min
started: 2026-04-28T13:56:00Z
completed: 2026-04-28T14:16:00Z
---

# Phase 9 Plan 01: Auto-Adapt Summary

**App-aware LLM text reshaping wired into dictation pipeline — detects frontmost macOS app at press time, applies per-app prompt via OpenAI-compatible API, opt-in via config.**

## Performance

| Metric | Value |
|--------|-------|
| Duration | ~20 min |
| Tasks | 2 of 2 |
| Files created | 2 |
| Files modified | 1 |
| Tests added | 21 |
| Full suite | 94/94 passing |

## Acceptance Criteria Results

| Criterion | Status | Notes |
|-----------|--------|-------|
| AC-1: Opt-in gate | Pass | No config / enabled=false → passthrough, no LLM call |
| AC-2: Built-in Slack preset | Pass | app="Slack" + enabled=true → LLM called with casual prompt |
| AC-3: Built-in Mail preset | Pass | app="Mail" + enabled=true → LLM called with formal email prompt |
| AC-4: Config override | Pass | [auto_adapt.X] with app + prompt → custom prompt used |
| AC-5: Unknown app passthrough | Pass | Unrecognised app → text returned unchanged |
| AC-6: Command mode excluded | Pass | auto_adapt.apply() absent from _command_record_and_process |
| AC-7: App captured at press time | Pass | get_active_app() called in _on_key_press, stored in self._active_app |
| AC-8: LLM failure → passthrough | Pass | Exception caught, original text returned, error to stderr |

## Accomplishments

- `auto_adapt.py` — 130 lines, zero new deps, NSWorkspace detection + config + LLM reshape
- Built-in Slack/Mail presets active without any config beyond `enabled = true`
- 21 targeted tests covering all 8 ACs including LLM mock path, failure modes, passthrough variants

## Files Created/Modified

| File | Change | Purpose |
|------|--------|---------|
| `src/local_whisper/auto_adapt.py` | Created | `get_active_app()` + `_get_prompt()` + `_is_enabled()` + `apply()` |
| `src/local_whisper/app.py` | Modified | Import + capture app at press time + wire `auto_adapt.apply()` in dictation path |
| `tests/test_auto_adapt.py` | Created | 21 unit tests covering opt-in, presets, config override, LLM path, failures |

## Decisions Made

| Decision | Rationale | Impact |
|----------|-----------|--------|
| openai at module level (try/except) | `patch("local_whisper.auto_adapt.openai")` requires module-level name; lazy import inside function is not patchable | Test suite can mock LLM without real API |
| Opt-in default (enabled = false) | Auto-adapt changes output significantly — user must explicitly enable | Safer UX; doesn't surprise users with unexpected reformatting |
| App captured at press time | Focus may change during recording (e.g., Spotlight opens); capturing at press gives correct target | AC-7 satisfied; matches UX intent |

## Deviations from Plan

### Summary

| Type | Count | Impact |
|------|-------|--------|
| Auto-fixed | 1 | Required for test suite |
| Scope additions | 0 | — |
| Deferred | 0 | — |

**Total impact:** Single essential fix for testability, no scope creep.

### Auto-fixed Issues

**1. Import structure — lazy openai import changed to module-level**
- **Found during:** Task 2 (tests failing with AttributeError)
- **Issue:** Plan specified lazy `import openai` inside `apply()` — not patchable via `patch("local_whisper.auto_adapt.openai")`
- **Fix:** Module-level `try: import openai except ImportError: openai = None` + `if openai is None:` guard
- **Files:** `src/local_whisper/auto_adapt.py`
- **Verification:** 4 previously failing LLM-mock tests now pass; 94/94 suite green

## Issues Encountered

| Issue | Resolution |
|-------|------------|
| `patch("local_whisper.auto_adapt.openai")` raised AttributeError | Moved openai to module-level import with try/except |

## Next Phase Readiness

**Ready:**
- Phase 9 (Auto-Adapt) fully delivered — v0.4 milestone complete
- Pipeline order: transcribe → auto_cleanup → auto_adapt → corrections → snippets
- Full test suite green at 94/94

**Concerns:**
- No user-configurable filler list (deferred from Phase 8) — still outstanding
- Auto-adapt uses same `LOCAL_WHISPER_COMMAND_MODEL` env var as command mode — shared model config may not suit all users

**Blockers:** None

---
*Phase: 09-auto-adapt, Plan: 01*
*Completed: 2026-04-28*
