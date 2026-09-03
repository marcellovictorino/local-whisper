"""Tests for audio.record_until_event — output contract."""

import logging
import threading
import time
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from local_whisper.audio import record_until_event


class FakeInputStream:
    """Minimal sounddevice.InputStream stub that delivers one chunk and sets the stop event."""

    def __init__(self, chunk: np.ndarray, stop: threading.Event, **kwargs: object) -> None:
        self._callback = kwargs["callback"]
        self._chunk = chunk
        self._stop = stop

    def __enter__(self) -> "FakeInputStream":
        frames = len(self._chunk)
        self._callback(self._chunk, frames, None, None)
        self._stop.set()
        return self

    def __exit__(self, *args: object) -> bool:
        return False


def test_returns_empty_array_when_no_audio_captured() -> None:
    stop = threading.Event()
    stop.set()  # stops immediately

    mock_stream = MagicMock()
    mock_stream.__enter__ = MagicMock(return_value=mock_stream)
    mock_stream.__exit__ = MagicMock(return_value=False)

    with patch("sounddevice.InputStream", return_value=mock_stream):
        result = record_until_event(stop)

    assert isinstance(result, np.ndarray)
    assert result.dtype == np.float32
    assert result.shape == (0,)


def test_returns_1d_float32_array() -> None:
    stop = threading.Event()
    chunk = np.ones((1024, 1), dtype="float32") * 0.5

    with patch("sounddevice.InputStream", lambda **kw: FakeInputStream(chunk, stop, **kw)):
        result = record_until_event(stop)

    assert result.ndim == 1
    assert result.dtype == np.float32


def test_on_amplitude_called_with_rms_per_chunk() -> None:
    stop = threading.Event()
    chunk = np.ones((512, 1), dtype="float32") * 0.5

    amplitudes: list[float] = []
    with patch("sounddevice.InputStream", lambda **kw: FakeInputStream(chunk, stop, **kw)):
        result = record_until_event(stop, on_amplitude=amplitudes.append)

    assert len(amplitudes) == 1
    assert abs(amplitudes[0] - 0.5) < 1e-5
    assert result.ndim == 1


class SilentFakeInputStream:
    """Delivers one near-silent chunk on entry, then never sets the stop event.

    Simulates a lost key-release event: the caller's stop_event never fires,
    so only the silence timeout can end the recording.
    """

    def __init__(self, chunk: np.ndarray, **kwargs: object) -> None:
        self._callback = kwargs["callback"]
        self._chunk = chunk

    def __enter__(self) -> "SilentFakeInputStream":
        self._callback(self._chunk, len(self._chunk), None, None)
        return self

    def __exit__(self, *args: object) -> bool:
        return False


def test_silence_timeout_auto_stops_a_recording_whose_stop_event_never_fires(
    caplog: pytest.LogCaptureFixture,
) -> None:
    stop = threading.Event()  # deliberately never set — the case a lost key-release leaves behind
    silent_chunk = np.zeros((512, 1), dtype="float32")

    with (
        patch("sounddevice.InputStream", lambda **kw: SilentFakeInputStream(silent_chunk, **kw)),
        caplog.at_level(logging.INFO, logger="local_whisper"),
    ):
        result = record_until_event(stop, silence_timeout_s=0.05)

    assert not stop.is_set()  # ended by the timeout, not by the caller
    assert result.shape == (512,)
    assert any("Silence timeout" in record.getMessage() for record in caplog.records)


class LoudFakeInputStream:
    """Keeps delivering loud chunks on a background thread until told to stop."""

    def __init__(self, chunk: np.ndarray, **kwargs: object) -> None:
        self._callback = kwargs["callback"]
        self._chunk = chunk
        self._keep_going = threading.Event()
        self._thread: threading.Thread | None = None

    def __enter__(self) -> "LoudFakeInputStream":
        self._keep_going.set()

        def _feed() -> None:
            while self._keep_going.is_set():
                self._callback(self._chunk, len(self._chunk), None, None)
                time.sleep(0.02)

        self._thread = threading.Thread(target=_feed, daemon=True)
        self._thread.start()
        return self

    def __exit__(self, *args: object) -> bool:
        self._keep_going.clear()
        assert self._thread is not None
        self._thread.join()
        return False


def test_continuous_speech_defers_the_silence_timeout(caplog: pytest.LogCaptureFixture) -> None:
    """Speech resets the silence clock, so a long-but-active dictation isn't cut off."""
    stop = threading.Event()
    loud_chunk = np.ones((512, 1), dtype="float32") * 0.5
    threading.Timer(0.15, stop.set).start()  # simulates the key eventually being released

    with (
        patch("sounddevice.InputStream", lambda **kw: LoudFakeInputStream(loud_chunk, **kw)),
        caplog.at_level(logging.INFO, logger="local_whisper"),
    ):
        result = record_until_event(stop, silence_timeout_s=0.05)

    assert result.size > 512  # multiple chunks captured — never cut short by silence
    assert not any("Silence timeout" in record.getMessage() for record in caplog.records)
