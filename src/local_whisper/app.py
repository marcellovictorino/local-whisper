from __future__ import annotations

import logging
import signal
import threading
from dataclasses import dataclass, field
from enum import StrEnum
from typing import TYPE_CHECKING

import numpy as np

from local_whisper import (
    audio,
    auto_adapt,
    auto_cleanup,
    clipboard,
    command,
    config,
    corrections,
    llm,
    snippets,
    transcribe,
)
from local_whisper.hotkey import HotkeyListener

if TYPE_CHECKING:
    from local_whisper.overlay import RecordingOverlay

logger = logging.getLogger("local_whisper")

_MIN_RECORD_DURATION_S = 0.3
_MIN_AUTO_ADAPT_DURATION_S = 10.0
_SILENCE_PEAK_THRESHOLD = 0.01


class _SessionMode(StrEnum):
    DICTATION = "dictation"
    COMMAND = "command"


@dataclass
class _Session:
    mode: _SessionMode
    stop_event: threading.Event = field(default_factory=threading.Event)
    selection: str = ""


def _run_dictation_pipeline(text: str, active_app: str, corrections_map: dict[str, str], duration_s: float) -> str:
    """Apply dictation post-processing pipeline and paste result."""
    text = auto_cleanup.apply(text)
    if duration_s >= _MIN_AUTO_ADAPT_DURATION_S:
        text = auto_adapt.apply(text, active_app)
    elif auto_adapt.is_active(active_app):
        logger.info("Skipping auto-adapt: recording too short (%.1fs < %.0fs)", duration_s, _MIN_AUTO_ADAPT_DURATION_S)
    text = corrections.apply(text, corrections_map)
    text = snippets.expand(text)
    clipboard.write_and_paste(text)
    return text


def _run_command_pipeline(selection: str, instruction: str) -> str:
    """Apply voice command to selection via LLM and paste result."""
    result = llm.apply_voice_command(selection, instruction)
    clipboard.write_and_paste(result)
    return result


class App:
    """Orchestrates hotkey → record → transcribe → paste flow.

    Hold Right Command to record. Mode is determined automatically at press time:
    - Text selected → command mode: voice instruction applied to selection via API.
    - No selection  → dictation mode: transcription pasted at cursor.

    Runs as a persistent background listener until interrupted.
    """

    def __init__(
        self,
        overlay: RecordingOverlay | None = None,
        model: str = transcribe.DEFAULT_MODEL,
        backend: str = transcribe.DEFAULT_BACKEND,
    ) -> None:
        self._overlay = overlay
        self._model = model
        self._backend = backend
        self._active_app: str = ""
        self._active: _Session | None = None
        self._corrections: dict[str, str] = corrections.load()
        self._listener = HotkeyListener(
            on_activate=self._on_key_press,
            on_deactivate=self._on_key_release,
        )

    def start(self) -> None:
        """Start the keyboard listener in a daemon thread. Non-blocking."""
        signal.signal(signal.SIGHUP, lambda _s, _f: self._reload_config())
        self._listener.start()
        logger.info("local-whisper running. Hold Right ⌘ to dictate (or apply command to selection). Ctrl+C to quit.")

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
            logger.info("Stopped.")

    def _reload_config(self) -> None:
        """Reload all config caches without restarting."""
        config.invalidate()
        self._corrections = corrections.load()
        logger.info("Config reloaded.")

    def _on_key_press(self) -> None:
        """Detect mode from selection, then start recording in a background thread."""
        if self._active is not None:
            return

        self._active_app = auto_adapt.get_active_app()
        selection = command.get_selection()

        if selection:
            session = _Session(mode=_SessionMode.COMMAND, selection=selection)
            if self._overlay:
                self._overlay.show_command()
        else:
            session = _Session(mode=_SessionMode.DICTATION)
            if self._overlay:
                if auto_adapt.is_active(self._active_app):
                    self._overlay.show_adapt()
                else:
                    self._overlay.show()

        self._active = session
        threading.Thread(target=self._run_session, args=(session,), daemon=True).start()

    def _on_key_release(self) -> None:
        """Signal the active recording to stop."""
        if self._active is not None:
            self._active.stop_event.set()

    def _run_session(self, session: _Session) -> None:
        """Record until stop_event, transcribe, apply pipeline, paste."""
        try:
            on_amp = self._overlay.update_amplitude if self._overlay else None
            audio_data: np.ndarray = audio.record_until_event(session.stop_event, on_amplitude=on_amp)
            if self._overlay:
                self._overlay.set_processing()
            if audio_data.size == 0:
                logger.info("No audio captured.")
                return
            if audio_data.size / 16000 < _MIN_RECORD_DURATION_S:
                logger.info("Skipping: recording too short.")
                return
            if np.max(np.abs(audio_data)) < _SILENCE_PEAK_THRESHOLD:
                logger.info("Skipping: silence detected.")
                return
            if not transcribe.wait_warmed(timeout=0):
                logger.info("Waiting for model warm-up...")
                if not transcribe.wait_warmed(timeout=60):
                    logger.warning("Warm-up timed out after 60s; proceeding anyway.")
            duration_s = audio_data.size / 16000
            vocab_prompt = corrections.build_prompt(self._corrections)
            text = transcribe.run(audio_data, model=self._model, backend=self._backend, initial_prompt=vocab_prompt)
            if not text:
                logger.info("Empty transcription.")
                return

            match session.mode:
                case _SessionMode.DICTATION:
                    _run_dictation_pipeline(text, self._active_app, self._corrections, duration_s)
                case _SessionMode.COMMAND:
                    _run_command_pipeline(session.selection, text)
        except Exception as exc:
            logger.error("Session error: %s", exc)
        finally:
            self._active = None
            if self._overlay:
                self._overlay.hide()
