"""Tests for command.get_selection and command.apply_command."""

from unittest.mock import MagicMock, patch

from local_whisper.command import apply_command, get_selection


def _mock_pasteboard(count_before: int, count_after: int, text: str) -> MagicMock:
    """Return mock _NSPasteboard with given changeCount sequence and stringForType_ value."""
    mock_pb = MagicMock()
    mock_pb.changeCount.side_effect = [count_before, count_after]
    mock_pb.stringForType_.return_value = text
    mock_NS = MagicMock()
    mock_NS.generalPasteboard.return_value = mock_pb
    return mock_NS


def _mock_llm_openai(text: str) -> tuple[MagicMock, MagicMock]:
    """Return (mock_openai_module, mock_client) wired to return text from chat completion."""
    msg = MagicMock()
    msg.content = text
    choice = MagicMock()
    choice.message = msg
    resp = MagicMock()
    resp.choices = [choice]
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = resp
    mock_openai = MagicMock()
    mock_openai.OpenAI.return_value = mock_client
    return mock_openai, mock_client


# --- get_selection: NSPasteboard changeCount path ---


def test_get_selection_returns_text_when_count_increments():
    mock_NS = _mock_pasteboard(5, 6, "selected text")
    with (
        patch("local_whisper.command._HAS_APPKIT", True),
        patch("local_whisper.command._NSPasteboard", mock_NS),
        patch("subprocess.run"),
        patch("time.sleep"),
    ):
        assert get_selection() == "selected text"


def test_get_selection_returns_empty_when_count_unchanged():
    mock_NS = _mock_pasteboard(5, 5, "whatever")
    with (
        patch("local_whisper.command._HAS_APPKIT", True),
        patch("local_whisper.command._NSPasteboard", mock_NS),
        patch("subprocess.run"),
        patch("time.sleep"),
    ):
        assert get_selection() == ""


def test_get_selection_detects_selection_when_text_equals_prior_clipboard():
    """Bug-fix: selected text identical to prior clipboard must still activate command mode."""
    # Simulates: dictated "my long thoughts", then user selects that exact text
    mock_NS = _mock_pasteboard(10, 11, "my long thoughts")
    with (
        patch("local_whisper.command._HAS_APPKIT", True),
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
        patch("local_whisper.command._HAS_APPKIT", True),
        patch("local_whisper.command._NSPasteboard", mock_NS),
        patch("subprocess.run"),
        patch("time.sleep"),
    ):
        assert get_selection() == ""


def test_get_selection_returns_empty_on_subprocess_error_appkit():
    mock_NS = MagicMock()
    mock_NS.generalPasteboard.return_value.changeCount.return_value = 1
    with (
        patch("local_whisper.command._HAS_APPKIT", True),
        patch("local_whisper.command._NSPasteboard", mock_NS),
        patch("subprocess.run", side_effect=Exception("osascript failed")),
    ):
        assert get_selection() == ""


# --- get_selection: string comparison fallback (no AppKit) ---


def test_get_selection_fallback_returns_text_when_clipboard_changed():
    with (
        patch("local_whisper.command._HAS_APPKIT", False),
        patch("pyperclip.paste", side_effect=["old text", "selected text"]),
        patch("subprocess.run"),
        patch("time.sleep"),
    ):
        assert get_selection() == "selected text"


def test_get_selection_fallback_returns_empty_when_clipboard_unchanged():
    with (
        patch("local_whisper.command._HAS_APPKIT", False),
        patch("pyperclip.paste", return_value="same text"),
        patch("subprocess.run"),
        patch("time.sleep"),
    ):
        assert get_selection() == ""


def test_get_selection_fallback_returns_empty_on_subprocess_error():
    with (
        patch("local_whisper.command._HAS_APPKIT", False),
        patch("pyperclip.paste", return_value="old"),
        patch("subprocess.run", side_effect=Exception("osascript failed")),
    ):
        assert get_selection() == ""


# --- apply_command ---


def test_apply_command_returns_voice_command_when_no_api_key(monkeypatch):
    monkeypatch.delenv("LOCAL_WHISPER_OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    assert apply_command("hello world", "make this uppercase") == "make this uppercase"


def test_apply_command_calls_api_and_returns_text(monkeypatch):
    monkeypatch.setenv("LOCAL_WHISPER_OPENAI_API_KEY", "sk-test")
    mock_openai, mock_client = _mock_llm_openai("HELLO WORLD")

    with patch("local_whisper.llm.openai", mock_openai):
        result = apply_command("hello world", "make this uppercase")

    assert result == "HELLO WORLD"
    call_kwargs = mock_client.chat.completions.create.call_args.kwargs
    assert call_kwargs["model"] == "gpt-4o-mini"
    assert "max_completion_tokens" in call_kwargs
    assert "max_tokens" not in call_kwargs
    user_msg = next(m for m in call_kwargs["messages"] if m["role"] == "user")
    assert "make this uppercase" in user_msg["content"]
    assert "hello world" in user_msg["content"]


def test_apply_command_uses_custom_model(monkeypatch):
    monkeypatch.setenv("LOCAL_WHISPER_OPENAI_API_KEY", "sk-test")
    monkeypatch.setenv("LOCAL_WHISPER_COMMAND_MODEL", "gpt-4o")
    mock_openai, mock_client = _mock_llm_openai("HELLO WORLD")

    with patch("local_whisper.llm.openai", mock_openai):
        apply_command("hello world", "make this uppercase")

    assert mock_client.chat.completions.create.call_args.kwargs["model"] == "gpt-4o"


def test_apply_command_uses_custom_base_url(monkeypatch):
    monkeypatch.setenv("LOCAL_WHISPER_OPENAI_API_KEY", "sk-test")
    monkeypatch.setenv("LOCAL_WHISPER_OPENAI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta/openai/")
    mock_openai, _ = _mock_llm_openai("result")

    with patch("local_whisper.llm.openai", mock_openai):
        apply_command("text", "command")

    assert mock_openai.OpenAI.call_args.kwargs["base_url"] == "https://generativelanguage.googleapis.com/v1beta/openai/"


def test_apply_command_returns_voice_command_on_import_error(monkeypatch):
    monkeypatch.setenv("LOCAL_WHISPER_OPENAI_API_KEY", "sk-test")
    with patch("local_whisper.llm.openai", None):
        assert apply_command("hello world", "make this uppercase") == "make this uppercase"


def test_apply_command_returns_voice_command_on_api_error(monkeypatch):
    monkeypatch.setenv("LOCAL_WHISPER_OPENAI_API_KEY", "sk-test")
    mock_client = MagicMock()
    mock_client.chat.completions.create.side_effect = Exception("API error")
    mock_openai = MagicMock()
    mock_openai.OpenAI.return_value = mock_client

    with patch("local_whisper.llm.openai", mock_openai):
        assert apply_command("hello world", "make this uppercase") == "make this uppercase"


def test_apply_command_handles_empty_selection(monkeypatch):
    monkeypatch.setenv("LOCAL_WHISPER_OPENAI_API_KEY", "sk-test")
    mock_openai, _ = _mock_llm_openai("A cat sat in the sun")

    with patch("local_whisper.llm.openai", mock_openai):
        assert apply_command("", "write a haiku about cats") == "A cat sat in the sun"
