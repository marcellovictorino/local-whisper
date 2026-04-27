import argparse
import sys

from local_whisper import audio, transcribe


def main() -> None:
    """CLI entry point for local-whisper."""
    parser = argparse.ArgumentParser(
        prog="local-whisper",
        description="Local offline speech-to-text on Apple Silicon.",
    )
    parser.add_argument(
        "--run",
        action="store_true",
        help="Start the background listener (hold Right ⌘ to dictate).",
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
        from local_whisper.app import App
        from local_whisper.overlay import RecordingOverlay

        overlay = RecordingOverlay()
        app = App(overlay=overlay)
        app.start()  # starts pynput listener in daemon thread (non-blocking)

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
