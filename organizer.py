"""
organizer.py
------------
The "brain" of the app: scanning a folder, previewing what would
happen, and actually moving files into category folders.

This module knows nothing about Tkinter - it only deals with paths,
files and folders. That separation is what makes it easy to test
(see tests/test_organizer.py) and easy to reuse from a different GUI
later if you ever wanted to.
"""

import shutil
from pathlib import Path

from categories import get_category_for_extension
from utils import get_unique_filename, calculate_total_size, format_size
import logger as log_module
import undo_manager

# Files that belong to the application itself. If the user ever selects
# the project folder to "organize", we skip these so the app can't
# accidentally move its own source code or logs.
APP_OWN_FILES = {
    "main.py", "organizer.py", "categories.py", "utils.py",
    "logger.py", "undo_manager.py", "organizer_log.txt",
    "last_operation.json", "requirements.txt", "README.md", ".gitignore",
}

# Common hidden/system files we should never touch.
IGNORED_FILENAMES = {"desktop.ini", "thumbs.db", ".ds_store"}


def scan_folder(folder_path) -> list:
    """
    Returns a list of pathlib.Path objects for every regular file
    directly inside folder_path.

    - Does NOT look inside subfolders (Version 1 requirement).
    - Skips subfolders themselves.
    - Skips common hidden/system files and the app's own files.

    Raises FileNotFoundError / NotADirectoryError with a clear message
    if the folder is invalid, so the GUI can show a friendly error.
    """
    folder_path = Path(folder_path)

    if not folder_path.exists():
        raise FileNotFoundError(f"The folder '{folder_path}' does not exist.")
    if not folder_path.is_dir():
        raise NotADirectoryError(f"'{folder_path}' is not a folder.")

    files = []
    for item in folder_path.iterdir():
        if not item.is_file():
            continue  # skip subfolders
        if item.name.lower() in IGNORED_FILENAMES:
            continue
        if item.name.startswith("."):
            continue
        if item.name in APP_OWN_FILES:
            continue
        files.append(item)

    return files


def preview_organization(folder_path) -> list:
    """
    Returns a list of (file_path, category) tuples describing what
    WOULD happen, without moving a single file.
    """
    files = scan_folder(folder_path)
    preview_list = []
    for file_path in files:
        category = get_category_for_extension(file_path.suffix)
        preview_list.append((file_path, category))
    return preview_list


def get_statistics(preview_list) -> dict:
    """
    Builds a small statistics dictionary out of a preview list:
    how many files per category, and the total size of all files.
    """
    counts_by_category = {}
    all_files = []

    for file_path, category in preview_list:
        counts_by_category[category] = counts_by_category.get(category, 0) + 1
        all_files.append(file_path)

    total_size_bytes = calculate_total_size(all_files)

    return {
        "total_files": len(all_files),
        "by_category": counts_by_category,
        "total_size_bytes": total_size_bytes,
        "total_size_readable": format_size(total_size_bytes),
    }


def create_category_folder(base_folder: Path, category_name: str) -> Path:
    """
    Creates (if it doesn't already exist) a category subfolder inside
    base_folder, and returns its path. Because this is only called
    right before a file needs to move there, empty category folders
    are never created.
    """
    category_folder = base_folder / category_name
    category_folder.mkdir(exist_ok=True)
    return category_folder


def move_file(file_path: Path, destination_folder: Path) -> Path:
    """
    Safely moves a single file into destination_folder, renaming it
    with get_unique_filename() if a file with the same name already
    exists there. Returns the final path the file was moved to.
    """
    unique_name = get_unique_filename(destination_folder, file_path.name)
    destination_path = destination_folder / unique_name
    shutil.move(str(file_path), str(destination_path))
    return destination_path


def organize_files(folder_path, progress_callback=None) -> dict:
    """
    Moves every file in folder_path into its category subfolder.

    progress_callback, if given, is called as progress_callback(done, total)
    after every file, so the GUI can update a progress bar.

    Returns a summary dict:
        {
            "total": int,
            "moved": [{"file": name, "destination": path}, ...],
            "errors": [{"file": name, "error": message}, ...],
        }

    Every successful move and every error is also written to
    logs/organizer_log.txt, and the successful moves are remembered
    so they can be undone later.
    """
    folder_path = Path(folder_path)
    logger = log_module.setup_logger()

    preview_list = preview_organization(folder_path)
    total = len(preview_list)

    moved = []
    errors = []
    moves_for_undo = []

    for index, (file_path, category) in enumerate(preview_list, start=1):
        try:
            destination_folder = create_category_folder(folder_path, category)
            destination_path = move_file(file_path, destination_folder)

            moved.append({"file": file_path.name, "destination": str(destination_path)})
            moves_for_undo.append({
                "original_path": str(file_path),
                "new_path": str(destination_path),
            })
            log_module.log_action(
                logger, file_path.name, str(file_path), str(destination_path), "MOVED"
            )

        except (OSError, PermissionError, FileNotFoundError) as e:
            # If one file fails (permission denied, file vanished, etc.)
            # we log it and keep going instead of crashing the whole run.
            errors.append({"file": file_path.name, "error": str(e)})
            log_module.log_action(
                logger, file_path.name, str(file_path), "-", "FAILED", error=str(e)
            )

        if progress_callback:
            progress_callback(index, total)

    if moves_for_undo:
        undo_manager.save_last_operation(moves_for_undo)

    return {"total": total, "moved": moved, "errors": errors}
