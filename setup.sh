#!/usr/bin/env bash
set -euo pipefail

# local-whisper — one-shot install script
# Usage: bash setup.sh
# Or:    git clone <repo> && cd local-whisper && bash setup.sh

# --- Prerequisites ---

if [[ "$(uname)" != "Darwin" ]]; then
    echo "Error: local-whisper requires macOS." >&2
    exit 1
fi

if ! command -v uv &>/dev/null; then
    echo "Error: uv is not installed." >&2
    echo "" >&2
    echo "Install uv first:" >&2
    echo "  curl -LsSf https://astral.sh/uv/install.sh | sh" >&2
    echo "" >&2
    echo "Then re-run: bash setup.sh" >&2
    exit 1
fi

# --- Install Python dependencies ---

echo "Installing dependencies..."
uv sync

# The parakeet backend is opt-in: only pulled in (with its ffmpeg requirement)
# when config.toml resolves to it. Ask the code, not a grep — it owns the
# model → backend mapping.
if uv run python -c "
from local_whisper.transcribe import Backend, get_backend, get_model
import sys
sys.exit(0 if get_backend(get_model()) == Backend.PARAKEET else 1)
"; then
    if ! command -v ffmpeg &>/dev/null; then
        echo "Error: config.toml selects a parakeet model, which requires ffmpeg." >&2
        echo "" >&2
        echo "Install ffmpeg first:" >&2
        echo "  brew install ffmpeg" >&2
        echo "" >&2
        echo "Then re-run: bash setup.sh" >&2
        exit 1
    fi
    echo "Parakeet model configured — installing parakeet extra..."
    uv sync --extra parakeet
fi

# --- Pre-download model ---

echo ""
uv run python -c "
from local_whisper.transcribe import get_model, _model_is_cached, _MODEL_SIZES
model = get_model()
size = _MODEL_SIZES.get(model, 'unknown size')
print(f'Checking model cache (may download {size} on first run)...', flush=True)
if _model_is_cached(model):
    print('Model already cached.', flush=True)
else:
    print(f'Downloading model (one-time, {size})...', flush=True)
    from huggingface_hub import snapshot_download
    snapshot_download(model)
"
echo "Model ready."

# --- Write and load launchd plist ---

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# The plist hard-codes PROJECT_DIR. A linked worktree gets deleted eventually,
# leaving the daemon pointing at a dead path — refuse unless explicitly confirmed.
if [[ "$(git -C "$PROJECT_DIR" rev-parse --git-dir 2>/dev/null)" != "$(git -C "$PROJECT_DIR" rev-parse --git-common-dir 2>/dev/null)" ]]; then
    echo "WARNING: running from a linked git worktree ($PROJECT_DIR)." >&2
    echo "The daemon will break when this worktree is deleted. Re-run from the canonical clone." >&2
    read -r -p "Continue anyway? [y/N] " _ans
    [[ "$_ans" == [yY]* ]] || exit 1
fi

UV_BIN="$(which uv)"
PLIST_NAME="com.local-whisper"
PLIST_DEST="$HOME/Library/LaunchAgents/$PLIST_NAME.plist"
LOG_FILE="$HOME/Library/Logs/local-whisper.log"

mkdir -p "$HOME/Library/LaunchAgents" "$HOME/Library/Logs"

# Snapshot LLM-related env vars from the current shell into the plist.
# launchd agents do not inherit ~/.zshrc / ~/.bashrc environment.
LLM_ENV_VARS=""
for _var in OPENAI_API_KEY LOCAL_WHISPER_OPENAI_API_KEY LOCAL_WHISPER_COMMAND_MODEL LOCAL_WHISPER_OPENAI_BASE_URL; do
    _val="${!_var:-}"
    if [[ -n "$_val" ]]; then
        LLM_ENV_VARS="${LLM_ENV_VARS}        <key>${_var}</key><string>${_val}</string>
"
    fi
done

cat > "$PLIST_DEST" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key><string>$PLIST_NAME</string>
    <key>ProgramArguments</key>
    <array>
        <string>$UV_BIN</string>
        <string>run</string>
        <string>--project</string>
        <string>$PROJECT_DIR</string>
        <string>python</string>
        <string>-m</string>
        <string>local_whisper</string>
        <string>--run</string>
    </array>
    <key>RunAtLoad</key><true/>
    <key>KeepAlive</key><true/>
    <key>ThrottleInterval</key><integer>30</integer>
    <key>WorkingDirectory</key><string>$PROJECT_DIR</string>
    <key>StandardOutPath</key><string>$LOG_FILE</string>
    <key>StandardErrorPath</key><string>$LOG_FILE</string>
    <key>EnvironmentVariables</key>
    <dict>
        <key>PYTHONWARNINGS</key>
        <string>ignore::UserWarning:multiprocessing</string>
        <key>PATH</key>
        <string>$PATH</string>
${LLM_ENV_VARS}    </dict>
</dict>
</plist>
PLIST

launchctl bootout "gui/$(id -u)" "$PLIST_DEST" 2>/dev/null || true
launchctl bootstrap "gui/$(id -u)" "$PLIST_DEST"

# --- Done ---

echo ""
echo "✓ local-whisper installed. Starts automatically on login."
echo ""
echo "LLM env vars captured in daemon (auto-adapt + command mode):"
_captured=0
for _var in OPENAI_API_KEY LOCAL_WHISPER_OPENAI_API_KEY LOCAL_WHISPER_COMMAND_MODEL LOCAL_WHISPER_OPENAI_BASE_URL; do
    if [[ -n "${!_var:-}" ]]; then
        echo "  ✓ $_var"
        _captured=$((_captured + 1))
    fi
done
if [[ $_captured -eq 0 ]]; then
    echo "  ✗ None found — set OPENAI_API_KEY in your shell and re-run setup.sh to enable LLM features."
fi
echo ""
echo "IMPORTANT: Grant Accessibility permission to complete setup:"
echo "  System Settings → Privacy & Security → Accessibility"
echo "  Add and enable the process running local-whisper"
echo "  (Terminal, or the uv binary: $UV_BIN)"
echo ""
echo "Logs: $LOG_FILE"
echo "To uninstall: just uninstall  (or: launchctl bootout gui/$(id -u) $PLIST_DEST && rm $PLIST_DEST)"
