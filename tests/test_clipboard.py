"""Tests for clipboard.write_and_paste — fallback behavior."""

import subprocess
from unittest.mock import patch

import pytest

from local_whisper.clipboard import write_and_paste


def test_copies_text_even_when_osascript_fails() -> None:
    copied = []

    with (
        patch("pyperclip.copy", side_effect=lambda t: copied.append(t)),
        patch("subprocess.run", side_effect=subprocess.CalledProcessError(1, "osascript")),
        patch("time.sleep"),
    ):
        write_and_paste("hello world")

    assert copied == ["hello world"]


def test_copies_and_pastes_successfully() -> None:
    copied = []

    with (
        patch("pyperclip.copy", side_effect=lambda t: copied.append(t)),
        patch("subprocess.run") as mock_run,
        patch("time.sleep"),
    ):
        mock_run.return_value = None
        write_and_paste("test text")

    assert copied == ["test text"]
    mock_run.assert_called_once()


def test_settle_ms_sleeps_before_paste() -> None:
    sleep_calls = []

    with (
        patch("pyperclip.copy"),
        patch("subprocess.run"),
        patch("time.sleep", side_effect=lambda s: sleep_calls.append(s)),
    ):
        write_and_paste("hi", settle_ms=150)

    assert sleep_calls and sleep_calls[0] == pytest.approx(0.15)


def test_retries_on_failure_success_on_second_attempt() -> None:
    call_count = []

    def _run_side_effect(*_a, **_kw):
        call_count.append(1)
        if len(call_count) == 1:
            raise subprocess.CalledProcessError(1, "osascript")

    with (
        patch("pyperclip.copy"),
        patch("subprocess.run", side_effect=_run_side_effect),
        patch("time.sleep"),
    ):
        write_and_paste("hello", retries=1)

    assert len(call_count) == 2


def test_paste_call_has_a_timeout() -> None:
    """A hung osascript/System Events call must not wedge the session thread forever."""
    with (
        patch("pyperclip.copy"),
        patch("subprocess.run") as mock_run,
        patch("time.sleep"),
    ):
        write_and_paste("hi")

    assert mock_run.call_args.kwargs["timeout"] == 10


def test_timeout_expired_is_treated_like_a_failed_paste() -> None:
    """A stalled osascript call must be caught, not left to hang the session."""
    copied = []

    with (
        patch("pyperclip.copy", side_effect=lambda t: copied.append(t)),
        patch("subprocess.run", side_effect=subprocess.TimeoutExpired("osascript", 10)),
        patch("time.sleep"),
        patch("local_whisper.clipboard.logger") as mock_logger,
    ):
        write_and_paste("hello")

    assert copied == ["hello"]
    mock_logger.warning.assert_called_once()
    assert "timed out" in mock_logger.warning.call_args[0]


def test_all_retries_exhausted_logs_warning_and_preserves_clipboard() -> None:
    copied = []

    with (
        patch("pyperclip.copy", side_effect=lambda t: copied.append(t)),
        patch("subprocess.run", side_effect=subprocess.CalledProcessError(1, "osascript")),
        patch("time.sleep"),
        patch("local_whisper.clipboard.logger") as mock_logger,
    ):
        write_and_paste("data", retries=1)

    assert copied == ["data"]
    mock_logger.warning.assert_called_once()
    warning_args = mock_logger.warning.call_args[0]
    assert 2 in warning_args
