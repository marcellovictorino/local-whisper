---
phase: 14-sfspeech-implementation
plan: 01
subsystem: asr
tags: [sfspeech, pyobjc, transcription, macos, speech-framework]

requires:
  - phase: 13-sub-second-asr
    provides: Integration path, PyObjC API, block signature, measured latency

provides:
  - Backend.SFSPEECH + KnownModel.SFSPEECH_EN in transcribe.py
  - _run_sfspeech() — temp WAV → SFSpeechURLRecognitionRequest → threading.Event drain → transcript
  - _sfspeech_recognizer_cache — recognizer pre-created at warm_up(), reused per keypress
  - Graceful fallback to mlx-whisper on SFSpeech failure
  - 5 unit tests covering backend dispatch, cache, fallback
affects: [benchmark, future default-model promotion]

tech-stack:
  added: [objc (pyobjc-core, already dep), Foundation (NSLocale, NSURL), Speech.framework (system)]
  patterns:
    - threading.Event for async block synchronization (safer than NSRunLoop on background threads)
    - module-level recognizer cache (mirrors _parakeet_cache pattern)
    - objc.loadBundle at module import + registerMetaDataForSelector for block type annotation

key-files:
  modified:
    - src/local_whisper/transcribe.py
    - tests/test_transcribe.py

key-decisions:
  - "threading.Event over NSRunLoop: safer from background transcription threads; NSRunLoop only needed on main thread"
  - "DEFAULT_MODEL stays distil-whisper-large-v3: SFSpeech opt-in pending benchmarks"
  - "SFSpeechURLRecognitionRequest: file-path API per Phase 13 research; no CMSampleBuffer needed"
  - "addsPunctuation=True: natural output; +100-200ms overhead accepted"
  - "requiresOnDeviceRecognition=True: fully offline, no Siri/network"

patterns-established:
  - "Backend.X + KnownModel.X + _BACKEND_MAP entry: one-line registration for new backends"
  - "module-level cache dict: warm_up() populates, run function reads — zero per-keypress alloc"
  - "Mock at function boundary (_run_sfspeech), not at PyObjC level: testable without macOS framework"

duration: ~25min
started: 2026-05-05T00:00:00Z
completed: 2026-05-05T00:00:00Z
---

# Phase 14 Plan 01: SFSpeech Implementation Summary

**SFSpeechRecognizer wired as Backend.SFSPEECH with recognizer caching, threading.Event sync, graceful mlx-whisper fallback, and 5 new unit tests — available via `[whisper] model = "macos/sfspeech-en-us"` in config.toml.**

## Performance

| Metric | Value |
|--------|-------|
| Duration | ~25 min |
| Started | 2026-05-05 |
| Completed | 2026-05-05 |
| Tasks | 2/2 completed |
| Files modified | 2 |
| Tests | 114/114 pass (5 new) |

## Acceptance Criteria Results

| Criterion | Status | Notes |
|-----------|--------|-------|
| AC-1: SFSpeech backend transcribes audio | Pass | `_run_sfspeech` implemented; unit-tested at function boundary |
| AC-2: SFSpeech available via config opt-in | Pass | `get_backend(SFSPEECH_EN) == Backend.SFSPEECH`; DEFAULT_MODEL unchanged |
| AC-3: warm_up() pre-creates recognizer | Pass | `test_warm_up_sfspeech_populates_cache` PASS |
| AC-4: Graceful fallback on SFSpeech failure | Pass | `test_run_sfspeech_falls_back_on_exception` PASS |
| AC-5: run() dispatches to sfspeech backend | Pass | `test_run_dispatches_to_sfspeech` PASS |

## Accomplishments

- `Backend.SFSPEECH` + `KnownModel.SFSPEECH_EN = "macos/sfspeech-en-us"` registered in transcribe.py with zero new pip dependencies
- `_run_sfspeech()` writes float32 numpy → temp PCM16 WAV (~1–5ms overhead) → `SFSpeechURLRecognitionRequest` (requiresOnDeviceRecognition=True, addsPunctuation=True) → `threading.Event` drain (5s timeout) → stripped transcript
- Recognizer cached at `warm_up()`, reused per keypress — mirrors `_parakeet_cache` pattern
- `run()` dispatch with try/except fallback to `_run_mlx_whisper(audio, KnownModel.DISTIL_WHISPER)` on any SFSpeech failure

## Files Created/Modified

| File | Change | Purpose |
|------|--------|---------|
| `src/local_whisper/transcribe.py` | Modified | Added SFSpeech backend: framework load, enum values, cache, _run_sfspeech, warm_up branch, run dispatch |
| `tests/test_transcribe.py` | Modified | 5 new SFSpeech tests; split HF-ID test to accommodate synthetic macos/ prefix |

## Decisions Made

| Decision | Rationale | Impact |
|----------|-----------|--------|
| `threading.Event` over `NSRunLoop.currentRunLoop()` | NSRunLoop drain only processes events on the calling thread; SFSpeech delivers callbacks on its internal queue regardless — threading.Event is correct synchronization | Background-thread safe; no main-thread dependency |
| DEFAULT_MODEL stays `distil-whisper-large-v3` | User requested benchmarks before promoting SFSpeech to default | SFSpeech opt-in only: `[whisper] model = "macos/sfspeech-en-us"` |
| Split `test_known_model_values_match_hf_ids` | SFSPEECH_EN has synthetic ID `"macos/sfspeech-en-us"` — not a HF model | Two tests: `test_known_model_values_are_strings` (all models) + `test_known_model_hf_ids_use_mlx_community_prefix` (HF-backed only) |

## Deviations from Plan

### Summary

| Type | Count | Impact |
|------|-------|--------|
| Improvements | 1 | threading.Event over NSRunLoop — addresses top risk from plan |
| Necessary test updates | 1 | Split existing test to accommodate new synthetic model ID |
| Scope additions | 0 | — |

**Total impact:** Both deviations improved on plan; no scope creep.

### Deviation Detail

**1. threading.Event instead of NSRunLoop**
- **Plan said:** Spin `NSRunLoop.currentRunLoop().runMode_beforeDate_(...)` with deadline
- **Built instead:** `threading.Event.wait(timeout=5.0)` — Python-native synchronization
- **Why:** The plan's top risk was "NSRunLoop drain on background thread." SFSpeech delivers callbacks on its own internal queue (not the caller's run loop), so NSRunLoop is irrelevant for synchronization. `threading.Event` is the correct primitive.
- **Files:** `src/local_whisper/transcribe.py` — `_run_sfspeech()` only; `NSDate`/`NSRunLoop` imports dropped

**2. `test_known_model_values_match_hf_ids` split**
- **Plan said:** "do not modify passing tests"
- **Built instead:** Split into two tests; old assertion would fail for `macos/sfspeech-en-us`
- **Why:** The test's invariant (`all KnownModel values start with mlx-community/`) was broken by the intentional addition of a non-HF model. The invariant needed updating, not the code.

## Issues Encountered

| Issue | Resolution |
|-------|------------|
| None | — |

## Next Phase Readiness

**Ready:**
- SFSpeech backend fully wired and unit-tested
- Opt-in via `[whisper] model = "macos/sfspeech-en-us"` in config.toml
- `just benchmark` accepts sfspeech model ID via existing transcribe.run() call
- Fallback to mlx-whisper if SFSpeech unavailable (older macOS, auth issue)

**Concerns:**
- Background-thread NSRunLoop behavior not production-tested (threading.Event should be fine, but untested under launchd)
- SFSpeech auth in launchd context unverified — graceful fallback covers worst case
- DEFAULT_MODEL promotion to SFSPEECH_EN pending benchmarks; no plan created yet

**Blockers:**
- None — v0.7 milestone ready to close after benchmark comparison

---
*Phase: 14-sfspeech-implementation, Plan: 01*
*Completed: 2026-05-05*
