__version__ = "0.1.0"

import logging
import sys
import time
from pathlib import Path


def _setup_logging() -> None:
    logger = logging.getLogger("local_whisper")
    if logger.handlers:
        return
    logger.setLevel(logging.DEBUG)

    console = logging.StreamHandler(sys.stderr)
    console.setLevel(logging.INFO)
    console.setFormatter(logging.Formatter("%(levelname)s | %(message)s"))
    logger.addHandler(console)

    log_dir = Path.home() / ".config" / "local-whisper"
    try:
        log_dir.mkdir(parents=True, exist_ok=True)
        fh = logging.FileHandler(log_dir / "local-whisper.log", encoding="utf-8")
        fh.setLevel(logging.DEBUG)
        fmt = logging.Formatter(
            "%(asctime)s UTC | %(levelname)s | %(module)s:%(lineno)d | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        fmt.converter = time.gmtime  # type: ignore[assignment]  # asctime must actually be UTC
        fh.setFormatter(fmt)
        logger.addHandler(fh)
    except OSError:
        pass


_setup_logging()
