"""Tests for corrections.load() and corrections.apply()."""

from pathlib import Path

from local_whisper.corrections import apply, load


def test_load_returns_empty_when_file_missing(tmp_path: Path) -> None:
    assert load(tmp_path / "nonexistent.toml") == {}


def test_load_parses_corrections_section(tmp_path: Path) -> None:
    config = tmp_path / "corrections.toml"
    config.write_text('[corrections]\n"wispy" = "Wispr"\n')
    result = load(config)
    assert result == {"wispy": "Wispr"}


def test_load_lowercases_keys(tmp_path: Path) -> None:
    config = tmp_path / "corrections.toml"
    config.write_text('[corrections]\n"GPT" = "GPT-4"\n')
    result = load(config)
    assert "gpt" in result


def test_load_returns_empty_on_malformed_toml(tmp_path: Path) -> None:
    config = tmp_path / "corrections.toml"
    config.write_text("not valid toml ][")
    assert load(config) == {}


def test_apply_replaces_word_in_sentence() -> None:
    assert apply("I use wispy every day", {"wispy": "Wispr"}) == "I use Wispr every day"


def test_apply_is_case_insensitive() -> None:
    assert apply("I use WISPY", {"wispy": "Wispr"}) == "I use Wispr"
    assert apply("I use Wispy", {"wispy": "Wispr"}) == "I use Wispr"


def test_apply_whole_word_only() -> None:
    # "in" correction must not touch "interesting" or "innovation" (both contain "in" mid/start-word)
    result = apply("interesting innovation in ideas", {"in": "inn"})
    assert result == "interesting innovation inn ideas"


def test_apply_multiple_corrections() -> None:
    corr = {"wispy": "Wispr", "gpt": "GPT-4"}
    result = apply("I use wispy with gpt", corr)
    assert result == "I use Wispr with GPT-4"


def test_apply_returns_unchanged_when_no_corrections() -> None:
    assert apply("hello world", {}) == "hello world"


def test_apply_returns_unchanged_when_no_match() -> None:
    assert apply("hello world", {"foo": "bar"}) == "hello world"


def test_apply_does_not_partially_match_hyphenated_token() -> None:
    # "gpt" correction must not fire on "gpt-4" — would produce "GPT-4-4"
    assert apply("gpt-4 is good", {"gpt": "GPT-4"}) == "gpt-4 is good"
    # but standalone "gpt" still corrected
    assert apply("use gpt today", {"gpt": "GPT-4"}) == "use GPT-4 today"
