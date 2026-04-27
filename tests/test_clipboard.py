"""Tests for clipboard.write_and_paste — fallback behavior."""
import subprocess
from unittest.mock import patch

from local_whisper.clipboard import write_and_paste


def test_copies_text_even_when_osascript_fails() -> None:
    copied = []

    with patch("pyperclip.copy", side_effect=lambda t: copied.append(t)), \
         patch("subprocess.run", side_effect=subprocess.CalledProcessError(1, "osascript")), \
         patch("time.sleep"):
        write_and_paste("hello world")

    assert copied == ["hello world"]


def test_copies_and_pastes_successfully() -> None:
    copied = []

    with patch("pyperclip.copy", side_effect=lambda t: copied.append(t)), \
         patch("subprocess.run") as mock_run, \
         patch("time.sleep"):
        mock_run.return_value = None
        write_and_paste("test text")

    assert copied == ["test text"]
    mock_run.assert_called_once()
