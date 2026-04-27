"""Tests for command.copy_selection and command.apply_command."""
from unittest.mock import MagicMock, patch

from local_whisper.command import apply_command, copy_selection


def _mock_openai(text: str) -> tuple[MagicMock, MagicMock]:
    """Return (mock_openai_module, mock_client) with response returning text."""
    mock_message = MagicMock()
    mock_message.content = text

    mock_choice = MagicMock()
    mock_choice.message = mock_message

    mock_response = MagicMock()
    mock_response.choices = [mock_choice]

    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = mock_response

    mock_openai = MagicMock()
    mock_openai.OpenAI.return_value = mock_client

    return mock_openai, mock_client


def test_apply_command_returns_voice_command_when_no_api_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    result = apply_command("hello world", "make this uppercase")
    assert result == "make this uppercase"


def test_apply_command_calls_api_and_returns_text(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    mock_openai, mock_client = _mock_openai("HELLO WORLD")

    with patch.dict("sys.modules", {"openai": mock_openai}):
        result = apply_command("hello world", "make this uppercase")

    assert result == "HELLO WORLD"
    call_kwargs = mock_client.chat.completions.create.call_args.kwargs
    assert call_kwargs["model"] == "gpt-4o-mini"
    messages = call_kwargs["messages"]
    user_msg = next(m for m in messages if m["role"] == "user")
    assert "make this uppercase" in user_msg["content"]
    assert "hello world" in user_msg["content"]


def test_apply_command_uses_custom_model(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    monkeypatch.setenv("LOCAL_WHISPER_MODEL", "gpt-4o")
    mock_openai, mock_client = _mock_openai("HELLO WORLD")

    with patch.dict("sys.modules", {"openai": mock_openai}):
        apply_command("hello world", "make this uppercase")

    call_kwargs = mock_client.chat.completions.create.call_args.kwargs
    assert call_kwargs["model"] == "gpt-4o"


def test_apply_command_uses_custom_base_url(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    monkeypatch.setenv("OPENAI_BASE_URL", "https://generativelanguage.googleapis.com/v1beta/openai/")
    mock_openai, _ = _mock_openai("result")

    with patch.dict("sys.modules", {"openai": mock_openai}):
        apply_command("text", "command")

    call_kwargs = mock_openai.OpenAI.call_args.kwargs
    assert call_kwargs["base_url"] == "https://generativelanguage.googleapis.com/v1beta/openai/"


def test_apply_command_returns_voice_command_on_api_error(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")

    mock_client = MagicMock()
    mock_client.chat.completions.create.side_effect = Exception("API error")

    mock_openai = MagicMock()
    mock_openai.OpenAI.return_value = mock_client

    with patch.dict("sys.modules", {"openai": mock_openai}):
        result = apply_command("hello world", "make this uppercase")

    assert result == "make this uppercase"


def test_apply_command_handles_empty_selection(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    mock_openai, _ = _mock_openai("A cat sat in the sun")

    with patch.dict("sys.modules", {"openai": mock_openai}):
        result = apply_command("", "write a haiku about cats")

    assert result == "A cat sat in the sun"


def test_copy_selection_calls_osascript_and_returns_clipboard():
    with patch("subprocess.run") as mock_run, \
         patch("pyperclip.paste", return_value="selected text"), \
         patch("time.sleep"):
        result = copy_selection()

    mock_run.assert_called_once()
    cmd_arg = mock_run.call_args.args[0]
    assert "keystroke" in cmd_arg[2]
    assert result == "selected text"


def test_copy_selection_returns_empty_on_subprocess_error():
    with patch("subprocess.run", side_effect=Exception("osascript failed")):
        result = copy_selection()
    assert result == ""
