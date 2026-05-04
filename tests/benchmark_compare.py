"""Compare transcription accuracy, latency, and quality across models using a real audio sample.

Usage:
    uv run python tests/benchmark_compare.py \
        --audio tests/sample.npy \
        --reference tests/accuracy_script.txt \
        [--models mlx-community/distil-whisper-large-v3 mlx-community/whisper-large-v3-turbo] \
        [--out results.json]

Reference file format: any text file — the EXPECTED TRANSCRIPT section (between the two
dashed separators after "EXPECTED TRANSCRIPT") is extracted automatically. If the marker
is absent, the entire file content is used as the reference.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path

import numpy as np

DEFAULT_MODELS = [
    "mlx-community/distil-whisper-large-v3",
    "mlx-community/whisper-large-v3-turbo",
]

FILLER_PATTERN = re.compile(
    r"\b(um+|uh+|er+|ah+|hmm+|you know|like|so|right)\b",
    flags=re.IGNORECASE,
)


def _extract_reference(path: Path) -> str:
    """Pull ground-truth text from accuracy_script.txt or use full file content."""
    text = path.read_text()
    marker = "EXPECTED TRANSCRIPT"
    if marker in text:
        after = text.split(marker, 1)[1]
        # Grab text between first two "---" separators
        parts = after.split("---")
        if len(parts) >= 2:
            return parts[1].strip()
    return text.strip()


def _normalize(text: str) -> str:
    """Lowercase, strip punctuation, collapse whitespace."""
    text = text.lower()
    text = re.sub(r"[^\w\s']", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _wer_details(reference: str, hypothesis: str) -> dict:
    """Compute WER and edit-distance breakdown between reference and hypothesis."""
    ref_words = _normalize(reference).split()
    hyp_words = _normalize(hypothesis).split()

    n, m = len(ref_words), len(hyp_words)
    # DP edit distance
    d = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(n + 1):
        d[i][0] = i
    for j in range(m + 1):
        d[0][j] = j
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            if ref_words[i - 1] == hyp_words[j - 1]:
                d[i][j] = d[i - 1][j - 1]
            else:
                d[i][j] = 1 + min(d[i - 1][j], d[i][j - 1], d[i - 1][j - 1])

    # Backtrace for substitution/insertion/deletion counts
    subs = ins = dels = 0
    i, j = n, m
    while i > 0 or j > 0:
        if i > 0 and j > 0 and ref_words[i - 1] == hyp_words[j - 1]:
            i -= 1
            j -= 1
        elif i > 0 and j > 0 and d[i][j] == d[i - 1][j - 1] + 1:
            subs += 1
            i -= 1
            j -= 1
        elif j > 0 and d[i][j] == d[i][j - 1] + 1:
            ins += 1
            j -= 1
        else:
            dels += 1
            i -= 1

    wer = round(d[n][m] / max(n, 1), 4)
    return {
        "wer": wer,
        "wer_pct": round(wer * 100, 1),
        "reference_words": n,
        "hypothesis_words": m,
        "substitutions": subs,
        "insertions": ins,
        "deletions": dels,
        "edit_distance": d[n][m],
    }


def _fillers_found(text: str) -> list[str]:
    return [m.group() for m in FILLER_PATTERN.finditer(text)]


def _run_model(audio: np.ndarray, model: str, reference: str) -> dict:
    from local_whisper import auto_cleanup, transcribe

    # Warm up
    t0 = time.perf_counter()
    transcribe.warm_up(model)
    warmup_s = round(time.perf_counter() - t0, 3)

    # Transcribe
    t0 = time.perf_counter()
    raw = transcribe.run(audio, model=model)
    transcription_s = round(time.perf_counter() - t0, 3)

    cleaned = auto_cleanup.apply(raw)

    raw_wer = _wer_details(reference, raw)
    cleaned_wer = _wer_details(reference, cleaned)
    fillers = _fillers_found(raw)

    return {
        "model": model,
        "warmup_s": warmup_s,
        "transcription_s": transcription_s,
        "raw_transcript": raw,
        "cleaned_transcript": cleaned,
        "accuracy": {
            "raw": raw_wer,
            "cleaned": cleaned_wer,
        },
        "quality": {
            "fillers_in_raw": fillers,
            "fillers_removed": len(fillers),
            "cleanup_delta_words": raw_wer["hypothesis_words"] - cleaned_wer["hypothesis_words"],
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare models on real audio sample.")
    parser.add_argument("--audio", type=Path, default=Path("tests/sample.npy"), help="Path to .npy audio file.")
    parser.add_argument(
        "--reference",
        type=Path,
        default=Path("tests/accuracy_script.txt"),
        help="Path to reference transcript.",
    )
    parser.add_argument("--models", nargs="+", default=DEFAULT_MODELS, help="HuggingFace model IDs to compare.")
    parser.add_argument("--out", type=Path, default=None, help="Save JSON results to file (optional).")
    args = parser.parse_args()

    if not args.audio.exists():
        print(f"Audio file not found: {args.audio}\nRun: uv run python tests/record_sample.py", file=sys.stderr)
        raise SystemExit(1)
    if not args.reference.exists():
        print(f"Reference file not found: {args.reference}", file=sys.stderr)
        raise SystemExit(1)

    audio = np.load(args.audio)
    reference = _extract_reference(args.reference)
    duration_s = round(len(audio) / 16000, 1)

    ref_words = len(reference.split())
    print(f"Audio: {duration_s}s  |  Reference: {ref_words} words  |  Models: {len(args.models)}", file=sys.stderr)
    print("-" * 60, file=sys.stderr)

    results = {
        "reference": reference,
        "audio_duration_s": duration_s,
        "models": [],
    }

    for model in args.models:
        print(f"\nRunning: {model}", file=sys.stderr, flush=True)
        result = _run_model(audio, model, reference)
        results["models"].append(result)
        wer = result["accuracy"]["cleaned"]["wer_pct"]
        lat = result["transcription_s"]
        print(f"  WER (cleaned): {wer}%  |  Latency: {lat}s", file=sys.stderr)

    # Summary table to stderr
    print("\n" + "=" * 60, file=sys.stderr)
    print(f"{'Model':<45} {'WER%':>6} {'Lat(s)':>8}", file=sys.stderr)
    print("-" * 60, file=sys.stderr)
    for r in results["models"]:
        name = r["model"].split("/")[-1]
        wer = r["accuracy"]["cleaned"]["wer_pct"]
        lat = r["transcription_s"]
        print(f"{name:<45} {wer:>6.1f} {lat:>8.3f}", file=sys.stderr)

    # Full JSON to stdout (pipeable)
    output = json.dumps(results, indent=2)
    print(output)

    if args.out:
        args.out.write_text(output)
        print(f"\nResults saved → {args.out}", file=sys.stderr)


if __name__ == "__main__":
    main()
