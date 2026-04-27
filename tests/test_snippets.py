"""Tests for snippets.expand — pure filesystem, no side effects."""
from pathlib import Path

from local_whisper import snippets


def _write_config(tmp_path: Path, content: str) -> Path:
    config = tmp_path / "snippets.toml"
    config.write_text(content, encoding="utf-8")
    return config


def test_no_config_file_returns_text_unchanged(tmp_path: Path) -> None:
    result = snippets.expand("hello world", config_path=tmp_path / "snippets.toml")
    assert result == "hello world"


def test_empty_snippets_section_returns_text_unchanged(tmp_path: Path) -> None:
    config = _write_config(tmp_path, "[snippets]\n")
    result = snippets.expand("hello world", config_path=config)
    assert result == "hello world"


def test_exact_key_expands(tmp_path: Path) -> None:
    config = _write_config(tmp_path, '[snippets]\n"my email" = "me@example.com"\n')
    result = snippets.expand("send to my email", config_path=config)
    assert result == "send to me@example.com"


def test_key_expands_inline(tmp_path: Path) -> None:
    config = _write_config(tmp_path, '[snippets]\n"my email" = "me@example.com"\n')
    result = snippets.expand("reach me at my email please", config_path=config)
    assert result == "reach me at me@example.com please"


def test_case_insensitive_match(tmp_path: Path) -> None:
    # uppercase key in config, mixed-case text — both must expand
    config = _write_config(tmp_path, "[snippets]\nBRB = \"be right back\"\n")
    assert snippets.expand("brb", config_path=config) == "be right back"
    assert snippets.expand("BRB", config_path=config) == "be right back"


def test_multiple_snippets_expanded(tmp_path: Path) -> None:
    config = _write_config(
        tmp_path,
        '[snippets]\nbrb = "be right back"\nomw = "on my way"\n',
    )
    result = snippets.expand("brb, omw", config_path=config)
    assert result == "be right back, on my way"


def test_no_match_returns_unchanged(tmp_path: Path) -> None:
    config = _write_config(tmp_path, "[snippets]\nbrb = \"be right back\"\n")
    result = snippets.expand("hello world", config_path=config)
    assert result == "hello world"


def test_repeated_key_in_text_all_expanded(tmp_path: Path) -> None:
    config = _write_config(tmp_path, "[snippets]\nbrb = \"be right back\"\n")
    result = snippets.expand("brb and then brb again", config_path=config)
    assert result == "be right back and then be right back again"


def test_expansion_with_special_regex_chars_in_key(tmp_path: Path) -> None:
    config = _write_config(tmp_path, '[snippets]\n"c++" = "C plus plus"\n')
    result = snippets.expand("I love c++", config_path=config)
    assert result == "I love C plus plus"


def test_longer_key_wins_over_shorter_prefix(tmp_path: Path) -> None:
    config = _write_config(
        tmp_path,
        '[snippets]\n"my email" = "short@x.com"\n"my email address" = "full@example.com"\n',
    )
    result = snippets.expand("send to my email address", config_path=config)
    assert result == "send to full@example.com"


def test_no_cascade_between_snippets(tmp_path: Path) -> None:
    # earlier expansion must not feed into a later snippet key
    config = _write_config(
        tmp_path,
        '[snippets]\nbrb = "be right back"\n"right back" = "soon"\n',
    )
    result = snippets.expand("brb", config_path=config)
    assert result == "be right back"


def test_malformed_toml_returns_text_unchanged(tmp_path: Path) -> None:
    config = tmp_path / "snippets.toml"
    config.write_text("not valid toml = = =", encoding="utf-8")
    result = snippets.expand("hello world", config_path=config)
    assert result == "hello world"


def test_unreadable_file_returns_text_unchanged(tmp_path: Path) -> None:
    import os
    config = _write_config(tmp_path, '[snippets]\nbrb = "be right back"\n')
    os.chmod(config, 0o000)
    try:
        result = snippets.expand("brb", config_path=config)
        assert result == "brb"
    finally:
        os.chmod(config, 0o644)


def test_non_string_values_are_ignored(tmp_path: Path) -> None:
    config = _write_config(tmp_path, "[snippets]\nbrb = 42\nomw = \"on my way\"\n")
    result = snippets.expand("brb omw", config_path=config)
    assert result == "brb on my way"


def test_snippets_not_a_table_returns_text_unchanged(tmp_path: Path) -> None:
    config = _write_config(tmp_path, 'snippets = "not a table"\n')
    result = snippets.expand("hello world", config_path=config)
    assert result == "hello world"


def test_empty_key_is_ignored(tmp_path: Path) -> None:
    config = _write_config(tmp_path, '[snippets]\n"" = "boom"\nomw = "on my way"\n')
    result = snippets.expand("omw", config_path=config)
    assert result == "on my way"


def test_whitespace_only_key_is_ignored(tmp_path: Path) -> None:
    config = _write_config(tmp_path, '[snippets]\n"   " = "boom"\nomw = "on my way"\n')
    result = snippets.expand("omw", config_path=config)
    assert result == "on my way"
