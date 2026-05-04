"""Record a fixed-duration audio sample to disk for repeatable benchmark comparisons.

Usage:
    uv run python tests/record_sample.py [--duration 30] [--out tests/sample.npy]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np


def main() -> None:
    parser = argparse.ArgumentParser(description="Record audio sample for benchmark.")
    parser.add_argument("--duration", type=float, default=30.0, help="Recording duration in seconds (default: 30).")
    parser.add_argument("--out", type=Path, default=Path("tests/sample.npy"), help="Output .npy file path.")
    args = parser.parse_args()

    from local_whisper import audio

    print(f"Recording {args.duration}s — speak now...", file=sys.stderr, flush=True)
    data = audio.record(duration=args.duration)
    np.save(args.out, data)
    print(f"Saved {data.shape[0] / 16000:.1f}s of audio → {args.out}", file=sys.stderr)


if __name__ == "__main__":
    main()
