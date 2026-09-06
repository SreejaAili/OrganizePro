"""
auth_manager.py
----------------
Local username/password authentication for Smart File Organizer.
"""

import json
import hashlib
import uuid
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
DATA_DIR = PROJECT_ROOT / "data"
USERS_FILE = DATA_DIR / "users.json"


def _load_users() -> dict:
    """Load saved users."""
    if not USERS_FILE.exists():
        return {}

    try:
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def _save_users(users: dict) -> None:
    """Save users to users.json."""
    DATA_DIR.mkdir(exist_ok=True)

    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=4)


def _hash_password(password: str, salt: str) -> str:
    """Hash password using SHA-256 and a per-user salt."""
    salted_password = (salt + password).encode("utf-8")
    return hashlib.sha256(salted_password).hexdigest()


def user_exists(username: str) -> bool:
    """Check whether username already exists."""
    return username.strip() in _load_users()


def register_user(username: str, password: str):
    """
    Register a new user.

    Returns:
        (success, message)
    """
    username = username.strip()

    if not username:
        return False, "Username cannot be empty."

    if not password:
        return False, "Password cannot be empty."

    users = _load_users()

    if username in users:
        return False, "That username is already taken."

    salt = uuid.uuid4().hex
    password_hash = _hash_password(password, salt)

    users[username] = {
        "salt": salt,
        "password_hash": password_hash
    }

    _save_users(users)

    return True, "Registration successful. You can now log in."


def verify_login(username: str, password: str):
    """
    Verify username and password.

    Returns:
        (success, message)
    """
    username = username.strip()

    users = _load_users()

    user_record = users.get(username)

    if not user_record:
        return False, "Invalid username or password."

    salt = user_record.get("salt", "")
    expected_hash = user_record.get("password_hash", "")

    entered_hash = _hash_password(password, salt)

    if entered_hash == expected_hash:
        return True, "Login successful."

    return False, "Invalid username or password."