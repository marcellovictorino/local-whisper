"""Tests for _run_dictation_pipeline, _run_command_pipeline, and _log_session."""

from __future__ import annotations

import logging
from unittest.mock import MagicMock, patch

import pytest

from local_whisper.app import _log_session, _run_command_pipeline, _run_dictation_pipeline, _SessionMode


@pytest.mark.parametrize(
    ("config_state", "expect_error"),
    [
        ("MALFORMED", True),
        ("MISSING", False),
        ("LOADED", False),
    ],
)
def test_startup_only_signals_a_malformed_initial_config(config_state: str, expect_error: bool) -> None:
    """Startup must surface a parse failure without alarming for empty or absent config."""
    from local_whisper import config
    from local_whisper.app import App

    overlay = MagicMock()
    load = config.ConfigLoad(getattr(config.ConfigState, config_state), {})
    with (
        patch("local_whisper.app.config.load_config", return_value=load),
        patch("local_whisper.app.corrections.load", return_value={}),
        patch("local_whisper.app.transcribe.supports_vocab_prompt", return_value=True),
        patch("local_whisper.app.HotkeyListener") as listener,
        patch("local_whisper.app.signal.signal"),
        patch("local_whisper.app.llm.is_available", return_value=True),
    ):
        app = App(overlay=overlay)
        app.start()

    listener.return_value.start.assert_called_once_with()
    if expect_error:
        overlay.show_error.assert_called_once_with()
    else:
        overlay.show_error.assert_not_called()


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
        result = _run_dictation_pipeline("hello", {"teh": "the"}, adapt_app="Slack")

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


def test_log_session_emits_line_on_failure_outcome(caplog: pytest.LogCaptureFixture) -> None:
    """Failing sessions must still produce a timing line — they are the ones worth investigating."""
    with caplog.at_level(logging.INFO, logger="local_whisper"):
        _log_session(_SessionMode.COMMAND, "llm-unavailable", 2.0, t0=10.0, t_transcribed=10.5)

    assert len(caplog.records) == 1
    line = caplog.records[0].getMessage()
    assert "outcome=llm-unavailable" in line
    assert "transcribe=0.50s" in line
    assert "paste=" not in line


def test_log_session_total_sums_all_stages(caplog: pytest.LogCaptureFixture) -> None:
    """total = record + transcribe + pipeline + paste, so the stages add up."""
    with caplog.at_level(logging.INFO, logger="local_whisper"):
        _log_session(_SessionMode.DICTATION, "ok", 2.0, t0=10.0, t_transcribed=10.5, t_pipeline=10.6, t_pasted=10.7)

    line = caplog.records[0].getMessage()
    assert "outcome=ok" in line
    assert "record=2.0s" in line
    assert "transcribe=0.50s" in line
    assert "pipeline=100ms" in line
    assert "paste=100ms" in line
    assert "total=2.70s" in line
