"""
settings_manager.py
--------------------
Loads and saves user-configurable settings to data/settings.json,
so preferences persist between application launches.
"""

import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
DATA_DIR = PROJECT_ROOT / "data"
SETTINGS_FILE = DATA_DIR / "settings.json"

DEFAULT_SETTINGS = {
    "large_file_threshold_mb": 100,
    "include_subfolders": False,
    "never_overwrite": True,          # always True - shown in Settings, not editable
    "enable_logging": True,
    "confirm_before_organize": True,
    "default_folder": "",
}


def load_settings() -> dict:
    """
    Returns the saved settings, merged on top of the defaults so that
    a missing key (e.g. after an update adds a new setting) never
    causes a crash - it just falls back to its default value.
    """
    if not SETTINGS_FILE.exists():
        return dict(DEFAULT_SETTINGS)

    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            saved_settings = json.load(f)
    except (json.JSONDecodeError, OSError):
        return dict(DEFAULT_SETTINGS)

    settings = dict(DEFAULT_SETTINGS)
    settings.update(saved_settings)
    return settings


def save_settings(settings: dict) -> None:
    """Writes the given settings dictionary to data/settings.json."""
    DATA_DIR.mkdir(exist_ok=True)
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=4)


def update_setting(key: str, value) -> dict:
    """
    Convenience helper: loads the current settings, updates a single
    key, saves the result, and returns the updated dictionary.
    """
    settings = load_settings()
    settings[key] = value
    save_settings(settings)
    return settings
