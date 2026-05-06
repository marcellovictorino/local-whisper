"""Shared configuration: config file path and mtime-cached TOML loader."""

from __future__ import annotations

import tomllib
from pathlib import Path

CONFIG_PATH = Path.home() / ".config" / "local-whisper" / "config.toml"

# Cache maps (path, mtime) → parsed dict. Cleared before each new entry to avoid unbounded growth.
_toml_cache: dict[tuple[Path, float], dict] = {}


def _load_toml(path: Path = CONFIG_PATH) -> dict:
    try:
        mtime = path.stat().st_mtime
    except FileNotFoundError:
        return {}
    except OSError:
        return {}
    key = (path, mtime)
    if key not in _toml_cache:
        try:
            with path.open("rb") as f:
                data = tomllib.load(f)
        except Exception:
            return {}
        _toml_cache.clear()
        _toml_cache[key] = data
        return data
    return _toml_cache.get(key, {})


def load_section(name: str, path: Path = CONFIG_PATH) -> dict:
    """Read a named section from config.toml. Returns {} if absent or on any error.

    Args:
        name: Top-level TOML key (e.g. "auto_cleanup").
        path: Path to config.toml.

    Returns:
        Section dict, or {} if section absent, file missing, or parse error.
    """
    section = _load_toml(path).get(name, {})
    return section if isinstance(section, dict) else {}


def invalidate() -> None:
    """Clear the config cache (call on SIGHUP to pick up changes immediately)."""
    _toml_cache.clear()


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


def is_auto_adapt_enabled(path: Path = CONFIG_PATH) -> bool:
    """Return [auto_adapt] enabled flag. Defaults to False (opt-in)."""
    return bool(load_section("auto_adapt", path).get("enabled", False))


def get_auto_adapt_section(path: Path = CONFIG_PATH) -> dict:
    """Return full [auto_adapt] section dict (for app-prompt resolution)."""
    return load_section("auto_adapt", path)
