"""Shared OpenAI-compatible LLM call helper."""

from __future__ import annotations

import logging
import os

try:
    import openai
except ImportError:
    openai = None  # type: ignore[assignment]

logger = logging.getLogger("local_whisper")


def transform(
    system: str,
    user: str,
    *,
    default_model: str,
    fallback: str,
    escape: bool = False,
) -> str:
    """Send a single chat completion turn and return the response text.

    Args:
        system: Instruction prompt (system role).
        user: Input text (user role).
        default_model: Model ID used unless LOCAL_WHISPER_COMMAND_MODEL overrides.
        fallback: Returned on missing API key, missing package, or API error.
        escape: If True, HTML-escape user and wrap in <text>…</text>.

    Returns:
        Model response text, or fallback on any failure.
    """
    api_key = os.environ.get("LOCAL_WHISPER_OPENAI_API_KEY") or os.environ.get("OPENAI_API_KEY", "")
    if not api_key:
        logger.warning("No OpenAI API key. Set LOCAL_WHISPER_OPENAI_API_KEY or OPENAI_API_KEY.")
        return fallback

    if openai is None:
        logger.warning("openai package not installed. Run: uv sync --extra command")
        return fallback

    if escape:
        import html

        user = f"<text>{html.escape(user)}</text>"

    model = os.environ.get("LOCAL_WHISPER_COMMAND_MODEL", default_model)
    base_url = os.environ.get("LOCAL_WHISPER_OPENAI_BASE_URL")
    try:
        client = openai.OpenAI(
            api_key=api_key,
            **({"base_url": base_url} if base_url else {}),
        )
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
    return transform(system, text, default_model="gpt-5-nano", fallback=text, escape=True)
