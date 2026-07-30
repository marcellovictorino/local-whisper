"""Validate the local-whisper TOML configuration file."""

import sys
import tomllib
from pathlib import Path

CONFIG_PATH = Path.home() / ".config" / "local-whisper" / "config.toml"


def main() -> int:
    """Parse the user config and report its validation outcome."""
    if not CONFIG_PATH.exists():
        print(f"Config file not found: {CONFIG_PATH}")
        return 0

    try:
        with CONFIG_PATH.open("rb") as config_file:
            tomllib.load(config_file)
    except tomllib.TOMLDecodeError as exc:
        print(f"Invalid TOML in {CONFIG_PATH}: {exc}", file=sys.stderr)
        return 1

    print(f"Config file is valid: {CONFIG_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
