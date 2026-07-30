"""Tests for config.load_section() — caching, invalidation, error handling."""

from __future__ import annotations

import logging
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


def test_load_config_distinguishes_empty_missing_and_malformed_files(tmp_path: Path) -> None:
    missing = cfg.load_config(tmp_path / "missing.toml")
    empty = cfg.load_config(_write(tmp_path / "empty.toml", ""))
    no_section = cfg.load_config(_write(tmp_path / "no-section.toml", "[other]\nvalue = 1\n"))
    malformed = cfg.load_config(_write(tmp_path / "malformed.toml", "not valid toml ]["))

    assert missing.state is cfg.ConfigState.MISSING
    assert empty.state is cfg.ConfigState.LOADED and empty.data == {}
    assert no_section.state is cfg.ConfigState.LOADED and "requested" not in no_section.data
    assert malformed.state is cfg.ConfigState.MALFORMED


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


def test_malformed_file_is_parsed_and_logged_once_per_mtime(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, caplog
) -> None:
    p = _write(tmp_path / "c.toml", "not valid toml ][")
    parse = cfg.tomllib.load
    attempts = 0

    def count_parse(file):
        nonlocal attempts
        attempts += 1
        return parse(file)

    monkeypatch.setattr(cfg.tomllib, "load", count_parse)
    with caplog.at_level(logging.ERROR, logger="local_whisper"):
        assert cfg.load_config(p).state is cfg.ConfigState.MALFORMED
        assert cfg.load_config(p).state is cfg.ConfigState.MALFORMED

    assert attempts == 1
    errors = [record for record in caplog.records if record.levelno == logging.ERROR]
    assert len(errors) == 1
    assert str(p) in errors[0].message
    assert "line" in errors[0].message and "column" in errors[0].message


def test_mtime_change_retries_malformed_file_and_clears_state(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    p = _write(tmp_path / "c.toml", "not valid toml ][")
    parse = cfg.tomllib.load
    attempts = 0

    def count_parse(file):
        nonlocal attempts
        attempts += 1
        return parse(file)

    monkeypatch.setattr(cfg.tomllib, "load", count_parse)
    assert cfg.load_config(p).state is cfg.ConfigState.MALFORMED
    old_mtime = p.stat().st_mtime
    p.write_text("[s]\nv = 1\n")
    os.utime(p, (old_mtime + 1, old_mtime + 1))

    result = cfg.load_config(p)
    assert attempts == 2
    assert result.state is cfg.ConfigState.LOADED
    assert result.data == {"s": {"v": 1}}


def test_invalidation_retries_malformed_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    p = _write(tmp_path / "c.toml", "not valid toml ][")
    parse = cfg.tomllib.load
    attempts = 0

    def count_parse(file):
        nonlocal attempts
        attempts += 1
        return parse(file)

    monkeypatch.setattr(cfg.tomllib, "load", count_parse)
    assert cfg.load_config(p).state is cfg.ConfigState.MALFORMED
    cfg.invalidate()
    assert cfg.load_config(p).state is cfg.ConfigState.MALFORMED
    assert attempts == 2


# --- typed accessors: default when absent ---


@pytest.mark.parametrize(
    "accessor,expected",
    [
        (cfg.get_whisper_model, None),
        (cfg.is_auto_cleanup_enabled, True),
        (cfg.get_corrections_raw, {}),
        (cfg.get_vocabulary_words, []),
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


def test_get_corrections_raw_returns_dict(tmp_path: Path) -> None:
    p = _write(tmp_path / "c.toml", '[corrections]\nteh = "the"\nadn = "and"\n')
    assert cfg.get_corrections_raw(p) == {"teh": "the", "adn": "and"}


def test_get_vocabulary_words_preserves_valid_terms_in_order(tmp_path: Path) -> None:
    p = _write(tmp_path / "c.toml", '[vocabulary]\nwords = ["loopctl", 42, "dbt"]\n')
    assert cfg.get_vocabulary_words(p) == ["loopctl", "dbt"]


@pytest.mark.parametrize(
    "toml",
    [
        "",
        "[vocabulary]\n",
        '[vocabulary]\nwords = "loopctl"\n',
        "[vocabulary]\nwords = [42]\n",
    ],
)
def test_get_vocabulary_words_returns_empty_for_absent_or_invalid_shapes(tmp_path: Path, toml: str) -> None:
    p = _write(tmp_path / "c.toml", toml)
    assert cfg.get_vocabulary_words(p) == []


def test_get_snippets_raw_returns_dict(tmp_path: Path) -> None:
    p = _write(tmp_path / "c.toml", '[snippets]\nbrb = "be right back"\n')
    assert cfg.get_snippets_raw(p) == {"brb": "be right back"}


def test_get_auto_adapt_section_returns_full_section(tmp_path: Path) -> None:
    toml = '[auto_adapt.slack]\napps = ["Slack"]\nprompt = "casual"\n'
    p = _write(tmp_path / "c.toml", toml)
    result = cfg.get_auto_adapt_section(p)
    assert result["slack"]["prompt"] == "casual"
