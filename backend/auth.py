import re

from passlib.context import CryptContext

from .database import get_db

password_context = CryptContext(
    schemes=["pbkdf2_sha256"],
    deprecated="auto",
)


def validate_username(username):
    if not isinstance(username, str):
        raise ValueError("Invalid username.")

    username = username.strip()

    if not re.fullmatch(r"[A-Za-z0-9_]{3,32}", username):
        raise ValueError(
            "Username must be 3-32 characters using letters, numbers or _."
        )

    return username


def hash_password(password):
    if not isinstance(password, str):
        raise ValueError("Invalid password.")

    if len(password) < 10:
        raise ValueError("Password must contain at least 10 characters.")

    if len(password) > 128:
        raise ValueError("Password is too long.")

    return password_context.hash(password)


def verify_password(password, password_hash):
    if not isinstance(password, str):
        return False

    if not isinstance(password_hash, str):
        return False

    try:
        return password_context.verify(password, password_hash)
    except (ValueError, TypeError):
        return False


def register_user(username, password, confirm_password):
    username = validate_username(username)

    if password != confirm_password:
        raise ValueError("Passwords do not match.")

    password_hash = hash_password(password)

    with get_db() as db:
        try:
            cursor = db.execute(
                """
                INSERT INTO users (username, password_hash)
                VALUES (?, ?)
                """,
                (username, password_hash),
            )
        except Exception as exc:
            import sqlite3

            if isinstance(exc, sqlite3.IntegrityError):
                raise ValueError(
                    "Username is already registered."
                ) from exc
            raise

        return {
            "id": cursor.lastrowid,
            "username": username,
        }


def authenticate_user(username, password):
    username = validate_username(username)

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
