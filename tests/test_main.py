"""Tests for __main__._check_accessibility — Accessibility permission gate."""

import logging
import sys
from unittest.mock import MagicMock, patch

import pytest

from local_whisper.__main__ import _check_accessibility


@pytest.fixture()
def _clean_logger_handlers():
    """Save and restore local_whisper logger handlers to prevent cross-test side-effects."""
    lw_logger = logging.getLogger("local_whisper")
    original = lw_logger.handlers[:]
    lw_logger.handlers.clear()
    yield lw_logger
    lw_logger.handlers.clear()
    lw_logger.handlers.extend(original)


def test_returns_true_when_library_not_found() -> None:
    with patch("ctypes.util.find_library", return_value=None):
        assert _check_accessibility() is True


def test_returns_true_when_process_is_trusted() -> None:
    mock_lib = MagicMock()
    mock_lib.AXIsProcessTrusted.return_value = True
    with (
        patch("ctypes.util.find_library", return_value="/fake/path"),
        patch("ctypes.cdll.LoadLibrary", return_value=mock_lib),
    ):
        assert _check_accessibility() is True


def test_returns_false_when_process_not_trusted() -> None:
    mock_lib = MagicMock()
    mock_lib.AXIsProcessTrusted.return_value = False
    with (
        patch("ctypes.util.find_library", return_value="/fake/path"),
        patch("ctypes.cdll.LoadLibrary", return_value=mock_lib),
    ):
        assert _check_accessibility() is False


def test_returns_true_on_exception() -> None:
    with (
        patch("ctypes.util.find_library", return_value="/fake/path"),
        patch("ctypes.cdll.LoadLibrary", side_effect=OSError("load failed")),
    ):
        assert _check_accessibility() is True


def test_logging_not_configured_on_import(_clean_logger_handlers: logging.Logger) -> None:
    """Importing local_whisper must NOT add handlers to the logger."""
    import local_whisper  # noqa: F401

    assert _clean_logger_handlers.handlers == []


def test_logging_configured_after_main(_clean_logger_handlers: logging.Logger) -> None:
    """main() must configure handlers on the local_whisper logger."""
    from local_whisper.__main__ import main

    with patch.object(sys, "argv", ["local-whisper", "--help"]):
        try:
            main()
        except SystemExit:
            pass

    assert _clean_logger_handlers.handlers
