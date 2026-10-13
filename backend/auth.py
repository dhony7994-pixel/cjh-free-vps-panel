import re
import sqlite3

from passlib.context import CryptContext

from .database import get_db

password_context = CryptContext(
    schemes=["pbkdf2_sha256"],
    deprecated="auto",
)


def validate_username(username):
    """Validate and normalize a username."""
    if not isinstance(username, str):
        raise ValueError("Invalid username.")

    username = username.strip()

    if not re.fullmatch(r"[A-Za-z0-9_]{3,32}", username):
        raise ValueError(
            "Username must be 3-32 characters using letters, numbers or _."
        )

    return username


def hash_password(password):
    """Hash a password before storing it."""
    if not isinstance(password, str):
        raise ValueError("Invalid password.")

    if not 10 <= len(password) <= 128:
        raise ValueError(
            "Password must contain 10-128 characters."
        )

    return password_context.hash(password)


def verify_password(password, password_hash):
    """Verify a password against its stored hash."""
    if not isinstance(password, str):
        return False

    if not isinstance(password_hash, str):
        return False

    try:
        return password_context.verify(password, password_hash)
    except (ValueError, TypeError):
        return False


def register_user(username, password, confirm_password):
    """Register a new user and return their public account details."""
    username = validate_username(username)

    if not isinstance(password, str):
        raise ValueError("Invalid password.")

    if password != confirm_password:
        raise ValueError("Passwords do not match.")

    password_hash = hash_password(password)

    try:
        with get_db() as db:
            cursor = db.execute(
                """
                INSERT INTO users (username, password_hash)
                VALUES (?, ?)
                """,
                (username, password_hash),
            )

            user_id = cursor.lastrowid

    except sqlite3.IntegrityError as exc:
        raise ValueError(
            "Username is already registered."
        ) from exc

    return {
        "id": user_id,
        "username": username,
    }


def authenticate_user(username, password):
    """Authenticate a user without exposing password information."""
    username = validate_username(username)

    if not isinstance(password, str):
        return None

    with get_db() as db:
        user = db.execute(
            """
            SELECT id, username, password_hash
            FROM users
            WHERE username = ?
            """,
            (username,),
        ).fetchone()

    if user is None:
        return None

    if not verify_password(password, user["password_hash"]):
        return None

    return {
        "id": user["id"],
        "username": user["username"],
                      }
