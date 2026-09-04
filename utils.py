"""
utils.py
--------
Small, reusable helper functions that don't belong to any single
part of the app: file-size math and the "don't overwrite files" logic.
"""

from pathlib import Path


def calculate_total_size(file_paths) -> int:
    """
    Adds up the size (in bytes) of every file in file_paths.
    Skips a file quietly if it can't be read (e.g. it was deleted
    by something else while we were scanning).
    """
    total_bytes = 0
    for file_path in file_paths:
        try:
            total_bytes += file_path.stat().st_size
        except OSError:
            continue
    return total_bytes


def format_size(size_in_bytes: float) -> str:
    """
    Converts a raw byte count into a human-readable string.

    Example:
        format_size(1932735283) -> "1.80 GB"
    """
    size = float(size_in_bytes)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if size < 1024:
            return f"{size:.2f} {unit}"
        size /= 1024
    return f"{size:.2f} PB"


def get_unique_filename(destination_folder: Path, filename: str) -> str:
    """
    Returns a filename that is guaranteed not to already exist inside
    destination_folder. If 'filename' is already free, it is returned
    unchanged. Otherwise it keeps trying photo_1.jpg, photo_2.jpg, ...
    until it finds a name that is free.

    This function NEVER overwrites an existing file - that's the whole
    point of it.
    """
    candidate_path = destination_folder / filename
    if not candidate_path.exists():
        return filename

    # Split "photo.jpg" into stem="photo" and suffix=".jpg"
    stem = candidate_path.stem
    suffix = candidate_path.suffix

    counter = 1
    while True:
        new_filename = f"{stem}_{counter}{suffix}"
        if not (destination_folder / new_filename).exists():
            return new_filename
        counter += 1
