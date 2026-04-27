---
phase: 06-corrections
plan: 01
status: complete
---

## What was built

- `src/local_whisper/corrections.py` — `load()` reads `~/.config/local-whisper/corrections.toml`, returns `dict[str, str]` with keys lowercased. `apply()` does whole-word, case-insensitive substitution via `re.sub` with `\b` boundaries.
- `src/local_whisper/app.py` — `corrections` imported, loaded at `__init__`, applied after `transcribe.run()`, `_reload_config()` method added with SIGHUP handler.
- `tests/test_corrections.py` — 10 unit tests covering all acceptance criteria.

## Adaptation note

Plan assumed `snippets.py` was already integrated. It lives on `mv/snippet-expansion-52c`, not on this branch. Corrections applied directly after `transcribe.run()` — ordering preserved once snippets merge.

## Test result

23 passed, 0 failed.

## AC coverage

- AC-1: word replacement ✓
- AC-2: case-insensitive match, exact-case replacement ✓
- AC-3: whole-word only (`\b` boundaries) ✓
- AC-4: missing config → empty dict, no error ✓
- AC-5: multiple corrections in one pass ✓
