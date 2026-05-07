"""Tests for snippets.expand — pure filesystem, no side effects."""

import os
from pathlib import Path

import pytest

from local_whisper import snippets


def _write_config(tmp_path: Path, content: str) -> Path:
    config = tmp_path / "snippets.toml"
    config.write_text(content, encoding="utf-8")
    return config


# --- no-op cases: text returned unchanged ---


@pytest.mark.parametrize(
    "setup",
    ["missing", "empty_section", "no_match", "malformed_toml", "snippets_not_table"],
)
def test_expand_returns_unchanged_on_no_op(tmp_path: Path, setup: str) -> None:
    text = "hello world"
    if setup == "missing":
        config_path = tmp_path / "snippets.toml"
    elif setup == "empty_section":
        config_path = _write_config(tmp_path, "[snippets]\n")
    elif setup == "no_match":
        config_path = _write_config(tmp_path, '[snippets]\nbrb = "be right back"\n')
    elif setup == "malformed_toml":
        config_path = _write_config(tmp_path, "not valid toml = = =")
    else:  # snippets_not_table
        config_path = _write_config(tmp_path, 'snippets = "not a table"\n')
    assert snippets.expand(text, config_path=config_path) == text


def test_expand_returns_unchanged_on_unreadable_file(tmp_path: Path) -> None:
    config = _write_config(tmp_path, '[snippets]\nbrb = "be right back"\n')
    os.chmod(config, 0o000)
    try:
        assert snippets.expand("brb", config_path=config) == "brb"
    finally:
        os.chmod(config, 0o644)


# --- expansion cases ---


@pytest.mark.parametrize(
    "text,expected",
    [
        ("send to my email", "send to me@example.com"),
        ("reach me at my email please", "reach me at me@example.com please"),
    ],
)
def test_expand_key_inline(tmp_path: Path, text: str, expected: str) -> None:
    config = _write_config(tmp_path, '[snippets]\n"my email" = "me@example.com"\n')
    assert snippets.expand(text, config_path=config) == expected


def test_case_insensitive_match(tmp_path: Path) -> None:
    config = _write_config(tmp_path, '[snippets]\nBRB = "be right back"\n')
    assert snippets.expand("brb", config_path=config) == "be right back"
    assert snippets.expand("BRB", config_path=config) == "be right back"


def test_multiple_snippets_expanded(tmp_path: Path) -> None:
    config = _write_config(tmp_path, '[snippets]\nbrb = "be right back"\nomw = "on my way"\n')
    assert snippets.expand("brb, omw", config_path=config) == "be right back, on my way"


def test_repeated_key_in_text_all_expanded(tmp_path: Path) -> None:
    config = _write_config(tmp_path, '[snippets]\nbrb = "be right back"\n')
    assert snippets.expand("brb and then brb again", config_path=config) == "be right back and then be right back again"


def test_expansion_with_special_regex_chars_in_key(tmp_path: Path) -> None:
    config = _write_config(tmp_path, '[snippets]\n"c++" = "C plus plus"\n')
    assert snippets.expand("I love c++", config_path=config) == "I love C plus plus"


def test_longer_key_wins_over_shorter_prefix(tmp_path: Path) -> None:
    config = _write_config(
        tmp_path,
        '[snippets]\n"my email" = "short@x.com"\n"my email address" = "full@example.com"\n',
    )
    assert snippets.expand("send to my email address", config_path=config) == "send to full@example.com"


def test_no_cascade_between_snippets(tmp_path: Path) -> None:
    config = _write_config(tmp_path, '[snippets]\nbrb = "be right back"\n"right back" = "soon"\n')
    assert snippets.expand("brb", config_path=config) == "be right back"


def test_non_string_values_are_ignored(tmp_path: Path) -> None:
    config = _write_config(tmp_path, '[snippets]\nbrb = 42\nomw = "on my way"\n')
    assert snippets.expand("brb omw", config_path=config) == "brb on my way"


@pytest.mark.parametrize("key", ['""', '"   "'])
def test_blank_key_is_ignored(tmp_path: Path, key: str) -> None:
    config = _write_config(tmp_path, f'[snippets]\n{key} = "boom"\nomw = "on my way"\n')
    assert snippets.expand("omw", config_path=config) == "on my way"
