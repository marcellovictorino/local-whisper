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
        "--test",
        action="store_true",
        help="Record 5 seconds and print transcription (smoke test).",
    )
    parser.add_argument(
        "--duration",
        type=float,
        default=5.0,
        help="Recording duration in seconds for --test mode (default: 5).",
    )
    args = parser.parse_args()

    if args.test:
        print(f"Speak now — recording for {args.duration}s...", file=sys.stderr)
        audio_data = audio.record(duration=args.duration)
        text = transcribe.run(audio_data)
        print(text)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
