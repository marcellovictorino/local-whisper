---
phase: 10-model-selection
plan: 01
subsystem: transcription
tags: [mlx-whisper, distil-whisper, config, benchmark, tomllib]

requires:
  - phase: 01-core-pipeline
    provides: transcribe.run() and warm_up() API

provides:
  - get_model() reads [whisper] model from config.toml, falls back to distil-whisper
  - DEFAULT_MODEL = mlx-community/distil-whisper-large-v3 (~2× faster than turbo)
  - Dynamic model size hint in first-run download message
  - benchmark.py module with run() + --benchmark CLI flag + just benchmark recipe
  - 4 new tests for get_model() (101 total)

affects: 11-backend-selection

tech-stack:
  added: [tomllib (stdlib, Python 3.11+)]
  patterns: [model resolved once at startup via get_model(), passed explicitly to warm_up/run/App]

key-files:
  created: [src/local_whisper/benchmark.py]
  modified:
    - src/local_whisper/transcribe.py
    - src/local_whisper/app.py
    - src/local_whisper/__main__.py
    - tests/test_transcribe.py
    - justfile

key-decisions:
  - "DEFAULT_MODEL = distil-whisper-large-v3: ~2× faster than turbo, ~600 MB vs ~1.5 GB"
  - "get_model() takes explicit path param for testability — no monkeypatching Path.home() needed"
  - "Config read once at startup (main()), not per keypress"
  - "Benchmark uses synthetic silence array — reproducible, no recorded audio committed"

patterns-established:
  - "Model flows: config.toml → get_model() → warm_up() + App._model → transcribe.run()"
  - "Dynamic size hint: _MODEL_SIZES.get(model, 'unknown size') — unknown IDs handled gracefully"

duration: 15min
started: 2026-05-04T00:00:00Z
completed: 2026-05-04T00:15:00Z
---

# Phase 10 Plan 01: Model Selection Summary

**Switched default ASR model to `distil-whisper-large-v3` (~2× faster, ~600 MB), added config override via `[whisper] model`, dynamic size hints, benchmark module, and 4 new tests.**

## Performance

| Metric | Value |
|--------|-------|
| Duration | ~15 min |
| Started | 2026-05-04 |
| Completed | 2026-05-04 |
| Tasks | 3 completed |
| Files modified | 5 modified, 1 created |

## Acceptance Criteria Results

| Criterion | Status | Notes |
|-----------|--------|-------|
| AC-1: Default model when no config | Pass | `get_model()` returns `distil-whisper-large-v3` — verified via CLI |
| AC-2: Config override respected | Pass | `test_get_model_returns_configured_model` passes |
| AC-3: Dynamic size hint on first run | Pass | `_MODEL_SIZES.get(model, "unknown size")` in `run()` |
| AC-4: No regressions | Pass | 101 tests pass (97 existing + 4 new) |
| AC-5: Benchmark produces repeatable timing output | Pass | `--benchmark` prints JSON with model, warmup_s, mean_s, min_s, max_s |

## Accomplishments

- `get_model()` reads `[whisper] model` from `~/.config/local-whisper/config.toml` via stdlib `tomllib`; graceful fallback on missing file or parse error
- Model wired through full pipeline: `get_model()` → `warm_up(model)` → `App(model=model)` → `transcribe.run(audio, model=model)`
- `benchmark.py` module: synthetic 30s audio, 3 runs, JSON output with warmup + mean/min/max timing
- `just benchmark` recipe for repeatable baseline measurement

## Files Created/Modified

| File | Change | Purpose |
|------|--------|---------|
| `src/local_whisper/transcribe.py` | Modified | Added `DEFAULT_MODEL`, `_MODEL_SIZES`, `_CONFIG_PATH`, `get_model()`; updated `warm_up`/`run` defaults |
| `src/local_whisper/app.py` | Modified | `model` param in `App.__init__()`, passed to both `transcribe.run()` call sites |
| `src/local_whisper/__main__.py` | Modified | `get_model()` at startup; model passed to `warm_up`, `App`, `--test`; `--benchmark` flag added |
| `src/local_whisper/benchmark.py` | Created | Benchmark module: warm-up + transcription timing over N runs, JSON output |
| `tests/test_transcribe.py` | Modified | 4 new `get_model()` tests (no config, no section, override, corrupt TOML) |
| `justfile` | Modified | `benchmark` recipe added |

## Decisions Made

| Decision | Rationale | Impact |
|----------|-----------|--------|
| `get_model()` takes explicit `path` param | Avoids `monkeypatch(Path, "home", ...)` in tests — cleaner isolation | Tests pass `tmp_path / "config.toml"` directly |
| Config read once at startup, not per keypress | Consistent with existing pattern (corrections, snippets read at event time, but model load is heavyweight) | Model change requires app restart |
| Benchmark uses `np.zeros` silence | Reproducible across machines; no real audio files committed | Timing reflects pure model inference, not audio content |

## Deviations from Plan

### Summary

| Type | Count | Impact |
|------|-------|--------|
| Auto-fixed | 1 | No scope change |
| Scope additions | 0 | — |
| Deferred | 0 | — |

### Auto-fixed Issues

**1. Ruff I001 — import block sort order in `benchmark.py`**
- **Found during:** Task 3 lint check
- **Issue:** `from __future__ import annotations` import order flagged by `ruff check`
- **Fix:** `ruff check --fix` + `ruff format` applied automatically
- **Verification:** `ruff check src/ tests/` → All checks passed

## Next Phase Readiness

**Ready:**
- `get_model()` abstraction in place — Phase 11 uses it to derive backend
- `get_backend(model)` can be added alongside `get_model()` in `transcribe.py`
- `App.__init__` already accepts `model` — Phase 11 adds `backend` param alongside it
- `benchmark.py` ready to accept `backend` param (Phase 11 Task 4)
- 101 tests baseline established

**Concerns:**
- None

**Blockers:**
- None

---
*Phase: 10-model-selection, Plan: 01*
*Completed: 2026-05-04*
