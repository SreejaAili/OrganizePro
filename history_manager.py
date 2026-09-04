"""
history_manager.py
--------------------
Keeps a persistent, append-only Activity History of every operation
(organize, undo), saved to data/history.json so it survives an app
restart.

This is separate from undo_manager.py: undo_manager only remembers the
MOST RECENT organize operation (so it can be reversed), while
history_manager keeps a running log of every operation that has ever
happened, purely for the user's own reference.
"""

import json
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).resolve().parent
DATA_DIR = PROJECT_ROOT / "data"
HISTORY_FILE = DATA_DIR / "history.json"

MAX_HISTORY_ENTRIES = 200  # keeps the file from growing forever


def load_history() -> list:
    """Returns the saved history as a list of dicts, newest first."""
    if not HISTORY_FILE.exists():
        return []
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return []


def add_history_entry(operation_type: str, files_count: int, success: bool, details: str = "") -> None:
    """
    Appends one entry describing an operation (e.g. "Organization",
    "Undo") to the history file.
    """
    history = load_history()
    entry = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "operation": operation_type,
        "files_count": files_count,
        "success": success,
        "details": details,
    }
    history.insert(0, entry)  # newest entries first
    history = history[:MAX_HISTORY_ENTRIES]

    DATA_DIR.mkdir(exist_ok=True)
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=4)
