"""
categories.py
-------------
Defines which file extensions belong to which category.

This is the single source of truth for "what kind of file is this?".
If you want to support a new file type later, you only need to add
the extension here - nothing else in the project needs to change.
"""

# Every category maps to a list of file extensions (always lowercase).
FILE_CATEGORIES = {
    "Documents": [".doc", ".docx", ".txt", ".rtf", ".odt"],
    "PDFs": [".pdf"],
    "Images": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".svg"],
    "Videos": [".mp4", ".mkv", ".avi", ".mov", ".wmv", ".webm"],
    "Audio": [".mp3", ".wav", ".aac", ".flac", ".ogg", ".m4a"],
    "Spreadsheets": [".xls", ".xlsx", ".csv", ".ods"],
    "Presentations": [".ppt", ".pptx", ".odp"],
    "Code": [".py", ".java", ".c", ".cpp", ".js", ".ts", ".html", ".css", ".sql", ".json"],
    "Archives": [".zip", ".rar", ".7z", ".tar", ".gz"],
    "Executables": [".exe", ".msi"],
}

# Anything that doesn't match a known extension (or has no extension)
# goes here.
OTHERS_CATEGORY = "Others"


def _build_extension_map():
    """
    Turns FILE_CATEGORIES (category -> [extensions]) "inside out" into
    (extension -> category), so looking up a single file's category is
    a fast dictionary lookup instead of looping through every category.
    """
    extension_map = {}
    for category_name, extensions in FILE_CATEGORIES.items():
        for extension in extensions:
            extension_map[extension.lower()] = category_name
    return extension_map


# Built once, when the module is imported.
EXTENSION_TO_CATEGORY = _build_extension_map()


def get_category_for_extension(extension: str) -> str:
    """
    Returns the category name for a given file extension.

    Example:
        get_category_for_extension(".pdf")  -> "PDFs"
        get_category_for_extension(".xyz")  -> "Others"
        get_category_for_extension("")      -> "Others"
    """
    if not extension:
        return OTHERS_CATEGORY
    return EXTENSION_TO_CATEGORY.get(extension.lower(), OTHERS_CATEGORY)
