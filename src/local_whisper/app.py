from __future__ import annotations

import logging
import signal
import threading
import time
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
    spelling,
    transcribe,
)
from local_whisper.audio import SAMPLE_RATE_HZ
from local_whisper.hotkey import HotkeyListener, Trigger

if TYPE_CHECKING:
    from local_whisper.overlay import RecordingOverlay

logger = logging.getLogger("local_whisper")

_MIN_RECORD_DURATION_S = 0.3
_SILENCE_PEAK_THRESHOLD = 0.01


class _SessionMode(StrEnum):
    DICTATION = "dictation"
    COMMAND = "command"
    ADAPT = "adapt"


@dataclass
class _Session:
    mode: _SessionMode
    stop_event: threading.Event = field(default_factory=threading.Event)
    selection: str = ""

    @property
    def trigger(self) -> Trigger:
        return Trigger.ADAPT if self.mode is _SessionMode.ADAPT else Trigger.DICTATE


def _run_dictation_pipeline(
    text: str,
    corrections_map: dict[str, str],
    spelling_variant: str | None = None,
    adapt_app: str | None = None,
) -> str:
    """Apply dictation post-processing pipeline; returns the text to paste.

    When adapt_app is given, the text is additionally reshaped by the LLM
    for that app. Spelling normalisation follows cleanup or adaptation, so
    configured corrections can override its replacements.
    """
    text = auto_cleanup.apply(text)
    if adapt_app is not None:
        text = auto_adapt.apply(text, adapt_app)
    text = spelling.apply(text, spelling_variant)
    text = corrections.apply(text, corrections_map)
    text = snippets.expand(text)
    return text.rstrip() + " "


def _run_command_pipeline(selection: str, instruction: str) -> str:
    """Apply voice command to selection via LLM; returns the text to paste.

    Raises:
        llm.LLMUnavailable: if LLM call fails. Caller preserves the selection.
    """
    return llm.apply_voice_command(selection, instruction)


def _log_session(
    mode: _SessionMode,
    outcome: str,
    record_s: float,
    t0: float,
    t_transcribed: float,
    t_pipeline: float | None = None,
    t_pasted: float | None = None,
) -> None:
    """Emit the one-per-session timing line, on success and failure alike.

    total = record + everything after key release, so stages sum to it.
    """
    parts = [
        f"mode={mode}",
        f"outcome={outcome}",
        f"record={record_s:.1f}s",
        f"transcribe={t_transcribed - t0:.2f}s",
    ]
    if t_pipeline is not None:
        parts.append(f"pipeline={(t_pipeline - t_transcribed) * 1000:.0f}ms")
    if t_pasted is not None and t_pipeline is not None:
        parts.append(f"paste={(t_pasted - t_pipeline) * 1000:.0f}ms")
    t_end = t_pasted if t_pasted is not None else time.perf_counter()
    parts.append(f"total={record_s + (t_end - t0):.2f}s")
    logger.info("session: %s", " ".join(parts))


class App:
    """Orchestrates hotkey → record → transcribe → paste flow.

    Hold Right Command to record. Mode is determined automatically at press time:
    - Text selected → command mode: voice instruction applied to selection via API.
    - No selection  → dictation mode: transcription pasted at cursor.

    Hold Right Option to dictate with LLM reshaping for the frontmost app
    (adapt mode). Selection is ignored in adapt mode.

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
        self._unsupported_vocab_notice_emitted = False
        self._corrections: dict[str, str] = corrections.load()
        self._spelling_variant = config.get_whisper_spelling()
        vocabulary_words = config.get_vocabulary_words()
        self._vocab_prompt: str | None = self._build_vocab_prompt(vocabulary_words)
        self._listener = HotkeyListener(
            on_activate=self._on_key_press,
            on_deactivate=self._on_key_release,
        )

    def start(self) -> None:
        """Start the keyboard listener in a daemon thread. Non-blocking."""
        signal.signal(signal.SIGHUP, lambda _s, _f: self._reload_config())
        self._listener.start()
        self._signal_if_config_malformed()
        logger.info(
            "local-whisper running. Hold Right ⌘ to dictate (or transform selection); "
            "hold Right ⌥ to dictate with app-adapted formatting. Ctrl+C to quit."
        )
        if not llm.is_available():
            logger.warning(
                "LLM features disabled (auto-adapt and command mode unavailable). "
                "Export OPENAI_API_KEY to the daemon — re-run setup.sh."
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
            logger.info("Stopped.")

    def _build_vocab_prompt(self, vocabulary_words: list[str]) -> str | None:
        """Build the Whisper vocabulary-seeding prompt; unavailable on Parakeet."""
        if not transcribe.supports_vocab_prompt(self._backend):
            if (vocabulary_words or self._corrections) and not self._unsupported_vocab_notice_emitted:
                logger.info(
                    "Configured vocabulary unavailable on %s; corrections still apply post-transcription.",
                    self._backend,
                )
                self._unsupported_vocab_notice_emitted = True
            return None
        return corrections.build_prompt(self._corrections, vocabulary_words)

    def _reload_config(self) -> None:
        """Reload all config caches without restarting."""
        config.invalidate()
        self._corrections = corrections.load()
        self._spelling_variant = config.get_whisper_spelling()
        vocabulary_words = config.get_vocabulary_words()
        self._vocab_prompt = self._build_vocab_prompt(vocabulary_words)
        self._signal_if_config_malformed()
        logger.info("Config reloaded.")

    def _signal_if_config_malformed(self) -> None:
        """Surface a startup or SIGHUP-reload overlay signal for a malformed config."""
        if self._overlay and config.load_config().state is config.ConfigState.MALFORMED:
            self._overlay.show_error()

    def _on_key_press(self, trigger: Trigger) -> None:
        """Detect mode from trigger and selection, then start recording in a background thread."""
        if self._active is not None:
            return

        if trigger == Trigger.ADAPT:
            self._active_app = auto_adapt.get_active_app()
            session = _Session(mode=_SessionMode.ADAPT)
        else:
            selection = command.get_selection()
            mode = _SessionMode.COMMAND if selection else _SessionMode.DICTATION
            session = _Session(mode=mode, selection=selection)

        if self._overlay:
            match session.mode:
                case _SessionMode.ADAPT:
                    self._overlay.show_adapt()
                case _SessionMode.COMMAND:
                    self._overlay.show_command()
                case _SessionMode.DICTATION:
                    self._overlay.show()

        self._active = session
        threading.Thread(target=self._run_session, args=(session,), daemon=True).start()

    def _on_key_release(self, trigger: Trigger) -> None:
        """Signal the active recording to stop, if this trigger started it."""
        active = self._active  # snapshot — the session thread nulls it on completion
        if active is not None and active.trigger == trigger:
            active.stop_event.set()

    def _run_session(self, session: _Session) -> None:
        """Record until stop_event, transcribe, apply pipeline, paste."""
        duration_s = t0 = t_transcribed = None
        try:
            on_amp = self._overlay.update_amplitude if self._overlay else None
            audio_data: np.ndarray = audio.record_until_event(session.stop_event, on_amplitude=on_amp)
            if self._overlay:
                self._overlay.set_processing()
            if audio_data.size == 0:
                logger.info("No audio captured.")
                return
            duration_s = audio_data.size / SAMPLE_RATE_HZ
            if duration_s < _MIN_RECORD_DURATION_S:
                logger.info("Skipping: recording too short.")
                return
            if np.max(np.abs(audio_data)) < _SILENCE_PEAK_THRESHOLD:
                logger.info("Skipping: silence detected.")
                return
            if not transcribe.wait_warmed(timeout=0):
                logger.info("Waiting for model warm-up...")
                if not transcribe.wait_warmed(timeout=60):
                    logger.warning("Warm-up timed out after 60s; proceeding anyway.")

            t0 = time.perf_counter()
            text = transcribe.run(
                audio_data, model=self._model, backend=self._backend, initial_prompt=self._vocab_prompt
            )
            t_transcribed = time.perf_counter()
            if not text:
                logger.info("Empty transcription.")
                _log_session(session.mode, "empty", duration_s, t0, t_transcribed)
                return

            match session.mode:
                case _SessionMode.DICTATION:
                    result = _run_dictation_pipeline(text, self._corrections, self._spelling_variant)
                case _SessionMode.ADAPT:
                    result = _run_dictation_pipeline(
                        text, self._corrections, self._spelling_variant, adapt_app=self._active_app
                    )
                case _SessionMode.COMMAND:
                    try:
                        result = _run_command_pipeline(session.selection, text)
                    except llm.LLMUnavailable as exc:
                        logger.error("Command failed (selection preserved): %s", exc)
                        if self._overlay:
                            self._overlay.show_error()
                        _log_session(session.mode, "llm-unavailable", duration_s, t0, t_transcribed)
                        return
            t_pipeline = time.perf_counter()
            clipboard.write_and_paste(result)
            t_pasted = time.perf_counter()
            _log_session(session.mode, "ok", duration_s, t0, t_transcribed, t_pipeline, t_pasted)
        except Exception as exc:
            logger.error("Session error: %s", exc)
            if t0 is not None:
                _log_session(
                    session.mode,
                    "error",
                    duration_s,
                    t0,
                    t_transcribed if t_transcribed is not None else time.perf_counter(),
                )
        finally:
            self._active = None
            if self._overlay:
                self._overlay.hide()
