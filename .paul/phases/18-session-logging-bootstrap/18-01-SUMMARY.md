---
phase: 18-session-logging-bootstrap
plan: 01
status: complete
---

## What Was Built

### Task 1: Logging Bootstrap Moved to `main()`

**`src/local_whisper/__init__.py`** — removed the bare `_setup_logging()` call at module level (line 36). The function definition is preserved and remains importable.

**`src/local_whisper/__main__.py`** — imported `_setup_logging` from `local_whisper` and added `_setup_logging()` as the first statement inside `main()`, before argument parsing.

**`tests/test_main.py`** — added 2 tests:
- `test_logging_not_configured_on_import`: clears handlers, reloads the module via `importlib.reload`, asserts `handlers == []`.
- `test_logging_configured_after_main`: clears handlers, calls `main()` with `sys.argv` patched to `["local-whisper", "--help"]` (catches `SystemExit`), asserts handlers are non-empty.

### Task 2: Session Adapters Extracted

**`src/local_whisper/app.py`** — added two classes above `App`:

- `DictationSession.run_pipeline(text, active_app, corrections_map)` — runs `auto_cleanup → auto_adapt → corrections → snippets → clipboard.write_and_paste` and returns the processed text.
- `CommandSession.run_pipeline(selection, instruction)` — calls `llm.apply_voice_command` then `clipboard.write_and_paste` and returns the result.

`App._run_session`'s `match session.mode:` block was replaced to delegate to these adapters, keeping the shared record/transcribe/validation logic unchanged.

**`tests/test_app.py`** (new file) — 4 tests:
- `test_dictation_pipeline_order`: mocks all 5 pipeline steps, verifies each is called with the output of the prior step and correct args.
- `test_dictation_pipeline_applies_corrections`: integration-style, passes a real corrections map, stubs surrounding steps as identity functions, verifies substitution applies.
- `test_command_pipeline`: mocks `llm.apply_voice_command` and `clipboard.write_and_paste`, verifies call args and return value.
- `test_command_pipeline_llm_failure`: LLM returns empty string, verifies `write_and_paste("")` is called and empty string is returned without exception.

## Decisions Made

- The `test_logging_not_configured_on_import` test clears handlers and uses `importlib.reload` rather than a subprocess, keeping it fast while accurately verifying the no-side-effect contract.
- Session adapters are plain classes with no `__init__` state — instantiated fresh in `App._run_session` as the plan specified. No ABC or Protocol added (YAGNI).
- The `call` import in `test_app.py` was included for completeness but is unused; individual `assert_called_once_with` calls provide sufficient call-order confidence when combined with the chained return values.

## Verification

- `uv run pytest -x` — 154 passed, 0 failed
- `uv run python -c "import local_whisper; import logging; print(logging.getLogger('local_whisper').handlers)"` → `[]`
- No bare `_setup_logging()` call in `__init__.py`
- `_setup_logging()` called on line 31 of `__main__.py` inside `main()`
- Both `DictationSession` (line 47) and `CommandSession` (line 74) present in `app.py`
