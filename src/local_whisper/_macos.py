"""Shared macOS AppKit availability guard."""

from __future__ import annotations

try:
    from AppKit import NSPasteboard, NSWorkspace

    HAS_APPKIT = True
except Exception:
    NSPasteboard = NSWorkspace = None  # type: ignore[assignment, misc]
    HAS_APPKIT = False
