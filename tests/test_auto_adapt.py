"""Tests for auto_adapt module — opt-in gate, preset matching, LLM path, passthrough."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from local_whisper.auto_adapt import _get_prompt, _is_enabled, apply, get_active_app


# ---------------------------------------------------------------------------
# _is_enabled
# ---------------------------------------------------------------------------

def test_is_enabled_defaults_false_when_file_missing(tmp_path: Path) -> None:
    assert _is_enabled(tmp_path / "nonexistent.toml") is False


def test_is_enabled_false_when_section_absent(tmp_path: Path) -> None:
    config = tmp_path / "config.toml"
    config.write_text("[auto_cleanup]\nenabled = true\n")
    assert _is_enabled(config) is False


def test_is_enabled_false_when_explicitly_false(tmp_path: Path) -> None:
    config = tmp_path / "config.toml"
    config.write_text("[auto_adapt]\nenabled = false\n")
    assert _is_enabled(config) is False


def test_is_enabled_true_when_explicitly_true(tmp_path: Path) -> None:
    config = tmp_path / "config.toml"
    config.write_text("[auto_adapt]\nenabled = true\n")
    assert _is_enabled(config) is True


# ---------------------------------------------------------------------------
# _get_prompt
# ---------------------------------------------------------------------------

def test_get_prompt_returns_builtin_slack() -> None:
    prompt = _get_prompt("Slack", {})
    assert prompt is not None
    assert "Slack" in prompt or "casual" in prompt.lower()


def test_get_prompt_returns_builtin_mail() -> None:
    prompt = _get_prompt("Mail", {})
    assert prompt is not None
    assert "email" in prompt.lower() or "formal" in prompt.lower()


def test_get_prompt_returns_none_for_unknown_app() -> None:
    assert _get_prompt("Finder", {}) is None


def test_get_prompt_config_override_takes_precedence() -> None:
    section = {
        "enabled": True,
        "custom": {"app": "Slack", "prompt": "My custom Slack prompt"},
    }
    assert _get_prompt("Slack", section) == "My custom Slack prompt"


def test_get_prompt_config_match_case_insensitive() -> None:
    section = {"miro": {"app": "Miro", "prompt": "Bullet points for diagrams"}}
    assert _get_prompt("miro", section) == "Bullet points for diagrams"


def test_get_prompt_config_new_app() -> None:
    section = {"notion": {"app": "Notion", "prompt": "Structured notes"}}
    assert _get_prompt("Notion", section) == "Structured notes"


# ---------------------------------------------------------------------------
# apply — passthrough cases
# ---------------------------------------------------------------------------

def test_apply_passthrough_when_disabled(tmp_path: Path) -> None:
    config = tmp_path / "config.toml"
    config.write_text("[auto_adapt]\nenabled = false\n")
    assert apply("hello world", app_name="Slack", path=config) == "hello world"


def test_apply_passthrough_when_no_config(tmp_path: Path) -> None:
    assert apply("hello", app_name="Slack", path=tmp_path / "missing.toml") == "hello"


def test_apply_passthrough_when_app_name_empty(tmp_path: Path) -> None:
    config = tmp_path / "config.toml"
    config.write_text("[auto_adapt]\nenabled = true\n")
    assert apply("hello", app_name="", path=config) == "hello"


def test_apply_passthrough_when_app_unknown(tmp_path: Path) -> None:
    config = tmp_path / "config.toml"
    config.write_text("[auto_adapt]\nenabled = true\n")
    assert apply("hello", app_name="Finder", path=config) == "hello"


def test_apply_passthrough_when_no_api_key(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    config = tmp_path / "config.toml"
    config.write_text("[auto_adapt]\nenabled = true\n")
    monkeypatch.delenv("LOCAL_WHISPER_OPENAI_API_KEY", raising=False)
    assert apply("hello", app_name="Slack", path=config) == "hello"


# ---------------------------------------------------------------------------
# apply — LLM path
# ---------------------------------------------------------------------------

def _make_openai_response(content: str) -> MagicMock:
    msg = MagicMock()
    msg.content = content
    choice = MagicMock()
    choice.message = msg
    resp = MagicMock()
    resp.choices = [choice]
    return resp


def test_apply_calls_llm_with_slack_builtin_prompt(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config = tmp_path / "config.toml"
    config.write_text("[auto_adapt]\nenabled = true\n")
    monkeypatch.setenv("LOCAL_WHISPER_OPENAI_API_KEY", "test-key")

    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = _make_openai_response("hey there 👋")

    with patch("local_whisper.auto_adapt.openai") as mock_openai:
        mock_openai.OpenAI.return_value = mock_client
        result = apply("hello there", app_name="Slack", path=config)

    assert result == "hey there 👋"
    call_kwargs = mock_client.chat.completions.create.call_args
    messages = call_kwargs.kwargs["messages"]
    user_content = messages[1]["content"]
    assert "hello there" in user_content


def test_apply_calls_llm_with_mail_builtin_prompt(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config = tmp_path / "config.toml"
    config.write_text("[auto_adapt]\nenabled = true\n")
    monkeypatch.setenv("LOCAL_WHISPER_OPENAI_API_KEY", "test-key")

    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = _make_openai_response("Dear Sir,")

    with patch("local_whisper.auto_adapt.openai") as mock_openai:
        mock_openai.OpenAI.return_value = mock_client
        result = apply("hey can you fix this", app_name="Mail", path=config)

    assert result == "Dear Sir,"


def test_apply_uses_config_override_prompt(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config = tmp_path / "config.toml"
    config.write_text(
        "[auto_adapt]\nenabled = true\n\n[auto_adapt.miro]\napp = \"Miro\"\nprompt = \"Bullet list\"\n"
    )
    monkeypatch.setenv("LOCAL_WHISPER_OPENAI_API_KEY", "test-key")

    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = _make_openai_response("• item one")

    with patch("local_whisper.auto_adapt.openai") as mock_openai:
        mock_openai.OpenAI.return_value = mock_client
        result = apply("item one for the diagram", app_name="Miro", path=config)

    assert result == "• item one"
    messages = mock_client.chat.completions.create.call_args.kwargs["messages"]
    assert "Bullet list" in messages[1]["content"]


def test_apply_returns_original_on_llm_exception(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config = tmp_path / "config.toml"
    config.write_text("[auto_adapt]\nenabled = true\n")
    monkeypatch.setenv("LOCAL_WHISPER_OPENAI_API_KEY", "test-key")

    mock_client = MagicMock()
    mock_client.chat.completions.create.side_effect = RuntimeError("API down")

    with patch("local_whisper.auto_adapt.openai") as mock_openai:
        mock_openai.OpenAI.return_value = mock_client
        result = apply("hello", app_name="Slack", path=config)

    assert result == "hello"


# ---------------------------------------------------------------------------
# get_active_app
# ---------------------------------------------------------------------------

def test_get_active_app_returns_string() -> None:
    result = get_active_app()
    assert isinstance(result, str)


def test_get_active_app_returns_empty_when_appkit_unavailable() -> None:
    with patch("local_whisper.auto_adapt._HAS_APPKIT", False):
        assert get_active_app() == ""
