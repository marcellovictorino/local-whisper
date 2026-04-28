from __future__ import annotations

import math
import queue
import signal
import time
from enum import StrEnum

import objc
from AppKit import (
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
_N_BARS = 5
_MAX_BAR_H = 18.0
_MIN_BAR_H = 3.0
# Amplitude below this → static bars (no animation)
_IDLE_THRESHOLD = 0.008
# Seconds to keep wave running after amplitude drops below threshold
_HOLD_SECS = 0.5
# EMA weight for incoming amplitude (higher = snappier response)
_AMP_EMA_ALPHA = 0.85

# Bar x positions (centered in pill)
_BAR_SPAN = _N_BARS * _BAR_W + (_N_BARS - 1) * _BAR_GAP  # 27px
_BAR_X_START = (_PILL_W - _BAR_SPAN) / 2
_BAR_X_POSITIONS = [_BAR_X_START + i * (_BAR_W + _BAR_GAP) for i in range(_N_BARS)]

# Per-bar phase offsets: 0.5 rad spread → smooth rolling gradient left-to-right
_BAR_PHASES = [i * 0.5 for i in range(_N_BARS)]


class _Cmd(StrEnum):
    SHOW = "show"
    SHOW_COMMAND = "show_command"
    PROCESSING = "processing"
    HIDE = "hide"
    QUIT = "quit"
    AMP = "amp"


class _Mode(StrEnum):
    DICTATION = "dictation"
    COMMAND = "command"
    PROCESSING = "processing"


class _OverlayController(NSObject):
    """Manages the NSPanel with animated waveform bars. Drains command queue via NSTimer."""

    @objc.python_method
    def setup(self, cmd_queue: queue.Queue) -> None:
        self._queue = cmd_queue
        self._panel: NSPanel | None = None
        self._bars: list = []
        self._amplitude: float = 0.0
        self._active: bool = False
        self._mode: _Mode = _Mode.DICTATION
        self._was_idle: bool = True
        self._last_active_t: float = 0.0  # monotonic time of last above-threshold frame
        self._CATransaction = objc.lookUpClass("CATransaction")

    def pollQueue_(self, _timer: object) -> None:
        try:
            while True:
                cmd = self._queue.get_nowait()
                if cmd == _Cmd.SHOW:
                    self._active = True
                    self._mode = _Mode.DICTATION
                    self._fade_in()
                elif cmd == _Cmd.SHOW_COMMAND:
                    self._active = True
                    self._mode = _Mode.COMMAND
                    self._fade_in()
                elif cmd == _Cmd.PROCESSING:
                    # Recording stopped — switch to processing animation without hiding.
                    self._mode = _Mode.PROCESSING
                    self._amplitude = 0.0
                    self._was_idle = True
                elif cmd == _Cmd.HIDE:
                    self._active = False
                    self._amplitude = 0.0
                    self._fade_out()
                elif cmd == _Cmd.QUIT:
                    NSApplication.sharedApplication().terminate_(None)
                    return
                elif isinstance(cmd, tuple) and cmd[0] == _Cmd.AMP:
                    raw = cmd[1]
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
        panel.setCollectionBehavior_(
            NSWindowCollectionBehaviorCanJoinAllSpaces
            | NSWindowCollectionBehaviorStationary
        )

        effect = NSVisualEffectView.alloc().initWithFrame_(NSMakeRect(0, 0, _PILL_W, _PILL_H))
        effect.setMaterial_(_HUD_MATERIAL)
        effect.setBlendingMode_(_BLEND_BEHIND)
        effect.setState_(_STATE_ACTIVE)
        effect.setWantsLayer_(True)
        effect.layer().setCornerRadius_(_PILL_H / 2)
        effect.layer().setMasksToBounds_(True)
        effect.layer().setBorderWidth_(1.0)
        effect.layer().setBorderColor_(
            NSColor.colorWithWhite_alpha_(0.1, 1.0).CGColor()
        )
        panel.setContentView_(effect)

        CALayer = objc.lookUpClass("CALayer")
        for bx in _BAR_X_POSITIONS:
            bar = CALayer.alloc().init()
            bar.setBackgroundColor_(NSColor.whiteColor().CGColor())
            bar.setCornerRadius_(_BAR_W / 2)
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
        color = (
            NSColor.colorWithRed_green_blue_alpha_(1.0, 0.76, 0.34, 1.0)
            if self._mode == _Mode.COMMAND
            else NSColor.whiteColor()
        )
        cgcolor = color.CGColor()
        for bar in self._bars:
            bar.setBackgroundColor_(cgcolor)
        self._last_active_t = time.monotonic()
        self._panel.orderFrontRegardless()
        self._panel.setAlphaValue_(0.95)

    @objc.python_method
    def _fade_out(self) -> None:
        self._active = False  # defensive — ensure bars stop even if called directly
        self._was_idle = True  # reset so next show starts with static bars
        self._last_active_t = 0.0  # reset hold timer
        if self._panel is None:
            return
        self._panel.setAlphaValue_(0.0)
        self._panel.orderOut_(None)

    @objc.python_method
    def _update_bars(self) -> None:
        if not self._bars or not self._active:
            return
        # Hard guard: if panel is hidden (alpha=0), skip CALayer work entirely.
        # CATransaction frame commits on an ordered-out window can cause it to reappear.
        if self._panel is None or self._panel.alphaValue() < 0.1:
            self._active = False
            return
        t = time.monotonic()
        amp = self._amplitude
        CT = self._CATransaction
        CT.begin()
        CT.setDisableActions_(True)
        try:
            if self._mode == _Mode.PROCESSING:
                # Transcription in progress: small bars, slow left-to-right wave.
                # Max ~45% of pill height — clearly smaller than active recording.
                for i, bar in enumerate(self._bars):
                    phase = _BAR_PHASES[i]
                    scale = 0.18 + 0.22 * abs(math.sin(t * 4.5 - phase))
                    bar_h = max(_MIN_BAR_H, scale * _MAX_BAR_H)
                    by = (_PILL_H - bar_h) / 2
                    bar.setFrame_(((_BAR_X_POSITIONS[i], by), (_BAR_W, bar_h)))
            elif amp >= _IDLE_THRESHOLD:
                # Speaking: track time, drive bars by amplitude.
                self._last_active_t = t
                self._was_idle = False
                normalized = min(1.0, math.sqrt(amp * 20.0))
                for i, bar in enumerate(self._bars):
                    phase = _BAR_PHASES[i]
                    osc = 0.65 + 0.35 * math.sin(t * 6.0 - phase)
                    bar_h = max(_MIN_BAR_H, normalized * osc * _MAX_BAR_H)
                    by = (_PILL_H - bar_h) / 2
                    bar.setFrame_(((_BAR_X_POSITIONS[i], by), (_BAR_W, bar_h)))
            else:
                # Silence: hold wave for _HOLD_SECS then snap to static.
                hold_elapsed = t - self._last_active_t
                if hold_elapsed < _HOLD_SECS:
                    decay = 1.0 - hold_elapsed / _HOLD_SECS
                    normalized = min(1.0, math.sqrt(_IDLE_THRESHOLD * decay * 20.0))
                    for i, bar in enumerate(self._bars):
                        phase = _BAR_PHASES[i]
                        osc = 0.65 + 0.35 * math.sin(t * 6.0 - phase)
                        bar_h = max(_MIN_BAR_H, normalized * osc * _MAX_BAR_H)
                        by = (_PILL_H - bar_h) / 2
                        bar.setFrame_(((_BAR_X_POSITIONS[i], by), (_BAR_W, bar_h)))
                elif not self._was_idle:
                    for i, bar in enumerate(self._bars):
                        by = (_PILL_H - _MIN_BAR_H) / 2
                        bar.setFrame_(((_BAR_X_POSITIONS[i], by), (_BAR_W, _MIN_BAR_H)))
                    self._was_idle = True
        finally:
            CT.commit()


class RecordingOverlay:
    """Native macOS pill overlay with animated waveform bars.

    Thread-safe: show()/hide()/update_amplitude()/quit() can be called from any thread.
    run() MUST be called from the main thread — blocks on AppKit event loop.
    """

    def __init__(self) -> None:
        self._queue: queue.Queue = queue.Queue()
        self._controller: _OverlayController | None = None

    def show(self) -> None:
        """Fade in the overlay (dictation mode). Thread-safe."""
        self._queue.put(_Cmd.SHOW)

    def show_command(self) -> None:
        """Fade in the overlay (command mode, amber bars). Thread-safe."""
        self._queue.put(_Cmd.SHOW_COMMAND)

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

    def run(self) -> None:
        """Start AppKit event loop on main thread. Blocks until quit() is called."""
        app = NSApplication.sharedApplication()
        app.setActivationPolicy_(_POLICY_ACCESSORY)

        controller = _OverlayController.alloc().init()
        controller.setup(self._queue)
        self._controller = controller

        NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(
            0.033, controller, b"pollQueue:", None, True
        )

        signal.signal(signal.SIGINT, lambda _s, _f: app.terminate_(None))

        app.run()
