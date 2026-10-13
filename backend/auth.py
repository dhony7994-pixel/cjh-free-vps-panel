import os
import re
import sqlite3
from pathlib import Path

from dotenv import load_dotenv
from passlib.context import CryptContext

load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:////opt/cjh-free-vps/cjh.db"
)

if not DATABASE_URL.startswith("sqlite:///"):
    raise RuntimeError("Only SQLite is supported.")

DB_PATH = Path(DATABASE_URL.replace("sqlite:///", "", 1))

password_context = CryptContext(
    schemes=["pbkdf2_sha256"],
    deprecated="auto"
)


def get_connection():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(DB_PATH, timeout=10)
    connection.row_factory = sqlite3.Row
    return connection


def validate_username(username):
    if not isinstance(username, str):
        raise ValueError("Username must be text.")

    username = username.strip()

    if not re.fullmatch(r"[A-Za-z0-9_]{3,32}", username):
        raise ValueError(
            "Username must be 3-32 characters: letters, numbers or _."
        )

    return username


def hash_password(password):
    if not isinstance(password, str) or len(password) < 10:
        raise ValueError("Password must contain at least 10 characters.")

    if len(password) > 128:
        raise ValueError("Password is too long.")

    return password_context.hash(password)


def verify_password(password, password_hash):
    try:
        return password_context.verify(password, password_hash)
    except (ValueError, TypeError):
        return False


def register_user(username, password, confirm_password):
    username = validate_username(username)

    if password != confirm_password:
        raise ValueError("Passwords do not match.")

    password_hash = hash_password(password)

    with get_connection() as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        try:
            cursor = db.execute(
                "INSERT INTO users (username, password_hash) VALUES (?, ?)",
                (username, password_hash)
            )
        except sqlite3.IntegrityError:
            raise ValueError("Username is already registered.")

        return {
            "id": cursor.lastrowid,
            "username": username
        }


def authenticate_user(username, password):
    username = validate_username(username)

    with get_connection() as db:
        user = db.execute(
            "SELECT id, username, password_hash FROM users WHERE username = ?",
            (username,)
        ).fetchone()

    if user is None or not verify_password(password, user["password_hash"]):
        return None

    return {
        "id": user["id"],
        "username": user["username"]
}
