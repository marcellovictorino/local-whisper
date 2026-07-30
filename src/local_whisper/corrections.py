"""Word-level corrections — fixes consistent ASR mishearings."""

from __future__ import annotations

import logging
import re
from itertools import chain
from pathlib import Path

from local_whisper import config

logger = logging.getLogger("local_whisper")

_PROMPT_TOKEN_LIMIT = 223  # mlx-whisper retains the final n_ctx // 2 - 1 prompt tokens.
_PROMPT_TERM_CHAR_LIMIT = 800
_PROMPT_INPUT_CHAR_LIMIT = 800


def _prompt_token_count(prompt: str) -> int:
    """Return the token count mlx-whisper uses for an initial prompt."""
    from mlx_whisper.tokenizer import get_tokenizer

    return len(get_tokenizer(False).encode(" " + prompt.strip()))


def build_prompt(corrections_map: dict[str, str], vocabulary_words: list[str] | None = None) -> str | None:
    """Build an initial_prompt string from corrections and configured vocabulary.

    Correction values precede vocabulary words so established corrections retain
    priority when the decoder prompt reaches its token limit.

    Args:
        corrections_map: Loaded corrections dict (keys=wrong form, values=correct form).
        vocabulary_words: Additional configured terms in their declared order.

    Returns:
        Comma-joined unique terms within mlx-whisper's 223-token prompt limit.
        Terms are included whole and in order. None if neither source contributes
        a usable term.
    """
    complete_terms: list[str] = []
    seen: set[str] = set()
    input_length = 0
    for term in chain(corrections_map.values(), vocabulary_words or []):
        if not isinstance(term, str) or len(term) > _PROMPT_TERM_CHAR_LIMIT:
            break
        separator_length = 2 if complete_terms else 0
        if input_length + separator_length + len(term) > _PROMPT_INPUT_CHAR_LIMIT:
            break
        input_length += separator_length + len(term)
        if not term.strip() or term in seen:
            continue
        seen.add(term)
        candidate = ", ".join([*complete_terms, term])
        if _prompt_token_count(candidate) > _PROMPT_TOKEN_LIMIT:
            break
        complete_terms.append(term)
    return ", ".join(complete_terms) or None


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
        corrections: dict[str, str] = {}
        input_length = 0
        for wrong, right in section.items():
            if not isinstance(right, str):
                continue
            if len(right) > _PROMPT_TERM_CHAR_LIMIT:
                break
            separator_length = 2 if corrections else 0
            if input_length + separator_length + len(right) > _PROMPT_INPUT_CHAR_LIMIT:
                break
            input_length += separator_length + len(right)
            corrections[wrong.lower()] = right
        return corrections
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
