from __future__ import annotations

import math
import queue
import signal
import time
from collections.abc import Callable
from enum import StrEnum

import objc
from AppKit import (
    NSAnimationContext,
    NSApplication,
    NSColor,
    NSMakeRect,
    NSObject,
    NSPanel,
    NSScreen,
    NSTimer,
    NSVisualEffectView,
    NSWindowCollectionBehaviorCanJoinAllSpaces,
    NSWindowCollectionBehaviorStationary,
    NSWindowStyleMaskBorderless,
)

from local_whisper import theme
from local_whisper._macos import ns_color

# NSFloatingWindowLevel = 5
_FLOATING_LEVEL = 5
# NSVisualEffectMaterialHUDWindow = 15 (dark frosted)
_HUD_MATERIAL = 15
# NSVisualEffectBlendingModeBehindWindow = 0
_BLEND_BEHIND = 0
# NSVisualEffectStateActive = 1
_STATE_ACTIVE = 1
# NSApplicationActivationPolicyAccessory = 2 (no dock icon)
_POLICY_ACCESSORY = 2
# NSBackingStoreBuffered = 2
_BACKING_BUFFERED = 2

_PILL_W = 56.0
_PILL_H = 28.0
_BAR_W = 3.0
_BAR_GAP = 3.0
_N_BARS = 4
_MAX_BAR_H = 18.0
_MIN_BAR_H = 3.0
# Amplitude below this → static bars (no animation)
_IDLE_THRESHOLD = 0.008
# Seconds to keep wave running after amplitude drops below threshold
_HOLD_SECS = 0.5
# EMA weight for incoming amplitude (higher = snappier response)
_AMP_EMA_ALPHA = 0.85

# Bar x positions (centered in pill). 4 bars → 21px span, comfortably inside _PILL_W.
_BAR_SPAN = _N_BARS * _BAR_W + (_N_BARS - 1) * _BAR_GAP  # 21px
_BAR_X_START = (_PILL_W - _BAR_SPAN) / 2
_BAR_X_POSITIONS = [_BAR_X_START + i * (_BAR_W + _BAR_GAP) for i in range(_N_BARS)]

# Per-bar phase offsets: 0.5 rad spread → smooth rolling gradient left-to-right
_BAR_PHASES = [i * 0.5 for i in range(_N_BARS)]

# "Whisper Cut" height envelope (tall, short, TALLEST, short) — the brand mark's
# W silhouette. Normalised to the tallest bar; shapes the SPEAKING peaks only,
# so the pill still reads as the icon when active while staying flat at rest.
_BAR_WEIGHTS = [0.87, 0.65, 1.0, 0.565]


class _Cmd(StrEnum):
    SHOW = "show"
    SHOW_COMMAND = "show_command"
    SHOW_ADAPT = "show_adapt"
    SHOW_ERROR = "show_error"
    PROCESSING = "processing"
    HIDE = "hide"
    QUIT = "quit"
    AMP = "amp"


# Which mode each show command paints. One table instead of a branch per mode, so
# adding a mode is a row here and a colour in theme.py.
_SHOW_MODES = {
    _Cmd.SHOW: theme.Mode.DICTATION,
    _Cmd.SHOW_COMMAND: theme.Mode.COMMAND,
    _Cmd.SHOW_ADAPT: theme.Mode.ADAPT,
    _Cmd.SHOW_ERROR: theme.Mode.ERROR,
}

# Immutable, so built once rather than per fade.
_EASE_STANDARD = objc.lookUpClass("CAMediaTimingFunction").alloc().initWithControlPoints____(*theme.EASE_STANDARD)


_QueueItem = str | tuple[str, float]


class _OverlayController(NSObject):
    """Manages the NSPanel with animated waveform bars. Drains command queue via NSTimer."""

    @objc.python_method
    def setup(self, cmd_queue: queue.Queue[_QueueItem]) -> None:
        self._queue: queue.Queue[_QueueItem] = cmd_queue
        self._on_mode_change: Callable[[theme.Mode | None], None] | None = None
        self._panel: NSPanel | None = None
        self._visible: bool = False
        self._bars: list = []
        self._amplitude: float = 0.0
        self._active: bool = False
        self._mode: theme.Mode = theme.Mode.DICTATION
        self._was_idle: bool = True
        self._last_active_t: float = 0.0  # monotonic time of last above-threshold frame
        self._last_normalized: float = 0.0  # normalized amplitude at last active frame
        self._error_until: float = 0.0  # suppress HIDE until this monotonic timestamp
        self._CATransaction = objc.lookUpClass("CATransaction")

    @objc.python_method
    def set_listener(self, listener: Callable[[theme.Mode | None], None] | None) -> None:
        self._on_mode_change = listener

    @objc.python_method
    def _set_mode(self, mode: theme.Mode | None) -> None:
        """Record the mode and tell any mirroring surface about it.

        Every write to ``_mode`` goes through here: the notification used to hang
        off ``_fade_in``, which meant the processing transition — which changes
        mode without re-showing — never reached the menu-bar item.
        """
        if mode is not None:
            self._mode = mode
        if self._on_mode_change is not None:
            self._on_mode_change(mode)

    def pollQueue_(self, _timer: object) -> None:
        try:
            while True:
                cmd = self._queue.get_nowait()
                match cmd:
                    case _Cmd.SHOW | _Cmd.SHOW_COMMAND | _Cmd.SHOW_ADAPT | _Cmd.SHOW_ERROR:
                        self._active = True
                        self._set_mode(_SHOW_MODES[cmd])
                        if self._mode is theme.Mode.ERROR:
                            self._error_until = time.monotonic() + theme.ERROR_FLASH_SECS
                        self._fade_in()
                    case _Cmd.PROCESSING:
                        # Recording stopped — switch to processing animation without hiding.
                        # The bars keep the session's mode colour: the hue is the mode
                        # signal, and the cadence change alone reads as "working".
                        self._set_mode(theme.Mode.PROCESSING)
                        self._amplitude = 0.0
                        self._was_idle = True
                    case _Cmd.HIDE:
                        if time.monotonic() < self._error_until:
                            pass  # suppressed — error display takes precedence
                        else:
                            self._active = False
                            self._amplitude = 0.0
                            self._fade_out()
                    case _Cmd.QUIT:
                        NSApplication.sharedApplication().terminate_(None)
                        return
                    case (_Cmd.AMP, float() as raw):
                        self._amplitude = _AMP_EMA_ALPHA * raw + (1 - _AMP_EMA_ALPHA) * self._amplitude
        except queue.Empty:
            pass
        self._update_bars()

    @objc.python_method
    def _build_panel(self) -> None:
        screen = NSScreen.mainScreen()
        if screen is None:
            return
        full = screen.frame()
        visible = screen.visibleFrame()
        sw = full.size.width

        x = (sw - _PILL_W) / 2
        y = visible.origin.y + visible.size.height - _PILL_H - 8

        panel = NSPanel.alloc().initWithContentRect_styleMask_backing_defer_(
            NSMakeRect(x, y, _PILL_W, _PILL_H),
            NSWindowStyleMaskBorderless,
            _BACKING_BUFFERED,
            False,
        )
        panel.setLevel_(_FLOATING_LEVEL)
        panel.setOpaque_(False)
        panel.setBackgroundColor_(NSColor.clearColor())
        panel.setAlphaValue_(0.0)
        panel.setIgnoresMouseEvents_(True)
        panel.setHasShadow_(True)
        panel.setHidesOnDeactivate_(False)
        panel.setCollectionBehavior_(NSWindowCollectionBehaviorCanJoinAllSpaces | NSWindowCollectionBehaviorStationary)

        effect = NSVisualEffectView.alloc().initWithFrame_(NSMakeRect(0, 0, _PILL_W, _PILL_H))
        effect.setMaterial_(_HUD_MATERIAL)
        effect.setBlendingMode_(_BLEND_BEHIND)
        effect.setState_(_STATE_ACTIVE)
        effect.setWantsLayer_(True)
        effect.layer().setCornerRadius_(_PILL_H / 2)
        effect.layer().setMasksToBounds_(True)
        effect.layer().setBorderWidth_(1.0)
        effect.layer().setBorderColor_(NSColor.colorWithWhite_alpha_(0.1, 1.0).CGColor())
        panel.setContentView_(effect)

        CALayer = objc.lookUpClass("CALayer")
        for bx in _BAR_X_POSITIONS:
            bar = CALayer.alloc().init()
            bar.setBackgroundColor_(NSColor.whiteColor().CGColor())
            bar.setCornerRadius_(_BAR_W / 2)
            # Bloom geometry: centred, no offset. On frosted dark glass a 3px bar
            # reads thin and dim, and amber and cyan lose most of their identity at
            # that width — the glow is what keeps the mode colour legible without
            # widening the mark. Opacity is per-mode and set in _fade_in.
            bar.setShadowOffset_((0.0, 0.0))
            bar.setShadowRadius_(theme.GLOW_RADIUS)
            initial_h = _MIN_BAR_H
            by = (_PILL_H - initial_h) / 2
            bar.setFrame_(((bx, by), (_BAR_W, initial_h)))
            effect.layer().addSublayer_(bar)
            self._bars.append(bar)

        self._panel = panel

    @objc.python_method
    def _fade_in(self) -> None:
        if self._panel is None:
            self._build_panel()
        if self._panel is None:
            return
        cgcolor = ns_color(theme.MODE_RGB[self._mode]).CGColor()
        # White bars get no bloom: on frosted glass it smears into the pill instead
        # of reading as a signal — and dictation, the common case, then costs the
        # render loop no offscreen blur at all.
        glow_opacity = 0.0 if self._mode in theme.WHITE_MODES else theme.GLOW_ALPHA
        for bar in self._bars:
            bar.setBackgroundColor_(cgcolor)
            bar.setShadowColor_(cgcolor)  # same hue as the bar — the bloom is the bar, blurred
            bar.setShadowOpacity_(glow_opacity)
        self._last_active_t = time.monotonic()
        self._visible = True
        self._panel.orderFrontRegardless()
        self._animate_alpha(theme.HUD_OPACITY)

    @objc.python_method
    def _animate_alpha(self, target: float, on_done: Callable[[], None] | None = None) -> None:
        """Ease the panel's opacity to ``target`` over FADE_SECS.

        Opacity only — no scale, no bounce. Straight ``setAlphaValue_`` made the
        pill pop in hard enough to read as a glitch at the edge of vision.
        """
        if self._panel is None:
            return
        NSAnimationContext.beginGrouping()
        context = NSAnimationContext.currentContext()
        context.setDuration_(theme.FADE_SECS)
        context.setTimingFunction_(_EASE_STANDARD)
        if on_done is not None:
            context.setCompletionHandler_(on_done)
        self._panel.animator().setAlphaValue_(target)
        NSAnimationContext.endGrouping()

    @objc.python_method
    def _fade_out(self) -> None:
        self._active = False  # defensive — ensure bars stop even if called directly
        self._visible = False  # stops bar rendering immediately, before the fade lands
        self._was_idle = True  # reset so next show starts with static bars
        self._last_active_t = 0.0
        self._last_normalized = 0.0
        self._set_mode(None)
        if self._panel is None:
            return
        panel = self._panel

        def _order_out() -> None:
            # Only pull the window if nothing showed it again during the fade.
            if not self._visible:
                panel.orderOut_(None)

        self._animate_alpha(0.0, on_done=_order_out)

    @objc.python_method
    def _draw_bars(self, heights: list[float]) -> None:
        """Centre each bar vertically at the given height."""
        for i, (bar, bar_h) in enumerate(zip(self._bars, heights, strict=True)):
            bar.setFrame_(((_BAR_X_POSITIONS[i], (_PILL_H - bar_h) / 2), (_BAR_W, bar_h)))

    @objc.python_method
    def _render_processing(self, t: float) -> None:
        self._draw_bars(
            [
                max(_MIN_BAR_H, (0.18 + 0.22 * abs(math.sin(t * 4.5 - phase))) * _MAX_BAR_H * weight)
                for phase, weight in zip(_BAR_PHASES, _BAR_WEIGHTS, strict=True)
            ]
        )

    @objc.python_method
    def _speaking_heights(self, normalized: float, t: float) -> list[float]:
        """The rolling W envelope at this amplitude — shared by speech and decay."""
        return [
            max(_MIN_BAR_H, normalized * (0.65 + 0.35 * math.sin(t * 6.0 - phase)) * _MAX_BAR_H * weight)
            for phase, weight in zip(_BAR_PHASES, _BAR_WEIGHTS, strict=True)
        ]

    @objc.python_method
    def _render_waveform(self, t: float) -> None:
        amp = self._amplitude
        if amp >= _IDLE_THRESHOLD:
            self._last_active_t = t
            self._was_idle = False
            self._last_normalized = min(1.0, math.sqrt(amp * 20.0))
            self._draw_bars(self._speaking_heights(self._last_normalized, t))
            return

        hold_elapsed = t - self._last_active_t
        if hold_elapsed < _HOLD_SECS:
            decay = 1.0 - hold_elapsed / _HOLD_SECS
            self._draw_bars(self._speaking_heights(self._last_normalized * decay, t))
        elif not self._was_idle:
            self._draw_bars([_MIN_BAR_H] * len(self._bars))
            self._was_idle = True

    @objc.python_method
    def _update_bars(self) -> None:
        if not self._bars or not self._active:
            return
        # Hard guard: if the panel is hidden, skip CALayer work entirely.
        # CATransaction frame commits on an ordered-out window can cause it to reappear.
        # Tracked as a flag, not read off alphaValue(): during the fade-in alpha is
        # legitimately near zero, and probing it there would stall the animation.
        if self._panel is None or not self._visible:
            self._active = False
            return
        if self._error_until > 0 and time.monotonic() >= self._error_until:
            self._error_until = 0.0
            self._active = False
            self._fade_out()
            return
        t = time.monotonic()
        CT = self._CATransaction
        CT.begin()
        CT.setDisableActions_(True)
        try:
            if self._mode is theme.Mode.PROCESSING:
                self._render_processing(t)
            else:
                self._render_waveform(t)
        finally:
            CT.commit()


class RecordingOverlay:
    """Native macOS pill overlay with animated waveform bars.

    Thread-safe: show()/hide()/update_amplitude()/quit() can be called from any thread.
    run() MUST be called from the main thread — blocks on AppKit event loop.
    """

    def __init__(self) -> None:
        self._queue: queue.Queue[_QueueItem] = queue.Queue()
        self._controller: _OverlayController | None = None
        self._on_mode_change: Callable[[theme.Mode | None], None] | None = None

    def set_mode_listener(self, listener: Callable[[theme.Mode | None], None] | None) -> None:
        """Mirror every mode change to a second surface (the menu-bar item).

        Fires with the mode on show, ``theme.Mode.PROCESSING`` when recording
        stops, and ``None`` on hide. The overlay is the single funnel all mode
        transitions pass through, so the daemon does not notify each surface
        itself. Main thread only — unlike show()/hide(), this does not go through
        the command queue, and the listener is invoked on the render timer.
        """
        self._on_mode_change = listener
        if self._controller is not None:
            self._controller.set_listener(listener)

    def show(self) -> None:
        """Fade in the overlay (dictation mode). Thread-safe."""
        self._queue.put(_Cmd.SHOW)

    def show_command(self) -> None:
        """Fade in the overlay (command mode, amber bars). Thread-safe."""
        self._queue.put(_Cmd.SHOW_COMMAND)

    def show_adapt(self) -> None:
        """Fade in the overlay (auto-adapt mode, cyan bars). Thread-safe."""
        self._queue.put(_Cmd.SHOW_ADAPT)

    def show_error(self) -> None:
        """Flash overlay red for ~1s to signal a transient error. Thread-safe."""
        self._queue.put(_Cmd.SHOW_ERROR)

    def set_processing(self) -> None:
        """Switch to processing animation after recording stops. Thread-safe."""
        self._queue.put(_Cmd.PROCESSING)

    def hide(self) -> None:
        """Fade out the overlay. Thread-safe."""
        self._queue.put(_Cmd.HIDE)

    def update_amplitude(self, value: float) -> None:
        """Feed audio RMS amplitude to the waveform animation. Thread-safe."""
        self._queue.put((_Cmd.AMP, value))

    def quit(self) -> None:
        """Exit the AppKit event loop. Thread-safe."""
        self._queue.put(_Cmd.QUIT)

    def run(self, on_ready: Callable[[], None] | None = None) -> None:
        """Start AppKit event loop on main thread. Blocks until quit() is called.

        ``on_ready`` runs once, on the main thread, after the shared
        NSApplication and accessory policy are set up but before the event loop
        starts — the correct context for attaching extra AppKit UI (e.g. the
        menu-bar status item) to this same app instance.
        """
        app = NSApplication.sharedApplication()
        app.setActivationPolicy_(_POLICY_ACCESSORY)

        controller = _OverlayController.alloc().init()
        controller.setup(self._queue)
        controller.set_listener(self._on_mode_change)
        self._controller = controller

        NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(
            0.033, controller, b"pollQueue:", None, True
        )

        signal.signal(signal.SIGINT, lambda _s, _f: app.terminate_(None))

        if on_ready is not None:
            on_ready()

        app.run()
