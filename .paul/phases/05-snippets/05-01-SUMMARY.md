---
phase: 05-snippets
plan: 01
status: complete
---

## What was built

- `src/local_whisper/snippets.py` — `_load()` reads `[snippets]` section from `~/.config/local-whisper/config.toml` (shared with corrections). `expand()` does regex-based multi-key substitution in a single pass, longer keys win on overlap, case-insensitive.
- `src/local_whisper/app.py` — snippets imported, `expand()` called after `corrections.apply()` in `_record_and_process()`. SIGHUP handler calls `_reload_config()` which reloads both corrections and snippets.
- `tests/test_snippets.py` — unit tests covering load, expand, case-insensitivity, multi-word keys, and no-match passthrough.

## Adaptation notes

- Plan assumed a separate `snippets.toml`; implementation consolidated into `config.toml` alongside `[corrections]` for simpler UX.
- `expand()` uses regex multi-substitution (not simple dict.get) to support partial-match expansion within longer transcriptions.
- Config reloads on every transcription call (not just SIGHUP) since `_load()` is called inside `expand()`.

## Test result

All tests passed.

## AC coverage

- AC-1: exact match expansion ✓
- AC-2: case-insensitive matching ✓
- AC-3: no match passes through unchanged ✓
- AC-4: missing config is safe (returns empty dict) ✓
- AC-5: hot-reload — config reloads on every transcription ✓
