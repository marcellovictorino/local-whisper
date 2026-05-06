import logging
import subprocess

import pyperclip

logger = logging.getLogger("local_whisper")


def write_and_paste(text: str) -> None:
    """Write text to clipboard and paste it at the active cursor position.

    Writes via pyperclip then sends Cmd+V via osascript. Falls back to
    copy-only if osascript fails (e.g. no focused text field).

    Args:
        text: Text to paste.
    """
    pyperclip.copy(text)
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
        logger.info("Pasted %d chars.", len(text))
    except subprocess.CalledProcessError as exc:
        stderr_msg = exc.stderr.decode().strip() if exc.stderr else ""
        logger.warning(
            "Paste via osascript failed: %s — text copied to clipboard, paste manually with Cmd+V.",
            stderr_msg,
        )
