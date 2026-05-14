"""Tests for corrections.load() and corrections.apply()."""

from pathlib import Path

from local_whisper.corrections import _PROMPT_CHAR_LIMIT, apply, build_prompt, load


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


def test_build_prompt_returns_none_for_empty_map() -> None:
    assert build_prompt({}) is None


def test_build_prompt_returns_correct_forms() -> None:
    result = build_prompt({"wispy": "Wispr", "gpt": "GPT"})
    assert result == "Wispr, GPT"


def test_build_prompt_deduplicates_values() -> None:
    result = build_prompt({"wispy": "Wispr", "whispy": "Wispr"})
    assert result == "Wispr"


def test_build_prompt_truncates_at_term_boundary() -> None:
    # Build a map whose joined prompt exceeds _PROMPT_CHAR_LIMIT.
    # Each value is "Term000" ... "Term999" (7 chars + ", " separator = 9 chars each).
    many = {f"wrong{i}": f"Term{i:03d}" for i in range(200)}
    result = build_prompt(many)
    assert result is not None
    assert len(result) <= _PROMPT_CHAR_LIMIT
    # Must not end mid-word — last char is a digit (complete term), not a comma/space.
    assert not result.endswith(",")
    assert not result.endswith(", ")


def test_build_prompt_truncation_edge_case_single_long_term() -> None:
    # If the first (and only) term exceeds the limit, rsplit finds no ", " and
    # returns the raw slice — still bounded by _PROMPT_CHAR_LIMIT.
    long_term = "A" * (_PROMPT_CHAR_LIMIT + 100)
    result = build_prompt({"wrong": long_term})
    assert result is not None
    assert len(result) <= _PROMPT_CHAR_LIMIT


def test_apply_does_not_partially_match_hyphenated_token() -> None:
    # "gpt" correction must not fire on "gpt-4" — would produce "GPT-4-4"
    assert apply("gpt-4 is good", {"gpt": "GPT-4"}) == "gpt-4 is good"
    # but standalone "gpt" still corrected
    assert apply("use gpt today", {"gpt": "GPT-4"}) == "use GPT-4 today"
