"""Shared macOS AppKit availability guard."""

from __future__ import annotations

try:
    from AppKit import NSColor, NSPasteboard, NSWorkspace

    HAS_APPKIT = True
except Exception:
    NSColor = NSPasteboard = NSWorkspace = None  # type: ignore[assignment, misc]
    HAS_APPKIT = False


def ns_color(rgb: tuple[float, float, float], alpha: float = 1.0) -> object:
    """Turn a ``theme`` RGB triple into an ``NSColor``.

    The one bridge between the AppKit-free token module and AppKit, so both
    visible surfaces read a token the same way.
    """
    r, g, b = rgb
    return NSColor.colorWithRed_green_blue_alpha_(r, g, b, alpha)
