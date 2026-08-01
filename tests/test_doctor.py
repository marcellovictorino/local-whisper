"""Tests for __main__._doctor — the health-check exit-code contract.

The point of doctor is to make silent failure modes loud in *both* output and
exit code. These tests pin the criticality rules: Accessibility and a cached
model are fatal (exit non-zero); a missing launchd service or LLM env vars are
warnings only (still exit 0 when the criticals pass).
"""

from contextlib import ExitStack
from unittest.mock import patch

import pytest

from local_whisper.__main__ import _doctor


@pytest.fixture()
def all_pass() -> ExitStack:
    """Patch every underlying check to its healthy state, LLM env vars absent.

    Yields the ExitStack so a test can override one check (e.g. flip
    Accessibility off) on top of an otherwise-green baseline.
    """
    with ExitStack() as stack:
        stack.enter_context(patch("platform.system", return_value="Darwin"))
        stack.enter_context(patch("local_whisper.__main__._check_accessibility", return_value=True))
        stack.enter_context(patch("local_whisper.transcribe.get_model", return_value="some/model"))
        stack.enter_context(patch("local_whisper.transcribe._model_is_cached", return_value=True))
        stack.enter_context(patch("local_whisper.__main__._service_loaded", return_value=True))
        stack.enter_context(patch.dict("os.environ", {}, clear=True))
        yield stack


@pytest.mark.usefixtures("all_pass")
def test_all_pass_exits_zero() -> None:
    assert _doctor() == 0


def test_missing_accessibility_exits_nonzero(all_pass: ExitStack) -> None:
    """No Accessibility grant means no keystroke synthesis — dictation is dead."""
    all_pass.enter_context(patch("local_whisper.__main__._check_accessibility", return_value=False))
    assert _doctor() != 0


def test_model_not_cached_exits_nonzero(all_pass: ExitStack) -> None:
    """A missing model means transcription can't run — fatal."""
    all_pass.enter_context(patch("local_whisper.transcribe._model_is_cached", return_value=False))
    assert _doctor() != 0


@pytest.mark.usefixtures("all_pass")
def test_missing_llm_env_vars_still_exits_zero() -> None:
    """LLM features are optional; plain dictation is fully local, so absent env
    vars are a warning, not a failure. The all_pass fixture clears os.environ,
    so no LLM env vars are set here."""
    assert _doctor() == 0


def test_service_not_loaded_still_exits_zero(all_pass: ExitStack) -> None:
    """The daemon is a convenience; `just run` works without it, so a
    not-loaded service is a warning, not a failure."""
    all_pass.enter_context(patch("local_whisper.__main__._service_loaded", return_value=False))
    assert _doctor() == 0
