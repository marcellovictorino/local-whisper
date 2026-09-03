"""Tests for HotkeyListener trigger mapping, per-key debounce, and release isolation."""

from __future__ import annotations

from unittest.mock import MagicMock

from pynput import keyboard

from local_whisper.hotkey import HotkeyListener, Trigger


def _listener(on_cancel: MagicMock | None = None) -> tuple[HotkeyListener, MagicMock, MagicMock]:
    on_activate = MagicMock()
    on_deactivate = MagicMock()
    return (
        HotkeyListener(on_activate=on_activate, on_deactivate=on_deactivate, on_cancel=on_cancel),
        on_activate,
        on_deactivate,
    )


def test_cmd_r_activates_dictate() -> None:
    listener, on_activate, _ = _listener()
    listener._handle_press(keyboard.Key.cmd_r)
    on_activate.assert_called_once_with(Trigger.DICTATE)


def test_alt_r_activates_adapt() -> None:
    listener, on_activate, _ = _listener()
    listener._handle_press(keyboard.Key.alt_r)
    on_activate.assert_called_once_with(Trigger.ADAPT)


def test_release_fires_deactivate_with_matching_trigger() -> None:
    listener, _, on_deactivate = _listener()
    listener._handle_press(keyboard.Key.alt_r)
    listener._handle_release(keyboard.Key.alt_r)
    on_deactivate.assert_called_once_with(Trigger.ADAPT)


def test_repeat_press_of_held_trigger_recovers_and_restarts() -> None:
    """A second physical press of a still-"held" trigger means its release was lost.

    Modifier keys don't auto-repeat in pynput, so a genuine second press only
    happens if the OS/tap dropped the release event — recover the wedged
    session, then start a fresh one rather than swallowing the press.
    """
    on_cancel = MagicMock()
    listener, on_activate, _ = _listener(on_cancel=on_cancel)
    listener._handle_press(keyboard.Key.cmd_r)
    listener._handle_press(keyboard.Key.cmd_r)
    on_cancel.assert_called_once_with(Trigger.DICTATE)
    assert on_activate.call_count == 2


def test_repeat_press_without_cancel_handler_still_restarts() -> None:
    listener, on_activate, _ = _listener()
    listener._handle_press(keyboard.Key.cmd_r)
    listener._handle_press(keyboard.Key.cmd_r)
    assert on_activate.call_count == 2


def test_esc_invokes_on_cancel_with_no_trigger() -> None:
    on_cancel = MagicMock()
    listener, on_activate, _ = _listener(on_cancel=on_cancel)
    listener._handle_press(keyboard.Key.esc)
    on_cancel.assert_called_once_with(None)
    on_activate.assert_not_called()


def test_esc_without_cancel_handler_is_a_noop() -> None:
    listener, on_activate, on_deactivate = _listener()
    listener._handle_press(keyboard.Key.esc)
    on_activate.assert_not_called()
    on_deactivate.assert_not_called()


def test_release_without_press_is_ignored() -> None:
    listener, _, on_deactivate = _listener()
    listener._handle_release(keyboard.Key.cmd_r)
    on_deactivate.assert_not_called()


def test_releasing_other_key_does_not_deactivate() -> None:
    """Releasing Right Cmd during a Right Option hold must not fire its deactivate."""
    listener, _, on_deactivate = _listener()
    listener._handle_press(keyboard.Key.alt_r)
    listener._handle_release(keyboard.Key.cmd_r)
    on_deactivate.assert_not_called()
    listener._handle_release(keyboard.Key.alt_r)
    on_deactivate.assert_called_once_with(Trigger.ADAPT)


def test_unrelated_keys_are_ignored() -> None:
    listener, on_activate, on_deactivate = _listener()
    listener._handle_press(keyboard.Key.cmd_l)
    listener._handle_press(keyboard.KeyCode.from_char("a"))
    listener._handle_release(keyboard.KeyCode.from_char("a"))
    on_activate.assert_not_called()
    on_deactivate.assert_not_called()


def test_both_keys_held_track_independently() -> None:
    listener, on_activate, on_deactivate = _listener()
    listener._handle_press(keyboard.Key.cmd_r)
    listener._handle_press(keyboard.Key.alt_r)
    assert on_activate.call_count == 2
    listener._handle_release(keyboard.Key.cmd_r)
    on_deactivate.assert_called_once_with(Trigger.DICTATE)
