"""Auto-adapt: reshape transcription via LLM based on frontmost macOS app."""
from __future__ import annotations

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

_BUILTIN_PROMPTS: dict[str, str] = {
    "Slack": "Rewrite as casual Slack message. Use emojis where natural. Short sentences.",
    "Mail": "Rewrite as formal professional email. Correct grammar, clear paragraphs, no casual language.",
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
        if value.get("app", "").lower() == app_name.lower():
            prompt = value.get("prompt", "")
            if prompt:
                return prompt

    return _BUILTIN_PROMPTS.get(app_name)


def _is_enabled(path: Path = _CONFIG_PATH) -> bool:
    """Return True only if [auto_adapt] enabled = true in config.

    Defaults to False (opt-in) when file or section is absent.

    Args:
        path: Path to config.toml.

    Returns:
        True if auto-adapt is explicitly enabled.
    """
    try:
        with path.open("rb") as f:
            data = tomllib.load(f)
        return data.get("auto_adapt", {}).get("enabled", False)
    except FileNotFoundError:
        return False
    except Exception as exc:
        print(f"[local-whisper] auto_adapt config error: {exc}", file=sys.stderr)
        return False


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
    if not section.get("enabled", False):
        return text

    prompt = _get_prompt(app_name, section)
    if prompt is None:
        return text

    api_key = os.environ.get("LOCAL_WHISPER_OPENAI_API_KEY")
    if not api_key:
        print(
            "[local-whisper] LOCAL_WHISPER_OPENAI_API_KEY not set — auto-adapt unavailable.",
            file=sys.stderr,
        )
        return text

    if openai is None:
        print(
            "[local-whisper] command mode dependencies not installed."
            " Run: uv sync --extra command",
            file=sys.stderr,
        )
        return text

    model = os.environ.get("LOCAL_WHISPER_COMMAND_MODEL", "gpt-4o-mini")
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
                    "content": (
                        "Reformat the following transcription. "
                        "Return only the reformatted text — no explanation, no preamble."
                    ),
                },
                {
                    "role": "user",
                    "content": f"{prompt}\n\n{text}",
                },
            ],
            max_completion_tokens=1024,
        )
        return response.choices[0].message.content or text
    except Exception as exc:
        print(f"[local-whisper] auto_adapt error: {exc}", file=sys.stderr)
        return text
