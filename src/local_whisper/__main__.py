import argparse
import json
import logging
import threading

from local_whisper import _setup_logging, audio, transcribe

logger = logging.getLogger("local_whisper")


def _check_accessibility() -> bool:
    """Return True if this process has Accessibility permission."""
    import ctypes
    import ctypes.util

    lib_path = ctypes.util.find_library("ApplicationServices")
    if not lib_path:
        return True  # can't check, proceed optimistically
    try:
        lib = ctypes.cdll.LoadLibrary(lib_path)
        lib.AXIsProcessTrusted.restype = ctypes.c_bool
        lib.AXIsProcessTrusted.argtypes = []
        return bool(lib.AXIsProcessTrusted())
    except Exception:
        return True  # can't check, proceed optimistically


def _prompt_accessibility() -> None:
    """Ask macOS to show the Accessibility grant dialog for this process.

    The prompting variant pre-adds the running process (the venv Python
    interpreter, which launchd runs directly) to the Accessibility list, so
    the user only has to flip the toggle instead of hunting for the binary.
    Best-effort: :func:`_check_accessibility` is the actual gate.
    """
    try:
        from ApplicationServices import (
            AXIsProcessTrustedWithOptions,
            kAXTrustedCheckOptionPrompt,
        )

        AXIsProcessTrustedWithOptions({kAXTrustedCheckOptionPrompt: True})
    except Exception:  # noqa: BLE001 — dialog is a convenience, not a gate
        logger.debug("Could not trigger the Accessibility prompt dialog.", exc_info=True)


def _ensure_accessibility() -> None:
    """Ensure Accessibility permission, or exit cleanly so launchd respawns.

    macOS does not let a *running* process observe a permission granted
    mid-life — the trust check only re-reads on a fresh process. So if
    permission is missing we pop the native dialog once (which pre-adds this
    binary to the Accessibility list) and exit 0. launchd's KeepAlive +
    ThrottleInterval respawns a fresh process that re-reads the grant, so the
    service self-heals within ~30s of the user flipping the toggle — no manual
    restart, and no infinite crash-loop (each spawn is throttled).
    """
    if _check_accessibility():
        return
    _prompt_accessibility()
    logger.warning(
        "Accessibility permission required. Enable local-whisper under System "
        "Settings → Privacy & Security → Accessibility. The service restarts "
        "itself and begins working within ~30s of granting."
    )
    raise SystemExit(0)


def main() -> None:
    """CLI entry point for local-whisper."""
    _setup_logging()
    parser = argparse.ArgumentParser(
        prog="local-whisper",
        description="Local offline speech-to-text on Apple Silicon.",
    )
    parser.add_argument(
        "--run",
        action="store_true",
        help=(
            "Start the background listener. "
            "Hold Right ⌘ to dictate. "
            "Select text first, then hold Right ⌘ to apply a voice command to the selection. "
            "Hold Right ⌥ to dictate with LLM reshaping for the frontmost app "
            "(LLM features require LOCAL_WHISPER_OPENAI_API_KEY env var)."
        ),
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Record N seconds and print transcription (smoke test).",
    )
    parser.add_argument(
        "--duration",
        type=float,
        default=5.0,
        help="Recording duration in seconds for --test mode (default: 5).",
    )
    parser.add_argument(
        "--benchmark",
        action="store_true",
        help="Run latency benchmark and exit.",
    )
    args = parser.parse_args()

    match (args.run, args.benchmark, args.test):
        case (True, _, _):
            _ensure_accessibility()

            from local_whisper.app import App
            from local_whisper.overlay import RecordingOverlay

            model = transcribe.get_model()
            backend = transcribe.get_backend(model)
            overlay = RecordingOverlay()
            app = App(overlay=overlay, model=model, backend=backend)
            app.start()

            # Pre-load model and compile Metal shaders so first keypress is instant.
            threading.Thread(target=transcribe.warm_up, args=(model, backend), daemon=True).start()
            transcribe.start_keepalive(model, backend)
            transcribe.start_wake_watcher(model, backend)

            try:
                overlay.run()  # AppKit event loop on main thread — blocks until quit()
            except KeyboardInterrupt:
                pass
            finally:
                app.stop()
                overlay.quit()

        case (_, True, _):
            from local_whisper import benchmark

            model = transcribe.get_model()
            backend = transcribe.get_backend(model)
            logger.info("Benchmarking %s (%ds audio, 3 runs)...", model, benchmark.DURATION_S)
            results = benchmark.run(model, backend=backend)
            print(json.dumps(results, indent=2))

        case (_, _, True):
            model = transcribe.get_model()
            backend = transcribe.get_backend(model)
            logger.info("Speak now — recording for %gs...", args.duration)
            audio_data = audio.record(duration=args.duration)
            text = transcribe.run(audio_data, model=model, backend=backend)
            print(text)

        case _:
            parser.print_help()


if __name__ == "__main__":
    main()
