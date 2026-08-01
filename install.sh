#!/usr/bin/env bash
set -euo pipefail

# local-whisper — remote one-liner installer
# Usage: curl -fsSL https://raw.githubusercontent.com/marcellovictorino/local-whisper/master/install.sh | bash
#
# Bootstrap only: clones (or updates) the repo to a stable directory, then hands
# off to setup.sh, which does the real work (uv sync, model download, launchd).
# We do NOT duplicate setup.sh's checks (uv, ffmpeg) here — it owns them.

# --- Prerequisites ---

if [[ "$(uname)" != "Darwin" ]]; then
    echo "Error: local-whisper requires macOS." >&2
    exit 1
fi

if ! command -v git &>/dev/null; then
    echo "Error: git is not installed." >&2
    echo "" >&2
    echo "Install the Xcode command line tools first:" >&2
    echo "  xcode-select --install" >&2
    echo "" >&2
    echo "Then re-run the install command." >&2
    exit 1
fi

# --- Clone (or update) to a stable directory ---

# A STABLE path matters: setup.sh hard-codes this project dir into the launchd
# plist. A temporary/throwaway clone would leave the daemon pointing at a dead
# path once it's removed. Override with LOCAL_WHISPER_DIR if you keep the repo
# elsewhere — but re-run this same installer so setup.sh re-pins the new path.
DIR="${LOCAL_WHISPER_DIR:-$HOME/.local/share/local-whisper}"
REPO="https://github.com/marcellovictorino/local-whisper"

if [[ -d "$DIR/.git" ]]; then
    echo "Updating existing clone at $DIR..."
    git -C "$DIR" pull --ff-only
else
    echo "Cloning local-whisper to $DIR..."
    git clone "$REPO" "$DIR"
fi

# --- Hand off to setup.sh ---

cd "$DIR"
exec bash setup.sh
