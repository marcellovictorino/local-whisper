"""Word-level corrections — fixes consistent ASR mishearings."""

from __future__ import annotations

import logging
import re
from pathlib import Path

from local_whisper import config

logger = logging.getLogger("local_whisper")

_PROMPT_CHAR_LIMIT = 800  # ~200 tokens; mlx-whisper hard limit is ~224 tokens


def build_prompt(corrections_map: dict[str, str], vocabulary_words: list[str] | None = None) -> str | None:
    """Build an initial_prompt string from corrections and configured vocabulary.

    Correction values precede vocabulary words so established corrections retain
    priority when the decoder prompt reaches its character limit.

    Args:
        corrections_map: Loaded corrections dict (keys=wrong form, values=correct form).
        vocabulary_words: Additional configured terms in their declared order.

    Returns:
        Comma-joined unique terms, clipped at the last complete term within the
        ~224-token limit. An oversized first term is clipped to the limit. None
        if neither source contributes a term.
    """
    terms = list(dict.fromkeys([*corrections_map.values(), *(vocabulary_words or [])]))
    if not terms:
        return None

    prompt = ", ".join(terms)
    if len(prompt) <= _PROMPT_CHAR_LIMIT:
        return prompt

    complete_terms: list[str] = []
    length = 0
    for term in terms:
        separator_length = 2 if complete_terms else 0
        if length + separator_length + len(term) > _PROMPT_CHAR_LIMIT:
            break
        complete_terms.append(term)
        length += separator_length + len(term)
    if complete_terms:
        return ", ".join(complete_terms)
    return terms[0][:_PROMPT_CHAR_LIMIT]


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
