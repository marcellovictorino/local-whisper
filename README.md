# local-whisper

Offline speech-to-text on macOS. Hold Right ⌘, speak, release — transcribed text pastes at your cursor. No cloud, no subscription, no internet required.

Built on [mlx-whisper](https://github.com/ml-explore/mlx-examples/tree/main/whisper) (whisper-large-v3-turbo) running natively on Apple Silicon via MLX.

## Requirements

- macOS with Apple Silicon (M1/M2/M3/M4+)
- [uv](https://docs.astral.sh/uv/) — Python package manager
- Accessibility permission for the process running local-whisper

## Install

```bash
git clone <repo-url> local-whisper
cd local-whisper
bash setup.sh
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
| Hold Right ⌥ | Recording pill (⚡) appears — command mode |
| Release Right ⌥ | Voice instruction applied to selected text, result pastes |

### Command mode

Command mode lets you speak an instruction and apply it to whatever text you have selected. Select a paragraph, hold Right ⌥, say "fix the grammar", release — done.

Requires the `command` optional dependency and an API key:

```bash
uv sync --extra command
```

Set these environment variables (add to `~/.zshrc` or `~/.bash_profile`):

```bash
# Required — your API key
export LOCAL_WHISPER_OPENAI_API_KEY=sk-...

# Optional — override the default model (default: gpt-4o-mini)
export LOCAL_WHISPER_COMMAND_MODEL=gpt-4o-mini

# Optional — use a different provider (see below)
export LOCAL_WHISPER_OPENAI_BASE_URL=https://...
```

#### Providers

Any OpenAI-compatible API works. Set `LOCAL_WHISPER_OPENAI_BASE_URL` to point at a different provider:

**OpenAI (default — no base URL needed)**
```bash
export LOCAL_WHISPER_OPENAI_API_KEY=sk-...
export LOCAL_WHISPER_COMMAND_MODEL=gpt-4o-mini   # or gpt-4o, o4-mini, etc.
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

### Day-to-day commands (requires [just](https://github.com/casey/just))

```bash
just install    # Install / reinstall service
just uninstall  # Remove service completely
just start      # Start service (without reinstalling)
just stop       # Stop service (without uninstalling)
just status     # Check if service is running
just run        # Run in foreground — useful for debugging (Ctrl+C to quit)
just logs       # Stream service logs
```

### Without just

```bash
bash setup.sh                                              # install
launchctl stop com.local-whisper                           # stop
launchctl start com.local-whisper                          # start
launchctl unload ~/Library/LaunchAgents/com.local-whisper.plist && \
  rm ~/Library/LaunchAgents/com.local-whisper.plist        # uninstall
tail -f ~/Library/Logs/local-whisper.log                   # logs
```

## Roadmap

| Phase | Feature | Status |
|-------|---------|--------|
| 1 | Core transcription pipeline (mlx-whisper + sounddevice) | ✅ v0.1 |
| 2 | Right ⌘ hold-to-record + clipboard paste | ✅ v0.1 |
| 3 | Frosted-glass recording indicator overlay | ✅ v0.1 |
| 4 | launchd auto-start + bash install script | ✅ v0.1 |
| — | Snippet expansion (spoken keywords → predefined text) | v0.2 |
| — | Personal dictionary (learned corrections) | v0.2 |
| 7 | Command mode (apply spoken prompt to selected text) | ✅ v0.2 |

## Troubleshooting

### uv not installed

```
Error: uv is not installed.
```

Install uv, then re-run `bash setup.sh`:

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

**Running via `just run` or terminal:** add Terminal (or iTerm2) to the Accessibility list.

**Running as a service (installed via `bash setup.sh`):** add the `uv` binary instead — launchd runs `uv` directly, not through a terminal.

To find the uv binary path:
```bash
which uv
```

Then in System Settings → Privacy & Security → Accessibility, click `+` and navigate to that path.

After granting permission, restart the service:
```bash
just stop && just start
```

---

### Service installed but not running

Check status:
```bash
launchctl list | grep local-whisper
```

Output format: `PID  ExitCode  Label`

- `12345  0  com.local-whisper` — running normally
- `-  1  com.local-whisper` — exited with error (likely Accessibility not granted)
- Not listed — service not loaded (re-run `bash setup.sh`)

Check logs for details:
```bash
just logs
```

---

### Model download hangs or fails

The model (~1.5 GB) is downloaded once to `~/.cache/huggingface/hub/`. If download is interrupted, re-run:

```bash
bash setup.sh
```

`setup.sh` is idempotent — safe to run multiple times.
