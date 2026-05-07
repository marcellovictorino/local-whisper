---
phase: 17-llm-interface
plan: 01
status: complete
completed: 2026-05-06
---

# Phase 17 Summary: LLM Module Interface

## What Was Built

Added two intention-level functions to `llm.py` and simplified their callers to single-line calls.

**`llm.apply_voice_command(text, instruction)`** — encapsulates system prompt, user message format (`f"{instruction}\n\n{text}"`), default model (`gpt-5-nano`), and fallback (`instruction`).

**`llm.reshape_for_app(text, prompt)`** — encapsulates system prompt construction, `escape=True`, default model, and fallback (`text`).

## Acceptance Criteria Results

| AC | Result |
|----|--------|
| AC-1: command.py owns no LLM mechanics | PASS — `apply_command()` is one line: `return llm.apply_voice_command(selected_text, voice_command)` |
| AC-2: auto_adapt.py owns no LLM mechanics | PASS — `apply()` last line: `return llm.reshape_for_app(text, prompt)` |
| AC-3: Fallback behavior preserved | PASS — verified by tests 2 and 4 |
| AC-4: Full test suite passes | PASS — 155 tests, 0 failures |

## Files Modified

- `src/local_whisper/llm.py` — +2 public functions after `transform()`
- `src/local_whisper/command.py` — `apply_command()` body: 3 lines → 1 line
- `src/local_whisper/auto_adapt.py` — `apply()` last block: 2 lines → 1 line
- `tests/test_llm.py` — +4 tests in `# --- intention-level functions ---` section (14 → 18 tests)

## Decisions

- `transform()` unchanged — stays as the low-level primitive; new functions are thin wrappers expressing intent
- Fallback values match existing caller behavior exactly: `instruction` for voice command, `text` for reshape
- No config-based model selection added to new functions — that policy stays in `transform()` via env var
