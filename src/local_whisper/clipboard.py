import logging
import subprocess
import time

import pyperclip

logger = logging.getLogger("local_whisper")


def write_and_paste(text: str, *, settle_ms: int = 0, retries: int = 0) -> None:
    """Write text to clipboard and paste it at the active cursor position.

    Writes via pyperclip then sends Cmd+V via osascript. Falls back to
    copy-only if all attempts fail.

    Args:
        text: Text to paste.
        settle_ms: Milliseconds to wait before sending Cmd+V (allows app focus to settle).
        retries: Number of additional attempts after the first failure.
    """
    pyperclip.copy(text)
    if settle_ms > 0:
        time.sleep(settle_ms / 1000)

    last_exc: subprocess.CalledProcessError | None = None
    for attempt in range(1 + retries):
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
            return
        except subprocess.CalledProcessError as exc:
            last_exc = exc
            if attempt < retries:
                time.sleep(0.1)

    stderr_msg = last_exc.stderr.decode().strip() if last_exc and last_exc.stderr else ""
    logger.warning(
        "Paste via osascript failed (after %d attempt(s)): %s — text copied to clipboard, paste manually with Cmd+V.",
        1 + retries,
        stderr_msg,
    )
