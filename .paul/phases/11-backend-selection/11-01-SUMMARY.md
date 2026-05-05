---
phase: 11-backend-selection
plan: 01
status: complete
executed: 2026-05-04
---

# Phase 11 APPLY Summary

## Execution Result

All 6 tasks completed. 107 tests passing. No deviations.

## Tasks Completed

| Task | Result |
|------|--------|
| Task 1: Spike — verify parakeet-mlx API | PASS — API documented; key deviation noted |
| Task 2: KnownModel + get_backend() + dispatch in transcribe.py | PASS |
| Task 3: Wire backend through app.py + __main__.py | PASS |
| Task 4: Update benchmark.py to report backend | PASS |
| Task 5: parakeet-mlx optional dependency in pyproject.toml | PASS (uv add did this automatically) |
| Task 6: 6 new tests | PASS — 107 total (101 existing + 6 new) |

## API Deviation (Task 1)

Plan assumed parakeet-mlx `transcribe()` accepts numpy array. Actual API differs:

- `transcribe(path: Path | str)` — takes **file path**, not numpy array
- Uses ffmpeg internally to load audio
- Returns `AlignedResult` with `.text: str` attribute (not `result["text"]` dict)

**Implemented:** `_run_parakeet()` writes numpy float32 array to temp WAV via `soundfile`, passes path, cleans up with `try/finally`. Returns `result.text.strip()`.

## Files Modified

- `src/local_whisper/transcribe.py` — KnownModel StrEnum, _BACKEND_MAP, DEFAULT_BACKEND, get_backend(), _run_mlx_whisper(), _run_parakeet(), updated warm_up() + run() signatures
- `src/local_whisper/app.py` — App.__init__ backend param, self._backend, transcribe.run() calls updated
- `src/local_whisper/__main__.py` — get_backend() call, backend passed to warm_up + App + benchmark
- `src/local_whisper/benchmark.py` — backend param, "backend" key in returned dict
- `tests/test_transcribe.py` — 6 new tests for KnownModel/get_backend/fallback
- `pyproject.toml` — [project.optional-dependencies] parakeet = ["parakeet-mlx>=0.5.1"]

## Verification Checks

- [x] `get_backend(KnownModel.PARAKEET_V2)` → `"parakeet-mlx"`
- [x] `get_backend("any/unknown")` → `"mlx-whisper"`
- [x] `pytest tests/ -q` → 107 passed
- [x] `ruff check src/ tests/` → no errors
- [x] `ruff format --check src/ tests/` → no reformats needed
- [x] Code review: backend flows config → get_model() → get_backend() → warm_up() + App._backend → run()

## Acceptance Criteria

- [x] AC-1: Backend inferred from model ID — no config key needed
- [x] AC-2: Unknown model ID falls back to mlx-whisper
- [x] AC-3: Graceful fallback when parakeet-mlx not installed
- [x] AC-4: KnownModel StrEnum covers all 4 current supported models
- [x] AC-5: Benchmark reports backend (verified structurally; actual JSON confirmed in implementation)
- [x] AC-6: No regressions — 107 tests passing
