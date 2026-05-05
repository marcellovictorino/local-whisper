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

# --- Pre-download model ---

echo ""
uv run python -c "
from local_whisper.transcribe import DEFAULT_MODEL, _model_is_cached, _MODEL_SIZES
size = _MODEL_SIZES.get(DEFAULT_MODEL, 'unknown size')
print(f'Checking model cache (may download {size} on first run)...', flush=True)
if _model_is_cached(DEFAULT_MODEL):
    print('Model already cached.', flush=True)
else:
    print(f'Downloading model (one-time, {size})...', flush=True)
    from huggingface_hub import snapshot_download
    snapshot_download(DEFAULT_MODEL)
"
echo "Model ready."

# --- Write and load launchd plist ---

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
UV_BIN="$(which uv)"
PLIST_NAME="com.local-whisper"
PLIST_DEST="$HOME/Library/LaunchAgents/$PLIST_NAME.plist"
LOG_FILE="$HOME/Library/Logs/local-whisper.log"

mkdir -p "$HOME/Library/LaunchAgents" "$HOME/Library/Logs"

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
    <key>WorkingDirectory</key><string>$PROJECT_DIR</string>
    <key>StandardOutPath</key><string>$LOG_FILE</string>
    <key>StandardErrorPath</key><string>$LOG_FILE</string>
    <key>EnvironmentVariables</key>
    <dict>
        <key>PYTHONWARNINGS</key>
        <string>ignore::UserWarning:multiprocessing</string>
    </dict>
</dict>
</plist>
PLIST

launchctl bootout "gui/$(id -u)" "$PLIST_DEST" 2>/dev/null || true
launchctl bootstrap "gui/$(id -u)" "$PLIST_DEST"

# --- Done ---

echo ""
echo "✓ local-whisper installed. Starts automatically on login."
echo ""
echo "IMPORTANT: Grant Accessibility permission to complete setup:"
echo "  System Settings → Privacy & Security → Accessibility"
echo "  Add and enable the process running local-whisper"
echo "  (Terminal, or the uv binary: $UV_BIN)"
echo ""
echo "Logs: $LOG_FILE"
echo "To uninstall: just uninstall  (or: launchctl bootout gui/$(id -u) $PLIST_DEST && rm $PLIST_DEST)"
