import sys
import threading

import numpy as np

from local_whisper import audio, clipboard, transcribe
from local_whisper.hotkey import HotkeyListener


class App:
    """Orchestrates hotkey → record → transcribe → paste flow.

    Hold Right Command to record. Release to transcribe and paste
    the result at the active cursor position. Runs as a persistent
    background listener until interrupted.
    """

    def __init__(self) -> None:
        self._stop_event = threading.Event()
        self._recording = False
        self._listener = HotkeyListener(
            on_activate=self._on_key_press,
            on_deactivate=self._on_key_release,
        )

    def run(self) -> None:
        """Start the app. Blocks until Ctrl+C."""
        self._listener.start()
        print(
            "local-whisper running. Hold Right ⌘ to dictate. Ctrl+C to quit.",
            file=sys.stderr,
            flush=True,
        )
        try:
            threading.Event().wait()  # block main thread forever
        except KeyboardInterrupt:
            pass
        finally:
            self._listener.stop()
            print("\nStopped.", file=sys.stderr)

    def _on_key_press(self) -> None:
        """Start recording in a background thread."""
        if self._recording:
            return  # already recording — debounce
        self._recording = True
        self._stop_event.clear()
        threading.Thread(target=self._record_and_process, daemon=True).start()

    def _on_key_release(self) -> None:
        """Signal recording to stop."""
        self._stop_event.set()

    def _record_and_process(self) -> None:
        """Record until stop_event, then transcribe and paste."""
        try:
            audio_data: np.ndarray = audio.record_until_event(self._stop_event)
            if audio_data.size == 0:
                print("[local-whisper] No audio captured.", file=sys.stderr)
                return
            text = transcribe.run(audio_data)
            if not text:
                print("[local-whisper] Empty transcription.", file=sys.stderr)
                return
            clipboard.write_and_paste(text)
        except Exception as exc:  # noqa: BLE001
            print(f"[local-whisper] Error: {exc}", file=sys.stderr)
        finally:
            self._recording = False
