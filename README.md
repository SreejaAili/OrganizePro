# Smart File Organizer

A beginner-friendly desktop application that automatically organizes the
files in a folder into category subfolders (Documents, Images, Videos,
Audio, Code, and more) — safely, with a preview step, undo support, and
an activity log.

## Overview

Smart File Organizer lets you pick any folder on your computer (like
your Downloads folder) and, with a couple of clicks, sorts every file
inside it into neatly labeled subfolders based on file type. Before
anything is moved, you get a full preview of what will happen. Nothing
is ever deleted, and existing files are never overwritten.

## Features

- **Folder selection** via a native folder picker dialog
- **Preview Organization** — see exactly where every file will go before
  anything moves, with a search box to filter the preview list
- **Safe file moving** — files are moved (never copied-and-deleted, never
  deleted outright)
- **Duplicate filename protection** — if `photo.jpg` already exists at
  the destination, the new file becomes `photo_1.jpg`, `photo_2.jpg`, etc.
  Nothing is ever overwritten.
- **Statistics dashboard** — total files found, a count per category,
  and total combined file size
- **Confirmation prompt** before any files are actually moved
- **Progress bar** while files are being organized
- **Activity log** written to `logs/organizer_log.txt` with a timestamp,
  filename, source, destination, action, and error (if any) for every file
- **Undo Last Organization** — moves every file back to where it came
  from, using a record saved in `data/last_operation.json`
- **Robust error handling** — a problem with one file (permission denied,
  file missing, etc.) is logged and skipped; the rest of the files are
  still processed
- **No recursion** — only files directly inside the selected folder are
  touched; subfolders are left alone

## Technologies

```text
Python 3
Tkinter    - GUI
pathlib    - filesystem paths
shutil     - moving files
json       - saving the undo record
logging    - activity log
unittest   - automated tests
```

No external / third-party packages are required — everything is part of
the Python standard library.

## How It Works

1. **Scan** — When you click *Preview Organization*, the app looks at
   every file directly inside the selected folder (it does not look
   inside subfolders).
2. **Categorize** — Each file's extension (`.pdf`, `.jpg`, `.mp3`, ...)
   is looked up in a category map (see `categories.py`). Unknown or
   missing extensions go into `Others`.
3. **Preview** — The filename → category pairing is shown in a table,
   along with a statistics summary (file counts and total size). No
   files are touched yet.
4. **Confirm** — Clicking *Organize Files* asks "Are you sure?" before
   doing anything.
5. **Move** — Each file is moved into a category subfolder that is
   created only when it's actually needed. If a name collision would
   occur, the file is renamed instead of overwritten.
6. **Log** — Every move (or failure) is written to
   `logs/organizer_log.txt`, and the full set of moves is saved to
   `data/last_operation.json` so it can be undone.
7. **Undo (optional)** — Clicking *Undo Last Organization* reads that
   JSON file and moves every file back to its original location.

## Project Structure

```text
Smart-File-Organizer/
│
├── main.py              # Tkinter GUI - the only file that draws windows/buttons
├── organizer.py          # Core logic: scan, preview, organize, move_file
├── categories.py         # Extension -> category mapping
├── utils.py              # get_unique_filename, size calculation/formatting
├── logger.py             # Activity log setup and writing
├── undo_manager.py        # Saves/restores the last organize operation
│
├── data/
│   └── last_operation.json   # Created automatically after organizing
│
├── logs/
│   └── organizer_log.txt     # Created automatically after organizing
│
├── tests/
│   └── test_organizer.py     # Automated unittest tests
│
├── README.md
├── requirements.txt
└── .gitignore
```

## Installation

1. Make sure you have **Python 3.9+** installed (Tkinter ships with
   standard Python installers on Windows, so no extra install step is
   needed there).
2. Download or clone this project folder.
3. (Optional) create a virtual environment:
   ```bash
   python -m venv venv
   venv\Scripts\activate      # Windows
   ```
4. Install requirements (there are none beyond the standard library,
   but this keeps things consistent):
   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. Run the app:
   ```bash
   python main.py
   ```
2. Click **Select Folder** and choose the folder you want to organize
   (e.g. your Downloads folder).
3. Click **Preview Organization** to see what will happen — check the
   file list and the statistics dashboard. Use the **Search** box to
   filter the preview if the folder has a lot of files.
4. Click **Organize Files** and confirm the prompt. Watch the progress
   bar as files are moved.
5. If you change your mind, click **Undo Last Organization** to move
   everything back.

## Screenshots

*(Add screenshots here after running the app, e.g.)*

```text
screenshots/main-window.png
screenshots/preview.png
screenshots/statistics.png
```

## Testing

Automated tests cover the core logic (file categorization, duplicate
filename handling, no-extension files, and full organize/undo cycles)
using temporary folders, so your real files are never at risk.

Run all tests from the project root:

```bash
python -m unittest discover tests
```

You should see something like:

```text
Ran 17 tests in 0.02s

OK
```

## Future Improvements

These are ideas for later versions — **not** implemented yet:

- Recursive organization (optional subfolder scanning)
- Content-based duplicate detection (not just filename-based)
- Learning user-specific categorization preferences over time
- Dark mode for the GUI
- Scheduled/automatic organization (e.g. run every night)
- Cloud storage support (Google Drive, Dropbox, etc.)
- Smarter, ML-based file categorization

## Author's Note

This project was built to strengthen fundamentals in Python file
handling, automation, GUI development with Tkinter, exception handling,
logging, and basic data persistence with JSON.
