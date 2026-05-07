"""Snippet expansion: replace spoken shorthand with predefined text.

Config: ~/.config/local-whisper/config.toml

    [snippets]
    "my email" = "you@example.com"
    brb = "be right back"

Keys are matched case-insensitively anywhere within the transcribed text.
Longer keys take precedence over shorter ones on overlap.
"""

from __future__ import annotations

import logging
import re
from pathlib import Path

from local_whisper import config

logger = logging.getLogger("local_whisper")


def _load(path: Path) -> dict[str, str]:
    """Load snippets from a TOML config file.

    Args:
        path: Path to the TOML config file.

    Returns:
        Mapping of shorthand → expansion (keys casefolded), or empty dict if
        file absent or malformed.
    """
    raw = config.get_snippets_raw(path)

    if not isinstance(raw, dict):
        logger.warning("Snippets config: 'snippets' must be a table; ignoring")
        return {}

    invalid = [k for k, v in raw.items() if not isinstance(v, str)]
    if invalid:
        logger.warning("Snippets config: non-string values ignored: %r", invalid)

    result: dict[str, str] = {}
    for k, v in raw.items():
        if not isinstance(v, str):
            continue
        if not k.strip():
            logger.warning("Snippets config: empty/whitespace key ignored: %r", k)
            continue
        result[k.casefold()] = v
    return result


def expand(text: str, config_path: Path = config.CONFIG_PATH) -> str:
    """Replace snippet keywords in text with their predefined expansions.

    Applies all substitutions in a single pass — earlier replacements cannot
    cascade into later ones.

    Args:
        text: Transcribed text to process.
        config_path: Path to snippets TOML config. Defaults to
            ~/.config/local-whisper/config.toml.

    Returns:
        Text with all matching snippet keys replaced by their values.
        Returns original text unchanged if expansion fails for any reason.
    """
    mapping = _load(config_path)
    if not mapping:
        return text

    try:
        # Longer keys first so "my email address" wins over "my email" on overlap.
        keys = sorted(mapping, key=len, reverse=True)
        pattern = re.compile("|".join(re.escape(k) for k in keys), flags=re.IGNORECASE)

        matched_keys: list[str] = []

        def _replace(match: re.Match[str]) -> str:
            key = match.group(0).casefold()
            matched_keys.append(key)
            return mapping[key]

        expanded = pattern.sub(_replace, text)
    except Exception as exc:
        logger.error("Snippet expansion failed: %s", exc)
        return text

    if matched_keys:
        logger.info("Snippet expanded using keys: %r", matched_keys)
    return expanded
