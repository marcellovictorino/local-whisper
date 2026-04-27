import argparse
import sys
import threading

from local_whisper import audio, transcribe


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


def main() -> None:
    """CLI entry point for local-whisper."""
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
            "Select text first, then hold Right ⌘ to apply a voice command to the selection "
            "(requires LOCAL_WHISPER_OPENAI_API_KEY and `uv sync --extra command`)."
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
    args = parser.parse_args()

    if args.run:
        if not _check_accessibility():
            print(
                "Accessibility permission required.\n"
                "\n"
                "  1. Open: System Settings → Privacy & Security → Accessibility\n"
                "  2. Add and enable the app running this script\n"
                "     (Terminal, iTerm2, or the launchd wrapper — whichever launched this)\n"
                "  3. Re-run: uv run python -m local_whisper --run\n",
                file=sys.stderr,
            )
            sys.exit(1)

        from local_whisper.app import App
        from local_whisper.overlay import RecordingOverlay

        overlay = RecordingOverlay()
        app = App(overlay=overlay)
        app.start()  # starts pynput listener in daemon thread (non-blocking)

        # Pre-load model and compile Metal shaders so first keypress is instant.
        threading.Thread(target=transcribe.warm_up, daemon=True).start()

        try:
            overlay.run()  # AppKit event loop on main thread — blocks until quit()
        except KeyboardInterrupt:
            pass
        finally:
            app.stop()
            overlay.quit()
    elif args.test:
        print(f"Speak now — recording for {args.duration}s...", file=sys.stderr)
        audio_data = audio.record(duration=args.duration)
        text = transcribe.run(audio_data)
        print(text)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
