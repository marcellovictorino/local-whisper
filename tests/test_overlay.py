"""Tests for the pill overlay's Whisper Cut render envelope.

Skipped whole-module on headless CI: overlay imports AppKit at module load, so
``importorskip`` skips here exactly where it can't run, matching how the suite
otherwise avoids importing overlay.
"""

from __future__ import annotations

import queue

import pytest

overlay = pytest.importorskip("local_whisper.overlay")


theme = pytest.importorskip("local_whisper.theme")


class _FakeBar:
    """Captures the last frame and glow set on it, so render output is inspectable."""

    def __init__(self) -> None:
        self.height = 0.0
        self.color: object = None
        self.glow: object = None
        self.glow_opacity = 0.0

    def setFrame_(self, frame: tuple[tuple[float, float], tuple[float, float]]) -> None:
        self.height = frame[1][1]

    def setBackgroundColor_(self, color: object) -> None:
        self.color = color

    def setShadowColor_(self, color: object) -> None:
        self.glow = color

    def setShadowOpacity_(self, value: float) -> None:
        self.glow_opacity = value


class _FakePanel:
    """Stands in for the NSPanel, recording the alpha the animator was driven to."""

    def __init__(self) -> None:
        self.alpha = 0.0
        self.ordered_out = False
        self.ordered_front = False

    def animator(self) -> _FakePanel:
        return self

    def setAlphaValue_(self, value: float) -> None:
        self.alpha = value

    def orderFrontRegardless(self) -> None:
        self.ordered_front = True

    def orderOut_(self, _sender: object) -> None:
        self.ordered_out = True


def _controller_with_bars(
    on_mode_change: object = None,
) -> tuple[object, list[_FakeBar]]:
    controller = overlay._OverlayController.alloc().init()
    controller.setup(queue.Queue())
    controller.set_listener(on_mode_change)
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


def test_bars_bloom_in_their_own_mode_hue() -> None:
    """The glow must carry the mode colour — a white bloom would flatten the signal."""
    controller, bars = _controller_with_bars()
    controller._panel = _FakePanel()
    controller._mode = theme.Mode.ADAPT

    controller._fade_in()

    assert all(bar.glow is not None for bar in bars)
    assert all(bar.glow == bar.color for bar in bars)
    assert all(bar.glow_opacity == theme.GLOW_ALPHA for bar in bars)


def test_white_bars_do_not_bloom() -> None:
    """A white bloom smears into the frosted pill instead of reading as a signal."""
    controller, bars = _controller_with_bars()
    controller._panel = _FakePanel()
    controller._mode = theme.Mode.DICTATION

    controller._fade_in()

    assert all(bar.glow_opacity == 0.0 for bar in bars)


def test_showing_eases_the_panel_to_hud_opacity() -> None:
    """Shown alpha is the design system's 0.95, reached through the animator."""
    controller, _bars = _controller_with_bars()
    panel = controller._panel = _FakePanel()
    controller._mode = theme.Mode.DICTATION

    controller._fade_in()

    assert panel.ordered_front
    assert panel.alpha == theme.HUD_OPACITY


def test_hiding_stops_bar_rendering_before_the_fade_lands() -> None:
    """Committing CALayer frames on a fading-out panel can make it reappear."""
    controller, bars = _controller_with_bars()
    controller._panel = _FakePanel()
    controller._mode = theme.Mode.DICTATION
    controller._fade_in()
    controller._active = True
    controller._amplitude = 1.0

    controller._fade_out()
    heights_before = [bar.height for bar in bars]
    controller._update_bars()

    assert [bar.height for bar in bars] == heights_before
    assert controller._active is False


def test_every_mode_transition_reaches_the_listener() -> None:
    """The menu-bar item mirrors the pill through this one callback — including the
    processing transition, which changes mode without re-showing the pill."""
    seen: list[object] = []
    controller, _bars = _controller_with_bars(on_mode_change=seen.append)
    controller._panel = _FakePanel()
    for cmd in (overlay._Cmd.SHOW_COMMAND, overlay._Cmd.PROCESSING, overlay._Cmd.HIDE):
        controller._queue.put(cmd)

    controller.pollQueue_(None)

    assert seen == [theme.Mode.COMMAND, theme.Mode.PROCESSING, None]


def test_idle_pose_is_flat_at_minimum_height() -> None:
    """At rest the pill stays flat — the W silhouette belongs to speaking only."""
    controller, bars = _controller_with_bars()
    controller._amplitude = 0.0
    controller._was_idle = False
    t = 100.0
    controller._last_active_t = t - overlay._HOLD_SECS - 1.0  # hold window expired

    controller._render_waveform(t)

    assert all(bar.height == overlay._MIN_BAR_H for bar in bars)
