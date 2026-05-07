"""Command mode — capture current text selection via macOS clipboard."""

from __future__ import annotations

import logging
import subprocess
import time

import pyperclip

from local_whisper._macos import HAS_APPKIT
from local_whisper._macos import NSPasteboard as _NSPasteboard

logger = logging.getLogger("local_whisper")


def get_selection() -> str:
    """Return the current text selection, or empty string if nothing is selected.

    Uses NSPasteboard.changeCount() to detect whether Cmd+C actually wrote to
    the pasteboard — unlike string comparison, this correctly handles the case
    where the selected text is identical to what was already in the clipboard
    (e.g. immediately after dictation).

    Falls back to string comparison if AppKit is unavailable.

    Returns:
        Selected text, or empty string if nothing is selected or on failure.
    """
    if HAS_APPKIT:
        pb = _NSPasteboard.generalPasteboard()
        count_before = pb.changeCount()
    else:
        previous = pyperclip.paste()

    try:
        subprocess.run(
            [
                "osascript",
                "-e",
                'tell application "System Events" to keystroke "c" using command down',
            ],
            check=True,
            capture_output=True,
        )
        time.sleep(0.1)
    except Exception as exc:
        logger.error("get_selection failed: %s", exc)
        return ""

    if HAS_APPKIT:
        if pb.changeCount() > count_before:
            return pb.stringForType_("public.utf8-plain-text") or ""
        return ""

    current = pyperclip.paste()
    return current if current != previous else ""
