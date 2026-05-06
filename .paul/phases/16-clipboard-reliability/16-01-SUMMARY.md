---
phase: 16-clipboard-reliability
plan: 01
subsystem: clipboard
tags: [clipboard, paste, retry, osascript, reliability]

requires:
  - phase: 15-config-deepening
    provides: stable config accessor pattern (no clipboard dependency, but v0.8 sequencing)

provides:
  - write_and_paste(text, *, settle_ms=0, retries=0) explicit paste contract
  - Retry loop with inter-retry 100ms sleep
  - Pre-paste settle delay (ms resolution)
  - 3 new tests covering retry + settle policy

affects: [phase-17, phase-18, app.py callers]

tech-stack:
  added: []
  patterns: [explicit contract pattern — timing/retry policy in signature, not hidden in implementation]

key-files:
  created: []
  modified:
    - src/local_whisper/clipboard.py
    - tests/test_clipboard.py
    - tests/test_command.py

key-decisions:
  - "settle_ms fires before first attempt only — not between retries"
  - "inter-retry delay hardcoded at 100ms — not a param (YAGNI)"
  - "defaults 0/0 keep all existing call sites unchanged"

patterns-established:
  - "Reliability policy expressed at module interface via keyword-only params"

duration: ~5min
started: 2026-05-06T00:00:00Z
completed: 2026-05-06T00:00:00Z
---

# Phase 16 Plan 01: Clipboard Reliability Policy Summary

**`write_and_paste` gains explicit `settle_ms` and `retries` contract; retry loop + settle delay implemented; 3 new tests; 151 total pass.**

## Performance

| Metric | Value |
|--------|-------|
| Duration | ~5 min |
| Tasks | 2 completed |
| Files modified | 3 |
| Tests added | 3 |
| Total test suite | 151 passed |

## Acceptance Criteria Results

| Criterion | Status | Notes |
|-----------|--------|-------|
| AC-1: Backward compatible defaults | Pass | No call site changes needed; defaults 0/0 |
| AC-2: settle_ms pre-paste delay | Pass | `time.sleep(settle_ms / 1000)` before first attempt |
| AC-3: Retry success path | Pass | osascript called N times until success, no warning |
| AC-4: Retry exhausted fallback | Pass | Warning logs attempt count; clipboard preserved |
| AC-5: Full suite passes | Pass | 151/151 passed |

## Accomplishments

- `write_and_paste(text, *, settle_ms=0, retries=0)` — explicit contract at module interface
- Retry loop: `for attempt in range(1 + retries)` — returns on first success, inter-retry 100ms sleep
- Settle delay fires before first attempt (app focus settling after mode switch)
- Stale `test_command.py` assertion (`"gpt-4o-mini"`) fixed as part of full-suite verification

## Files Modified

| File | Change | Purpose |
|------|--------|---------|
| `src/local_whisper/clipboard.py` | Modified | Added `import time`, `settle_ms`/`retries` params, retry loop |
| `tests/test_clipboard.py` | Modified | +`import pytest`; +3 tests (5 total) |
| `tests/test_command.py` | Modified | Model assertion updated `"gpt-4o-mini"` → `"gpt-5-nano"` |

## Decisions Made

| Decision | Rationale | Impact |
|----------|-----------|--------|
| `settle_ms` fires before first attempt only | Settle is about app focus, not inter-retry | Simpler; retries don't need settle |
| Inter-retry sleep hardcoded at 100ms | No evidence of needing configurability (YAGNI) | One fewer param |
| Defaults `0, 0` | All existing `write_and_paste("text")` call sites unchanged | Zero migration cost |

## Deviations from Plan

### Auto-fixed Issues

**1. Stale model assertion in test_command.py**
- **Found during:** Task 2 full-suite run
- **Issue:** `test_apply_command_calls_api_and_returns_text` asserted `model == "gpt-4o-mini"` — stale since default changed to `gpt-5-nano`
- **Fix:** Updated assertion to `"gpt-5-nano"`
- **Files:** `tests/test_command.py:147`
- **Verification:** 151/151 pass

## Issues Encountered

None.

## Next Phase Readiness

**Ready:**
- Clipboard module has stable, explicit contract — Phase 17/18 can call `write_and_paste` with settle/retry if needed
- 151 tests passing cleanly

**Concerns:**
- None

**Blockers:**
- None — Phase 17 (LLM Module Interface) ready to plan

---
*Phase: 16-clipboard-reliability, Plan: 01*
*Completed: 2026-05-06*
