"""
logger.py
---------
Handles writing the activity log to logs/organizer_log.txt using
Python's built-in `logging` module.

Every move, skip, and error gets one line in the log file, with a
timestamp, so you always have a record of what the program did.
"""

import logging
from pathlib import Path

# logs/ lives next to this file, so it works no matter where the
# app is launched from.
PROJECT_ROOT = Path(__file__).resolve().parent
LOG_DIR = PROJECT_ROOT / "logs"
LOG_FILE = LOG_DIR / "organizer_log.txt"

_logger = None  # module-level cache so we only configure logging once


def setup_logger() -> logging.Logger:
    """
    Creates (if needed) the logs folder and configures a logger that
    writes to organizer_log.txt. Safe to call multiple times - it will
    only attach the file handler once.
    """
    global _logger
    if _logger is not None:
        return _logger

    LOG_DIR.mkdir(exist_ok=True)

    logger = logging.getLogger("smart_file_organizer")
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
        formatter = logging.Formatter(
            "%(asctime)s | %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    _logger = logger
    return logger


def log_action(logger, filename, source, destination, action, error=None):
    """
    Writes one line to the log file describing what happened to a file.

    action is a short word like "MOVED", "SKIPPED" or "FAILED".
    error is optional - only pass it when something went wrong.
    """
    if error:
        message = (
            f"FILE: {filename} | FROM: {source} | TO: {destination} "
            f"| ACTION: {action} | ERROR: {error}"
        )
        logger.error(message)
    else:
        message = (
            f"FILE: {filename} | FROM: {source} | TO: {destination} "
            f"| ACTION: {action}"
        )
        logger.info(message)
