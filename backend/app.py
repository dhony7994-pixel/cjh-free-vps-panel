import os
import hmac
import hashlib
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
pwd_context = CryptContext(
    schemes=["pbkdf2_sha256"],
    deprecated="auto"
)


def get_connection():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(DB_PATH, timeout=10)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys = ON")
    return db


def hash_password(password: str) -> str:
    if len(password) < 10:
        raise ValueError("Password must contain at least 10 characters.")

    return pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return pwd_context.verify(password, password_hash)
    except (ValueError, TypeError):
        return False


def authenticate_user(username: str, password: str):
    with get_connection() as db:
        user = db.execute(
            "SELECT id, username, password_hash "
            "FROM users WHERE username = ?",
            (username.strip(),)
        ).fetchone()

    if user is None:
        return None

    if not verify_password(password, user["password_hash"]):
        return None

    return {
        "id": user["id"],
        "username": user["username"]
}
