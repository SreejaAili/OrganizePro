"""
undo_manager.py
---------------
Remembers the most recent "Organize Files" operation and can move
every file back to where it came from.

Only ONE level of undo is supported on purpose (per the project spec):
running "Organize Files" again overwrites the remembered operation.
"""

import json
import shutil
from pathlib import Path
from datetime import datetime

from utils import get_unique_filename

PROJECT_ROOT = Path(__file__).resolve().parent
DATA_DIR = PROJECT_ROOT / "data"
UNDO_FILE = DATA_DIR / "last_operation.json"


def save_last_operation(moves: list) -> None:
    """
    Saves the list of moves performed during the last organize
    operation, so they can be reversed later.

    moves is a list of dicts, each shaped like:
        {"original_path": "...", "new_path": "..."}
    """
    DATA_DIR.mkdir(exist_ok=True)
    operation_data = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "moves": moves,
    }
    with open(UNDO_FILE, "w", encoding="utf-8") as f:
        json.dump(operation_data, f, indent=4)


def has_undo_available() -> bool:
    """True if there is a remembered operation that can be undone."""
    return UNDO_FILE.exists()


def undo_last_operation():
    """
    Moves every file from the last organize operation back to its
    original location.

    Returns a tuple: (success: bool, message: str, details: dict)
    details has "restored" (list of strings) and "errors" (list of strings).
    """
    if not UNDO_FILE.exists():
        return False, "No previous organization found to undo.", {}

    with open(UNDO_FILE, "r", encoding="utf-8") as f:
        operation_data = json.load(f)

    moves = operation_data.get("moves", [])
    restored = []
    errors = []

    # Undo in reverse order, in case any later logic ever depends on it.
    for move in reversed(moves):
        original_path = Path(move["original_path"])
        new_path = Path(move["new_path"])

        try:
            if not new_path.exists():
                errors.append(f"{new_path.name}: file not found, cannot undo.")
                continue

            original_path.parent.mkdir(parents=True, exist_ok=True)

            # If something already occupies the original spot, don't
            # overwrite it - give the restored file a safe unique name.
            target_name = original_path.name
            if original_path.exists():
                target_name = get_unique_filename(original_path.parent, target_name)
            final_original_path = original_path.parent / target_name

            shutil.move(str(new_path), str(final_original_path))
            restored.append(f"{new_path.name} -> {final_original_path}")

        except OSError as e:
            errors.append(f"{new_path.name}: {e}")

    # The undo has been "used up" - remove the record so it can't be
    # accidentally run twice.
    UNDO_FILE.unlink(missing_ok=True)

    message = "Undo completed."
    return True, message, {"restored": restored, "errors": errors}
