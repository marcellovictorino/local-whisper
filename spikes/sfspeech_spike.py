"""SFSpeechRecognizer spike — measures latency and transcription quality.

Usage:
    uv run python spikes/sfspeech_spike.py [audio_file]

If no file given, uses hardcoded test clips at /tmp/test_5s.aiff and /tmp/test_15s.aiff.
Generate them first:
    say -o /tmp/test_5s.aiff "The quick brown fox jumped over the lazy dog"
    say -o /tmp/test_15s.aiff "Longer passage here"

Results (2026-05-05, Apple M-series, on-device, requiresOnDeviceRecognition=True):
    5s clip (cold): ~520ms
    5s clip (warm): ~165ms   (without punctuation)
    5s clip (warm): ~639ms   (with addsPunctuation=True)
    15s clip:       ~354ms   (without punctuation)
    15s clip:       ~603ms   (with addsPunctuation=True)

Transcription quality: high — comparable to distil-whisper on clear English speech.
No model download required — uses built-in macOS Siri speech model.
"""

import sys
import threading
import time
from pathlib import Path

import objc
from Foundation import NSURL, NSDate, NSLocale, NSRunLoop

objc.loadBundle("Speech", globals(), bundle_path="/System/Library/Frameworks/Speech.framework")
SFSpeechRecognizer = globals()["SFSpeechRecognizer"]
SFSpeechURLRecognitionRequest = globals()["SFSpeechURLRecognitionRequest"]

# Register block signature for recognitionTaskWithRequest:resultHandler:
# (PyObjC cannot infer it from the framework metadata alone)
objc.registerMetaDataForSelector(
    b"SFSpeechRecognizer",
    b"recognitionTaskWithRequest:resultHandler:",
    {
        "arguments": {
            3: {
                "callable": {
                    "retval": {"type": b"v"},
                    "arguments": {
                        0: {"type": b"^v"},  # implicit block self pointer
                        1: {"type": b"@"},  # SFSpeechRecognitionResult*
                        2: {"type": b"@"},  # NSError*
                    },
                }
            }
        }
    },
)


def transcribe_file(audio_path: Path, label: str, punctuation: bool = True) -> dict:
    """Transcribe audio file using SFSpeechRecognizer with on-device recognition."""
    locale = NSLocale.alloc().initWithLocaleIdentifier_("en-US")
    recognizer = SFSpeechRecognizer.alloc().initWithLocale_(locale)

    if not recognizer or not recognizer.isAvailable():
        return {"label": label, "error": "Recognizer not available"}

    if not recognizer.supportsOnDeviceRecognition():
        return {"label": label, "error": "On-device recognition not supported on this hardware"}

    url = NSURL.fileURLWithPath_(str(audio_path))
    request = SFSpeechURLRecognitionRequest.alloc().initWithURL_(url)
    request.setRequiresOnDeviceRecognition_(True)
    request.setShouldReportPartialResults_(False)
    if punctuation:
        request.setAddsPunctuation_(True)

    done_event = threading.Event()
    transcript_holder = [None]
    error_holder = [None]

    def result_handler(result, error):
        if error:
            error_holder[0] = str(error)
            done_event.set()
            return
        if result and result.isFinal():
            transcript_holder[0] = result.bestTranscription().formattedString()
            done_event.set()

    t_start = time.perf_counter()
    task = recognizer.recognitionTaskWithRequest_resultHandler_(request, result_handler)  # noqa: F841

    deadline = time.monotonic() + 60.0
    while not done_event.is_set() and time.monotonic() < deadline:
        NSRunLoop.mainRunLoop().runUntilDate_(NSDate.dateWithTimeIntervalSinceNow_(0.02))

    latency_ms = (time.perf_counter() - t_start) * 1000

    if not done_event.is_set():
        task.cancel()
        return {"label": label, "error": "Timeout (60s)", "latency_ms": round(latency_ms, 1)}

    if error_holder[0]:
        return {"label": label, "error": error_holder[0], "latency_ms": round(latency_ms, 1)}

    return {
        "label": label,
        "latency_ms": round(latency_ms, 1),
        "transcript": transcript_holder[0],
        "punctuation": punctuation,
    }


def main():
    print("=== SFSpeechRecognizer Spike ===")
    print(f"Auth status: {SFSpeechRecognizer.authorizationStatus()} (0=notDetermined, 3=authorized)")
    print("Note: auth is granted implicitly when Terminal/Python has Speech Recognition permission.")
    print()

    test_files: list[tuple[Path, str]]
    if len(sys.argv) > 1:
        p = Path(sys.argv[1])
        test_files = [(p, p.name)]
    else:
        test_files = [
            (Path("/tmp/test_5s.aiff"), "~5s audio"),
            (Path("/tmp/test_15s.aiff"), "~15s audio"),
        ]

    for audio_path, label in test_files:
        if not audio_path.exists():
            print(f"SKIP {label}: file not found at {audio_path}")
            print(f"  Generate with: say -o {audio_path} 'Your test sentence here'")
            continue

        for punct in (False, True):
            suffix = " [+punct]" if punct else " [no punct]"
            result = transcribe_file(audio_path, label + suffix, punctuation=punct)
            if "error" in result:
                print(f"  {result['label']}: ERROR — {result['error']} ({result.get('latency_ms', '?')}ms)")
            else:
                print(f"  {result['label']}: {result['latency_ms']}ms")
                print(f"    -> {result['transcript']}")

    print("\n=== Done ===")


if __name__ == "__main__":
    main()
