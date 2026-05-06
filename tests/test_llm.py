"""Tests for llm.transform() — all success/fallback branches."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest


def _make_response(content: str) -> MagicMock:
    msg = MagicMock()
    msg.content = content
    choice = MagicMock()
    choice.message = msg
    resp = MagicMock()
    resp.choices = [choice]
    return resp


def _mock_openai(content: str) -> tuple[MagicMock, MagicMock]:
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = _make_response(content)
    mock_openai = MagicMock()
    mock_openai.OpenAI.return_value = mock_client
    return mock_openai, mock_client


# --- import-time safety ---


def test_module_imports_without_openai() -> None:
    with patch("local_whisper.llm.openai", None):
        from local_whisper import llm  # noqa: F401 — just confirming no crash


# --- fallback: missing API key ---


def test_returns_fallback_when_no_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("LOCAL_WHISPER_OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    from local_whisper.llm import transform

    assert transform("sys", "user", default_model="m", fallback="FALLBACK") == "FALLBACK"


def test_uses_openai_api_key_env_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("LOCAL_WHISPER_OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("OPENAI_API_KEY", "sk-fallback")
    mock_openai, mock_client = _mock_openai("ok")
    mock_client.chat.completions.create.return_value = _make_response("ok")

    with patch("local_whisper.llm.openai", mock_openai):
        from local_whisper.llm import transform

        result = transform("sys", "user", default_model="m", fallback="FALLBACK")

    assert result == "ok"


# --- fallback: openai package unavailable ---


def test_returns_fallback_when_openai_none(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LOCAL_WHISPER_OPENAI_API_KEY", "sk-test")
    with patch("local_whisper.llm.openai", None):
        from local_whisper.llm import transform

        assert transform("sys", "user", default_model="m", fallback="FALLBACK") == "FALLBACK"


# --- fallback: API exception ---


def test_returns_fallback_on_api_exception(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LOCAL_WHISPER_OPENAI_API_KEY", "sk-test")
    mock_openai = MagicMock()
    mock_openai.OpenAI.return_value.chat.completions.create.side_effect = RuntimeError("down")

    with patch("local_whisper.llm.openai", mock_openai):
        from local_whisper.llm import transform

        assert transform("sys", "user", default_model="m", fallback="FALLBACK") == "FALLBACK"


# --- success path ---


def test_returns_response_content(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LOCAL_WHISPER_OPENAI_API_KEY", "sk-test")
    mock_openai, mock_client = _mock_openai("transformed text")

    with patch("local_whisper.llm.openai", mock_openai):
        from local_whisper.llm import transform

        result = transform("do X", "input", default_model="gpt-4o-mini", fallback="F")

    assert result == "transformed text"
    call = mock_client.chat.completions.create.call_args.kwargs
    assert call["max_completion_tokens"] == 4096
    assert call["messages"][0] == {"role": "system", "content": "do X"}
    assert call["messages"][1] == {"role": "user", "content": "input"}


def test_uses_local_whisper_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LOCAL_WHISPER_OPENAI_API_KEY", "sk-local")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    mock_openai, _ = _mock_openai("ok")

    with patch("local_whisper.llm.openai", mock_openai):
        from local_whisper.llm import transform

        transform("sys", "user", default_model="m", fallback="F")

    assert mock_openai.OpenAI.call_args.kwargs["api_key"] == "sk-local"


# --- env var overrides ---


def test_respects_command_model_override(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LOCAL_WHISPER_OPENAI_API_KEY", "sk-test")
    monkeypatch.setenv("LOCAL_WHISPER_COMMAND_MODEL", "gpt-4o")
    mock_openai, mock_client = _mock_openai("ok")

    with patch("local_whisper.llm.openai", mock_openai):
        from local_whisper.llm import transform

        transform("sys", "user", default_model="gpt-4o-mini", fallback="F")

    assert mock_client.chat.completions.create.call_args.kwargs["model"] == "gpt-4o"


def test_uses_default_model_when_no_override(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LOCAL_WHISPER_OPENAI_API_KEY", "sk-test")
    monkeypatch.delenv("LOCAL_WHISPER_COMMAND_MODEL", raising=False)
    mock_openai, mock_client = _mock_openai("ok")

    with patch("local_whisper.llm.openai", mock_openai):
        from local_whisper.llm import transform

        transform("sys", "user", default_model="gpt-4o-mini", fallback="F")

    assert mock_client.chat.completions.create.call_args.kwargs["model"] == "gpt-4o-mini"


def test_sets_base_url_when_provided(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LOCAL_WHISPER_OPENAI_API_KEY", "sk-test")
    monkeypatch.setenv("LOCAL_WHISPER_OPENAI_BASE_URL", "https://api.example.com/v1/")
    mock_openai, _ = _mock_openai("ok")

    with patch("local_whisper.llm.openai", mock_openai):
        from local_whisper.llm import transform

        transform("sys", "user", default_model="m", fallback="F")

    assert mock_openai.OpenAI.call_args.kwargs["base_url"] == "https://api.example.com/v1/"


def test_no_base_url_when_not_set(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LOCAL_WHISPER_OPENAI_API_KEY", "sk-test")
    monkeypatch.delenv("LOCAL_WHISPER_OPENAI_BASE_URL", raising=False)
    mock_openai, _ = _mock_openai("ok")

    with patch("local_whisper.llm.openai", mock_openai):
        from local_whisper.llm import transform

        transform("sys", "user", default_model="m", fallback="F")

    assert "base_url" not in mock_openai.OpenAI.call_args.kwargs


# --- escape=True ---


def test_escape_wraps_and_html_escapes_user(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LOCAL_WHISPER_OPENAI_API_KEY", "sk-test")
    mock_openai, mock_client = _mock_openai("ok")

    with patch("local_whisper.llm.openai", mock_openai):
        from local_whisper.llm import transform

        transform("sys", "hello <b>world</b>", default_model="m", fallback="F", escape=True)

    user_content = mock_client.chat.completions.create.call_args.kwargs["messages"][1]["content"]
    assert user_content == "<text>hello &lt;b&gt;world&lt;/b&gt;</text>"


def test_no_escape_sends_user_text_verbatim(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LOCAL_WHISPER_OPENAI_API_KEY", "sk-test")
    mock_openai, mock_client = _mock_openai("ok")

    with patch("local_whisper.llm.openai", mock_openai):
        from local_whisper.llm import transform

        transform("sys", "raw <text>", default_model="m", fallback="F")

    user_content = mock_client.chat.completions.create.call_args.kwargs["messages"][1]["content"]
    assert user_content == "raw <text>"


# --- response content=None fallback ---


def test_returns_fallback_when_response_content_is_none(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LOCAL_WHISPER_OPENAI_API_KEY", "sk-test")
    msg = MagicMock()
    msg.content = None
    choice = MagicMock()
    choice.message = msg
    resp = MagicMock()
    resp.choices = [choice]
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = resp
    mock_openai = MagicMock()
    mock_openai.OpenAI.return_value = mock_client

    with patch("local_whisper.llm.openai", mock_openai):
        from local_whisper.llm import transform

        assert transform("sys", "user", default_model="m", fallback="FALLBACK") == "FALLBACK"


# --- intention-level functions ---


def test_apply_voice_command_sends_correct_messages(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LOCAL_WHISPER_OPENAI_API_KEY", "sk-test")
    mock_openai, mock_client = _mock_openai("result")
    with patch("local_whisper.llm.openai", mock_openai):
        from local_whisper.llm import apply_voice_command

        result = apply_voice_command("selected text", "make uppercase")
    assert result == "result"
    msgs = mock_client.chat.completions.create.call_args.kwargs["messages"]
    assert msgs[1]["content"] == "make uppercase\n\nselected text"


def test_apply_voice_command_fallback_is_instruction(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("LOCAL_WHISPER_OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    from local_whisper.llm import apply_voice_command

    assert apply_voice_command("some text", "translate to French") == "translate to French"


def test_reshape_for_app_escapes_text_and_uses_prompt(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LOCAL_WHISPER_OPENAI_API_KEY", "sk-test")
    mock_openai, mock_client = _mock_openai("reshaped")
    with patch("local_whisper.llm.openai", mock_openai):
        from local_whisper.llm import reshape_for_app

        result = reshape_for_app("hello <world>", "Casual Slack message.")
    assert result == "reshaped"
    call = mock_client.chat.completions.create.call_args.kwargs
    assert "Casual Slack message." in call["messages"][0]["content"]
    assert "&lt;world&gt;" in call["messages"][1]["content"]


def test_reshape_for_app_fallback_is_original_text(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("LOCAL_WHISPER_OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    from local_whisper.llm import reshape_for_app

    assert reshape_for_app("original text", "some prompt") == "original text"
