# Roadmap: local-whisper

## Overview

Build a macOS speech-to-text tool running fully offline on Apple Silicon. Start with a working transcription pipeline (Phase 1), add the keyboard trigger and clipboard paste (Phase 2), then add a visual recording indicator (Phase 3). Phase 4 covers distribution and packaging for real-world use. v0.2 adds power-user features: snippets, corrections, and command mode. v0.5-v0.6 focus on speed: faster default model, then faster inference backend (parakeet-mlx → CoreML).

## Current Milestone

**v0.8 Architecture Deepening** (v0.8.0)
Status: 🚧 In Progress
Phases: 0 of 4 complete

---

**v0.7 Sub-second ASR** (v0.7.0)
Status: ✅ Complete
Phases: 2 of 2 complete

---

**v0.6 Speed** (v0.6.0)
Status: ✅ Complete
Phases: 2 of 2 complete

---

**v0.5 Model Selection** (v0.5.0)
Status: ✅ Complete
Phases: 1 of 1 complete

---

**v0.4 Auto-Adapt** (v0.4.0)
Status: ✅ Complete
Phases: 1 of 1 complete

---

**v0.3 Polish** (v0.3.0)
Status: ✅ Complete
Phases: 1 of 1 complete

---

**v0.2 Enhancements** (v0.2.0)
Status: ✅ Complete
Phases: 3 of 3 complete

---

**v0.1 MVP** (v0.1.0)
Status: ✅ Complete
Phases: 4 of 4 complete

## Phases

### v0.8 Architecture Deepening

| Phase | Name | Plans | Status | Completed |
|-------|------|-------|--------|-----------|
| 15 | Config Module Deepening | 1 | ✅ Complete | 2026-05-06 |
| 16 | Clipboard Reliability Policy | 1 | ✅ Complete | 2026-05-06 |
| 17 | LLM Module Interface | TBD | Not started | - |
| 18 | Session + Logging Bootstrap | TBD | Not started | - |

### v0.7 Sub-second ASR

| Phase | Name | Plans | Status | GitHub Issue | Completed |
|-------|------|-------|--------|--------------|-----------|
| 13 | Sub-second ASR Research | 1 | ✅ Complete | - | 2026-05-05 |
| 14 | SFSpeech Evaluation + Revert | 1 | ❌ Dropped | - | 2026-05-05 |

### v0.6 Speed

| Phase | Name | Plans | Status | GitHub Issue | Completed |
|-------|------|-------|--------|--------------|-----------|
| 11 | Backend Selection | 1 | ✅ Complete | - | 2026-05-04 |
| 12 | CoreML Backend | 1 | ✅ Complete | - | 2026-05-04 |

### v0.5 Model Selection

| Phase | Name | Plans | Status | GitHub Issue | Completed |
|-------|------|-------|--------|--------------|-----------|
| 10 | Model Selection | 1 | ✅ Complete | - | 2026-05-04 |

### v0.4 Auto-Adapt

| Phase | Name | Plans | Status | GitHub Issue | Completed |
|-------|------|-------|--------|--------------|-----------|
| 9 | Auto-Adapt | 1 | ✅ Complete | - | 2026-04-28 |

### v0.3 Polish

| Phase | Name | Plans | Status | GitHub Issue | Completed |
|-------|------|-------|--------|--------------|-----------|
| 8 | Auto-Cleanup | 1 | ✅ Complete | - | 2026-04-28 |

### v0.2 Enhancements

| Phase | Name | Plans | Status | GitHub Issue | Completed |
|-------|------|-------|--------|--------------|-----------|
| 5 | Snippet Expansion | 1 | ✅ Complete | #4 | 2026-04-27 |
| 6 | Personal Corrections | 1 | ✅ Complete | #2 | 2026-04-27 |
| 7 | Command Mode | 1 | ✅ Complete | #3 | 2026-04-27 |

### v0.1 MVP

| Phase | Name | Plans | Status | Completed |
|-------|------|-------|--------|-----------|
| 1 | Core Pipeline | 1/1 | ✅ Complete | 2026-04-27 |
| 2 | Hotkey + Clipboard | 1/1 | ✅ Complete | 2026-04-27 |
| 3 | Visual Overlay | 1/1 | ✅ Complete | 2026-04-27 |
| 4 | Distribution | 1/1 | ✅ Complete | 2026-04-27 |

## Phase Details

### Phase 1: Core Pipeline

**Goal:** Record audio from microphone and transcribe it to text via a local model — no UI, no hotkey yet. Validate the full audio → text path works on Apple Silicon.
**Depends on:** Nothing (first phase)
**Research:** Unlikely (using mlx-whisper, established on Apple Silicon)

**Scope:**
- Python project setup (uv, pyproject.toml, src layout)
- Audio capture module (sounddevice → numpy array)
- Transcription module (mlx-whisper, lazy model load)
- CLI smoke test: `python -m local_whisper --test` records 5s → prints transcript

**Plans:**
- [ ] 01-01: Project setup, audio capture, transcription pipeline

### Phase 2: Hotkey + Clipboard

**Goal:** Trigger recording via a global keyboard shortcut (Right Command), transcribe, write result to clipboard, and paste at active cursor position.
**Depends on:** Phase 1 (transcription module)
**Research:** Unlikely (pynput for hotkey, pyperclip + AppleScript for paste)

**Scope:**
- Global hotkey listener (pynput, requires Accessibility permission)
- Toggle-mode recording (press to start, press to stop)
- Clipboard write + `osascript` paste at cursor

**Plans:**
- [ ] 02-01: Hotkey listener + clipboard paste integration

### Phase 3: Visual Overlay

**Goal:** Show a small always-on-top bubble/indicator while recording is active. Auto-dismiss when transcription completes.
**Depends on:** Phase 2 (application loop exists)
**Research:** Unlikely (tkinter or rumps for macOS menubar/overlay)

**Scope:**
- Small floating window (recording indicator)
- Show on hotkey press, hide on transcription complete
- Non-blocking — runs in separate thread

**Plans:**
- [x] 03-01: Recording indicator overlay

### Phase 4: Distribution

**Goal:** Package as a launchable macOS app or background service users can install and run at login.
**Depends on:** Phase 3 (feature complete)
**Research:** Likely (py2app vs PyInstaller vs Swift wrapper)

**Scope:**
- Packaging as `.app` or `launchd` service
- First-run setup (permissions, model download)
- README with install instructions

**Plans:**
- [ ] 04-01: macOS distribution packaging

### Phase 10: Model Selection

**Goal:** Switch default model to `mlx-community/distil-whisper-large-v3` (~2× faster than turbo at runtime, same ~1.5 GB download, <1% WER on English). Allow users to override via `[whisper] model` in config.toml. Document `mlx-community/whisper-large-v3-turbo` as the switch for multilingual support or higher accuracy.
**Depends on:** Phase 1 (transcribe module)
**Research:** Not needed (mlx-whisper already accepts any HF model ID)

**Scope:**
- Change default model to `mlx-community/distil-whisper-large-v3`
- `transcribe.get_model()` reads `[whisper] model` from config, falls back to default
- Dynamic size hint per model in first-run download message
- `App` and `__main__` resolve model once at startup, pass through to `warm_up()` and `run()`
- `benchmark.py`: warm-up time + transcription mean/min/max over 3×30s synthetic audio runs
- `--benchmark` CLI flag + `just benchmark` recipe — establishes baseline for tracking evolution
- 4 new unit tests for `get_model()`

**Plans:**
- [ ] 10-01: get_model() + default change + App wiring + benchmark + tests

### Phase 11: Backend Selection

**Goal:** Add `parakeet-mlx` as a faster inference backend (~0.3–0.5s vs ~0.5–0.7s for distil-whisper). Backend is **inferred automatically from the model ID** — no separate config key. Users switch by setting `[whisper] model` to a parakeet model ID. A `KnownModel` StrEnum lists all supported models; adding future models = one line.
**Depends on:** Phase 10 (`get_model()` abstraction, benchmark module)
**Research:** Minimal — spike to verify parakeet-mlx API (Task 1) before coding

**Scope:**
- `KnownModel` StrEnum: all supported HF model IDs with their backend assignment
- `_BACKEND_MAP: dict[str, str]` — maps model ID → `"mlx-whisper"` | `"parakeet-mlx"`
- `get_backend(model: str) -> str` — pure lookup, no file I/O, no config read
- `run()` and `warm_up()` accept `backend` param, dispatch to backend implementation
- parakeet-mlx optional extra (`uv sync --extra parakeet`), graceful fallback if absent
- benchmark.py updated to include `"backend"` in JSON output
- Config stays simple: `[whisper] model = "mlx-community/parakeet-tdt-0.6b-v2"` → backend auto-inferred

**Plans:**
- [ ] 11-01: KnownModel StrEnum + get_backend() + dispatch + fallback + tests

### Phase 12: CoreML Backend

**Goal:** Maximum speed transcription (~80–250ms) via Apple CoreML/ANE — ~5× faster than mlx-whisper turbo, ~2-3× faster than parakeet-mlx. Trivial install (no native compilation). macOS M-series only (already the target).
**Depends on:** Phase 11 (multi-backend dispatch infrastructure)
**Research:** Required — three candidate paths with different trade-offs

**Background — what "native compilation" means:**
Python packages that include C/Swift/Rust code need platform-specific compiled `.so` files. When a pre-built wheel exists for macOS arm64: `uv add somepackage` works instantly, no tools required. When no arm64 wheel exists: pip tries to compile from source, which requires Xcode + cmake + (sometimes) Swift toolchain — fails silently or with cryptic errors for non-developer users. Phase 12 MUST use a path that ships pre-built arm64 wheels OR uses only system frameworks (CoreML is already on every macOS installation).

**Candidate paths (research questions):**

1. **`coremltools` + pre-converted WhisperKit/Parakeet CoreML models** *(lowest friction candidate)*
   - Apple-maintained package; ships pre-built arm64 wheels — no compilation
   - Uses system CoreML framework (zero extra install on macOS)
   - Models: `argmaxinc/whisperkit-coreml-*` on HuggingFace (`.mlpackage` format, not `.safetensors`)
   - Parakeet CoreML models may also be available via argmaxinc or NVIDIA
   - Research: confirm `coremltools` arm64 wheels exist; confirm inference API for audio input; measure latency
   - Risk: model format different from mlx (new download, different cache management)

2. **`pywhispercpp` (whisper.cpp Python bindings)**
   - whisper.cpp uses Metal Performance Shaders (GPU) — not CoreML/ANE, but still fast (~0.2–0.4s)
   - Pre-built arm64 wheels available on PyPI
   - GGML model format (single file, smaller than mlx snapshots)
   - Research: confirm arm64 wheels; measure latency on M-series vs CoreML path
   - Risk: MPS ≠ ANE — may be slower than true CoreML path

3. **WhisperKit CLI binary (pre-compiled Swift, subprocess)**
   - WhisperKit ships a macOS arm64 CLI binary (`whisperkit-cli`)
   - Python calls it via subprocess — no Swift compilation needed by user
   - Fastest path (~80–190ms), full CoreML/ANE utilisation
   - Research: binary distribution mechanism (Homebrew? direct download?); subprocess interface; model download flow
   - Risk: binary distribution adds complexity to setup.sh; subprocess adds latency overhead vs direct API

**Recommended research order:** Start with `coremltools` (lowest friction, Apple-maintained). If latency is acceptable, no need to go further. Fall back to pywhispercpp if coremltools API is too low-level. Evaluate WhisperKit CLI only if target <100ms is required.

**Plans:**
- [ ] 12-00: Research — benchmark all three paths, document API, recommend winner
- [ ] 12-01: Implement chosen backend + config key + tests (after research complete)

### Phase 9: Auto-Adapt

**Goal:** Detect the frontmost macOS app at key press time and automatically reshape the transcription via LLM using a per-app prompt before pasting. Opt-in via config; command mode takes full priority.
**Depends on:** Phase 7 (command mode / OpenAI client established)
**Research:** Unlikely (NSWorkspace already available via PyObjC, reuses existing LLM infra)

**Scope:**
- App detection: `NSWorkspace.sharedWorkspace().frontmostApplication().localizedName()` at press time
- Config: `[auto_adapt]` section with `enabled = false` default + per-app sub-sections (`[auto_adapt.email]`, `[auto_adapt.slack]`)
- Two built-in presets: email (formal) + Slack (casual, emojis, bullets)
- Pipeline: after `auto_cleanup`, before `corrections` + `snippets` — replaces text when rule matches
- Command mode (text selected) takes full priority — auto-adapt skipped
- Fallback: unrecognised app → passthrough
- README: latency/cost note, config examples

**Plans:**
- [ ] 09-01: auto_adapt module + config + pipeline integration + README

### Phase 14: SFSpeech Evaluation + Revert

**Outcome: DROPPED** — SFSpeech implemented, benchmarked, and reverted. No net code change from v0.6.

**What was tried:** Full PyObjC integration of `SFSpeechRecognizer` as `Backend.SFSPEECH` with recognizer caching, XPC run loop handling, authorization flow, and 5 unit tests.

**Benchmark result (30s real audio, 2026-05-05):**
| Backend | WER% | Latency |
|---------|------|---------|
| SFSpeech (on-device, en-US) | 57.1% | 2.45s |
| distil-whisper-large-v3 | 12.2% | 1.85s |

**Why dropped:**
1. **Quality**: 57.1% WER unacceptable for dictation — on-device Siri model is weaker than distil-whisper
2. **Privacy UX**: macOS shows "sends voice to Apple" in permission dialog regardless of `requiresOnDeviceRecognition=True` — contradicts "zero cloud" product promise
3. **Complexity**: Required `objc.registerMetaDataForSelector` block registration, XPC run loop spin, explicit authorization flow — significant PyObjC plumbing for a worse result

**Plans:**
- [x] 14-01: SFSpeech backend wiring + benchmark + revert

### Phase 13: Sub-second ASR Research

**Goal:** Research viable paths to <1s transcription latency on Apple Silicon. Three candidates need evaluation before committing to implementation.
**Depends on:** Phase 12 (multi-backend infrastructure in place)
**Research:** Required — candidates have very different trade-offs

**Candidates:**

1. **macOS SFSpeechRecognizer** (via PyObjC) — *lowest friction candidate*
   - Built into every macOS installation, no model download, true ANE
   - PyObjC already a project dependency (used for overlay)
   - `requiresOnDeviceRecognition = true` runs fully offline
   - Research: confirm PyObjC bindings for SFSpeechAudioBufferRecognitionRequest; measure latency; measure WER vs distil-whisper; check streaming vs batch API
   - Risk: accuracy unknown; Siri language model vs Whisper quality; English-only

2. **whisper.cpp with CoreML (pre-compiled binary, subprocess)**
   - Pre-compile whisper.cpp with CoreML/ANE on dev machine; distribute binary via GitHub Releases or Homebrew tap
   - `setup.sh` downloads pre-compiled binary — zero compilation for end users
   - Models in GGML format (~300–800 MB), downloaded on first run
   - Research: confirm arm64 + CoreML build process; benchmark latency; design subprocess interface; evaluate Homebrew tap vs GitHub Releases distribution; assess model management (GGML vs current HuggingFace MLX format)
   - Risk: per-macOS-version binary compatibility; subprocess overhead; model format migration

3. **distil-whisper-small / whisper-tiny (smaller model)** — *fallback*
   - Trivial: change DEFAULT_MODEL; existing infrastructure unchanged
   - Research: benchmark WER and latency for distil-whisper-small on real audio
   - Risk: likely 15–20%+ WER vs ~12% current — probably unacceptable for dictation use

**Research order:** SFSpeechRecognizer first (zero install friction, already have PyObjC). If WER acceptable, done. If not, evaluate whisper.cpp CoreML binary distribution. Smaller model as fallback only if both fail.

**Plans:**
- [ ] 13-00: Research — spike all three paths, benchmark WER + latency, recommend winner

### Phase 15: Config Module Deepening

**Goal:** Replace raw-dict `load_section()` callers with typed domain accessors. Centralize all defaults, type coercion, malformed-value behavior, and cache invalidation in `config.py`.
**Depends on:** Refactor PR #16 (config.py exists)
**Research:** Not needed

**Scope:**
- Typed accessor functions: `get_auto_adapt_config()`, `get_auto_cleanup_config()`, `get_corrections_config()`, `get_snippets_config()`, `get_whisper_config()`
- Each returns a typed dataclass or TypedDict; callers no longer own key/default/type knowledge
- Tests: per-section defaults, type validation, malformed values, cache behavior

**Plans:**
- [ ] 15-01: Typed config accessors + callers updated + tests

### Phase 16: Clipboard Reliability Policy

**Goal:** Make paste strategy explicit at the module Interface. Define a contract for settle delay, retry/backoff, and fallback ("copied, manual paste required").
**Depends on:** Phase 15 (stable config access)
**Research:** Not needed

**Scope:**
- Explicit `write_and_paste(text, *, settle_ms=0, retries=0)` or equivalent Interface
- Platform-specific timing/retry details contained in implementation
- Tests: success path, failure path with warning + clipboard preserved, retry policy

**Plans:**
- [ ] 16-01: Explicit paste contract + retry policy + tests

### Phase 17: LLM Module Interface

**Goal:** Evolve `llm.transform()` from generic helper to intention-level operations. Callers stop owning model/env/fallback policy.
**Depends on:** Phase 15 (stable config access)
**Research:** Not needed

**Scope:**
- Intention-level functions: `apply_voice_command(selected_text, instruction)` and `reshape_for_app(text, app_name, prompt)`
- Or: options object encapsulating model env var, escaping mode, token policy, base URL policy
- Callers (`command.py`, `auto_adapt.py`) shrink to single-line calls
- Tests: missing key/package fallback, API exception, env precedence, escaping behavior

**Plans:**
- [ ] 17-01: Intention-level LLM interface + callers updated + tests

### Phase 18: Session + Logging Bootstrap

**Goal:** Move `_setup_logging()` from import-time side effect to explicit startup call in `__main__`. Introduce per-mode session adapters in `app.py` for cleaner mode-specific testing.
**Depends on:** Phase 17 (stable LLM interface)
**Research:** Not needed

**Scope:**
- Move `_setup_logging()` call from `__init__.py` to `__main__.main()`; keep `__init__.py` side-effect free
- Per-mode adapters behind session seam: `DictationSession`, `CommandSession` — shared record/transcribe runner common
- Tests: logging only configured when `main()` runs (not on import); per-mode adapter behavior

**Plans:**
- [ ] 18-01: Logging bootstrap relocation + session adapters + tests

### Phase 8: Auto-Cleanup

**Goal:** Post-process every transcription to remove filler words and immediate repetitions before paste. Always-on by default, opt-out via config.
**Depends on:** Phase 7 (pipeline established)
**Research:** Unlikely (rule-based, no new deps)

**Scope:**
- Filler word removal (`um`, `uh`, `like`, `you know`, etc.)
- Immediate repetition collapse (`I I need` → `I need`)
- Config: `[auto_cleanup] enabled = true` in `config.toml`
- Pipeline position: transcribe → auto-cleanup → snippets → corrections → paste

**Plans:**
- [ ] 08-01: Auto-cleanup module + config integration

---
*Roadmap created: 2026-04-27*
*Last updated: 2026-05-06 — Phase 16 (Clipboard Reliability Policy) complete*
