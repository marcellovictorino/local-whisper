"""Tests for command.get_selection."""

from unittest.mock import MagicMock, patch

from local_whisper.command import get_selection


def _mock_pasteboard(count_before: int, count_after: int, text: str) -> MagicMock:
    """Return mock NSPasteboard with given changeCount sequence and stringForType_ value."""
    mock_pb = MagicMock()
    mock_pb.changeCount.side_effect = [count_before, count_after]
    mock_pb.stringForType_.return_value = text
    mock_NS = MagicMock()
    mock_NS.generalPasteboard.return_value = mock_pb
    return mock_NS


# --- get_selection: NSPasteboard changeCount path ---


def test_get_selection_returns_text_when_count_increments():
    mock_NS = _mock_pasteboard(5, 6, "selected text")
    with (
        patch("local_whisper.command.HAS_APPKIT", True),
        patch("local_whisper.command._NSPasteboard", mock_NS),
        patch("subprocess.run"),
        patch("time.sleep"),
    ):
        assert get_selection() == "selected text"


def test_get_selection_returns_empty_when_count_unchanged():
    mock_NS = _mock_pasteboard(5, 5, "whatever")
    with (
        patch("local_whisper.command.HAS_APPKIT", True),
        patch("local_whisper.command._NSPasteboard", mock_NS),
        patch("subprocess.run"),
        patch("time.sleep"),
    ):
        assert get_selection() == ""


def test_get_selection_detects_selection_when_text_equals_prior_clipboard():
    """Bug-fix: selected text identical to prior clipboard must still activate command mode."""
    mock_NS = _mock_pasteboard(10, 11, "my long thoughts")
    with (
        patch("local_whisper.command.HAS_APPKIT", True),
        patch("local_whisper.command._NSPasteboard", mock_NS),
        patch("subprocess.run"),
        patch("time.sleep"),
    ):
        assert get_selection() == "my long thoughts"


def test_get_selection_returns_empty_when_stringForType_returns_none():
    mock_pb = MagicMock()
    mock_pb.changeCount.side_effect = [3, 4]
    mock_pb.stringForType_.return_value = None
    mock_NS = MagicMock()
    mock_NS.generalPasteboard.return_value = mock_pb
    with (
        patch("local_whisper.command.HAS_APPKIT", True),
        patch("local_whisper.command._NSPasteboard", mock_NS),
        patch("subprocess.run"),
        patch("time.sleep"),
    ):
        assert get_selection() == ""


def test_get_selection_returns_empty_on_subprocess_error_appkit():
    mock_NS = MagicMock()
    mock_NS.generalPasteboard.return_value.changeCount.return_value = 1
    with (
        patch("local_whisper.command.HAS_APPKIT", True),
        patch("local_whisper.command._NSPasteboard", mock_NS),
        patch("subprocess.run", side_effect=Exception("osascript failed")),
    ):
        assert get_selection() == ""


# --- get_selection: string comparison fallback (no AppKit) ---


def test_get_selection_fallback_returns_text_when_clipboard_changed():
    with (
        patch("local_whisper.command.HAS_APPKIT", False),
        patch("pyperclip.paste", side_effect=["old text", "selected text"]),
        patch("subprocess.run"),
        patch("time.sleep"),
    ):
        assert get_selection() == "selected text"


def test_get_selection_fallback_returns_empty_when_clipboard_unchanged():
    with (
        patch("local_whisper.command.HAS_APPKIT", False),
        patch("pyperclip.paste", return_value="same text"),
        patch("subprocess.run"),
        patch("time.sleep"),
    ):
        assert get_selection() == ""


def test_get_selection_fallback_returns_empty_on_subprocess_error():
    with (
        patch("local_whisper.command.HAS_APPKIT", False),
        patch("pyperclip.paste", return_value="old"),
        patch("subprocess.run", side_effect=Exception("osascript failed")),
    ):
        assert get_selection() == ""
