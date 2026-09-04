"""
analyzer.py
-----------
Analyzes the selected folder and reports information about files.

IMPORTANT:
The analyzer has its OWN scanning logic.

Unlike organizer.py, the analyzer DOES enter category folders.

Therefore:

TEST/
    Images/
        photo.jpg
    Documents/
        notes.pdf

will correctly report:

2 files
2 categories

This allows the user to analyze the same folder repeatedly
after organizing it.
"""

import os
from pathlib import Path
from datetime import datetime

from categories import get_category_for_extension
from utils import format_size


# ------------------------------------------------------------
# Folders belonging to the application
# ------------------------------------------------------------

APP_OWN_DIRS = {
    "data",
    "logs",
    "reports",
    "tests",
    "__pycache__",
    ".git",
    "venv",
    ".venv",
    ".vscode",
    ".idea",
}


# ------------------------------------------------------------
# Hidden/system files
# ------------------------------------------------------------

IGNORED_FILENAMES = {
    "desktop.ini",
    "thumbs.db",
    ".ds_store",
}


# ------------------------------------------------------------
# Application files
# ------------------------------------------------------------

APP_OWN_FILES = {
    "main.py",
    "organizer.py",
    "categories.py",
    "utils.py",
    "analyzer.py",
    "duplicate_detector.py",
    "settings_manager.py",
    "history_manager.py",
    "report_generator.py",
    "logger.py",
    "undo_manager.py",
    "organizer_log.txt",
    "last_operation.json",
    "history.json",
    "settings.json",
    "requirements.txt",
    "README.md",
    ".gitignore",
}


# ------------------------------------------------------------
# Check whether a file should be ignored
# ------------------------------------------------------------

def _should_skip_file(file_path: Path) -> bool:
    """
    Determines whether the analyzer should ignore a file.
    """

    if file_path.name.lower() in IGNORED_FILENAMES:
        return True

    if file_path.name.startswith("."):
        return True

    if file_path.name in APP_OWN_FILES:
        return True

    return False


# ------------------------------------------------------------
# Analyzer directory scanner
# ------------------------------------------------------------

def _walk_analysis_dirs(root: Path):
    """
    Recursively walks through directories for ANALYSIS.

    IMPORTANT:

    Unlike organizer.py, this function DOES enter category folders.

    It only skips folders belonging to the application itself.
    """

    for current_root, dirs, files in os.walk(root):

        current_path = Path(current_root)

        # ----------------------------------------------------
        # Remove application folders from recursion
        # ----------------------------------------------------

        dirs[:] = [
            directory
            for directory in dirs
            if (
                directory not in APP_OWN_DIRS
                and not directory.startswith(".")
            )
        ]

        # ----------------------------------------------------
        # Yield current directory and its files
        # ----------------------------------------------------

        yield current_path, files


# ------------------------------------------------------------
# Analyze folder
# ------------------------------------------------------------

def analyze_folder(
    folder_path,
    include_subfolders: bool = False,
) -> list:
    """
    Analyzes files inside folder_path.

    DIFFERENCE FROM ORGANIZER:

    Analyzer DOES scan category folders.

    Example:

        TEST/
            Images/
                photo.jpg

    Analyzer will detect photo.jpg.

    If include_subfolders=False:
        only files directly inside TEST are analyzed.

    If include_subfolders=True:
        all user subfolders, including category folders,
        are analyzed.
    """

    folder_path = Path(folder_path)

    if not folder_path.exists():
        raise FileNotFoundError(
            f"The folder '{folder_path}' does not exist."
        )

    if not folder_path.is_dir():
        raise NotADirectoryError(
            f"'{folder_path}' is not a folder."
        )

    metadata_list = []

    # --------------------------------------------------------
    # Only selected folder
    # --------------------------------------------------------

    if not include_subfolders:

        try:
            entries = list(folder_path.iterdir())
        except OSError:
            return []

        for item in entries:

            if (
                item.is_file()
                and not _should_skip_file(item)
            ):
                try:
                    metadata_list.append(
                        get_file_metadata(item)
                    )
                except OSError:
                    continue

        return metadata_list

    # --------------------------------------------------------
    # Recursive analysis
    # --------------------------------------------------------

    for current_dir, filenames in _walk_analysis_dirs(
        folder_path
    ):

        for filename in filenames:

            file_path = current_dir / filename

            if _should_skip_file(file_path):
                continue

            try:
                metadata_list.append(
                    get_file_metadata(file_path)
                )
            except OSError:
                continue

    return metadata_list


# ------------------------------------------------------------
# File metadata
# ------------------------------------------------------------

def get_file_metadata(
    file_path: Path,
) -> dict:
    """
    Returns useful metadata for a file.
    """

    stat_result = file_path.stat()

    category = get_category_for_extension(
        file_path.suffix
    )

    return {
        "name": file_path.name,
        "extension": file_path.suffix or "(none)",
        "category": category,
        "path": str(file_path),
        "size_bytes": stat_result.st_size,
        "size_readable": format_size(
            stat_result.st_size
        ),
        "created": datetime.fromtimestamp(
            stat_result.st_ctime
        ).strftime("%d-%b-%Y %H:%M"),
        "modified": datetime.fromtimestamp(
            stat_result.st_mtime
        ).strftime("%d-%b-%Y %H:%M"),
    }


# ------------------------------------------------------------
# Category distribution
# ------------------------------------------------------------

def get_category_distribution(
    metadata_list: list,
) -> dict:
    """
    Returns:

        {
            "Images": 5,
            "Documents": 3,
            "Audio": 2
        }
    """

    distribution = {}

    for entry in metadata_list:

        category = entry["category"]

        distribution[category] = (
            distribution.get(category, 0) + 1
        )

    return distribution


# ------------------------------------------------------------
# Dashboard statistics
# ------------------------------------------------------------

def get_dashboard_stats(
    metadata_list,
    duplicate_group_count=0,
    large_file_count=0,
    empty_folder_count=0,
) -> dict:
    """
    Builds statistics for the Dashboard.
    """

    total_size = sum(
        entry["size_bytes"]
        for entry in metadata_list
    )

    distribution = get_category_distribution(
        metadata_list
    )

    return {
        "total_files": len(metadata_list),
        "total_size_bytes": total_size,
        "total_size_readable": format_size(
            total_size
        ),
        "duplicates": duplicate_group_count,
        "large_files": large_file_count,
        "empty_folders": empty_folder_count,
        "categories": len(distribution),
        "distribution": distribution,
    }


# ------------------------------------------------------------
# Large file detection
# ------------------------------------------------------------

def find_large_files(
    metadata_list,
    threshold_mb: float,
) -> list:
    """
    Returns files whose size is greater than or equal
    to the configured threshold.
    """

    threshold_bytes = (
        threshold_mb * 1024 * 1024
    )

    large_files = [
        entry
        for entry in metadata_list
        if entry["size_bytes"] >= threshold_bytes
    ]

    large_files.sort(
        key=lambda entry: entry["size_bytes"],
        reverse=True,
    )

    return large_files


# ------------------------------------------------------------
# Empty folder detection
# ------------------------------------------------------------

def find_empty_folders(
    folder_path,
) -> list:
    """
    Finds empty user folders.

    Application folders are ignored.

    Category folders containing files are NOT considered empty.

    Empty category folders are also ignored because category folders
    are created by the organizer and are not useful as user cleanup
    candidates.
    """

    folder_path = Path(folder_path)

    empty_folders = []

    # Import here to avoid unnecessary dependency issues.
    from categories import FILE_CATEGORIES, OTHERS_CATEGORY

    category_folder_names = (
        set(FILE_CATEGORIES.keys())
        | {OTHERS_CATEGORY}
    )

    ignored_dirs = (
        APP_OWN_DIRS
        | category_folder_names
    )

    # --------------------------------------------------------
    # Walk bottom-up so child folders are checked first
    # --------------------------------------------------------

    for root, dirs, files in os.walk(
        folder_path,
        topdown=False,
    ):

        root_path = Path(root)

        # Don't report selected folder itself
        if root_path == folder_path:
            continue

        # Don't report application folders
        if root_path.name in APP_OWN_DIRS:
            continue

        # Don't report hidden folders
        if root_path.name.startswith("."):
            continue

        # Don't report category folders
        if root_path.name in ignored_dirs:
            continue

        # Direct files mean this folder isn't empty
        if files:
            continue

        # Check child folders
        remaining_subdirs = [
            root_path / directory
            for directory in dirs
            if (
                directory not in APP_OWN_DIRS
                and not directory.startswith(".")
            )
        ]

        # If it has no usable child folders, it's empty
        if not remaining_subdirs:
            empty_folders.append(
                str(root_path)
            )
            continue

        # Check whether all child folders are empty
        all_children_empty = all(
            str(child) in empty_folders
            for child in remaining_subdirs
        )

        if all_children_empty:
            empty_folders.append(
                str(root_path)
            )

    return sorted(empty_folders)