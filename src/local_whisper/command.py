"""Command mode — apply spoken prompt to selected text via OpenAI-compatible API."""
from __future__ import annotations

import os
import subprocess
import sys
import time

import pyperclip


def copy_selection() -> str:
    """Copy the active selection to clipboard and return it.

    Sends Cmd+C to the frontmost app via osascript, then reads the clipboard.
    Returns empty string on failure.
    """
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
        time.sleep(0.1)  # give target app time to write the clipboard
        return pyperclip.paste()
    except Exception as exc:
        print(f"[local-whisper] copy_selection failed: {exc}", file=sys.stderr)
        return ""


def apply_command(selected_text: str, voice_command: str) -> str:
    """Apply voice command to selected text using an OpenAI-compatible API.

    Reads OPENAI_API_KEY from the environment. Optionally reads OPENAI_BASE_URL
    (for Gemini or other OpenAI-compatible providers) and LOCAL_WHISPER_MODEL
    to override the default model. Falls back to returning voice_command unchanged
    if the key is absent or the request fails.

    Args:
        selected_text: Text from the active selection (may be empty).
        voice_command: Transcribed instruction to apply.

    Returns:
        Transformed text, or voice_command if API is unavailable.
    """
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print(
            "[local-whisper] OPENAI_API_KEY not set — command mode unavailable.",
            file=sys.stderr,
        )
        return voice_command

    try:
        import openai
    except ImportError:
        print(
            "[local-whisper] openai package not installed. Run: uv add openai",
            file=sys.stderr,
        )
        return voice_command

    model = os.environ.get("LOCAL_WHISPER_MODEL", "gpt-4o-mini")
    base_url = os.environ.get("OPENAI_BASE_URL")

    try:
        client = openai.OpenAI(
            api_key=api_key,
            **({"base_url": base_url} if base_url else {}),
        )
        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Apply the instruction to the provided text. "
                        "Return only the transformed text — no explanation, no preamble."
                    ),
                },
                {
                    "role": "user",
                    "content": f"{voice_command}\n\n{selected_text}",
                },
            ],
            max_tokens=4096,  # generous ceiling for long-form edits
        )
        return response.choices[0].message.content or voice_command
    except Exception as exc:
        print(f"[local-whisper] Command mode error: {exc}", file=sys.stderr)
        return voice_command
