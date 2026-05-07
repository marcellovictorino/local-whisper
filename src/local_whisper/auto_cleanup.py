"""Auto-cleanup: remove filler words and collapse immediate word repetitions."""

from __future__ import annotations

import logging
import re
from pathlib import Path

from local_whisper import config

logger = logging.getLogger("local_whisper")

_FILLER_PATTERNS = [
    r"\byou\s+know\b",
    r"\bum\b",
    r"\buh\b",
    r"\ber\b",
    r"\bah\b",
    r"\bhmm\b",
]

_REPETITION_RE = re.compile(r"\b(\w+)\b(\s+\1)+\b", re.IGNORECASE)
_MULTI_SPACE_RE = re.compile(r" {2,}")


def _is_enabled(path: Path = config.CONFIG_PATH) -> bool:
    """Return True unless [auto_cleanup] enabled = false in config.

    Args:
        path: Path to config.toml.

    Returns:
        True if auto-cleanup is enabled (default when file or section absent).
    """
    return config.is_auto_cleanup_enabled(path)


def apply(text: str, path: Path = config.CONFIG_PATH) -> str:
    """Remove filler words and collapse immediate word repetitions.

    Fillers stripped: um, uh, er, ah, hmm, you know.
    Immediate repetitions collapsed: "I I need" → "I need".
    Non-adjacent repetitions are preserved.

    Args:
        text: Transcribed text to clean.
        path: Path to config.toml for enabled check.

    Returns:
        Cleaned text, or original text if disabled or on error.
    """
    if not _is_enabled(path):
        return text
    try:
        text = _REPETITION_RE.sub(r"\1", text)
        for pattern in _FILLER_PATTERNS:
            text = re.sub(pattern, "", text, flags=re.IGNORECASE)
        text = _MULTI_SPACE_RE.sub(" ", text).strip()
    except Exception as exc:
        logger.error("auto_cleanup failed: %s", exc)
    return text
