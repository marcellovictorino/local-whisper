import subprocess
import sys
import time

import pyperclip


def copy(text: str) -> None:
    """Write text to the system clipboard.

    Args:
        text: Text to copy.
    """
    pyperclip.copy(text)


def write_and_paste(text: str) -> None:
    """Write text to clipboard and paste it at the active cursor position.

    Writes via pyperclip then sends Cmd+V via osascript. Falls back to
    copy-only if osascript fails (e.g. no focused text field).

    Args:
        text: Text to paste.
    """
    copy(text)
    time.sleep(0.05)  # give clipboard time to settle before paste

    try:
        subprocess.run(
            [
                "osascript",
                "-e",
                'tell application "System Events" to keystroke "v" using command down',
            ],
            check=True,
            capture_output=True,
        )
        print(f"Pasted {len(text)} chars.", file=sys.stderr, flush=True)
    except subprocess.CalledProcessError as exc:
        print(
            f"[local-whisper] Paste via osascript failed: {exc.stderr.decode().strip()}\n"
            "  → Text copied to clipboard — paste manually with Cmd+V.",
            file=sys.stderr,
        )
