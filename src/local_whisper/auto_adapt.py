"""Auto-adapt: reshape transcription via LLM based on frontmost macOS app."""

from __future__ import annotations

import logging
from pathlib import Path

from local_whisper import config, llm
from local_whisper._macos import HAS_APPKIT
from local_whisper._macos import NSWorkspace as _NSWorkspace

logger = logging.getLogger("local_whisper")

_EMAIL_PROMPT = (
    "Transform the following text into a well-structured email, maintaining the original language of the input text. "
    "Analyze the tone and style of the input text (casual, professional, cordial, informal, etc.) and maintain that same tone throughout. "
    'Add an appropriate greeting like "Hi," and closing like "Cheers," that matches the detected tone. '
    "Do not use placeholders like [name] or [signature]. "
    "Organize the information in clear paragraphs. Only return the email text, without subject."
)

_SLACK_PROMPT = (
    "Clean up and format the following transcription, maintaining the original language, tone, style and words. "
    "Only fix small inconsistencies, errors, and organize the text into proper paragraphs with correct punctuation. "
    "Do not add emojis, greetings, or closings. Do not change the conversational style or add formalities. "
    "Simply present the cleaned transcription with proper formatting."
)

_BUILTIN_PROMPTS: dict[str, str] = {
    "Slack": _SLACK_PROMPT,
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
    if not HAS_APPKIT:
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


def is_active(app_name: str, path: Path = config.CONFIG_PATH) -> bool:
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
    if not llm.is_available():
        return False
    if not config.is_auto_adapt_enabled(path):
        return False
    return _get_prompt(app_name, config.get_auto_adapt_section(path)) is not None


def apply(text: str, app_name: str = "", path: Path = config.CONFIG_PATH) -> str:
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

    if not config.is_auto_adapt_enabled(path):
        return text

    prompt = _get_prompt(app_name, config.get_auto_adapt_section(path))
    if prompt is None:
        return text

    return llm.reshape_for_app(text, prompt)
