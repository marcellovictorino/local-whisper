"""Auto-cleanup: remove filler words and collapse immediate word repetitions."""

from __future__ import annotations

import re
import sys
import tomllib
from pathlib import Path

_CONFIG_PATH = Path.home() / ".config" / "local-whisper" / "config.toml"

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


def _is_enabled(path: Path = _CONFIG_PATH) -> bool:
    """Return True unless [auto_cleanup] enabled = false in config.

    Args:
        path: Path to config.toml.

    Returns:
        True if auto-cleanup is enabled (default when file or section absent).
    """
    if not path.exists():
        return True
    try:
        with path.open("rb") as f:
            data = tomllib.load(f)
        return data.get("auto_cleanup", {}).get("enabled", True)
    except Exception as exc:
        print(f"[local-whisper] auto_cleanup config error: {exc}", file=sys.stderr)
        return True


def apply(text: str, path: Path = _CONFIG_PATH) -> str:
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
        print(f"[local-whisper] auto_cleanup failed: {exc}", file=sys.stderr)
    return text
