# Contributing to local-whisper

## Dev Setup

```bash
git clone <repo> local-whisper && cd local-whisper
uv sync --group dev
just test  # verify everything passes
just run   # verify the app works
```

Requirements: macOS Apple Silicon, [uv](https://docs.astral.sh/uv/), Accessibility permission granted to Terminal.

## Project Structure

```
src/local_whisper/
  audio.py       # microphone capture (sounddevice)
  transcribe.py  # mlx-whisper inference
  hotkey.py      # Right ⌘ global listener (pynput)
  clipboard.py   # write + paste via osascript
  app.py         # orchestrates the full flow
  overlay.py     # NSPanel recording pill (PyObjC)
  __main__.py    # CLI entry point

tests/           # pytest — run with: just test
setup.sh         # one-shot install (launchd service)
justfile         # day-to-day ops
```

## How Issues Are Structured

Each feature issue includes:
- **What** — user-facing description
- **Acceptance Criteria** — Gherkin scenarios, directly testable
- **Scope** — exact files to create/modify
- **Out of scope** — explicit boundaries

Issues labelled `agent-ready` have a pre-written PAUL plan at `.paul/phases/XX-name/XX-01-PLAN.md`. These can be executed autonomously.

## Implementing a Feature

### With a pre-written plan (agent-ready issues)

```bash
git checkout -b feat/issue-N-short-name
# In Claude Code:
/paul:apply .paul/phases/XX-name/XX-01-PLAN.md
```

### Without a pre-written plan

```bash
git checkout -b feat/issue-N-short-name
# In Claude Code:
/paul:plan  # generates a plan from the issue spec
/paul:apply .paul/phases/XX-name/XX-01-PLAN.md
```

### Autonomous overnight run

```bash
claude --dangerously-skip-permissions \
  -p "/paul:apply .paul/phases/XX-name/XX-01-PLAN.md"
```

This runs to completion, commits, and exits. Open a PR in the morning.

## PR Checklist

- [ ] `just test` passes
- [ ] `just run` — manual smoke test (hold Right ⌘, speak, release)
- [ ] No new dependencies added without discussion
- [ ] No changes to `overlay.py` or `hotkey.py` unless the issue explicitly requires it

## Constraints

- **macOS Apple Silicon only** — no cross-platform abstractions needed
- **No new runtime deps** without discussion — keep install simple
- **No cloud calls** — all processing must be local and offline
- **Config files** go in `~/.config/local-whisper/` (XDG-style)
