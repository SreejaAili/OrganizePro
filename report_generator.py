"""
report_generator.py
---------------------
Exports a snapshot of the current analysis to a CSV or JSON file
inside reports/, so the user has something shareable outside of the
application itself.
"""

import csv
import json
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).resolve().parent
REPORTS_DIR = PROJECT_ROOT / "reports"


def _make_report_path(extension: str) -> Path:
    REPORTS_DIR.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return REPORTS_DIR / f"report_{timestamp}.{extension}"


def export_csv(metadata_list: list) -> Path:
    """
    Writes filename, category, size, and path for every scanned file
    to a CSV file. Returns the path to the created file.
    """
    report_path = _make_report_path("csv")
    with open(report_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["filename", "category", "size_bytes", "size_readable", "path"])
        for entry in metadata_list:
            writer.writerow([
                entry["name"], entry["category"], entry["size_bytes"],
                entry["size_readable"], entry["path"],
            ])
    return report_path


def export_json(stats: dict) -> Path:
    """
    Writes a dashboard-style statistics summary to a JSON file.
    Returns the path to the created file.
    """
    report_path = _make_report_path("json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=4)
    return report_path
