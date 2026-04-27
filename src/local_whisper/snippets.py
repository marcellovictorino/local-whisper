"""Snippet expansion: replace spoken shorthand with predefined text.

Config: ~/.config/local-whisper/snippets.toml

    [snippets]
    "my email" = "you@example.com"
    brb = "be right back"

Keys are matched case-insensitively anywhere within the transcribed text.
Longer keys take precedence over shorter ones on overlap.
"""
from __future__ import annotations

import re
import sys
import tomllib
from pathlib import Path

_CONFIG_PATH = Path.home() / ".config" / "local-whisper" / "snippets.toml"


def _load(path: Path) -> dict[str, str]:
    """Load snippets from a TOML config file.

    Args:
        path: Path to the TOML config file.

    Returns:
        Mapping of shorthand → expansion (keys casefolded), or empty dict if
        file absent or malformed.
    """
    try:
        with open(path, "rb") as f:
            data = tomllib.load(f)
    except FileNotFoundError:
        return {}
    except OSError as exc:
        print(f"[local-whisper] Cannot read snippets config: {exc}", file=sys.stderr, flush=True)
        return {}
    except tomllib.TOMLDecodeError as exc:
        print(f"[local-whisper] Snippets config parse error: {exc}", file=sys.stderr, flush=True)
        return {}

    raw = data.get("snippets", {})
    if not isinstance(raw, dict):
        print(
            "[local-whisper] Snippets config: 'snippets' must be a table; ignoring",
            file=sys.stderr,
            flush=True,
        )
        return {}

    invalid = [k for k, v in raw.items() if not isinstance(v, str)]
    if invalid:
        print(
            f"[local-whisper] Snippets config: non-string values ignored: {invalid!r}",
            file=sys.stderr,
            flush=True,
        )

    # Filter empty/whitespace-only keys — they match everywhere and blow up output.
    result: dict[str, str] = {}
    for k, v in raw.items():
        if not isinstance(v, str):
            continue
        if not k.strip():
            print(
                f"[local-whisper] Snippets config: empty/whitespace key ignored: {k!r}",
                file=sys.stderr,
                flush=True,
            )
            continue
        result[k.casefold()] = v
    return result


def expand(text: str, config_path: Path = _CONFIG_PATH) -> str:
    """Replace snippet keywords in text with their predefined expansions.

    Applies all substitutions in a single pass — earlier replacements cannot
    cascade into later ones.

    Args:
        text: Transcribed text to process.
        config_path: Path to snippets TOML config. Defaults to
            ~/.config/local-whisper/snippets.toml.

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
    except Exception as exc:  # noqa: BLE001
        print(f"[local-whisper] Snippet expansion failed: {exc}", file=sys.stderr, flush=True)
        return text

    if matched_keys:
        print(
            f"[local-whisper] Snippet expanded using keys: {matched_keys!r}",
            file=sys.stderr,
            flush=True,
        )
    return expanded
