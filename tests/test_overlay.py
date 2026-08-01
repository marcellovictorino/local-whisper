"""Tests for the pill overlay's Whisper Cut render envelope.

Skipped whole-module on headless CI: overlay imports AppKit at module load, so
``importorskip`` skips here exactly where it can't run, matching how the suite
otherwise avoids importing overlay.
"""

from __future__ import annotations

import queue

import pytest

overlay = pytest.importorskip("local_whisper.overlay")


class _FakeBar:
    """Captures the last frame set on it, so render output is inspectable."""

    def __init__(self) -> None:
        self.height = 0.0

    def setFrame_(self, frame: tuple[tuple[float, float], tuple[float, float]]) -> None:
        self.height = frame[1][1]


def _controller_with_bars() -> tuple[object, list[_FakeBar]]:
    controller = overlay._OverlayController.alloc().init()
    controller.setup(queue.Queue())
    bars = [_FakeBar() for _ in range(overlay._N_BARS)]
    controller._bars = bars
    return controller, bars


def test_pill_has_four_bars_matching_the_mark() -> None:
    assert overlay._N_BARS == 4
    assert len(overlay._BAR_WEIGHTS) == 4
    assert overlay._BAR_SPAN <= overlay._PILL_W


def test_speaking_envelope_peaks_at_the_tallest_weighted_bar() -> None:
    """At one amplitude, each bar's peak over a cycle tracks its W weight."""
    controller, bars = _controller_with_bars()
    controller._amplitude = 1.0  # well above _IDLE_THRESHOLD → normalized == 1.0

    peaks = [0.0] * overlay._N_BARS
    for step in range(240):  # sweep a full oscillation so each bar hits its max
        t = controller._last_active_t = step * 0.02
        controller._render_waveform(t)
        for i, bar in enumerate(bars):
            peaks[i] = max(peaks[i], bar.height)

    # Bar index 2 carries weight 1.0 — it must be the tallest peak.
    assert peaks.index(max(peaks)) == 2
    # Peak ordering follows the weight ordering (envelope, not noise).
    assert [sorted(peaks).index(p) for p in peaks] == [
        sorted(overlay._BAR_WEIGHTS).index(w) for w in overlay._BAR_WEIGHTS
    ]


def test_idle_pose_is_flat_at_minimum_height() -> None:
    """At rest the pill stays flat — the W silhouette belongs to speaking only."""
    controller, bars = _controller_with_bars()
    controller._amplitude = 0.0
    controller._was_idle = False
    t = 100.0
    controller._last_active_t = t - overlay._HOLD_SECS - 1.0  # hold window expired

    controller._render_waveform(t)

    assert all(bar.height == overlay._MIN_BAR_H for bar in bars)
