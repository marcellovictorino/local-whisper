"""Tests for __main__._check_accessibility — Accessibility permission gate."""

import importlib
import logging
import sys
from unittest.mock import MagicMock, patch

from local_whisper.__main__ import _check_accessibility


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


def test_logging_not_configured_on_import() -> None:
    """Importing local_whisper must NOT add handlers to the logger."""
    import local_whisper

    lw_logger = logging.getLogger("local_whisper")
    # Clear any handlers that may have been configured by a prior main() call
    # in this test session, then reload to verify import does not re-add them.
    lw_logger.handlers.clear()
    importlib.reload(local_whisper)
    assert lw_logger.handlers == [], f"Expected no handlers after import, got: {lw_logger.handlers}"


def test_logging_configured_after_main() -> None:
    """main() must configure handlers on the local_whisper logger."""
    from local_whisper.__main__ import main

    lw_logger = logging.getLogger("local_whisper")
    # Start from a clean slate so the _setup_logging guard does not short-circuit.
    lw_logger.handlers.clear()

    with patch.object(sys, "argv", ["local-whisper", "--help"]):
        try:
            main()
        except SystemExit:
            pass

    assert lw_logger.handlers, "Expected handlers to be configured after main() runs"
