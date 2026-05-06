---
phase: 15-config-deepening
plan: 01
subsystem: config
tags: [config, toml, typed-accessors, caching]

requires:
  - phase: refactor-607 (PR #16)
    provides: config.py with load_section() and mtime cache

provides:
  - 6 typed domain accessors in config.py
  - All 5 caller modules decoupled from TOML key names and defaults
  - 18 new accessor tests in test_config.py

affects: [auto_adapt, auto_cleanup, corrections, snippets, transcribe, phase-16, phase-17]

tech-stack:
  added: []
  patterns: [typed-accessor pattern — config.py owns all TOML key names and defaults; callers use named functions]

key-files:
  created: []
  modified:
    - src/local_whisper/config.py
    - src/local_whisper/transcribe.py
    - src/local_whisper/auto_cleanup.py
    - src/local_whisper/auto_adapt.py
    - src/local_whisper/corrections.py
    - src/local_whisper/snippets.py
    - tests/test_config.py

key-decisions:
  - "get_whisper_model() returns str | None — avoids circular import with transcribe.py; caller applies DEFAULT_MODEL fallback"
  - "get_auto_adapt_section() kept separate from is_auto_adapt_enabled() — _get_prompt() needs full section dict for sub-section iteration"
  - "Validation logic (str filtering, casefolding) stays in corrections.py and snippets.py — domain concern, not config concern"

patterns-established:
  - "config.py is the only module that knows TOML section names and key names"
  - "Callers use named accessor functions; load_section() is config-internal"

duration: ~15min
started: 2026-05-06T00:00:00Z
completed: 2026-05-06T00:00:00Z
---

# Phase 15 Plan 01: Config Module Deepening Summary

**6 typed accessors added to config.py; all 5 caller modules decoupled from raw TOML key/default knowledge; 18 new tests; 148 total pass.**

## Performance

| Metric | Value |
|--------|-------|
| Duration | ~15 min |
| Tasks | 2 completed |
| Files modified | 7 |
| Tests added | 18 |
| Total test suite | 148 passed |

## Acceptance Criteria Results

| Criterion | Status | Notes |
|-----------|--------|-------|
| AC-1: Callers own no TOML key names or defaults | Pass | grep confirms load_section only in config.py |
| AC-2: Correct defaults when config absent | Pass | 18 new tests cover absent/missing file cases |
| AC-3: Correct values when config present | Pass | 18 new tests cover present-value cases |
| AC-4: All existing tests still pass | Pass | 148/148 passed |

## Accomplishments

- `config.py` now owns all TOML section names, key names, and defaults — no caller knows them
- `get_whisper_model`, `is_auto_cleanup_enabled`, `is_auto_adapt_enabled`, `get_corrections_raw`, `get_snippets_raw`, `get_auto_adapt_section` added
- 5 caller modules updated (transcribe, auto_cleanup, auto_adapt, corrections, snippets)
- 18 new tests covering defaults, present values, absent sections, missing file for all 6 accessors

## Files Modified

| File | Change | Purpose |
|------|--------|---------|
| `src/local_whisper/config.py` | Modified | +6 typed accessor functions |
| `src/local_whisper/transcribe.py` | Modified | `get_whisper_model()` replaces raw load_section |
| `src/local_whisper/auto_cleanup.py` | Modified | `is_auto_cleanup_enabled()` replaces raw load_section |
| `src/local_whisper/auto_adapt.py` | Modified | `is_auto_adapt_enabled()` + `get_auto_adapt_section()` replace raw load_section (2 call sites) |
| `src/local_whisper/corrections.py` | Modified | `get_corrections_raw()` replaces raw load_section |
| `src/local_whisper/snippets.py` | Modified | `get_snippets_raw()` replaces raw load_section |
| `tests/test_config.py` | Modified | +18 per-accessor tests (24 total in file) |

## Decisions Made

| Decision | Rationale | Impact |
|----------|-----------|--------|
| `get_whisper_model()` returns `str \| None` | Avoids circular import (transcribe.DEFAULT_MODEL in config.py) | Caller does `config.get_whisper_model(path) or DEFAULT_MODEL` |
| Separate `is_auto_adapt_enabled` + `get_auto_adapt_section` | `_get_prompt()` needs full section dict for sub-section iteration; can't reduce to scalar | auto_adapt.py uses both; two cache hits but same mtime-cached entry |
| Validation (str filtering, casefolding) stays in caller modules | Domain concern, not config concern — corrections/snippets own their validation warnings | Callers still do post-processing on raw dict |

## Deviations from Plan

None — executed exactly as planned.

## Issues Encountered

None.

## Next Phase Readiness

**Ready:**
- config.py accessor pattern established — Phases 16/17 can extend it if needed
- All callers decoupled; adding/renaming TOML keys requires only config.py edits

**Concerns:**
- None

**Blockers:**
- None — Phase 16 (Clipboard Reliability Policy) ready to plan

---
*Phase: 15-config-deepening, Plan: 01*
*Completed: 2026-05-06*
