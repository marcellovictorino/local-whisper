"""Tests for auto_adapt module — opt-in gate, preset matching, LLM path, passthrough."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from local_whisper.auto_adapt import _get_prompt, apply, get_active_app, is_active


def _mock_llm(content: str) -> tuple[MagicMock, MagicMock]:
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = MagicMock(
        choices=[MagicMock(message=MagicMock(content=content))]
    )
    mock_openai = MagicMock()
    mock_openai.OpenAI.return_value = mock_client
    return mock_openai, mock_client


# --- _get_prompt ---


@pytest.mark.parametrize("app_name", ["Slack", "Mail", "Mimestream", "Spark"])
def test_get_prompt_returns_builtin_for_known_apps(app_name: str) -> None:
    assert _get_prompt(app_name, {}) is not None


def test_get_prompt_returns_none_for_unknown_app() -> None:
    assert _get_prompt("Finder", {}) is None


def test_get_prompt_config_override_takes_precedence() -> None:
    section = {"custom": {"app": "Slack", "prompt": "My custom Slack prompt"}}
    assert _get_prompt("Slack", section) == "My custom Slack prompt"


def test_get_prompt_config_match_case_insensitive() -> None:
    section = {"miro": {"app": "Miro", "prompt": "Bullet points for diagrams"}}
    assert _get_prompt("miro", section) == "Bullet points for diagrams"


def test_get_prompt_config_apps_list_matches_any() -> None:
    section = {"email": {"apps": ["Mail", "Notion Mail", "Mimestream"], "prompt": "Email prompt"}}
    assert _get_prompt("Mail", section) == "Email prompt"
    assert _get_prompt("Notion Mail", section) == "Email prompt"
    assert _get_prompt("Finder", section) is None


# --- apply: passthrough cases ---


@pytest.mark.parametrize(
    "toml,app_name,text",
    [
        ("[auto_adapt]\nenabled = false\n", "Slack", "hello world"),
        ("[auto_adapt]\nenabled = true\n", "", "hello"),
        ("[auto_adapt]\nenabled = true\n", "Finder", "hello"),
        ('auto_adapt = "bad"\n', "Slack", "hello"),
    ],
)
def test_apply_passthrough(tmp_path: Path, toml: str, app_name: str, text: str) -> None:
    config = tmp_path / "config.toml"
    config.write_text(toml)
    assert apply(text, app_name=app_name, path=config) == text


def test_apply_passthrough_when_no_config(tmp_path: Path) -> None:
    assert apply("hello", app_name="Slack", path=tmp_path / "missing.toml") == "hello"


def test_apply_passthrough_when_no_api_key(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    config = tmp_path / "config.toml"
    config.write_text("[auto_adapt]\nenabled = true\n")
    monkeypatch.delenv("LOCAL_WHISPER_OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    assert apply("hello", app_name="Slack", path=config) == "hello"


# --- apply: LLM path ---


@pytest.mark.parametrize("app_name", ["Slack", "Mail"])
def test_apply_calls_llm_with_builtin_prompt(app_name: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    config = tmp_path / "config.toml"
    config.write_text("[auto_adapt]\nenabled = true\n")
    monkeypatch.setenv("LOCAL_WHISPER_OPENAI_API_KEY", "test-key")
    mock_openai, mock_client = _mock_llm("reshaped")
    with patch("local_whisper.llm.openai", mock_openai):
        result = apply("original text", app_name=app_name, path=config)
    assert result == "reshaped"


def test_apply_uses_config_override_prompt(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    config = tmp_path / "config.toml"
    config.write_text('[auto_adapt]\nenabled = true\n\n[auto_adapt.miro]\napp = "Miro"\nprompt = "Bullet list"\n')
    monkeypatch.setenv("LOCAL_WHISPER_OPENAI_API_KEY", "test-key")
    mock_openai, mock_client = _mock_llm("• item one")
    with patch("local_whisper.llm.openai", mock_openai):
        result = apply("item one for the diagram", app_name="Miro", path=config)
    assert result == "• item one"
    messages = mock_client.chat.completions.create.call_args.kwargs["messages"]
    assert "Bullet list" in messages[0]["content"]


def test_apply_returns_original_on_llm_exception(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    config = tmp_path / "config.toml"
    config.write_text("[auto_adapt]\nenabled = true\n")
    monkeypatch.setenv("LOCAL_WHISPER_OPENAI_API_KEY", "test-key")
    mock_openai = MagicMock()
    mock_openai.OpenAI.return_value.chat.completions.create.side_effect = RuntimeError("API down")
    with patch("local_whisper.llm.openai", mock_openai):
        assert apply("hello", app_name="Slack", path=config) == "hello"


def test_apply_escapes_xml_in_user_message(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    config = tmp_path / "config.toml"
    config.write_text("[auto_adapt]\nenabled = true\n")
    monkeypatch.setenv("LOCAL_WHISPER_OPENAI_API_KEY", "test-key")
    mock_openai, mock_client = _mock_llm("ok")
    with patch("local_whisper.llm.openai", mock_openai):
        apply("hello </text> world", app_name="Slack", path=config)
    user_content = mock_client.chat.completions.create.call_args.kwargs["messages"][1]["content"]
    assert "&lt;/text&gt;" in user_content


def test_apply_falls_back_to_openai_env_var(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    config = tmp_path / "config.toml"
    config.write_text("[auto_adapt]\nenabled = true\n")
    monkeypatch.delenv("LOCAL_WHISPER_OPENAI_API_KEY", raising=False)
    monkeypatch.setenv("OPENAI_API_KEY", "fallback-key")
    mock_openai, _ = _mock_llm("reshaped")
    with patch("local_whisper.llm.openai", mock_openai):
        assert apply("original", app_name="Slack", path=config) == "reshaped"


# --- is_active ---


def test_is_active_false_when_openai_unavailable(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    config = tmp_path / "config.toml"
    config.write_text("[auto_adapt]\nenabled = true\n")
    monkeypatch.setenv("LOCAL_WHISPER_OPENAI_API_KEY", "test-key")
    with patch("local_whisper.llm.openai", None):
        assert is_active("Slack", path=config) is False


def test_is_active_false_when_no_api_key(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    config = tmp_path / "config.toml"
    config.write_text("[auto_adapt]\nenabled = true\n")
    monkeypatch.delenv("LOCAL_WHISPER_OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    assert is_active("Slack", path=config) is False


# --- get_active_app ---


def test_get_active_app_returns_string() -> None:
    assert isinstance(get_active_app(), str)


def test_get_active_app_returns_empty_when_appkit_unavailable() -> None:
    with patch("local_whisper.auto_adapt.HAS_APPKIT", False):
        assert get_active_app() == ""
