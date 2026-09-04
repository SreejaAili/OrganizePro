"""
duplicate_detector.py
----------------------
Finds duplicate files using SHA-256 content hashing (not filenames).

To avoid hashing every single file (slow for thousands of files), we
first group files by size - two files can only be byte-for-byte
duplicates if they are exactly the same size. Only files that share a
size with at least one other file are actually hashed.
"""

import hashlib
from pathlib import Path

from utils import format_size

CHUNK_SIZE = 65536  # 64 KB per chunk - keeps memory usage low even for huge files


def compute_sha256(file_path: Path) -> str:
    """
    Computes the SHA-256 hash of a file's contents, reading it in small
    chunks instead of loading the whole file into memory at once.
    This is what lets the app safely hash a multi-gigabyte video file.
    """
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        while True:
            chunk = f.read(CHUNK_SIZE)
            if not chunk:
                break
            hasher.update(chunk)
    return hasher.hexdigest()


def find_duplicates(metadata_list: list) -> list:
    """
    metadata_list: list of dicts from analyzer.get_file_metadata()
    (each must include "path" and "size_bytes").

    Returns a list of duplicate groups, each shaped like:
        {
            "hash": "...",
            "files": [metadata_dict, ...],   # 2 or more entries
            "size_each": int,
            "wasted_space_bytes": int,
            "wasted_space_readable": str,
        }
    Groups are sorted by wasted space, largest first.
    """
    # Step 1: group by size. Only sizes shared by 2+ files can possibly
    # be duplicates, so single-file size groups are dropped immediately
    # without ever being hashed - this is the main performance win.
    by_size = {}
    for entry in metadata_list:
        by_size.setdefault(entry["size_bytes"], []).append(entry)

    size_candidates = [group for group in by_size.values() if len(group) > 1]

    # Step 2: within each same-size group, hash the files and group by hash.
    duplicate_groups = []
    for size_group in size_candidates:
        by_hash = {}
        for entry in size_group:
            try:
                file_hash = compute_sha256(Path(entry["path"]))
            except OSError:
                continue  # file vanished or became unreadable - skip it safely
            by_hash.setdefault(file_hash, []).append(entry)

        for file_hash, files in by_hash.items():
            if len(files) > 1:
                size_each = files[0]["size_bytes"]
                wasted_bytes = size_each * (len(files) - 1)
                duplicate_groups.append({
                    "hash": file_hash,
                    "files": files,
                    "size_each": size_each,
                    "wasted_space_bytes": wasted_bytes,
                    "wasted_space_readable": format_size(wasted_bytes),
                })

    duplicate_groups.sort(key=lambda group: group["wasted_space_bytes"], reverse=True)
    return duplicate_groups
