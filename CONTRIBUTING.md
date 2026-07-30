# Contributing to local-whisper

## Dev Setup

```bash
git clone <repo> local-whisper && cd local-whisper
uv sync --group dev
just test  # verify everything passes
just run   # verify the app works
```

Requirements: macOS Apple Silicon, [uv](https://docs.astral.sh/uv/), Accessibility permission granted to Terminal.

Task tracking uses the [`td`](https://github.com/gtayl0r/td) CLI (`brew install td`). Run `td usage --new-session` at the start of a session to see current focus and next work; state is local under a gitignored `.todos/`. See [docs/agents/issue-tracker.md](docs/agents/issue-tracker.md).

## Project Structure

```
src/local_whisper/
  audio.py       # microphone capture (sounddevice)
  transcribe.py  # STT inference (mlx-whisper default; parakeet-mlx opt-in)
  hotkey.py      # Right ⌘ / Right ⌥ global listener (pynput)
  clipboard.py   # write + paste via osascript
  app.py         # orchestrates the full flow
  overlay.py     # NSPanel recording pill (PyObjC)
  __main__.py    # CLI entry point

tests/           # pytest — run with: just test
scripts/         # standalone dev-tooling CLIs (e.g. validate_config.py)
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
- [ ] PR title follows [Conventional Commits](https://www.conventionalcommits.org/) (see below)

## Releases

PRs are squash-merged, so **the PR title becomes the commit message on `master`**. [python-semantic-release](https://python-semantic-release.readthedocs.io/) reads that history after every push to `master`. When it finds a releasable commit, CI opens or updates a `release/next` pull request containing the version bump (`pyproject.toml` + `src/local_whisper/__init__.py`) and [CHANGELOG.md](CHANGELOG.md). Review and merge that release pull request like any other PR. Its merge causes CI to create the matching git tag and GitHub Release; the bot never writes directly to `master`.

This makes the original PR title load-bearing, not cosmetic. Use a [Conventional Commits](https://www.conventionalcommits.org/) type:

| Prefix | Effect |
|--------|--------|
| `feat:` | minor version bump |
| `fix:`, `perf:` | patch version bump |
| `feat!:`, or `BREAKING CHANGE:` in the body | major version bump (or minor, while pre-1.0 — see `major_on_zero` in `pyproject.toml`) |
| `chore:`, `ci:`, `docs:`, `refactor:`, `style:`, `test:`, `build:` | no version bump, no changelog entry |

A PR title lint (`.github/workflows/pr-title-lint.yml`) enforces this format — an unparseable title fails loudly at PR time instead of silently producing no release later. Do not change the generated release pull request title: `chore(release): <version>` is how CI recognises its approved merge and publishes that version.

## Constraints

- **macOS Apple Silicon only** — no cross-platform abstractions needed
- **No new runtime deps** without discussion — keep install simple
- **Core dictation stays local and offline** — LLM features (command mode, adapt mode) are opt-in via API key and must degrade gracefully without one
- **Config files** go in `~/.config/local-whisper/` (XDG-style)
