"""Validate the local-whisper TOML configuration file."""

import sys

from local_whisper.config import CONFIG_PATH, ConfigState, load_config


def main() -> int:
    """Parse the user config and report its validation outcome."""
    result = load_config()

    if result.state is ConfigState.MISSING:
        print(f"Config file not found: {CONFIG_PATH}")
        return 0

    if result.state is ConfigState.MALFORMED:
        print(f"Invalid TOML in {CONFIG_PATH}: {result.error}", file=sys.stderr)
        return 1

    print(f"Config file is valid: {CONFIG_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
