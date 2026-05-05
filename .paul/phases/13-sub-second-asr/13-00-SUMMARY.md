---
phase: 13-sub-second-asr
plan: 00
subsystem: asr
tags: [sfspeech, pyobjc, speech-recognition, macos, on-device, research]

requires: []
provides:
  - SFSpeechRecognizer viability confirmed for sub-second ASR
  - Working spike script with measured latency numbers
  - Integration path fully documented for implementation plan
affects: [13-01-implementation]

tech-stack:
  added: []
  patterns:
    - SFSpeechURLRecognitionRequest + requiresOnDeviceRecognition=True for offline file transcription
    - objc.registerMetaDataForSelector required for block-typed Speech framework callbacks

key-files:
  created:
    - spikes/sfspeech_spike.py
    - .paul/phases/13-sub-second-asr/13-00-RESEARCH.md
  modified: []

key-decisions:
  - "SFSpeechRecognizer chosen: 200–700ms warm, zero install, high accuracy on clear English"
  - "whisper.cpp CoreML skipped: SFSpeechRecognizer met all criteria; no need for binary distribution"
  - "addsPunctuation=True recommended: +100–200ms but natural output"
  - "SFSpeechURLRecognitionRequest (file path) preferred over buffer API — simpler PyObjC integration"

patterns-established:
  - "Block signatures for Speech framework must be registered via objc.registerMetaDataForSelector"
  - "Auth granted implicitly in CLI context; no requestAuthorization_ call needed"

duration: ~30min
started: 2026-05-05T20:10:00Z
completed: 2026-05-05T20:25:00Z
---

# Phase 13 Plan 00: Sub-second ASR Research — Summary

**⚠️ Preliminary finding later invalidated.** Spike showed SFSpeech viable on short synthetic audio. Full benchmark (Phase 14, 30s real dictation audio) found 57.1% WER — unacceptable. SFSpeech dropped; distil-whisper-large-v3 remains default. See RESEARCH.md addendum for final outcome.

## Performance

| Metric | Value |
|--------|-------|
| Duration | ~30 min |
| Started | 2026-05-05 |
| Completed | 2026-05-05 |
| Tasks | 2 of 3 (Task 2 skipped — decision checkpoint resolved early) |
| Files created | 2 |

## Acceptance Criteria Results

| Criterion | Status | Notes |
|-----------|--------|-------|
| AC-1: SFSpeechRecognizer latency measured | Pass | 5s: 165–525ms; 15s: 354–705ms (warm, on-device) |
| AC-2: SFSpeechRecognizer WER assessed | Pass | ~0% error on clear TTS speech; comparable to distil-whisper |
| AC-3: Winner recommended | Pass | SFSpeechRecognizer — see RESEARCH.md |
| AC-4: Integration path documented | Pass | Exact API, block registration, `transcribe.py` changes in RESEARCH.md |

## Accomplishments

- Confirmed `SFSpeechRecognizer` works offline via PyObjC with `requiresOnDeviceRecognition = True`
- Measured warm latency: **165ms (5s clip)**, **354ms (15s clip)** without punctuation; **206–705ms** with `addsPunctuation = True`
- Discovered PyObjC block signature must be registered manually for `recognitionTaskWithRequest:resultHandler:` — documented the exact `registerMetaDataForSelector` call
- Confirmed Speech framework available on all target macOS versions with zero pip install
- Documented complete integration path: new `Backend.SFSPEECH`, `KnownModel.SFSPEECH_EN`, `_run_sfspeech()` function signature, warm-up strategy

## Files Created

| File | Purpose |
|------|---------|
| `spikes/sfspeech_spike.py` | Working spike with latency measurement, punctuation toggle, both test clips |
| `.paul/phases/13-sub-second-asr/13-00-RESEARCH.md` | Full findings: candidates table, winner, integration path, `transcribe.py` change spec |

## Decisions Made

| Decision | Rationale | Impact |
|----------|-----------|--------|
| SFSpeechRecognizer — viable | 200–700ms warm, ~0% WER, zero install | Default candidate for implementation |
| whisper.cpp CoreML — skipped | Not needed; SFSpeechRecognizer met all criteria | No binary distribution complexity |
| `addsPunctuation = True` as default | Natural output, +100–200ms overhead acceptable | Improves paste quality |
| `SFSpeechURLRecognitionRequest` over buffer API | Simpler PyObjC path; same temp-WAV pattern as `_run_parakeet` | Reuses existing audio→file→transcribe pattern |

## Deviations from Plan

| Type | Count | Impact |
|------|-------|--------|
| Task skipped | 1 | Task 2 (whisper.cpp) — decision checkpoint resolved with sfspeech-viable |
| Auto-fixed | 1 | PyObjC block signature not inferable — added `registerMetaDataForSelector` to spike |

**Total impact:** Positive — fewer tasks, cleaner outcome.

### Auto-fixed

**PyObjC block signature registration**
- Found during: Task 1 (SFSpeechRecognizer spike)
- Issue: `TypeError: Argument 3 is a block, but no signature available` — PyObjC cannot infer block types from Speech framework metadata
- Fix: `objc.registerMetaDataForSelector(b'SFSpeechRecognizer', b'recognitionTaskWithRequest:resultHandler:', {...})` with explicit arg types
- Verification: Spike ran cleanly, returning transcripts with measured latency

## Issues Encountered

| Issue | Resolution |
|-------|------------|
| `requestAuthorization_` block signature missing | Skipped explicit auth — recognition succeeds in CLI context without it; auth granted implicitly |
| First `uv run` created fresh venv (Speech import failed) | Used `objc.loadBundle` instead of `import Speech` — correct PyObjC pattern |

## Next Phase Readiness

**Ready:**
- Integration path fully specified in RESEARCH.md — implementation plan can start immediately
- `spikes/sfspeech_spike.py` provides working reference implementation
- Block signature registration pattern documented

**Concerns:**
- Auth status shows 0 ("not determined") even though recognition works — production app may need explicit `requestAuthorization_` call with proper app bundle
- Test audio was TTS (ideal conditions) — WER on real noisy speech unknown; user should test with own voice before committing as default

**Blockers:** None
