"""Tests for llm.transform(), is_available(), and intention-level helpers."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest


def _mock_openai(content: str) -> tuple[MagicMock, MagicMock]:
    msg = MagicMock()
    msg.content = content
    choice = MagicMock()
    choice.message = msg
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = MagicMock(choices=[choice])
    mock_openai = MagicMock()
    mock_openai.OpenAI.return_value = mock_client
    return mock_openai, mock_client


# --- fallbacks ---


@pytest.mark.parametrize(
    "api_key_env,openai_mod",
    [
        (None, MagicMock()),  # no key
        ("sk-test", None),  # package missing
    ],
)
def test_transform_returns_fallback(monkeypatch: pytest.MonkeyPatch, api_key_env, openai_mod) -> None:
    monkeypatch.delenv("LOCAL_WHISPER_OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    if api_key_env:
        monkeypatch.setenv("LOCAL_WHISPER_OPENAI_API_KEY", api_key_env)
    with patch("local_whisper.llm.openai", openai_mod):
        from local_whisper.llm import transform

        assert transform("sys", "user", default_model="m", fallback="FALLBACK") == "FALLBACK"


def test_transform_returns_fallback_on_api_exception(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LOCAL_WHISPER_OPENAI_API_KEY", "sk-test")
    mock_openai = MagicMock()
    mock_openai.OpenAI.return_value.chat.completions.create.side_effect = RuntimeError("down")
    with patch("local_whisper.llm.openai", mock_openai):
        from local_whisper.llm import transform

        assert transform("sys", "user", default_model="m", fallback="FALLBACK") == "FALLBACK"


def test_transform_returns_fallback_when_content_is_none(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LOCAL_WHISPER_OPENAI_API_KEY", "sk-test")
    mock_openai, _ = _mock_openai(None)  # type: ignore[arg-type]
    with patch("local_whisper.llm.openai", mock_openai):
        from local_whisper.llm import transform

        assert transform("sys", "user", default_model="m", fallback="FALLBACK") == "FALLBACK"


# --- success path ---


def test_transform_sends_correct_messages(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LOCAL_WHISPER_OPENAI_API_KEY", "sk-test")
    mock_openai, mock_client = _mock_openai("transformed text")
    with patch("local_whisper.llm.openai", mock_openai):
        from local_whisper.llm import transform

        result = transform("do X", "input", default_model="gpt-4o-mini", fallback="F")
    assert result == "transformed text"
    call = mock_client.chat.completions.create.call_args.kwargs
    assert call["max_completion_tokens"] == 4096
    assert call["messages"] == [
        {"role": "system", "content": "do X"},
        {"role": "user", "content": "input"},
    ]


def test_transform_uses_local_whisper_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LOCAL_WHISPER_OPENAI_API_KEY", "sk-local")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    mock_openai, _ = _mock_openai("ok")
    with patch("local_whisper.llm.openai", mock_openai):
        from local_whisper.llm import transform

        transform("sys", "user", default_model="m", fallback="F")
    assert mock_openai.OpenAI.call_args.kwargs["api_key"] == "sk-local"


def test_transform_uses_openai_api_key_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("LOCAL_WHISPER_OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("OPENAI_API_KEY", "sk-fallback")
    mock_openai, _ = _mock_openai("ok")
    with patch("local_whisper.llm.openai", mock_openai):
        from local_whisper.llm import transform

        assert transform("sys", "user", default_model="m", fallback="F") == "ok"


# --- env var overrides ---


@pytest.mark.parametrize(
    "model_env,default,expected",
    [
        ("gpt-4o", "gpt-4o-mini", "gpt-4o"),
        (None, "gpt-4o-mini", "gpt-4o-mini"),
    ],
)
def test_transform_model_selection(monkeypatch: pytest.MonkeyPatch, model_env, default, expected) -> None:
    monkeypatch.setenv("LOCAL_WHISPER_OPENAI_API_KEY", "sk-test")
    monkeypatch.delenv("LOCAL_WHISPER_COMMAND_MODEL", raising=False)
    if model_env:
        monkeypatch.setenv("LOCAL_WHISPER_COMMAND_MODEL", model_env)
    mock_openai, mock_client = _mock_openai("ok")
    with patch("local_whisper.llm.openai", mock_openai):
        from local_whisper.llm import transform

        transform("sys", "user", default_model=default, fallback="F")
    assert mock_client.chat.completions.create.call_args.kwargs["model"] == expected


@pytest.mark.parametrize(
    "base_url",
    ["https://api.example.com/v1/", None],
)
def test_transform_base_url(monkeypatch: pytest.MonkeyPatch, base_url) -> None:
    monkeypatch.setenv("LOCAL_WHISPER_OPENAI_API_KEY", "sk-test")
    monkeypatch.delenv("LOCAL_WHISPER_OPENAI_BASE_URL", raising=False)
    if base_url:
        monkeypatch.setenv("LOCAL_WHISPER_OPENAI_BASE_URL", base_url)
    mock_openai, _ = _mock_openai("ok")
    with patch("local_whisper.llm.openai", mock_openai):
        from local_whisper.llm import transform

        transform("sys", "user", default_model="m", fallback="F")
    assert mock_openai.OpenAI.call_args.kwargs["base_url"] == base_url


# --- is_available() ---


@pytest.mark.parametrize(
    "key_env,openai_mod,expected",
    [
        ("sk-test", MagicMock(), True),
        (None, MagicMock(), False),
        ("sk-test", None, False),
    ],
)
def test_is_available(monkeypatch: pytest.MonkeyPatch, key_env, openai_mod, expected) -> None:
    monkeypatch.delenv("LOCAL_WHISPER_OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    if key_env:
        monkeypatch.setenv("LOCAL_WHISPER_OPENAI_API_KEY", key_env)
    with patch("local_whisper.llm.openai", openai_mod):
        from local_whisper.llm import is_available

        assert is_available() is expected


# --- intention-level helpers ---


def test_apply_voice_command_sends_correct_messages(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LOCAL_WHISPER_OPENAI_API_KEY", "sk-test")
    mock_openai, mock_client = _mock_openai("result")
    with patch("local_whisper.llm.openai", mock_openai):
        from local_whisper.llm import apply_voice_command

        result = apply_voice_command("selected text", "make uppercase")
    assert result == "result"
    msgs = mock_client.chat.completions.create.call_args.kwargs["messages"]
    assert msgs[1]["content"] == "make uppercase\n\nselected text"


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


@pytest.mark.parametrize(
    "fn_name,args,expected_fallback",
    [
        ("apply_voice_command", ("some text", "translate to French"), "translate to French"),
        ("reshape_for_app", ("original text", "some prompt"), "original text"),
    ],
)
def test_intention_helpers_fallback_when_no_api_key(
    monkeypatch: pytest.MonkeyPatch, fn_name, args, expected_fallback
) -> None:
    monkeypatch.delenv("LOCAL_WHISPER_OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    import importlib

    mod = importlib.import_module("local_whisper.llm")
    fn = getattr(mod, fn_name)
    assert fn(*args) == expected_fallback
