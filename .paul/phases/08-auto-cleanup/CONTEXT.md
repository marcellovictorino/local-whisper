---
phase: 08-auto-cleanup
status: pre-plan
created: 2026-04-28
---

# Phase 8: Auto-Cleanup

## Goals

1. Remove filler words (`um`, `uh`, `like`, `you know`, `actually`, `basically`, `so`, `right`, `well`) from every transcription before paste
2. Collapse immediate word repetitions (`I I need` → `I need`)
3. Always-on by default — opt-out via `[auto_cleanup] enabled = false` in `config.toml`
4. Zero new deps, fully offline, negligible latency

## Approach

- Rule-based post-processing: regex filler strip + repetition collapse
- Pipeline position: transcribe → **auto-cleanup** → snippets → corrections → paste
- Config: `[auto_cleanup]` section in `~/.config/local-whisper/config.toml`, `enabled = true` default
- Filler list hardcoded; may expose as user-configurable in config in future
- Reuse existing config loading pattern (same as snippets/corrections)

## Out of Scope

- Grammar fixes, rephrasing, sentence restructuring
- LLM-based cleanup (deferred to future phase — good candidate once rule-based baseline validated)
- Adaptive/learning cleanup

## Constraints

- Must not alter meaning — only remove known fillers and exact immediate repetitions
- Opt-out must be respected before any processing
- No new dependencies

## Open Questions

- Should filler list be user-extensible in config this phase, or hardcoded first?
- Repetition detection: only immediate (`I I`) or also near-duplicates (`I need I need`)?
