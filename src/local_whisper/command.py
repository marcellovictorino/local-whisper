"""Command mode — apply spoken prompt to selected text via OpenAI-compatible API."""

from __future__ import annotations

import logging
import subprocess
import time

import pyperclip

try:
    from AppKit import NSPasteboard as _NSPasteboard

    _HAS_APPKIT = True
except Exception:
    _NSPasteboard = None
    _HAS_APPKIT = False

from local_whisper import llm

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
    if _HAS_APPKIT:
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

    if _HAS_APPKIT:
        if pb.changeCount() > count_before:
            return pb.stringForType_("public.utf8-plain-text") or ""
        return ""

    current = pyperclip.paste()
    return current if current != previous else ""


def apply_command(selected_text: str, voice_command: str) -> str:
    """Apply voice command to selected text using an OpenAI-compatible API.

    Reads LOCAL_WHISPER_OPENAI_API_KEY from the environment. Optionally reads
    LOCAL_WHISPER_OPENAI_BASE_URL (for Gemini or other OpenAI-compatible providers)
    and LOCAL_WHISPER_COMMAND_MODEL to override the default model. Falls back to returning
    voice_command unchanged if the key is absent or the request fails.

    Args:
        selected_text: Text from the active selection (may be empty).
        voice_command: Transcribed instruction to apply.

    Returns:
        Transformed text, or voice_command if API is unavailable.
    """
    return llm.apply_voice_command(selected_text, voice_command)
