"""Tests for _run_dictation_pipeline and _run_command_pipeline."""

from __future__ import annotations

from unittest.mock import patch

from local_whisper.app import _run_command_pipeline, _run_dictation_pipeline


def test_dictation_pipeline_order() -> None:
    """Each pipeline step is called in the correct order with correct args."""
    with (
        patch("local_whisper.app.auto_cleanup.apply", return_value="cleaned") as mock_cleanup,
        patch("local_whisper.app.auto_adapt.apply", return_value="adapted") as mock_adapt,
        patch("local_whisper.app.corrections.apply", return_value="corrected") as mock_corrections,
        patch("local_whisper.app.snippets.expand", return_value="expanded") as mock_snippets,
        patch("local_whisper.app.clipboard.write_and_paste") as mock_paste,
    ):
        result = _run_dictation_pipeline("hello", "Slack", {"teh": "the"})

    mock_cleanup.assert_called_once_with("hello")
    mock_adapt.assert_called_once_with("cleaned", "Slack")
    mock_corrections.assert_called_once_with("adapted", {"teh": "the"})
    mock_snippets.assert_called_once_with("corrected")
    mock_paste.assert_called_once_with("expanded")
    assert result == "expanded"


def test_dictation_pipeline_applies_corrections() -> None:
    """Corrections substitution is applied without mocking (integration-style)."""
    with (
        patch("local_whisper.app.auto_cleanup.apply", side_effect=lambda t: t),
        patch("local_whisper.app.auto_adapt.apply", side_effect=lambda t, _a: t),
        patch("local_whisper.app.snippets.expand", side_effect=lambda t: t),
        patch("local_whisper.app.clipboard.write_and_paste"),
    ):
        result = _run_dictation_pipeline("teh world", "Terminal", {"teh": "the"})

    assert result == "the world"


def test_command_pipeline() -> None:
    """apply_voice_command is called with correct args and result is pasted."""
    with (
        patch("local_whisper.app.llm.apply_voice_command", return_value="fixed") as mock_llm,
        patch("local_whisper.app.clipboard.write_and_paste") as mock_paste,
    ):
        result = _run_command_pipeline("original", "fix grammar")

    mock_llm.assert_called_once_with("original", "fix grammar")
    mock_paste.assert_called_once_with("fixed")
    assert result == "fixed"


def test_command_pipeline_llm_failure() -> None:
    """An empty string from the LLM is pasted without raising an exception."""
    with (
        patch("local_whisper.app.llm.apply_voice_command", return_value="") as mock_llm,
        patch("local_whisper.app.clipboard.write_and_paste") as mock_paste,
    ):
        result = _run_command_pipeline("original", "translate to French")

    mock_llm.assert_called_once_with("original", "translate to French")
    mock_paste.assert_called_once_with("")
    assert result == ""
