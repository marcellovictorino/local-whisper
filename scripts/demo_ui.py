"""Drive the pill and the menu-bar item through every visual state, no mic needed.

Exists so a visual change can be judged side by side against `master` without
speaking into the machine forty times: amplitude is a synthesised envelope, so
each mode holds long enough to look at. The menu-bar item is installed too, with
the real menu but harmless actions (reload and quit are stubs), so the icon's
mode tint and the status row can be checked in the same pass.

    just demo-ui            # loop through every state
    just demo-ui adapt      # hold one mode and keep it fed

Ctrl+C to quit.
"""

from __future__ import annotations

import logging
import math
import sys
import threading
import time

from local_whisper import menubar, theme
from local_whisper.overlay import RecordingOverlay

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("demo_ui")

# One "utterance": speech-shaped amplitude, then silence so the decay-to-flat
# and the hold window are both visible.
_SPEAK_SECS = 2.6
_SILENCE_SECS = 0.9
_PROCESSING_SECS = 1.4
_GAP_SECS = 1.0
_FRAME_SECS = 0.02

# The modes a hotkey can start. Error is a flash, processing a transition — both
# are driven separately in _cycle.
_MODES = (theme.Mode.DICTATION, theme.Mode.COMMAND, theme.Mode.ADAPT)


def _amplitude(t: float) -> float:
    """Synthetic speech envelope: syllable-rate bursts under a slow swell.

    Shaped rather than random so successive runs are comparable — the point is to
    judge the render, and noise would make two runs disagree for the wrong reason.
    """
    syllables = 0.5 + 0.5 * math.sin(t * 7.0)
    swell = 0.45 + 0.55 * math.sin(t * 1.1)
    return 0.06 * syllables * swell


def _feed(overlay: RecordingOverlay, seconds: float, *, speaking: bool, t0: float) -> None:
    """Feed the overlay for ``seconds`` — a speech envelope, or silence.

    Silence is fed rather than simply waited out because that is what exercises
    the hold-then-decay-to-flat path.
    """
    end = time.monotonic() + seconds
    while time.monotonic() < end:
        overlay.update_amplitude(_amplitude(time.monotonic() - t0) if speaking else 0.0)
        time.sleep(_FRAME_SECS)


def _show(overlay: RecordingOverlay, mode: theme.Mode) -> None:
    {
        theme.Mode.DICTATION: overlay.show,
        theme.Mode.COMMAND: overlay.show_command,
        theme.Mode.ADAPT: overlay.show_adapt,
    }[mode]()


def _cycle(overlay: RecordingOverlay, only: theme.Mode | None) -> None:
    """Walk every state forever, or hold a single mode if ``only`` is given."""
    t0 = time.monotonic()
    time.sleep(0.6)  # let the event loop settle before the first show
    while True:
        for mode in (only,) if only else _MODES:
            logger.info("%s: recording", mode)
            _show(overlay, mode)
            _feed(overlay, _SPEAK_SECS, speaking=True, t0=t0)
            _feed(overlay, _SILENCE_SECS, speaking=False, t0=t0)
            logger.info("%s: processing", mode)
            overlay.set_processing()
            time.sleep(_PROCESSING_SECS)
            overlay.hide()
            time.sleep(_GAP_SECS)
        if only:
            continue
        logger.info("error: %gs red flash", theme.ERROR_FLASH_SECS)
        overlay.show_error()
        time.sleep(theme.ERROR_FLASH_SECS + _GAP_SECS)


def main() -> None:
    arg = sys.argv[1] if len(sys.argv) > 1 else None
    if arg is not None and arg not in _MODES:
        raise SystemExit(f"unknown mode {arg!r} — pick one of {', '.join(_MODES)}")
    only = theme.Mode(arg) if arg else None

    overlay = RecordingOverlay()
    menu_bar: list[object] = []  # the status item drops off the bar if its owner is released

    def _install_menu_bar() -> None:
        menu_bar.append(
            menubar.install(
                overlay,
                reload_config=lambda: logger.info("menu: reload config (stub)"),
                quit_app=overlay.quit,
                session_info=lambda: {"Model": "demo", "Backend": "demo"},
            )
        )
        threading.Thread(target=_cycle, args=(overlay, only), daemon=True).start()

    logger.info("demo-ui: %s — Ctrl+C to quit", only or "all states")
    overlay.run(on_ready=_install_menu_bar)


if __name__ == "__main__":
    main()
