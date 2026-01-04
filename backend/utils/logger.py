import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional

# Resolve project root safely
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Single canonical log directory
LOG_DIR = PROJECT_ROOT / "external_memory" / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

_LOGGERS = {}


def get_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """
    Returns a configured singleton logger.

    - Console + file logging
    - No duplicate handlers
    - One log file per day
    """
    if name in _LOGGERS:
        return _LOGGERS[name]

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.propagate = False  # prevent double logging

    # Formatter
    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] [%(name)s] %(message)s"
    )

    # File handler (daily)
    log_file = LOG_DIR / f"{datetime.now():%Y%m%d}.log"
    fh = logging.FileHandler(log_file, encoding="utf-8")
    fh.setFormatter(formatter)
    fh.setLevel(level)

    # Console handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setFormatter(formatter)
    ch.setLevel(level)

    logger.addHandler(fh)
    logger.addHandler(ch)

    _LOGGERS[name] = logger
    return logger
