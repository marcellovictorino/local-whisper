"""Tests for auto_cleanup._is_enabled() and auto_cleanup.apply()."""

from pathlib import Path

import pytest

from local_whisper.auto_cleanup import _is_enabled, apply


def test_is_enabled_defaults_true_when_file_missing(tmp_path: Path) -> None:
    assert _is_enabled(tmp_path / "nonexistent.toml") is True


@pytest.mark.parametrize("enabled,expected", [(False, False), (True, True)])
def test_is_enabled_reads_from_config(tmp_path: Path, enabled: bool, expected: bool) -> None:
    config = tmp_path / "config.toml"
    config.write_text(f"[auto_cleanup]\nenabled = {str(enabled).lower()}\n")
    assert _is_enabled(config) is expected


def test_is_enabled_defaults_true_when_section_absent(tmp_path: Path) -> None:
    config = tmp_path / "config.toml"
    config.write_text('[snippets]\nbrb = "be right back"\n')
    assert _is_enabled(config) is True


@pytest.mark.parametrize(
    "text,expected",
    [
        ("um hello there", "hello there"),
        ("uh I was saying", "I was saying"),
        ("you know what I mean", "what I mean"),
        ("UM hello UH world", "hello world"),
        ("you  know what", "what"),
    ],
)
def test_apply_removes_fillers(text: str, expected: str) -> None:
    assert apply(text) == expected


@pytest.mark.parametrize(
    "text,expected",
    [
        ("I I need to go", "I need to go"),
        ("the the the end", "the end"),
    ],
)
def test_apply_collapses_repetition(text: str, expected: str) -> None:
    assert apply(text) == expected


def test_apply_does_not_collapse_nonadjacent_repetition() -> None:
    assert apply("the cat and the dog") == "the cat and the dog"


def test_apply_preserves_case_of_non_filler_words() -> None:
    assert apply("Um Hello World") == "Hello World"


def test_apply_no_double_spaces_after_removal() -> None:
    assert apply("go um there") == "go there"


def test_apply_returns_unchanged_when_disabled(tmp_path: Path) -> None:
    config = tmp_path / "config.toml"
    config.write_text("[auto_cleanup]\nenabled = false\n")
    raw = "um I I need to go you know"
    assert apply(raw, path=config) == raw


def test_apply_enabled_by_default_when_no_config(tmp_path: Path) -> None:
    assert apply("um hello", path=tmp_path / "nonexistent.toml") == "hello"


def test_apply_returns_unchanged_on_empty_string() -> None:
    assert apply("") == ""


def test_apply_repetition_then_filler() -> None:
    assert apply("I I need um to go") == "I need to go"
