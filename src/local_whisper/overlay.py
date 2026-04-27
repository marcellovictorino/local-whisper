from __future__ import annotations

import queue
import signal

import objc
from AppKit import (
    NSApplication,
    NSColor,
    NSFont,
    NSMakeRect,
    NSObject,
    NSPanel,
    NSScreen,
    NSTextField,
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


class _OverlayController(NSObject):
    """Manages the NSPanel and drains the command queue via NSTimer."""

    @objc.python_method
    def setup(self, cmd_queue: queue.Queue[str]) -> None:
        self._queue = cmd_queue
        self._panel: NSPanel | None = None

    def pollQueue_(self, _timer: object) -> None:
        try:
            while True:
                cmd = self._queue.get_nowait()
                if cmd == "show":
                    self._fade_in()
                elif cmd == "hide":
                    self._fade_out()
                elif cmd == "quit":
                    NSApplication.sharedApplication().terminate_(None)
                    return
        except queue.Empty:
            pass

    @objc.python_method
    def _build_panel(self) -> None:
        screen = NSScreen.mainScreen()
        if screen is None:
            # Display sleeping, headless login, or no screen attached — skip build.
            # _fade_in() checks self._panel is None and returns safely.
            return
        full = screen.frame()
        visible = screen.visibleFrame()  # excludes menu bar + dock
        sw = full.size.width

        w, h = 80, 24
        x = (sw - w) / 2  # horizontally centered
        # Just below the menu bar (top of visible frame with a small gap)
        y = visible.origin.y + visible.size.height - h - 8

        panel = NSPanel.alloc().initWithContentRect_styleMask_backing_defer_(
            NSMakeRect(x, y, w, h),
            NSWindowStyleMaskBorderless,
            _BACKING_BUFFERED,
            False,
        )
        panel.setLevel_(_FLOATING_LEVEL)
        panel.setOpaque_(False)
        panel.setBackgroundColor_(NSColor.clearColor())
        panel.setAlphaValue_(0.0)  # hidden initially
        panel.setIgnoresMouseEvents_(True)
        panel.setHasShadow_(True)
        # NSPanel hides on app deactivation by default — accessory apps are NEVER
        # "active", so without this the panel auto-hides immediately after showing.
        panel.setHidesOnDeactivate_(False)
        panel.setCollectionBehavior_(
            NSWindowCollectionBehaviorCanJoinAllSpaces
            | NSWindowCollectionBehaviorStationary
        )

        # Glassy frosted background
        effect = NSVisualEffectView.alloc().initWithFrame_(NSMakeRect(0, 0, w, h))
        effect.setMaterial_(_HUD_MATERIAL)
        effect.setBlendingMode_(_BLEND_BEHIND)
        effect.setState_(_STATE_ACTIVE)
        effect.setWantsLayer_(True)
        effect.layer().setCornerRadius_(h / 2)  # perfect pill
        effect.layer().setMasksToBounds_(True)
        # Dark border for contrast and grounding
        effect.layer().setBorderWidth_(1.0)
        effect.layer().setBorderColor_(
            NSColor.colorWithWhite_alpha_(0.1, 1.0).CGColor()
        )
        panel.setContentView_(effect)

        # Label — white text on dark frosted glass, centered both axes.
        # Bypass NSTextField alignment (unreliable for single-line labels):
        # measure natural size via sizeToFit(), then manually position at center.
        label = NSTextField.labelWithString_("⏺ ...")
        label.setFont_(NSFont.systemFontOfSize_(12))
        label.setTextColor_(NSColor.whiteColor())
        label.setBackgroundColor_(NSColor.clearColor())
        label.setBordered_(False)
        label.sizeToFit()
        nat = label.frame()
        lx = (w - nat.size.width) / 2
        ly = (h - nat.size.height) / 2
        label.setFrame_(NSMakeRect(lx, ly, nat.size.width, nat.size.height))
        effect.addSubview_(label)

        self._panel = panel

    @objc.python_method
    def _fade_in(self) -> None:
        # Lazy build: NSScreen.mainScreen() is only reliable after app.run() starts.
        if self._panel is None:
            self._build_panel()
        if self._panel is None:
            return
        # orderFrontRegardless() is required for NSApplicationActivationPolicyAccessory
        # apps — they are never "active", so orderFront_(None) is a silent no-op.
        self._panel.orderFrontRegardless()
        self._panel.setAlphaValue_(0.95)

    @objc.python_method
    def _fade_out(self) -> None:
        if self._panel is None:
            return
        self._panel.setAlphaValue_(0.0)
        self._panel.orderOut_(None)


class RecordingOverlay:
    """Native macOS pill overlay recording indicator.

    Thread-safe: show()/hide()/quit() can be called from any thread.
    run() MUST be called from the main thread — blocks on AppKit event loop.
    """

    def __init__(self) -> None:
        self._queue: queue.Queue[str] = queue.Queue()
        self._controller: _OverlayController | None = None  # strong ref — prevents GC

    def show(self) -> None:
        """Fade in the overlay. Thread-safe."""
        self._queue.put("show")

    def hide(self) -> None:
        """Fade out the overlay. Thread-safe."""
        self._queue.put("hide")

    def quit(self) -> None:
        """Exit the AppKit event loop. Thread-safe."""
        self._queue.put("quit")

    def run(self) -> None:
        """Start AppKit event loop on main thread. Blocks until quit() is called."""
        app = NSApplication.sharedApplication()
        app.setActivationPolicy_(_POLICY_ACCESSORY)  # no dock icon

        controller = _OverlayController.alloc().init()
        controller.setup(self._queue)
        self._controller = controller  # strong ref — prevent garbage collection

        # Schedule the polling timer. NSTimer.scheduledTimerWithTimeInterval_ adds
        # to [NSRunLoop currentRunLoop] (= mainRunLoop on main thread). The timer
        # fires once app.run() starts processing the run loop.
        # Panel is built lazily on first "show" — NSScreen.mainScreen() is only
        # reliable after the run loop is running.
        NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(
            0.05, controller, b"pollQueue:", None, True
        )

        # SIGINT handler: terminate the AppKit event loop.
        # app.run() blocks in C code and never yields to Python's default SIGINT
        # handler, so we must install our own that calls terminate_() directly.
        signal.signal(signal.SIGINT, lambda _s, _f: app.terminate_(None))

        app.run()
