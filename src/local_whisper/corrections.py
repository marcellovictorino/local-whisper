"""Word-level corrections — fixes consistent ASR mishearings."""

from __future__ import annotations

import logging
import re
from pathlib import Path

from local_whisper import config

logger = logging.getLogger("local_whisper")

_PROMPT_CHAR_LIMIT = 800  # ~200 tokens; mlx-whisper hard limit is ~224 tokens


def build_prompt(corrections_map: dict[str, str]) -> str | None:
    """Build an initial_prompt string from corrections to bias Whisper's vocabulary.

    Feeds the correct forms (values) into mlx-whisper's decoder prompt so known
    terms are transcribed correctly on the first pass, not only post-corrected.

    Args:
        corrections_map: Loaded corrections dict (keys=wrong form, values=correct form).

    Returns:
        Comma-joined correct forms, clipped at last complete term within the
        ~224-token limit. None if map is empty.
    """
    if not corrections_map:
        return None
    unique_terms = list(dict.fromkeys(corrections_map.values()))
    prompt = ", ".join(unique_terms)
    if len(prompt) > _PROMPT_CHAR_LIMIT:
        prompt = prompt[:_PROMPT_CHAR_LIMIT].rsplit(", ", 1)[0]
    return prompt or None


def load(path: Path = config.CONFIG_PATH) -> dict[str, str]:
    """Load corrections from TOML config file.

    Returns empty dict if file does not exist.

    Args:
        path: Path to config.toml. Defaults to ~/.config/local-whisper/config.toml.

    Returns:
        Dict mapping misheard words (lowercased) to correct replacements.
    """
    try:
        section = config.get_corrections_raw(path)
        return {k.lower(): v for k, v in section.items() if isinstance(v, str)}
    except Exception as exc:
        logger.error("Failed to load corrections: %s", exc)
        return {}


def apply(text: str, corrections: dict[str, str]) -> str:
    """Apply word-level corrections to transcribed text.

    Matches whole words only, case-insensitive. Replacement preserves the
    exact case specified in the corrections config.

    Args:
        text: Transcribed text to correct.
        corrections: Loaded corrections dict (keys already lowercased).

    Returns:
        Text with corrections applied.
    """
    if not corrections:
        return text
    for wrong, right in corrections.items():
        text = re.sub(
            rf"(?<![\w-]){re.escape(wrong)}(?![\w-])",
            lambda _, r=right: r,
            text,
            flags=re.IGNORECASE,
        )
    return text
