"""Tests for _run_dictation_pipeline, _run_command_pipeline, and _log_session."""

from __future__ import annotations

import logging
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from local_whisper import config
from local_whisper.app import App, _log_session, _run_command_pipeline, _run_dictation_pipeline, _Session, _SessionMode
from local_whisper.transcribe import Backend


@pytest.mark.parametrize(
    ("config_state", "expect_error"),
    [
        (config.ConfigState.MALFORMED, True),
        (config.ConfigState.MISSING, False),
        (config.ConfigState.LOADED, False),
    ],
)
def test_startup_only_signals_a_malformed_initial_config(config_state: config.ConfigState, expect_error: bool) -> None:
    """Startup must surface a parse failure without alarming for empty or absent config."""
    overlay = MagicMock()
    load = config.ConfigLoad(config_state, {})
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
        patch("local_whisper.app.spelling.apply", return_value="normalised") as mock_spelling,
        patch("local_whisper.app.corrections.apply", return_value="corrected") as mock_corrections,
        patch("local_whisper.app.snippets.expand", return_value="expanded") as mock_snippets,
    ):
        result = _run_dictation_pipeline("hello", {"teh": "the"})

    mock_cleanup.assert_called_once_with("hello")
    mock_spelling.assert_called_once_with("cleaned", None)
    mock_corrections.assert_called_once_with("normalised", {"teh": "the"})
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


def test_dictation_pipeline_corrections_override_spelling() -> None:
    """Personal corrections take precedence over built-in spelling replacements."""
    with (
        patch("local_whisper.app.auto_cleanup.apply", side_effect=lambda t: t),
        patch("local_whisper.app.snippets.expand", side_effect=lambda t: t),
    ):
        result = _run_dictation_pipeline("color", {"colour": "ColorSync"}, "en-GB")

    assert result == "ColorSync "


def test_adapt_pipeline_normalises_before_corrections() -> None:
    """Adapted text is normalised, then personal corrections take precedence."""
    with patch("local_whisper.app.auto_adapt.apply", return_value="color") as mock_adapt:
        result = _run_dictation_pipeline("hello", {"colour": "ColorSync"}, "en-GB", adapt_app="Slack")

    mock_adapt.assert_called_once_with("hello", "Slack")
    assert result == "ColorSync "


def test_adapt_pipeline_order() -> None:
    """Adapt pipeline: cleanup → adapt → spelling → corrections → snippets → trailing space."""
    with (
        patch("local_whisper.app.auto_cleanup.apply", return_value="cleaned") as mock_cleanup,
        patch("local_whisper.app.auto_adapt.apply", return_value="adapted") as mock_adapt,
        patch("local_whisper.app.spelling.apply", return_value="normalised") as mock_spelling,
        patch("local_whisper.app.corrections.apply", return_value="corrected") as mock_corrections,
        patch("local_whisper.app.snippets.expand", return_value="expanded") as mock_snippets,
    ):
        result = _run_dictation_pipeline("hello", {"teh": "the"}, adapt_app="Slack")

    mock_cleanup.assert_called_once_with("hello")
    mock_adapt.assert_called_once_with("cleaned", "Slack")
    mock_spelling.assert_called_once_with("adapted", None)
    mock_corrections.assert_called_once_with("normalised", {"teh": "the"})
    mock_snippets.assert_called_once_with("corrected")
    assert result == "expanded "


def test_command_pipeline() -> None:
    """apply_voice_command is called with correct args and its result returned."""
    with patch("local_whisper.app.llm.apply_voice_command", return_value="fixed") as mock_llm:
        result = _run_command_pipeline("original", "fix grammar")

    mock_llm.assert_called_once_with("original", "fix grammar")
    assert result == "fixed"


def test_command_pipeline_does_not_normalise_spelling() -> None:
    """Commands transform selected text without dictation normalisation."""
    with (
        patch("local_whisper.app.llm.apply_voice_command", return_value="fixed") as mock_llm,
        patch("local_whisper.app.spelling.apply") as mock_spelling,
    ):
        result = _run_command_pipeline("original", "fix grammar")

    mock_llm.assert_called_once_with("original", "fix grammar")
    mock_spelling.assert_not_called()
    assert result == "fixed"


def test_command_pipeline_llm_failure_raises() -> None:
    """LLMUnavailable propagates so the caller can preserve the selection."""
    from local_whisper.llm import LLMUnavailable

    with patch("local_whisper.app.llm.apply_voice_command", side_effect=LLMUnavailable("no key")):
        with pytest.raises(LLMUnavailable):
            _run_command_pipeline("original", "translate to French")


def test_app_builds_one_merged_vocab_prompt_at_startup() -> None:
    """Startup reads vocabulary once and merges it with loaded corrections for Whisper."""
    with (
        patch("local_whisper.app.corrections.load", return_value={"wispy": "Wispr"}) as mock_load,
        patch("local_whisper.app.config.get_vocabulary_words", return_value=["dbt", "tmux"]) as mock_vocabulary,
        patch("local_whisper.app.corrections.build_prompt", return_value="Wispr, dbt, tmux") as mock_build,
    ):
        app = App(backend=Backend.MLX_WHISPER)

    mock_load.assert_called_once_with()
    mock_vocabulary.assert_called_once_with()
    mock_build.assert_called_once_with({"wispy": "Wispr"}, ["dbt", "tmux"])
    assert app._vocab_prompt == "Wispr, dbt, tmux"


def test_reload_refreshes_corrections_and_vocabulary_before_rebuilding_prompt() -> None:
    """SIGHUP replaces both prompt sources then constructs one fresh stored prompt."""
    with (
        patch("local_whisper.app.corrections.load", side_effect=[{"old": "Old"}, {"new": "New"}]) as mock_load,
        patch(
            "local_whisper.app.config.get_vocabulary_words", side_effect=[["old-term"], ["new-term"]]
        ) as mock_vocabulary,
        patch(
            "local_whisper.app.corrections.build_prompt", side_effect=["Old, old-term", "New, new-term"]
        ) as mock_build,
        patch("local_whisper.app.config.invalidate") as mock_invalidate,
    ):
        app = App(backend=Backend.MLX_WHISPER)
        mock_load.reset_mock()
        mock_vocabulary.reset_mock()
        mock_build.reset_mock()
        app._reload_config()

    mock_invalidate.assert_called_once_with()
    mock_load.assert_called_once_with()
    mock_vocabulary.assert_called_once_with()
    mock_build.assert_called_once_with({"new": "New"}, ["new-term"])
    assert app._vocab_prompt == "New, new-term"


def test_reloaded_spelling_preference_changes_next_dictation_output() -> None:
    """SIGHUP applies the new spelling preference to the next dictation session."""
    with (
        patch("local_whisper.app.corrections.load", return_value={}),
        patch("local_whisper.app.config.get_whisper_spelling", side_effect=["en-US", "en-GB"]),
        patch("local_whisper.app.config.get_vocabulary_words", return_value=[]),
        patch("local_whisper.app.config.invalidate"),
        patch("local_whisper.app.audio.record_until_event", return_value=np.ones(4_800, dtype="float32")),
        patch("local_whisper.app.transcribe.wait_warmed", return_value=True),
        patch("local_whisper.app.transcribe.run", return_value="color"),
        patch("local_whisper.app.clipboard.write_and_paste") as mock_paste,
    ):
        app = App(backend=Backend.MLX_WHISPER)
        app._reload_config()
        app._run_session(_Session(mode=_SessionMode.DICTATION))

    mock_paste.assert_called_once_with("colour ")


def test_dictation_session_uses_stored_prompt_without_reloading_or_rebuilding() -> None:
    """The dictation hot path must use the startup prompt, not read configuration."""
    with (
        patch("local_whisper.app.corrections.load", return_value={}),
        patch("local_whisper.app.config.get_vocabulary_words", return_value=["dbt"]),
        patch("local_whisper.app.corrections.build_prompt", return_value="dbt"),
    ):
        app = App(backend=Backend.MLX_WHISPER)

    with (
        patch("local_whisper.app.audio.record_until_event", return_value=np.ones(4_800, dtype="float32")),
        patch("local_whisper.app.transcribe.wait_warmed", return_value=True),
        patch("local_whisper.app.transcribe.run", return_value="hello") as mock_transcribe,
        patch("local_whisper.app.corrections.load", side_effect=AssertionError("session read corrections")),
        patch("local_whisper.app.config.get_vocabulary_words", side_effect=AssertionError("session read vocabulary")),
        patch("local_whisper.app.corrections.build_prompt", side_effect=AssertionError("session rebuilt prompt")),
        patch("local_whisper.app.clipboard.write_and_paste"),
    ):
        app._run_session(_Session(mode=_SessionMode.DICTATION))

    assert mock_transcribe.call_args.kwargs["initial_prompt"] == "dbt"


def test_parakeet_logs_configured_vocabulary_once_across_reloads(caplog: pytest.LogCaptureFixture) -> None:
    """Parakeet reports unavailable vocabulary at startup, not on dictation or reload."""
    with (
        patch("local_whisper.app.corrections.load", return_value={}),
        patch("local_whisper.app.config.get_vocabulary_words", return_value=["dbt"]),
        patch("local_whisper.app.audio.record_until_event", return_value=np.ones(4_800, dtype="float32")),
        patch("local_whisper.app.transcribe.wait_warmed", return_value=True),
        patch("local_whisper.app.transcribe.run", return_value="hello"),
        patch("local_whisper.app.clipboard.write_and_paste"),
        caplog.at_level(logging.INFO, logger="local_whisper"),
    ):
        app = App(backend=Backend.PARAKEET)
        app._run_session(_Session(mode=_SessionMode.DICTATION))
        app._reload_config()
        app._reload_config()

    messages = [record.getMessage() for record in caplog.records]
    message = "Configured vocabulary unavailable on parakeet-mlx; corrections still apply post-transcription."
    assert messages.count(message) == 1


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
