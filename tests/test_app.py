"""Tests for _run_dictation_pipeline, _run_adapt_pipeline, and _run_command_pipeline."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from local_whisper.app import _run_adapt_pipeline, _run_command_pipeline, _run_dictation_pipeline


def test_dictation_pipeline_order() -> None:
    """Each pipeline step is called in the correct order with correct args."""
    with (
        patch("local_whisper.app.auto_cleanup.apply", return_value="cleaned") as mock_cleanup,
        patch("local_whisper.app.corrections.apply", return_value="corrected") as mock_corrections,
        patch("local_whisper.app.snippets.expand", return_value="expanded") as mock_snippets,
    ):
        result = _run_dictation_pipeline("hello", {"teh": "the"})

    mock_cleanup.assert_called_once_with("hello")
    mock_corrections.assert_called_once_with("cleaned", {"teh": "the"})
    mock_snippets.assert_called_once_with("corrected")
    assert result == "expanded "


def test_dictation_pipeline_never_calls_adapt() -> None:
    """Plain dictation must not invoke the LLM reshaping stage."""
    with (
        patch("local_whisper.app.auto_cleanup.apply", side_effect=lambda t: t),
        patch("local_whisper.app.auto_adapt.apply") as mock_adapt,
        patch("local_whisper.app.snippets.expand", side_effect=lambda t: t),
    ):
        _run_dictation_pipeline("hello", {})

    mock_adapt.assert_not_called()


def test_dictation_pipeline_applies_corrections() -> None:
    """Corrections substitution is applied without mocking (integration-style)."""
    with (
        patch("local_whisper.app.auto_cleanup.apply", side_effect=lambda t: t),
        patch("local_whisper.app.snippets.expand", side_effect=lambda t: t),
    ):
        result = _run_dictation_pipeline("teh world", {"teh": "the"})

    assert result == "the world "


def test_adapt_pipeline_order() -> None:
    """Adapt pipeline: cleanup → adapt → corrections → snippets → trailing space."""
    with (
        patch("local_whisper.app.auto_cleanup.apply", return_value="cleaned") as mock_cleanup,
        patch("local_whisper.app.auto_adapt.apply", return_value="adapted") as mock_adapt,
        patch("local_whisper.app.corrections.apply", return_value="corrected") as mock_corrections,
        patch("local_whisper.app.snippets.expand", return_value="expanded") as mock_snippets,
    ):
        result = _run_adapt_pipeline("hello", "Slack", {"teh": "the"})

    mock_cleanup.assert_called_once_with("hello")
    mock_adapt.assert_called_once_with("cleaned", "Slack")
    mock_corrections.assert_called_once_with("adapted", {"teh": "the"})
    mock_snippets.assert_called_once_with("corrected")
    assert result == "expanded "


def test_command_pipeline() -> None:
    """apply_voice_command is called with correct args and its result returned."""
    with patch("local_whisper.app.llm.apply_voice_command", return_value="fixed") as mock_llm:
        result = _run_command_pipeline("original", "fix grammar")

    mock_llm.assert_called_once_with("original", "fix grammar")
    assert result == "fixed"


def test_command_pipeline_llm_failure_raises() -> None:
    """LLMUnavailable propagates so the caller can preserve the selection."""
    from local_whisper.llm import LLMUnavailable

    with patch("local_whisper.app.llm.apply_voice_command", side_effect=LLMUnavailable("no key")):
        with pytest.raises(LLMUnavailable):
            _run_command_pipeline("original", "translate to French")
