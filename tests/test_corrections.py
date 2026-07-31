"""Tests for corrections.load() and corrections.apply()."""

from pathlib import Path
from unittest.mock import Mock, call

import pytest

import local_whisper.corrections as corrections
from local_whisper.corrections import (
    _PROMPT_INPUT_CHAR_LIMIT,
    _PROMPT_TERM_CHAR_LIMIT,
    _PROMPT_TOKEN_LIMIT,
    _prompt_token_count,
    apply,
    build_prompt,
    load,
)

# The token cap needs mlx's real tokenizer, which only loads on Apple Silicon.
# Elsewhere (e.g. Linux CI) _prompt_token_count returns 0 and the character caps
# govern; tests that assert token-specific behaviour are skipped there.
_MLX_AVAILABLE = _prompt_token_count("probe") > 0
requires_mlx = pytest.mark.skipif(not _MLX_AVAILABLE, reason="mlx tokenizer unavailable on this platform")


def _maximal_fitting_prefix(terms: list[str]) -> list[str]:
    """Derive the documented whole-term prefix independently of build_prompt."""
    accepted: list[str] = []
    for term in terms:
        candidate = ", ".join([*accepted, term])
        if (
            len(term) > _PROMPT_TERM_CHAR_LIMIT
            or len(candidate) > _PROMPT_INPUT_CHAR_LIMIT
            or _prompt_token_count(candidate) > _PROMPT_TOKEN_LIMIT
        ):
            break
        accepted.append(term)
    return accepted


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


def test_load_retains_oversized_correction_for_post_processing(tmp_path: Path) -> None:
    config = tmp_path / "corrections.toml"
    replacement = "x" * (corrections._PROMPT_TERM_CHAR_LIMIT + 1)
    config.write_text(f'[corrections]\nwrong = "{replacement}"\n')

    assert load(config) == {"wrong": replacement}


def test_load_retains_later_correction_after_prompt_budget_is_exhausted(tmp_path: Path) -> None:
    config = tmp_path / "corrections.toml"
    first = "x" * 799
    config.write_text(f'[corrections]\nfirst = "{first}"\nlate = "LATE"\n')

    assert apply("late", load(config)) == "LATE"


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


def test_build_prompt_merges_corrections_before_vocabulary_with_stable_deduplication() -> None:
    result = build_prompt(
        {"dee bee tee": "dbt", "open a i": "OpenAI"},
        ["dbt", "loopctl", "OpenAI", "axi"],
    )
    assert result == "dbt, OpenAI, loopctl, axi"


def test_build_prompt_returns_none_when_corrections_and_vocabulary_are_empty() -> None:
    assert build_prompt({}, []) is None


def test_build_prompt_budgets_token_dense_ascii_terms_without_splitting() -> None:
    terms = [f"x{i:03d}" for i in range(131)]

    assert build_prompt({f"wrong{i}": term for i, term in enumerate(terms)}) == ", ".join(
        _maximal_fitting_prefix(terms)
    )


def test_build_prompt_budgets_token_dense_unicode_terms_without_splitting() -> None:
    terms = [f"漢字{i:03d}" for i in range(131)]

    assert build_prompt({}, terms) == ", ".join(_maximal_fitting_prefix(terms))


@requires_mlx
def test_build_prompt_stays_within_both_whisper_tokenizer_limits() -> None:
    """A multilingual-only overflow must not reach Whisper's initial prompt."""
    from mlx_whisper.tokenizer import get_tokenizer

    terms = [f"🙂{i:03d}" for i in range(100)]
    prompt = build_prompt({}, terms)

    assert prompt == ", ".join(terms[:37])
    assert all(
        len(get_tokenizer(multilingual).encode(" " + prompt.strip())) <= _PROMPT_TOKEN_LIMIT
        for multilingual in (False, True)
    )


def test_build_prompt_returns_none_when_all_terms_are_blank() -> None:
    assert build_prompt({"wrong": ""}, [" ", "\t"]) is None


def test_build_prompt_ignores_blank_terms_before_deduplicating() -> None:
    assert build_prompt({"empty": "", "dbt": "dbt"}, [" ", "dbt"]) == "dbt"


def test_build_prompt_does_not_charge_blank_or_duplicate_terms_to_input_budget() -> None:
    assert build_prompt({}, [" " * 799, "dbt", "dbt"]) == "dbt"


@requires_mlx
def test_build_prompt_returns_none_when_first_term_exceeds_token_budget() -> None:
    assert build_prompt({"wrong": "漢" * 300}) is None


def test_build_prompt_rejects_oversized_first_term_before_tokenising(monkeypatch) -> None:
    token_count = Mock(return_value=0)
    monkeypatch.setattr(corrections, "_prompt_token_count", token_count)

    result = build_prompt({"wrong": "x" * (corrections._PROMPT_TERM_CHAR_LIMIT + 1)})

    assert result is None
    token_count.assert_not_called()


def test_build_prompt_stops_at_oversized_vocabulary_input(monkeypatch) -> None:
    token_count = Mock(return_value=0)
    monkeypatch.setattr(corrections, "_prompt_token_count", token_count)
    first = "a" * 399
    second = "b" * 399

    def vocabulary() -> object:
        yield first
        yield second
        raise AssertionError("prompt construction consumed vocabulary after exhausting its character budget")

    result = build_prompt({}, vocabulary())

    assert result == f"{first}, {second}"
    assert token_count.call_args_list == [call(first), call(f"{first}, {second}")]


def test_apply_does_not_partially_match_hyphenated_token() -> None:
    # "gpt" correction must not fire on "gpt-4" — would produce "GPT-4-4"
    assert apply("gpt-4 is good", {"gpt": "GPT-4"}) == "gpt-4 is good"
    # but standalone "gpt" still corrected
    assert apply("use gpt today", {"gpt": "GPT-4"}) == "use GPT-4 today"
