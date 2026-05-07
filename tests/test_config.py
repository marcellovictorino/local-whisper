"""Tests for config.load_section() — caching, invalidation, error handling."""

from __future__ import annotations

import os
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


def test_returns_section_content(tmp_path: Path) -> None:
    p = _write(tmp_path / "c.toml", "[auto_cleanup]\nenabled = true\n")
    assert cfg.load_section("auto_cleanup", p) == {"enabled": True}


@pytest.mark.parametrize(
    "toml,section",
    [
        ("[other]\nfoo = 1\n", "missing_section"),
        ('auto_adapt = "bad"\n', "auto_adapt"),
        ("not valid toml ][", "auto_cleanup"),
    ],
)
def test_returns_empty_on_bad_or_missing_section(tmp_path: Path, toml: str, section: str) -> None:
    p = _write(tmp_path / "c.toml", toml)
    assert cfg.load_section(section, p) == {}


# --- mtime-based caching ---


def test_cache_hit_avoids_reread(tmp_path: Path) -> None:
    p = _write(tmp_path / "c.toml", "[s]\nv = 1\n")
    first = cfg.load_section("s", p)

    original_mtime = p.stat().st_mtime
    p.write_text("[s]\nv = 999\n")
    os.utime(p, (original_mtime, original_mtime))

    second = cfg.load_section("s", p)
    assert second == first
    assert second["v"] == 1


def test_cache_miss_on_mtime_change(tmp_path: Path) -> None:
    p = _write(tmp_path / "c.toml", "[s]\nv = 1\n")
    cfg.load_section("s", p)
    old_mtime = p.stat().st_mtime
    p.write_text("[s]\nv = 42\n")
    os.utime(p, (old_mtime + 1, old_mtime + 1))
    assert cfg.load_section("s", p)["v"] == 42


def test_invalidate_clears_cache(tmp_path: Path) -> None:
    p = _write(tmp_path / "c.toml", "[s]\nv = 1\n")
    cfg.load_section("s", p)
    p.write_text("[s]\nv = 99\n")
    cfg.invalidate()
    assert cfg.load_section("s", p)["v"] == 99


# --- typed accessors: default when absent ---


@pytest.mark.parametrize(
    "accessor,expected",
    [
        (cfg.get_whisper_model, None),
        (cfg.is_auto_cleanup_enabled, True),
        (cfg.is_auto_adapt_enabled, False),
        (cfg.get_corrections_raw, {}),
        (cfg.get_snippets_raw, {}),
        (cfg.get_auto_adapt_section, {}),
    ],
)
def test_accessor_returns_default_when_file_missing(tmp_path: Path, accessor, expected) -> None:
    assert accessor(tmp_path / "missing.toml") == expected


# --- typed accessors: returns configured values ---


def test_get_whisper_model_returns_value(tmp_path: Path) -> None:
    p = _write(tmp_path / "c.toml", '[whisper]\nmodel = "my-model"\n')
    assert cfg.get_whisper_model(p) == "my-model"


@pytest.mark.parametrize("enabled,expected", [(True, True), (False, False)])
def test_is_auto_cleanup_enabled(tmp_path: Path, enabled: bool, expected: bool) -> None:
    p = _write(tmp_path / "c.toml", f"[auto_cleanup]\nenabled = {str(enabled).lower()}\n")
    assert cfg.is_auto_cleanup_enabled(p) is expected


@pytest.mark.parametrize("enabled,expected", [(True, True), (False, False)])
def test_is_auto_adapt_enabled(tmp_path: Path, enabled: bool, expected: bool) -> None:
    p = _write(tmp_path / "c.toml", f"[auto_adapt]\nenabled = {str(enabled).lower()}\n")
    assert cfg.is_auto_adapt_enabled(p) is expected


def test_get_corrections_raw_returns_dict(tmp_path: Path) -> None:
    p = _write(tmp_path / "c.toml", '[corrections]\nteh = "the"\nadn = "and"\n')
    assert cfg.get_corrections_raw(p) == {"teh": "the", "adn": "and"}


def test_get_snippets_raw_returns_dict(tmp_path: Path) -> None:
    p = _write(tmp_path / "c.toml", '[snippets]\nbrb = "be right back"\n')
    assert cfg.get_snippets_raw(p) == {"brb": "be right back"}


def test_get_auto_adapt_section_returns_full_section(tmp_path: Path) -> None:
    toml = '[auto_adapt]\nenabled = true\n\n[auto_adapt.slack]\napps = ["Slack"]\nprompt = "casual"\n'
    p = _write(tmp_path / "c.toml", toml)
    result = cfg.get_auto_adapt_section(p)
    assert result["enabled"] is True
    assert result["slack"]["prompt"] == "casual"
