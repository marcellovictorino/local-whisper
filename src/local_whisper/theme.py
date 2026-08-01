"""Design tokens for the two visible surfaces — pure data, no AppKit import.

Mirrors the design system's ``tokens/colors.css`` and ``tokens/motion.css``.
The mode colour is the *only* mode indicator in the product, so the pill and the
menu-bar item must read identically; keeping the values here (instead of inline
in each surface) is what stops them drifting. Values are 0–1 RGB floats because
that is what both ``NSColor`` and ``CGColor`` take.

Never add a fifth hue: a new colour in this product means a new mode.
"""

from __future__ import annotations

from enum import StrEnum


class Mode(StrEnum):
    """What the bars are signalling right now."""

    DICTATION = "dictation"
    COMMAND = "command"
    ADAPT = "adapt"
    ERROR = "error"
    PROCESSING = "processing"


RGB = tuple[float, float, float]

# --lw-mode-* — lifted from the design system, which lifted them from _fade_in().
MODE_RGB: dict[Mode, RGB] = {
    Mode.DICTATION: (1.0, 1.0, 1.0),  # #ffffff
    Mode.COMMAND: (1.0, 0.76, 0.34),  # #ffc257 amber
    Mode.ADAPT: (0.0, 0.85, 1.0),  # #00d9ff electric cyan
    Mode.ERROR: (1.0, 0.27, 0.27),  # #ff4545 red
    # Processing is white *as a colour*, but the pill never repaints on entering
    # it: the bars keep the session's hue and only the cadence changes, because
    # the hue is the mode signal and dropping it mid-session would lose it. This
    # entry is what the surfaces use when processing is the only state they know
    # (the menu-bar item at cold start), and it is what makes WHITE_MODES honest.
    Mode.PROCESSING: (1.0, 1.0, 1.0),
}

# Modes whose hue is white — i.e. the absence of a tint. They get no bloom, and
# the menu-bar mark stays a template image for them so macOS can invert it
# against a light menu bar. Derived, not listed, so a palette edit can't
# contradict it.
WHITE_MODES = frozenset(mode for mode, rgb in MODE_RGB.items() if rgb == (1.0, 1.0, 1.0))

# --lw-glow-* — the same hue at low alpha, bloomed behind the bar on dark glass.
# White is excluded on purpose: "no glow except the bar bloom in the mode colour
# on non-white bars" — a white bloom on frosted glass smears into the pill
# instead of reading as a signal.
GLOW_ALPHA = 0.45

# CSS `0 0 6px` is a 6px blur diameter; CALayer shadowRadius is the half-width.
GLOW_RADIUS = 3.0

# --lw-duration-fast + --lw-ease-standard: show/hide is opacity only, no scale,
# no spring. 150ms is long enough to stop the pill snapping into vision and
# short enough that it never lags the hotkey.
FADE_SECS = 0.15
EASE_STANDARD = (0.4, 0.0, 0.2, 1.0)

# --lw-hud-opacity — panel alpha when shown.
HUD_OPACITY = 0.95

# --lw-error-flash — how long a failure holds the pill red before it hides.
ERROR_FLASH_SECS = 1.0

# --lw-status-* — menu-bar status dot only; not mode signal.
STATUS_OK_RGB: RGB = (0.196, 0.843, 0.294)  # #32d74b
STATUS_IDLE_RGB: RGB = (0.557, 0.557, 0.576)  # #8e8e93 --lw-grey-1
