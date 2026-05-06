"""Tests for config.load_section() — caching, invalidation, error handling."""

from __future__ import annotations

import time
from pathlib import Path

import pytest

import local_whisper.config as cfg


@pytest.fixture(autouse=True)
def clear_cache():
    """Ensure each test starts and ends with a clean cache."""
    cfg.invalidate()
    yield
    cfg.invalidate()


def _write(path: Path, content: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
    return path


# --- basic load_section behavior ---


def test_returns_empty_when_file_missing(tmp_path: Path) -> None:
    assert cfg.load_section("anything", tmp_path / "missing.toml") == {}


def test_returns_empty_when_section_absent(tmp_path: Path) -> None:
    p = _write(tmp_path / "c.toml", "[other]\nfoo = 1\n")
    assert cfg.load_section("missing_section", p) == {}


def test_returns_section_content(tmp_path: Path) -> None:
    p = _write(tmp_path / "c.toml", "[auto_cleanup]\nenabled = true\n")
    assert cfg.load_section("auto_cleanup", p) == {"enabled": True}


def test_returns_empty_when_section_is_not_dict(tmp_path: Path) -> None:
    p = _write(tmp_path / "c.toml", 'auto_adapt = "bad"\n')
    assert cfg.load_section("auto_adapt", p) == {}


def test_returns_empty_on_corrupt_toml(tmp_path: Path) -> None:
    p = _write(tmp_path / "c.toml", "not valid toml ][")
    assert cfg.load_section("auto_cleanup", p) == {}


# --- mtime-based caching ---


def test_cache_hit_avoids_reread(tmp_path: Path) -> None:
    p = _write(tmp_path / "c.toml", "[s]\nv = 1\n")
    first = cfg.load_section("s", p)

    # Overwrite with different content but keep same mtime by restoring it
    original_mtime = p.stat().st_mtime
    p.write_text("[s]\nv = 999\n")
    import os

    os.utime(p, (original_mtime, original_mtime))

    second = cfg.load_section("s", p)
    assert second == first  # served from cache
    assert second["v"] == 1


def test_cache_miss_on_mtime_change(tmp_path: Path) -> None:
    p = _write(tmp_path / "c.toml", "[s]\nv = 1\n")
    cfg.load_section("s", p)

    # Wait briefly to ensure a new mtime, then overwrite
    time.sleep(0.01)
    p.write_text("[s]\nv = 42\n")

    result = cfg.load_section("s", p)
    assert result["v"] == 42


# --- invalidate() ---


def test_invalidate_clears_cache(tmp_path: Path) -> None:
    p = _write(tmp_path / "c.toml", "[s]\nv = 1\n")
    cfg.load_section("s", p)

    p.write_text("[s]\nv = 99\n")
    cfg.invalidate()  # force-evict without mtime change

    result = cfg.load_section("s", p)
    assert result["v"] == 99


# --- typed accessors ---


# get_whisper_model


def test_get_whisper_model_absent_returns_none(tmp_path: Path) -> None:
    p = _write(tmp_path / "c.toml", "[other]\nfoo = 1\n")
    assert cfg.get_whisper_model(p) is None


def test_get_whisper_model_missing_file_returns_none(tmp_path: Path) -> None:
    assert cfg.get_whisper_model(tmp_path / "missing.toml") is None


def test_get_whisper_model_returns_value(tmp_path: Path) -> None:
    p = _write(tmp_path / "c.toml", '[whisper]\nmodel = "my-model"\n')
    assert cfg.get_whisper_model(p) == "my-model"


def test_get_whisper_model_non_string_returns_value_as_is(tmp_path: Path) -> None:
    p = _write(tmp_path / "c.toml", "[whisper]\nmodel = 42\n")
    assert cfg.get_whisper_model(p) == 42


# is_auto_cleanup_enabled


def test_is_auto_cleanup_enabled_absent_returns_true(tmp_path: Path) -> None:
    assert cfg.is_auto_cleanup_enabled(tmp_path / "missing.toml") is True


def test_is_auto_cleanup_enabled_false(tmp_path: Path) -> None:
    p = _write(tmp_path / "c.toml", "[auto_cleanup]\nenabled = false\n")
    assert cfg.is_auto_cleanup_enabled(p) is False


def test_is_auto_cleanup_enabled_true(tmp_path: Path) -> None:
    p = _write(tmp_path / "c.toml", "[auto_cleanup]\nenabled = true\n")
    assert cfg.is_auto_cleanup_enabled(p) is True


# is_auto_adapt_enabled


def test_is_auto_adapt_enabled_absent_returns_false(tmp_path: Path) -> None:
    assert cfg.is_auto_adapt_enabled(tmp_path / "missing.toml") is False


def test_is_auto_adapt_enabled_true(tmp_path: Path) -> None:
    p = _write(tmp_path / "c.toml", "[auto_adapt]\nenabled = true\n")
    assert cfg.is_auto_adapt_enabled(p) is True


def test_is_auto_adapt_enabled_false(tmp_path: Path) -> None:
    p = _write(tmp_path / "c.toml", "[auto_adapt]\nenabled = false\n")
    assert cfg.is_auto_adapt_enabled(p) is False


# get_corrections_raw


def test_get_corrections_raw_absent_returns_empty(tmp_path: Path) -> None:
    assert cfg.get_corrections_raw(tmp_path / "missing.toml") == {}


def test_get_corrections_raw_returns_dict(tmp_path: Path) -> None:
    p = _write(tmp_path / "c.toml", '[corrections]\nteh = "the"\nadn = "and"\n')
    assert cfg.get_corrections_raw(p) == {"teh": "the", "adn": "and"}


# get_snippets_raw


def test_get_snippets_raw_absent_returns_empty(tmp_path: Path) -> None:
    assert cfg.get_snippets_raw(tmp_path / "missing.toml") == {}


def test_get_snippets_raw_returns_dict(tmp_path: Path) -> None:
    p = _write(tmp_path / "c.toml", '[snippets]\nbrb = "be right back"\n')
    assert cfg.get_snippets_raw(p) == {"brb": "be right back"}


# get_auto_adapt_section


def test_get_auto_adapt_section_absent_returns_empty(tmp_path: Path) -> None:
    assert cfg.get_auto_adapt_section(tmp_path / "missing.toml") == {}


def test_get_auto_adapt_section_returns_full_section(tmp_path: Path) -> None:
    toml = '[auto_adapt]\nenabled = true\n\n[auto_adapt.slack]\napps = ["Slack"]\nprompt = "casual"\n'
    p = _write(tmp_path / "c.toml", toml)
    result = cfg.get_auto_adapt_section(p)
    assert result["enabled"] is True
    assert result["slack"]["prompt"] == "casual"
