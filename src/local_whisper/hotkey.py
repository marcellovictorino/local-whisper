import sys
from collections.abc import Callable

from pynput import keyboard


class HotkeyListener:
    """Listen for Right Command key globally.

    Right Command (hold/release): on_activate / on_deactivate.

    Debounced — repeated press events while held do not re-trigger.

    Requires macOS Accessibility permission for the running
    terminal app (System Settings → Privacy & Security →
    Accessibility).
    """

    def __init__(
        self,
        on_activate: Callable[[], None],
        on_deactivate: Callable[[], None],
    ) -> None:
        """Initialise the listener.

        Args:
            on_activate: Called once when Right Command is pressed.
            on_deactivate: Called once when Right Command is released.
        """
        self._on_activate = on_activate
        self._on_deactivate = on_deactivate
        self._pressed = False
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
            print(
                f"[local-whisper] Failed to start hotkey listener: {exc}\n"
                "  → Grant Accessibility permission: System Settings → "
                "Privacy & Security → Accessibility → add your terminal app.",
                file=sys.stderr,
            )
            raise

    def stop(self) -> None:
        """Stop the keyboard listener."""
        if self._listener is not None:
            self._listener.stop()
            self._listener = None

    def _handle_press(self, key: keyboard.Key | keyboard.KeyCode) -> None:
        if key == keyboard.Key.cmd_r and not self._pressed:
            self._pressed = True
            self._on_activate()

    def _handle_release(self, key: keyboard.Key | keyboard.KeyCode) -> None:
        if key == keyboard.Key.cmd_r and self._pressed:
            self._pressed = False
            self._on_deactivate()
