# local-whisper

Offline speech-to-text on macOS. Hold Right ⌘, speak, release — transcribed text pastes at your cursor. No cloud, no subscription, no internet required.

Built on [mlx-whisper](https://github.com/ml-explore/mlx-examples/tree/main/whisper) (whisper-large-v3-turbo) running natively on Apple Silicon via MLX.

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
2. Pre-downloads the model (~1.5 GB, only happens once)
3. Installs a launchd service that starts local-whisper automatically on login

After install, grant Accessibility permission when prompted — see [Accessibility permission](#accessibility-permission) below.

## Usage

Once installed, local-whisper runs in the background automatically.

| Action | Result |
|--------|--------|
| Hold Right ⌘ | Recording pill (⏺) appears — dictation mode |
| Release Right ⌘ | Transcription runs, text pastes at cursor |
| Select text, then hold Right ⌘ | Recording pill (⚡) appears — command mode |
| Release Right ⌘ | Voice instruction applied to selection, result pastes |

**Command mode** activates automatically when you have text selected — no separate key to remember. Select a paragraph, hold Right ⌘, say "fix the grammar", release — done.

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
<summary><strong>Command mode</strong> — apply a voice instruction to selected text</summary>

### What it does

Select any text, hold Right ⌘, speak an instruction, release — the transformed text replaces the selection.

**Examples:**
- Select a paragraph → say _"summarize as TLDR"_ → bullet-point summary pastes
- Select a sentence → say _"fix the grammar"_ → corrected sentence pastes
- Select code → say _"add docstring"_ → documented version pastes

### Setup

Install the command mode dependency:

```bash
uv sync --extra command
```

Set your API key (add to `~/.zshrc` or `~/.bash_profile`):

```bash
export LOCAL_WHISPER_OPENAI_API_KEY=sk-...
```

Restart the service to pick up the new env var:

```bash
just stop && just start
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

## Model

Uses **whisper-large-v3-turbo** via [mlx-whisper](https://github.com/ml-explore/mlx-examples/tree/main/whisper) — MLX-native, runs on Apple Neural Engine + GPU.

**Alternatives evaluated:**
- **Parakeet** (NVIDIA NeMo) — CUDA-optimized; CPU-only on Apple Silicon, no ANE/GPU acceleration → slower
- **distil-whisper** variants — MLX-native, ~6× faster with minor accuracy tradeoff; candidate for future config option

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

```
Accessibility permission required.
  1. Open: System Settings → Privacy & Security → Accessibility
  2. Add and enable the app running this script
  3. Re-run: uv run python -m local_whisper --run
```

**Running as a service (default):** add the `uv` binary — launchd runs `uv` directly.

```bash
which uv   # find the path, then add it in System Settings
```

After granting permission, restart the service:

```bash
just stop && just start
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

The model (~1.5 GB) downloads once to `~/.cache/huggingface/hub/`. If interrupted, re-run:

```bash
bash setup.sh
```

`setup.sh` is idempotent — safe to run multiple times.
