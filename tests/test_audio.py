"""Tests for audio.record_until_event — output contract."""

import threading
from unittest.mock import MagicMock, patch

import numpy as np

from local_whisper.audio import record_until_event


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

    class FakeInputStream:
        def __init__(self, **kwargs: object) -> None:
            self._callback = kwargs["callback"]

        def __enter__(self) -> "FakeInputStream":
            # Deliver one chunk then unblock wait()
            self._callback(chunk, 1024, None, None)
            stop.set()
            return self

        def __exit__(self, *args: object) -> bool:
            return False

    with patch("sounddevice.InputStream", FakeInputStream):
        result = record_until_event(stop)

    assert result.ndim == 1
    assert result.dtype == np.float32


def test_on_amplitude_called_with_rms_per_chunk() -> None:
    stop = threading.Event()
    chunk = np.ones((512, 1), dtype="float32") * 0.5

    class FakeInputStream:
        def __init__(self, **kwargs: object) -> None:
            self._callback = kwargs["callback"]

        def __enter__(self) -> "FakeInputStream":
            self._callback(chunk, 512, None, None)
            stop.set()
            return self

        def __exit__(self, *args: object) -> bool:
            return False

    amplitudes: list[float] = []
    with patch("sounddevice.InputStream", FakeInputStream):
        result = record_until_event(stop, on_amplitude=amplitudes.append)

    assert len(amplitudes) == 1
    assert abs(amplitudes[0] - 0.5) < 1e-5
    assert result.ndim == 1
