"""Tests for __main__._check_accessibility — Accessibility permission gate."""
from unittest.mock import MagicMock, patch

from local_whisper.__main__ import _check_accessibility


def test_returns_true_when_library_not_found() -> None:
    with patch("ctypes.util.find_library", return_value=None):
        assert _check_accessibility() is True


def test_returns_true_when_process_is_trusted() -> None:
    mock_lib = MagicMock()
    mock_lib.AXIsProcessTrusted.return_value = True
    with patch("ctypes.util.find_library", return_value="/fake/path"), \
         patch("ctypes.cdll.LoadLibrary", return_value=mock_lib):
        assert _check_accessibility() is True


def test_returns_false_when_process_not_trusted() -> None:
    mock_lib = MagicMock()
    mock_lib.AXIsProcessTrusted.return_value = False
    with patch("ctypes.util.find_library", return_value="/fake/path"), \
         patch("ctypes.cdll.LoadLibrary", return_value=mock_lib):
        assert _check_accessibility() is False


def test_returns_true_on_exception() -> None:
    with patch("ctypes.util.find_library", return_value="/fake/path"), \
         patch("ctypes.cdll.LoadLibrary", side_effect=OSError("load failed")):
        assert _check_accessibility() is True
