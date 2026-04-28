from __future__ import annotations

import signal
import sys
import threading
from typing import TYPE_CHECKING

import numpy as np

from local_whisper import audio, clipboard, command, corrections, snippets, transcribe
from local_whisper.hotkey import HotkeyListener

if TYPE_CHECKING:
    from local_whisper.overlay import RecordingOverlay


class App:
    """Orchestrates hotkey → record → transcribe → paste flow.

    Hold Right Command to record. Mode is determined automatically at press time:
    - Text selected → command mode: voice instruction applied to selection via API.
    - No selection  → dictation mode: transcription pasted at cursor.

    Runs as a persistent background listener until interrupted.
    """

    def __init__(self, overlay: RecordingOverlay | None = None) -> None:
        self._overlay = overlay
        self._stop_event = threading.Event()
        self._recording = False
        self._corrections: dict[str, str] = corrections.load()
        self._command_stop_event = threading.Event()
        self._command_recording = False
        self._command_selection: str = ""
        self._listener = HotkeyListener(
            on_activate=self._on_key_press,
            on_deactivate=self._on_key_release,
        )

    def start(self) -> None:
        """Start the keyboard listener in a daemon thread. Non-blocking."""
        signal.signal(signal.SIGHUP, lambda _s, _f: self._reload_config())
        self._listener.start()
        print(
            "local-whisper running. Hold Right ⌘ to dictate (or apply command to selection). Ctrl+C to quit.",
            file=sys.stderr,
            flush=True,
        )

    def stop(self) -> None:
        """Stop the keyboard listener."""
        self._listener.stop()

    def run(self) -> None:
        """Start listener and block until Ctrl+C. Use when running without overlay."""
        self.start()
        try:
            threading.Event().wait()
        except KeyboardInterrupt:
            pass
        finally:
            self.stop()
            print("\nStopped.", file=sys.stderr)

    def _reload_config(self) -> None:
        """Reload corrections config without restarting."""
        self._corrections = corrections.load()
        print("[local-whisper] Config reloaded.", file=sys.stderr, flush=True)

    def _on_key_press(self) -> None:
        """Detect mode from selection, then start recording in a background thread."""
        if self._recording or self._command_recording:
            return  # already recording — debounce

        selection = command.get_selection()

        if selection:
            self._command_selection = selection
            self._command_recording = True
            self._command_stop_event.clear()
            if self._overlay:
                self._overlay.show_command()
            threading.Thread(target=self._command_record_and_process, daemon=True).start()
        else:
            self._recording = True
            self._stop_event.clear()
            if self._overlay:
                self._overlay.show()
            threading.Thread(target=self._record_and_process, daemon=True).start()

    def _on_key_release(self) -> None:
        """Signal the active recording to stop."""
        if self._command_recording:
            self._command_stop_event.set()
        else:
            self._stop_event.set()

    def _record_and_process(self) -> None:
        """Record until stop_event, then transcribe and paste."""
        try:
            on_amp = self._overlay.update_amplitude if self._overlay else None
            audio_data: np.ndarray = audio.record_until_event(self._stop_event, on_amplitude=on_amp)
            if self._overlay:
                self._overlay.set_processing()
            if audio_data.size == 0:
                print("[local-whisper] No audio captured.", file=sys.stderr)
                return
            text = transcribe.run(audio_data)
            if not text:
                print("[local-whisper] Empty transcription.", file=sys.stderr)
                return
            text = corrections.apply(text, self._corrections)
            text = snippets.expand(text)
            clipboard.write_and_paste(text)
        except Exception as exc:  # noqa: BLE001
            print(f"[local-whisper] Error: {exc}", file=sys.stderr)
        finally:
            self._recording = False
            if self._overlay:
                self._overlay.hide()

    def _command_record_and_process(self) -> None:
        """Record until stop_event, transcribe, apply voice command via API, paste."""
        try:
            on_amp = self._overlay.update_amplitude if self._overlay else None
            audio_data: np.ndarray = audio.record_until_event(self._command_stop_event, on_amplitude=on_amp)
            if self._overlay:
                self._overlay.set_processing()
            if audio_data.size == 0:
                print("[local-whisper] No audio captured.", file=sys.stderr)
                return
            voice_cmd = transcribe.run(audio_data)
            if not voice_cmd:
                print("[local-whisper] Empty transcription.", file=sys.stderr)
                return
            result = command.apply_command(self._command_selection, voice_cmd)
            clipboard.write_and_paste(result)
        except Exception as exc:  # noqa: BLE001
            print(f"[local-whisper] Command mode error: {exc}", file=sys.stderr)
        finally:
            self._command_recording = False
            self._command_selection = ""
            if self._overlay:
                self._overlay.hide()
