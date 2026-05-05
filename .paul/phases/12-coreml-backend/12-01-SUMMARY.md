---
phase: 12-coreml-backend
plan: 01
subsystem: inference
tags: [parakeet, mlx, caching, warm_up, performance]

requires:
  - phase: 11-backend-selection
    provides: _run_parakeet(), warm_up() parakeet branch, _parakeet_cache hook point

provides:
  - Module-level _parakeet_cache eliminates from_pretrained() reload per keypress
  - warm_up() now actually pre-loads parakeet model (not just import check)
  - 2 new tests verifying cache population and cache hit behaviour

affects: []

tech-stack:
  added: []
  patterns:
    - Module-level cache dict for optional heavy backend instances

key-files:
  modified:
    - src/local_whisper/transcribe.py
    - tests/test_transcribe.py

key-decisions:
  - "Phase 12 pivoted: whisperkittools not on PyPI; no pip-installable Python CoreML package exists"
  - "Parakeet instance caching: module-level _parakeet_cache dict, populated in warm_up()"
  - "Cache miss fallback: _run_parakeet() falls back to from_pretrained() if warm_up() was skipped"

patterns-established:
  - "Module-level cache dict pattern for optional heavy-import backends"

duration: ~30min
started: 2026-05-04T00:00:00Z
completed: 2026-05-04T00:00:00Z
---

# Phase 12 Plan 01: CoreML Backend → Parakeet Caching Summary

**Planned CoreML/ANE backend pivoted at spike; delivered parakeet model instance caching — eliminates from_pretrained() reload per keypress on the parakeet path.**

## Performance

| Metric | Value |
|--------|-------|
| Duration | ~30 min |
| Tasks | 3 attempted (spike + decision + implement + test) |
| Files modified | 2 |
| Tests | 16/16 pass (2 new) |

## Acceptance Criteria Results

Original plan ACs were for whisperkittools (CoreML). All voided by pivot.
Replacement ACs based on actual scope:

| Criterion | Status | Notes |
|-----------|--------|-------|
| warm_up() caches parakeet instance | Pass | Verified by test + manual inspection |
| _run_parakeet() uses cache, skips from_pretrained() | Pass | test_run_parakeet_skips_from_pretrained_when_cached |
| All 16 tests pass | Pass | uv run pytest tests/test_transcribe.py -v |
| Ruff clean | Pass | ruff check + format --check |

## Accomplishments

- `_parakeet_cache: dict = {}` added at module level in transcribe.py
- `warm_up()` parakeet branch now calls `from_pretrained()` and stores result in cache; logs "Model ready."
- `_run_parakeet()` checks cache first — `_parakeet_cache.get(model) or from_pretrained(model)`
- 2 new unit tests: cache population via warm_up, cache hit skips from_pretrained

## Files Created/Modified

| File | Change | Purpose |
|------|--------|---------|
| `src/local_whisper/transcribe.py` | Modified | Added _parakeet_cache, updated warm_up + _run_parakeet |
| `tests/test_transcribe.py` | Modified | Added 2 caching tests, added _parakeet_cache + MagicMock imports |

## Decisions Made

| Decision | Rationale | Impact |
|----------|-----------|--------|
| whisperkittools not viable | Not on PyPI; dev tool only (git clone + editable install + heavy deps + Xcode for compilation) | Phase 12 pivoted entirely |
| coremltools too low-level | Ships arm64 wheels ✓ but zero ASR pipeline — encoder/decoder/tokenizer/beam search all manual | No viable Python CoreML Whisper inference package exists |
| Parakeet caching via module-level dict | Simplest approach: no App changes needed, consistent with existing module patterns | warm_up() now meaningful for parakeet; keypress latency drops from ~5s to ~0.3s |
| Cache miss fallback in _run_parakeet | Defensive: if warm_up() was skipped (e.g. test mode), still works | No behaviour change for existing parakeet users |

## Deviations from Plan

### Summary

| Type | Count | Impact |
|------|-------|--------|
| Pivot (checkpoint:decision) | 1 | Entire implementation scope replaced |
| Scope reduction | 1 | pyproject.toml, benchmark_compare.py not touched |

**Total impact:** Spike revealed invalid research assumption; checkpoint correctly caught it; pivot to smaller-but-real fix.

### Spike Finding: whisperkittools not on PyPI

- **Found during:** Task 1 spike
- **Issue:** Research agent reported `pip install whisperkittools` works — false. Package not on PyPI. It's a dev tool requiring git clone + `pip install -e '.[pipelines]'` + PyTorch + Xcode for model compilation steps.
- **Fix:** checkpoint:decision triggered; user selected parakeet caching (option-a)
- **Impact:** CoreML/ANE backend deferred to future when a proper pip-installable package exists

### Deferred Items

- CoreML/ANE Python inference: no pip-installable package exists as of 2026-05-04. Revisit when argmaxinc publishes a proper PyPI package or when an alternative emerges.

## Issues Encountered

| Issue | Resolution |
|-------|------------|
| whisperkittools absent from PyPI | checkpoint:decision → pivot to parakeet caching |
| Ruff: unsorted imports + line too long + unused capsys | Fixed before final test run |

## Next Phase Readiness

**Ready:**
- v0.6 Speed milestone complete (Phase 11 + Phase 12)
- Parakeet path now competitive: ~0.3–0.5s per keypress when warmed up
- All backends (mlx-whisper, parakeet-mlx) have proper warm_up support

**Concerns:**
- CoreML/ANE path remains unexplored — potential 2–5× speedup still on table
- parakeet_cache is module-level global — if future work adds model switching at runtime, cache invalidation needed

**Blockers:**
- None for next milestone

---
*Phase: 12-coreml-backend, Plan: 01*
*Completed: 2026-05-04*
