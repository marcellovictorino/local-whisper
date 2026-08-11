import logging
from collections.abc import Callable
from enum import StrEnum

from pynput import keyboard

logger = logging.getLogger("local_whisper")


class Trigger(StrEnum):
    """Hold-to-record hotkeys, each mapped to a recording behavior."""

    DICTATE = "dictate"  # Right Command — plain dictation (or command mode if text selected)
    ADAPT = "adapt"  # Right Option — dictation reshaped for the frontmost app


_KEY_TO_TRIGGER: dict[keyboard.Key, Trigger] = {
    keyboard.Key.cmd_r: Trigger.DICTATE,
    keyboard.Key.alt_r: Trigger.ADAPT,
}


class HotkeyListener:
    """Listen globally for hold-to-record modifier keys.

    Right Command (hold/release): on_activate / on_deactivate with Trigger.DICTATE.
    Right Option (hold/release): same callbacks with Trigger.ADAPT.

    Debounced per key — repeated press events while held do not re-trigger.

    Requires macOS Accessibility permission for the running
    Python interpreter — the venv binary launchd runs (System
    Settings → Privacy & Security → Accessibility).
    """

    def __init__(
        self,
        on_activate: Callable[[Trigger], None],
        on_deactivate: Callable[[Trigger], None],
    ) -> None:
        """Initialise the listener.

        Args:
            on_activate: Called once when a trigger key is pressed.
            on_deactivate: Called once when that trigger key is released.
        """
        self._on_activate = on_activate
        self._on_deactivate = on_deactivate
        self._pressed: set[Trigger] = set()
        self._listener: keyboard.Listener | None = None

    def start(self) -> None:
        """Start the keyboard listener in a daemon background thread."""
        try:
            self._listener = keyboard.Listener(
                on_press=self._handle_press,
                on_release=self._handle_release,
                daemon=True,
            )
            self._listener.start()
        except Exception as exc:  # noqa: BLE001
            logger.error(
                "Failed to start hotkey listener: %s\n"
                "  → Grant Accessibility permission: System Settings → Privacy "
                "& Security → Accessibility → enable the 'Python' entry "
                "(the venv interpreter launchd runs). The service restarts "
                "itself and begins working within ~30s of granting.",
                exc,
            )
            raise

    def stop(self) -> None:
        """Stop the keyboard listener."""
        if self._listener is not None:
            self._listener.stop()
            self._listener = None

    def _handle_press(self, key: keyboard.Key | keyboard.KeyCode) -> None:
        trigger = _KEY_TO_TRIGGER.get(key)  # type: ignore[arg-type]
        if trigger is not None and trigger not in self._pressed:
            self._pressed.add(trigger)
            self._on_activate(trigger)

    def _handle_release(self, key: keyboard.Key | keyboard.KeyCode) -> None:
        trigger = _KEY_TO_TRIGGER.get(key)  # type: ignore[arg-type]
        if trigger is not None and trigger in self._pressed:
            self._pressed.discard(trigger)
            self._on_deactivate(trigger)
