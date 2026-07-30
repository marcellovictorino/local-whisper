"""Shared configuration: config file path and mtime-cached TOML loader."""

from __future__ import annotations

import logging
import tomllib
from dataclasses import dataclass
from enum import Enum, auto
from pathlib import Path

CONFIG_PATH = Path.home() / ".config" / "local-whisper" / "config.toml"

logger = logging.getLogger("local_whisper")


class ConfigState(Enum):
    """The outcome of reading a config file."""

    MISSING = auto()
    MALFORMED = auto()
    LOADED = auto()


@dataclass(frozen=True)
class ConfigLoad:
    """A config read result, including states that otherwise look empty."""

    state: ConfigState
    data: dict
    error: str | None = None


# Single-slot cache: (key, result) tuple swapped atomically on invalidation.
_toml_cache: tuple[tuple[Path, float], ConfigLoad] | None = None


def load_config(path: Path = CONFIG_PATH) -> ConfigLoad:
    """Read config.toml and retain whether it was missing, malformed, or loaded.

    A malformed file is cached by path and mtime so its parse error is logged once
    until the file changes or :func:`invalidate` is called.
    """
    global _toml_cache
    try:
        mtime = path.stat().st_mtime
    except OSError:
        return ConfigLoad(ConfigState.MISSING, {})
    key = (path, mtime)
    cached = _toml_cache  # local ref — single read is atomic in CPython
    if cached is not None and cached[0] == key:
        return cached[1]
    try:
        with path.open("rb") as f:
            result = ConfigLoad(ConfigState.LOADED, tomllib.load(f))
    except tomllib.TOMLDecodeError as exc:
        logger.error("config.toml parse error for %s: %s", path, exc)
        result = ConfigLoad(ConfigState.MALFORMED, {}, error=str(exc))
    except OSError:
        return ConfigLoad(ConfigState.MISSING, {})
    _toml_cache = (key, result)  # atomic ref swap
    return result


def load_section(name: str, path: Path = CONFIG_PATH) -> dict:
    """Read a named section from config.toml. Returns {} if absent or on any error.

    Args:
        name: Top-level TOML key (e.g. "auto_cleanup").
        path: Path to config.toml.

    Returns:
        Section dict, or {} if section absent, file missing, or parse error.
    """
    section = load_config(path).data.get(name, {})
    return section if isinstance(section, dict) else {}


def invalidate() -> None:
    """Clear the config cache (call on SIGHUP to pick up changes immediately)."""
    global _toml_cache
    _toml_cache = None


def get_whisper_model(path: Path = CONFIG_PATH) -> str | None:
    """Return [whisper] model value, or None if absent."""
    return load_section("whisper", path).get("model")


def is_auto_cleanup_enabled(path: Path = CONFIG_PATH) -> bool:
    """Return [auto_cleanup] enabled flag. Defaults to True (opt-out)."""
    return bool(load_section("auto_cleanup", path).get("enabled", True))


def get_corrections_raw(path: Path = CONFIG_PATH) -> dict:
    """Return raw [corrections] section dict."""
    return load_section("corrections", path)


def get_snippets_raw(path: Path = CONFIG_PATH) -> dict:
    """Return raw [snippets] section dict."""
    return load_section("snippets", path)


def get_auto_adapt_section(path: Path = CONFIG_PATH) -> dict:
    """Return full [auto_adapt] section dict (for app-prompt resolution)."""
    return load_section("auto_adapt", path)
