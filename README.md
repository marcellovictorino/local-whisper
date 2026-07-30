# local-whisper

[![CI](https://github.com/marcellovictorino/local-whisper/actions/workflows/ci.yml/badge.svg)](https://github.com/marcellovictorino/local-whisper/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/github/license/marcellovictorino/local-whisper)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue)](pyproject.toml)
[![Platform: macOS arm64](https://img.shields.io/badge/platform-macOS%20arm64-lightgrey)](#requirements)

Offline speech-to-text on macOS. Hold Right ⌘, speak, release — transcribed text pastes at your cursor. No cloud, no subscription, no internet required.

Runs natively on Apple Silicon via MLX. Default model: whisper-small.en (English, ~250 MB, ~500ms inference).

## Requirements

- macOS with Apple Silicon (M1/M2/M3/M4+)
- [uv](https://docs.astral.sh/uv/) — Python package manager
- [just](https://github.com/casey/just) — command runner
- Accessibility permission for the process running local-whisper

## Install

```bash
git clone https://github.com/marcellovictorino/local-whisper && cd local-whisper && bash setup.sh
```

`setup.sh` does everything in one shot:
1. Installs Python dependencies via `uv sync`
2. Pre-downloads the model (~250 MB default, only happens once)
3. Installs a launchd service that starts local-whisper automatically on login

After install, grant Accessibility permission when prompted — see [Accessibility permission](#accessibility-permission) below.

## Usage

Once installed, local-whisper runs in the background automatically.

| Action | Result |
|--------|--------|
| Hold Right ⌘ | White pill — dictation mode |
| Release Right ⌘ | Transcription pastes at cursor |
| Hold Right ⌘ (text selected) | Amber pill — command mode |
| Release Right ⌘ | Voice instruction applied to selection, result pastes |
| Hold Right ⌥ | Cyan pill — adapt mode |
| Release Right ⌥ | Transcription reshaped for the frontmost app, pastes at cursor |

**Command mode** activates automatically when you have text selected — no separate key to remember. Select a paragraph, hold Right ⌘, say "fix the grammar", release — done.

**Adapt mode** is explicit: hold Right ⌥ instead of Right ⌘ when you want LLM reshaping (e.g. format as email). Plain dictation never calls an LLM and stays fast and fully local. Selection is ignored in adapt mode.

## How-To

<details>
<summary><strong>Snippet expansion</strong> — spoken shorthand → predefined text</summary>

### What it does

After transcription, spoken keywords matching entries in your config are replaced with predefined expansions before pasting. Matching is case-insensitive and works anywhere within the transcription.

**Example:** say _"reach me at my email"_ → pastes _"reach me at you@example.com"_

### Setup

Create the config file (run once):

```bash
mkdir -p ~/.config/local-whisper && cat > ~/.config/local-whisper/config.toml << 'EOF'
[snippets]
"my email" = "you@example.com"
brb = "be right back"
omw = "on my way"
EOF
```

Changes take effect immediately — no restart needed.

### Config format

```toml
[snippets]
# Single-word keys
brb = "be right back"

# Multi-word keys (use quotes)
"my email" = "you@example.com"
"my address" = "123 Main St, Springfield"

# Keys with special characters (use quotes)
"c++" = "C plus plus"

# Multi-line values
"email sig" = """
Best regards,
Your Name
your@email.com"""
```

Keys are matched **case-insensitively**. `BRB`, `brb`, and `Brb` all expand the same entry.

### Invalid configuration

A malformed `config.toml` shows a brief red startup overlay when local-whisper starts. The overlay appears once per startup; valid, empty, and missing config files do not show it.

From the repository checkout, validate the file and use the reported path, line, and column to correct the TOML:

```bash
just validate-config
```

Run the command again after editing. A valid or missing config exits successfully; invalid TOML exits with an error.

</details>

<details>
<summary><strong>Personal corrections</strong> — fix consistent ASR mishearings</summary>

### What it does

After transcription, whole-word corrections are applied before pasting. Useful for fixing model quirks — words it consistently mishears.

**Example:** Whisper writes _"open a I"_ → corrects to _"OpenAI"_

### Setup

Add a `[corrections]` section to `~/.config/local-whisper/config.toml`:

```toml
[corrections]
# wrong = "right"
"open a I" = "OpenAI"
whisper = "Whisper"
```

Matching is case-insensitive and whole-word only — `"open"` won't match `"openly"`.

Changes take effect immediately — no restart needed. To reload without waiting, send SIGHUP to the process:

```bash
kill -HUP $(pgrep -f local_whisper)
```

</details>

<details>
<summary><strong>Auto-cleanup</strong> — remove filler words and repeated phrases</summary>

### What it does

After transcription, filler words and immediate word repetitions are stripped before pasting.

- Removes: _um, uh, er, ah, hmm, you know_
- Collapses: _"the the meeting"_ → _"the meeting"_

Enabled by default — no setup needed.

### Disable

Add to `~/.config/local-whisper/config.toml`:

```toml
[auto_cleanup]
enabled = false
```

Changes take effect immediately — no restart needed.

</details>

<details>
<summary><strong>Command mode</strong> — apply a voice instruction to selected text</summary>

### What it does

Select any text, hold Right ⌘, speak an instruction, release — the transformed text replaces the selection.

**Examples:**
- Select a paragraph → say _"summarize as TLDR"_ → bullet-point summary pastes
- Select a sentence → say _"fix the grammar"_ → corrected sentence pastes
- Select code → say _"add docstring"_ → documented version pastes

### Setup

Set your API key (add to `~/.zshrc` or `~/.bash_profile`):

```bash
export LOCAL_WHISPER_OPENAI_API_KEY=sk-...
```

Re-run setup so the daemon picks up the new env var (launchd does not read your shell profile):

```bash
bash setup.sh
```

### Providers

Any OpenAI-compatible API works.

**OpenAI (default)**
```bash
export LOCAL_WHISPER_OPENAI_API_KEY=sk-...
export LOCAL_WHISPER_COMMAND_MODEL=gpt-5-nano      # fast and cheap
# export LOCAL_WHISPER_COMMAND_MODEL=gpt-5-mini    # higher quality
```

**Google Gemini (free tier available)**
```bash
# Get a free key at aistudio.google.com
export LOCAL_WHISPER_OPENAI_API_KEY=AIza...
export LOCAL_WHISPER_OPENAI_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai/
export LOCAL_WHISPER_COMMAND_MODEL=gemini-2.0-flash
```

**Ollama (fully local, no API key needed)**
```bash
# Start Ollama first: ollama serve
export LOCAL_WHISPER_OPENAI_API_KEY=ollama   # any non-empty string
export LOCAL_WHISPER_OPENAI_BASE_URL=http://localhost:11434/v1
export LOCAL_WHISPER_COMMAND_MODEL=llama3.2
```

If `LOCAL_WHISPER_OPENAI_API_KEY` is not set, command mode falls back to pasting the raw transcription — no crash.

</details>

<details>
<summary><strong>Adapt mode</strong> — reshape transcription for the frontmost app (Right ⌥)</summary>

### What it does

Hold **Right ⌥** instead of Right ⌘ to dictate with LLM reshaping. The transcription is rewritten using a prompt picked by whichever app is in focus: emails come out formal and structured, Slack messages get cleaned up but stay casual. Apps without a configured prompt get a generic cleanup prompt (punctuation, paragraphs, small fixes).

The recording pill is **cyan** in adapt mode. Plain dictation (Right ⌘) never calls an LLM.

### Setup

Requires the same API key as command mode. If command mode is already set up, nothing extra is needed.

```bash
export LOCAL_WHISPER_OPENAI_API_KEY=sk-...   # or OPENAI_API_KEY
bash setup.sh                                # re-snapshot env into the daemon
```

### Built-in presets

| App | Behaviour |
|-----|-----------|
| Slack | Clean up punctuation and paragraphs, keep conversational tone |
| Mail, Notion Mail, Mimestream, Spark, Superhuman, Airmail 5 | Professional email, fixed grammar, clear paragraphs |
| Any other app | Generic cleanup prompt |

### Custom prompts

Override a built-in or add any new app in `~/.config/local-whisper/config.toml`:

```toml
# Single app
[auto_adapt.notion]
app = "Notion"
prompt = "Structured notes with headers and bullet points."

# Multiple apps sharing one prompt
[auto_adapt.email]
apps = ["Mail", "Notion Mail", "Mimestream"]
prompt = "Formal French email. Fix grammar, clear paragraphs."
```

`apps = [...]` applies one prompt to multiple apps. Config overrides always win over built-in presets. Changes take effect immediately — no restart needed.

If the LLM is unavailable, adapt mode pastes the cleaned raw transcription instead — no crash.

</details>

## Model

MLX-native inference on Apple Neural Engine + GPU, via [mlx-whisper](https://github.com/ml-explore/mlx-examples/tree/main/whisper) (default) or [parakeet-mlx](https://github.com/senstella/parakeet-mlx) (opt-in).

Default: **whisper-small.en-mlx** (~250 MB, English only, ~500ms latency).

### Changing the model

Add a `[whisper]` section to `~/.config/local-whisper/config.toml`:

```toml
[whisper]
model = "mlx-community/whisper-large-v3-turbo"
```

Restart the service to apply:

```bash
just stop && just start
```

### Supported models

| Model | Size | Languages | Speed | Accuracy | Best for |
|-------|------|-----------|-------|----------|----------|
| `mlx-community/whisper-small.en-mlx` *(default)* | ~250 MB | English only | ⚡⚡⚡ fast | ★★★★ | Best latency/accuracy balance; ~500ms on real speech |
| `mlx-community/distil-whisper-large-v3` | ~600 MB | English only | ⚡⚡ moderate | ★★★★ | Higher accuracy; ~1.3s on real speech |
| `mlx-community/whisper-large-v3-turbo` | ~1.5 GB | 99 languages | ⚡ slow | ★★★★★ | Multilingual or highest accuracy required |
| `mlx-community/parakeet-tdt-0.6b-v2` | ~600 MB | English only | ⚡⚡⚡ fastest | unbenchmarked | Experimental; requires optional install (see below) |

**Parakeet** is opt-in and unbenchmarked on this repo's test audio (no WER row below yet). It requires an optional dependency and `ffmpeg` (used internally to load audio):

```bash
brew install ffmpeg
uv sync --extra parakeet
```

Then set the model in config and restart:

```toml
[whisper]
model = "mlx-community/parakeet-tdt-0.6b-v2"
```

Note: vocabulary seeding from `[corrections]` (biasing the decoder toward your terms) only works on whisper models — parakeet still applies corrections as post-processing.

To switch to multilingual/higher accuracy:

```toml
[whisper]
model = "mlx-community/whisper-large-v3-turbo"
```

To switch back to the default, remove the `[whisper]` section or set it explicitly:

```toml
[whisper]
model = "mlx-community/whisper-small.en-mlx"
```

Models download automatically on first use (once, to `~/.cache/huggingface/hub/`).

### Model benchmark history

Benchmarked 2026-05-13 on 30s real-speech audio (49 words, English, technical vocabulary including `Tmux`, `NeoVim`, `dbt`).

| Model | Size | WER% | Latency | Verdict |
|-------|------|------|---------|---------|
| `mlx-community/whisper-small.en-mlx` | 250 MB | **16.3%** | **508ms** | ✅ Default — strict improvement over distil-large |
| `mlx-community/distil-whisper-large-v3` | 600 MB | 18.4% | 1,268ms | Prior default; superseded |
| `mlx-community/whisper-base.en-mlx` | 150 MB | 28.6% | 163ms | ❌ WER too high for dictation |
| `mlx-community/whisper-tiny.en-mlx` | 75 MB | 32.6% | 116ms | ❌ WER too high; mangled technical terms |

## Roadmap

| Phase | Feature | Status |
|-------|---------|--------|
| 1 | Core transcription pipeline (mlx-whisper + sounddevice) | ✅ v0.1 |
| 2 | Right ⌘ hold-to-record + clipboard paste | ✅ v0.1 |
| 3 | Frosted-glass recording indicator overlay | ✅ v0.1 |
| 4 | launchd auto-start + bash install script | ✅ v0.1 |
| 5 | Snippet expansion (spoken keywords → predefined text) | ✅ v0.2 |
| 6 | Personal corrections (fix consistent ASR mishearings) | ✅ v0.2 |
| 7 | Command mode (apply spoken prompt to selected text) | ✅ v0.2 |
| 8 | Auto-cleanup (filler word removal, repetition collapse) | ✅ v0.3 |
| 9 | Auto-adapt (app-aware LLM text reshaping, cyan pill) | ✅ v0.4 |
| 10 | Configurable model — distil-whisper default, config override | ✅ v0.5 |
| 11 | Parakeet backend — optional faster English-only inference | ✅ v0.6 |
| 12 | Model pre-load at startup — first keypress instant after warm-up | ✅ v0.6 |
| 13 | Explicit adapt hotkey (Right ⌥) + per-stage session timing | ✅ v0.12 |

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Task tracking uses the [`td`](https://github.com/gtayl0r/td) CLI (`brew install td`); run `td usage --new-session` to see current work. State lives in a local, gitignored `.todos/` — see [docs/agents/issue-tracker.md](docs/agents/issue-tracker.md).

Releases are versioned and tagged automatically from [Conventional Commits](https://www.conventionalcommits.org/) on merge to `master` — see [CHANGELOG.md](CHANGELOG.md) and [Releases](https://github.com/marcellovictorino/local-whisper/releases).

## Troubleshooting

### uv not installed

```
Error: uv is not installed.
```

Install uv, then re-run the install command:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Restart your terminal after install so `uv` is on your PATH.

---

### Accessibility permission

local-whisper synthesises keystrokes to paste transcribed text, which macOS
gates behind Accessibility permission. macOS does not allow this grant to be
automated — it must be done once by hand.

On first run the service pops a system dialog and adds itself to the
Accessibility list. The service runs the venv Python interpreter directly, so
it is the `Python` entry — not Terminal, not `uv` — that needs the grant:

```
System Settings → Privacy & Security → Accessibility → enable "Python"
```

No manual restart needed — after you grant it, the service exits and launchd
respawns a fresh process that picks up the permission, within ~30s. If the
dialog didn't appear:

```bash
open "x-apple.systempreferences:com.apple.preference.security?Privacy_Accessibility"
# enable the entry for <repo>/.venv/bin/python
```

---

### Service not running

```bash
just status   # check if running
just logs     # see recent output
just run      # run in foreground for debugging (Ctrl+C to quit)
```

Common causes:
- Accessibility permission not granted (see above)
- `launchctl list | grep local-whisper` shows exit code `1`

Re-run `bash setup.sh` to reinstall the service cleanly.

---

### Model download hangs or fails

The model downloads once to `~/.cache/huggingface/hub/` (default: ~250 MB). If interrupted, re-run:

```bash
bash setup.sh
```

`setup.sh` is idempotent — safe to run multiple times.

## Updating

After merging changes, re-run setup **from the canonical clone** — never from a git worktree:

```bash
cd ~/path/to/local-whisper && git pull && bash setup.sh
```

The launchd plist hard-codes the directory `setup.sh` is run from. If that directory is an ephemeral worktree that later gets deleted, the daemon silently dies. `setup.sh` warns and asks for confirmation when run from a linked worktree.
