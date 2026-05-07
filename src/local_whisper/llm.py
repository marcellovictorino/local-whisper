"""Shared OpenAI-compatible LLM call helper."""

from __future__ import annotations

import html
import logging
import os

try:
    import openai
except ImportError:
    openai = None  # type: ignore[assignment]

logger = logging.getLogger("local_whisper")

# Cached clients keyed by (api_key, base_url) to reuse connection pools across calls.
_client_cache: dict[tuple[str, str | None], openai.OpenAI] = {}  # type: ignore[type-arg]


def _get_api_key() -> str:
    return os.environ.get("LOCAL_WHISPER_OPENAI_API_KEY") or os.environ.get("OPENAI_API_KEY", "")


def is_available() -> bool:
    """Return True if the OpenAI package is installed and an API key is configured.

    Returns:
        True if LLM calls can be attempted, False otherwise.
    """
    return openai is not None and bool(_get_api_key())


def _get_client(api_key: str, base_url: str | None) -> openai.OpenAI:  # type: ignore[name-defined]
    key = (api_key, base_url)
    if key not in _client_cache:
        _client_cache[key] = openai.OpenAI(api_key=api_key, base_url=base_url)
    return _client_cache[key]


def transform(
    system: str,
    user: str,
    *,
    default_model: str,
    fallback: str,
) -> str:
    """Send a single chat completion turn and return the response text.

    Args:
        system: Instruction prompt (system role).
        user: Input text (user role).
        default_model: Model ID used unless LOCAL_WHISPER_COMMAND_MODEL overrides.
        fallback: Returned on missing API key, missing package, or API error.

    Returns:
        Model response text, or fallback on any failure.
    """
    api_key = _get_api_key()
    if not api_key:
        logger.warning("No OpenAI API key. Set LOCAL_WHISPER_OPENAI_API_KEY or OPENAI_API_KEY.")
        return fallback

    if openai is None:
        logger.warning("openai package not installed. Run: uv sync --extra command")
        return fallback

    model = os.environ.get("LOCAL_WHISPER_COMMAND_MODEL", default_model)
    base_url = os.environ.get("LOCAL_WHISPER_OPENAI_BASE_URL")
    try:
        client = _get_client(api_key, base_url)
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            max_completion_tokens=4096,
        )
        return response.choices[0].message.content or fallback
    except Exception as exc:
        logger.error("LLM call failed: %s", exc)
        return fallback


def apply_voice_command(text: str, instruction: str) -> str:
    """Apply a spoken instruction to selected text via LLM.

    Args:
        text: Selected text to transform.
        instruction: Voice command describing the transformation.

    Returns:
        Transformed text, or instruction unchanged if API unavailable.
    """
    system = (
        "Apply the instruction to the provided text. Return only the transformed text — no explanation, no preamble."
    )
    user = f"{instruction}\n\n{text}"
    return transform(system, user, default_model="gpt-5-nano", fallback=instruction)


def reshape_for_app(text: str, prompt: str) -> str:
    """Reshape transcribed text for a specific app context via LLM.

    Args:
        text: Transcribed text to reshape.
        prompt: App-specific formatting instruction (from config or built-in presets).

    Returns:
        Reshaped text, or original text unchanged if API unavailable.
    """
    system = f"{prompt} Return only the reformatted text — no explanation, no preamble."
    user = f"<text>{html.escape(text)}</text>"
    return transform(system, user, default_model="gpt-5-nano", fallback=text)
