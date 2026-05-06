"""Shared pytest fixtures."""

from __future__ import annotations

from unittest.mock import MagicMock


def make_openai_response(content: str) -> MagicMock:
    """Build a mock OpenAI chat completion response with the given content."""
    msg = MagicMock()
    msg.content = content
    choice = MagicMock()
    choice.message = msg
    resp = MagicMock()
    resp.choices = [choice]
    return resp


def make_openai_client(content: str) -> tuple[MagicMock, MagicMock]:
    """Return (mock_openai_module, mock_client) with chat response returning content."""
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = make_openai_response(content)
    mock_openai = MagicMock()
    mock_openai.OpenAI.return_value = mock_client
    return mock_openai, mock_client
