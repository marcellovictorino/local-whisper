"""Auto-adapt: reshape transcription via LLM based on frontmost macOS app."""

from __future__ import annotations

import html
import os
import sys
import tomllib
from pathlib import Path

try:
    from AppKit import NSWorkspace as _NSWorkspace

    _HAS_APPKIT = True
except Exception:
    _NSWorkspace = None
    _HAS_APPKIT = False

try:
    import openai
except ImportError:
    openai = None  # type: ignore[assignment]


_CONFIG_PATH = Path.home() / ".config" / "local-whisper" / "config.toml"

_EMAIL_PROMPT = "Professional email. Fix grammar, clear paragraphs, formal tone."

_BUILTIN_PROMPTS: dict[str, str] = {
    "Slack": "Casual Slack message. Bullet points, short sentences, natural emojis.",
    "Mail": _EMAIL_PROMPT,
    "Notion Mail": _EMAIL_PROMPT,
    "Mimestream": _EMAIL_PROMPT,
    "Spark": _EMAIL_PROMPT,
    "Superhuman": _EMAIL_PROMPT,
    "Airmail 5": _EMAIL_PROMPT,
}


def get_active_app() -> str:
    """Return the localised name of the frontmost macOS application.

    Returns:
        App name, or empty string if AppKit unavailable or on any error.
    """
    if not _HAS_APPKIT:
        return ""
    try:
        app = _NSWorkspace.sharedWorkspace().frontmostApplication()
        return app.localizedName() or ""
    except Exception:
        return ""


def _get_prompt(app_name: str, section: dict) -> str | None:
    """Find prompt for app_name from config section or built-in presets.

    Checks config sub-sections first (each must have 'app' and 'prompt' keys),
    then falls back to _BUILTIN_PROMPTS.

    Args:
        app_name: Localised name of the frontmost app.
        section: Parsed [auto_adapt] config dict (may contain sub-dicts).

    Returns:
        Prompt string if a match is found, else None.
    """
    for value in section.values():
        if not isinstance(value, dict):
            continue
        apps = value.get("apps") or ([value.get("app")] if value.get("app") else [])
        if any(a.lower() == app_name.lower() for a in apps):
            prompt = value.get("prompt", "")
            if prompt:
                return prompt

    return _BUILTIN_PROMPTS.get(app_name)


def is_active(app_name: str, path: Path = _CONFIG_PATH) -> bool:
    """Return True if auto-adapt will reshape output for this app.

    Reads config at call time. Used to pick overlay colour at press time.
    Returns False if prerequisites (API key, openai package) are not met.

    Args:
        app_name: Localised name of the frontmost app.
        path: Path to config.toml.

    Returns:
        True if auto-adapt is enabled, a prompt exists, and LLM is available.
    """
    if not app_name:
        return False
    if openai is None:
        return False
    api_key = os.environ.get("LOCAL_WHISPER_OPENAI_API_KEY") or os.environ.get("OPENAI_API_KEY", "")
    if not api_key:
        return False
    try:
        with path.open("rb") as f:
            data = tomllib.load(f)
    except FileNotFoundError:
        return False
    except Exception as exc:
        print(f"[local-whisper] auto_adapt config error: {exc}", file=sys.stderr)
        return False
    section = data.get("auto_adapt", {})
    if not isinstance(section, dict) or not section.get("enabled", False):
        return False
    return _get_prompt(app_name, section) is not None


def apply(text: str, app_name: str = "", path: Path = _CONFIG_PATH) -> str:
    """Reshape transcription via LLM using per-app prompt if configured.

    Opt-in: does nothing unless [auto_adapt] enabled = true in config.
    Falls back to original text on any error, missing API key, or unknown app.

    Args:
        text: Transcribed text to reshape.
        app_name: Localised name of the frontmost app (captured at press time).
        path: Path to config.toml.

    Returns:
        Reshaped text, or original text if disabled, unmatched, or on error.
    """
    if not app_name:
        return text

    try:
        with path.open("rb") as f:
            data = tomllib.load(f)
    except FileNotFoundError:
        return text
    except Exception as exc:
        print(f"[local-whisper] auto_adapt config error: {exc}", file=sys.stderr)
        return text

    section = data.get("auto_adapt", {})
    if not isinstance(section, dict) or not section.get("enabled", False):
        return text

    prompt = _get_prompt(app_name, section)
    if prompt is None:
        return text

    api_key = os.environ.get("LOCAL_WHISPER_OPENAI_API_KEY") or os.environ.get("OPENAI_API_KEY", "")
    if not api_key:
        print(
            "[local-whisper] No OpenAI API key found. Set LOCAL_WHISPER_OPENAI_API_KEY or OPENAI_API_KEY env var.",
            file=sys.stderr,
        )
        return text

    if openai is None:
        print(
            "[local-whisper] auto-adapt dependencies not installed. Run: uv sync --extra command",
            file=sys.stderr,
        )
        return text

    model = os.environ.get("LOCAL_WHISPER_COMMAND_MODEL", "gpt-5-nano")
    base_url = os.environ.get("LOCAL_WHISPER_OPENAI_BASE_URL")
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
                    "content": (f"{prompt} Return only the reformatted text — no explanation, no preamble."),
                },
                {
                    "role": "user",
                    "content": f"<text>{html.escape(text)}</text>",
                },
            ],
            max_completion_tokens=4096,
        )
        return response.choices[0].message.content or text
    except Exception as exc:
        print(f"[local-whisper] auto_adapt error: {exc}", file=sys.stderr)
        return text
