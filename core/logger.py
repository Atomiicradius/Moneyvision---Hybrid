"""
core/logger.py
--------------
Centralised logging setup for the entire project.

Why a custom logger?
  - Consistent timestamps in IST
  - Separate log levels for tools (DEBUG) vs UI (INFO)
  - Easy to pipe into a file later without touching any other module
"""

import logging
import sys
from datetime import datetime
import pytz

IST = pytz.timezone("Asia/Kolkata")


class ISTFormatter(logging.Formatter):
    """Custom formatter that converts log timestamps to IST."""

    def formatTime(self, record: logging.LogRecord, datefmt: str = None) -> str:
        utc_dt = datetime.utcfromtimestamp(record.created).replace(tzinfo=pytz.utc)
        ist_dt = utc_dt.astimezone(IST)
        return ist_dt.strftime(datefmt or "%Y-%m-%d %H:%M:%S %Z")


def get_logger(name: str, level: int = logging.DEBUG) -> logging.Logger:
    """
    Returns a named logger with IST-aware timestamps.

    Usage:
        from core.logger import get_logger
        logger = get_logger(__name__)
        logger.info("Fetching stock data...")
    """
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger  # Avoid duplicate handlers on re-import

    logger.setLevel(level)

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)

    fmt = ISTFormatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    )
    handler.setFormatter(fmt)
    logger.addHandler(handler)
    return logger
