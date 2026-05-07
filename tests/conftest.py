"""Shared pytest fixtures."""

from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def clear_llm_client_cache() -> None:
    """Clear the LLM client cache so each test gets a fresh OpenAI client."""
    from local_whisper import llm

    llm._client_cache.clear()
