---
phase: 08-auto-cleanup
plan: 01
subsystem: transcription
tags: [auto_cleanup, filler-words, post-processing, config, python]

requires:
  - phase: 07-command-mode
    provides: established pipeline (transcribe → corrections → snippets → paste)

provides:
  - auto_cleanup module with filler removal + repetition collapse
  - config opt-out via [auto_cleanup] enabled = false
  - pipeline integration: transcribe → auto_cleanup → corrections → snippets → paste

affects: future LLM-cleanup phase (baseline rule-based approach established)

tech-stack:
  added: []
  patterns: [read-config-per-call (no state in App), fail-open on config error]

key-files:
  created: [src/local_whisper/auto_cleanup.py, tests/test_auto_cleanup.py]
  modified: [src/local_whisper/app.py]

key-decisions:
  - "Config read per call (no App state) — consistent with snippets pattern"
  - "Filler set conservative: um/uh/er/ah/hmm/you know only — avoids false removals"
  - "Command mode excluded — voice instructions must reach LLM verbatim"

patterns-established:
  - "_is_enabled(path) + apply(text, path) — testable config-gated module pattern"

duration: ~15min
started: 2026-04-28T00:00:00Z
completed: 2026-04-28T00:15:00Z
---

# Phase 8 Plan 01: Auto-Cleanup Summary

**Rule-based filler removal + immediate repetition collapse wired into dictation pipeline, always-on by default with config opt-out.**

## Performance

| Metric | Value |
|--------|-------|
| Duration | ~15 min |
| Tasks | 2 of 2 |
| Files created | 2 |
| Files modified | 1 |
| Tests added | 17 |
| Full suite | 73/73 passing |

## Acceptance Criteria Results

| Criterion | Status | Notes |
|-----------|--------|-------|
| AC-1: Filler words removed | Pass | um/uh/er/ah/hmm/you know stripped, spaces collapsed |
| AC-2: Immediate repetitions collapsed | Pass | `I I need` → `I need`; non-adjacent preserved |
| AC-3: Config opt-out disables cleanup | Pass | `[auto_cleanup] enabled = false` → passthrough |
| AC-4: Enabled by default with no config | Pass | Missing file/section → cleanup runs |
| AC-5: Command mode not affected | Pass | `auto_cleanup.apply()` only in `_record_and_process` |

## Accomplishments

- `auto_cleanup.py` — 60 lines, zero new deps, regex-based filler strip + repetition collapse
- Wired after `transcribe.run()`, before `corrections.apply()` in dictation path only
- 17 targeted tests covering edge cases (triple repetition, non-adjacent, empty string, disabled)

## Files Created/Modified

| File | Change | Purpose |
|------|--------|---------|
| `src/local_whisper/auto_cleanup.py` | Created | `_is_enabled()` + `apply()` functions |
| `src/local_whisper/app.py` | Modified | Import + `auto_cleanup.apply(text)` in `_record_and_process` |
| `tests/test_auto_cleanup.py` | Created | 17 unit tests |

## Decisions Made

| Decision | Rationale | Impact |
|----------|-----------|--------|
| Config read per call (no App state) | Consistent with snippets; no SIGHUP needed | Config changes take effect immediately |
| Conservative filler set (6 items) | Avoid false positives on "like", "so", "right" | Safer UX; LLM cleanup phase can expand later |
| Command mode excluded | Voice instructions reach LLM verbatim | AC-5 satisfied; no unintended prompt mangling |

## Deviations from Plan

None. Plan executed exactly as written.

## Issues Encountered

None.

## Next Phase Readiness

**Ready:**
- Dictation output is now clean by default
- Opt-out pattern established for future optional features
- Full test suite green — no regressions

**Concerns:**
- Filler list is hardcoded; user customization deferred to future phase
- LLM-based cleanup (higher quality) is the natural next step for v0.3+

**Blockers:** None

---
*Phase: 08-auto-cleanup, Plan: 01*
*Completed: 2026-04-28*
