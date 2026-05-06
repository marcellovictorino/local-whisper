# Refactor Opportunities (Architecture Deepening)

This document captures architectural deepening opportunities identified in this worktree, using the Module / Interface / Implementation / Seam vocabulary.

## Recommended start order (Top 3)

1. **Deepen the config Module**
2. **Deepen the clipboard Module reliability policy**
3. **Deepen the LLM Module interface**

These three give the best near-term leverage on correctness, regression reduction, and testability.

---

## 1) Deepen the config Module (**Recommended #1**)

**Files**
- `src/local_whisper/config.py`
- Callers:
  - `src/local_whisper/auto_adapt.py`
  - `src/local_whisper/auto_cleanup.py`
  - `src/local_whisper/corrections.py`
  - `src/local_whisper/snippets.py`
  - `src/local_whisper/transcribe.py`

**Problem**
- The current Interface returns raw dict sections.
- Callers still own section-key knowledge, default behavior, and value-shape checks.
- This makes the Module somewhat shallow: config semantics leak across multiple callers.

**Deepening solution**
- Add typed/domain accessors (or config dataclasses), e.g.:
  - `get_auto_adapt_config()`
  - `get_auto_cleanup_config()`
  - `get_corrections_config()`
  - `get_snippets_config()`
  - `get_whisper_config()`
- Centralize:
  - defaults
  - type coercion/validation
  - malformed-value behavior
  - cache invalidation behavior

**Benefits (Leverage + Locality)**
- **Leverage:** callers consume a small, stable Interface.
- **Locality:** config correctness lives in one Module.
- Fewer regressions from per-caller config handling drift.
- Cleaner tests through one config test surface.

**Tests to add**
- Cache behavior (`mtime` changes, invalidation via `invalidate()`).
- Missing file / parse failure behavior.
- Per-section defaults and type validation.

---

## 2) Deepen the clipboard Module reliability policy (**Recommended #2**)

**Files**
- `src/local_whisper/clipboard.py`

**Problem**
- Clipboard/paste reliability policy is implicit.
- The previous settle delay was removed; immediate paste may race clipboard propagation on macOS.
- Reliability behavior is not explicit at the Module Interface.

**Deepening solution**
- Make paste strategy part of the Interface:
  - optional settle delay
  - optional retry/backoff on paste failure
  - explicit fallback contract (“copied, manual paste required”)
- Keep platform-specific details in an adapter behind the same seam.

**Benefits (Leverage + Locality)**
- **Leverage:** callers get one reliable `write_and_paste` contract.
- **Locality:** timing and automation quirks are contained in one Module.
- Better user-facing correctness and fewer flaky behaviors.

**Tests to add**
- Paste command success path.
- Paste command failure path with warning + clipboard preserved.
- Timing/retry policy behavior (with mocked subprocess).

---

## 3) Deepen the LLM Module interface (**Recommended #3**)

**Files**
- `src/local_whisper/llm.py`
- Callers:
  - `src/local_whisper/auto_adapt.py`
  - `src/local_whisper/command.py`

**Problem**
- Shared helper improves reuse, but Interface is still generic and partially command-oriented (`LOCAL_WHISPER_COMMAND_MODEL`).
- Callers still implicitly depend on model/env/fallback mechanics.
- A bug in one shared path can affect both command and auto-adapt flows.

**Deepening solution**
- Evolve Interface to intention-level operations or explicit options:
  - intention-level: `apply_voice_command(...)`, `reshape_for_app(...)`
  - or options object: model env var, escaping mode, token policy, base URL policy
- Keep provider mechanics inside Implementation.

**Benefits (Leverage + Locality)**
- **Leverage:** call sites become smaller and less policy-aware.
- **Locality:** provider/env/error handling stays in one Module.
- Reduced cross-feature regression risk.

**Tests to add**
- Missing key/package fallback.
- API exception fallback.
- Env precedence (`LOCAL_WHISPER_OPENAI_API_KEY` vs `OPENAI_API_KEY`, model/base URL vars).
- Escaping behavior for adapt flows.

---

## Additional candidates (after top 3)

### 4) Deepen session handling Module in `app.py`

**Files**
- `src/local_whisper/app.py`

**Problem**
- `_run_session` handles mode branching and pipeline orchestration in one implementation.

**Solution**
- Introduce per-mode adapters behind one session seam (dictation adapter, command adapter), keeping shared record/transcribe runner common.

**Benefits**
- Better locality per mode.
- Easier mode-specific testing and future extension.

### 5) Deepen logging bootstrap Module

**Files**
- `src/local_whisper/__init__.py`

**Problem**
- Import-time side effects initialize logging globally.

**Solution**
- Move setup to explicit startup path (e.g. called from `__main__`) and keep package import side-effect free.

**Benefits**
- Cleaner Interface for embedding/testing.
- Better startup policy locality.

---

## Recommendation

Start with the **top 3** in this order:
1. config Module
2. clipboard Module reliability policy
3. LLM Module interface

This sequence maximizes early correctness and regression reduction while improving testability and AI navigability.