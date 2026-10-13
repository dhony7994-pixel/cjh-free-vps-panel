import os
import sqlite3
from pathlib import Path
from contextlib import contextmanager

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:////opt/cjh-free-vps/cjh.db"
)

if not DATABASE_URL.startswith("sqlite:///"):
    raise RuntimeError("Only SQLite is supported by this module.")

DB_PATH = Path(DATABASE_URL.replace("sqlite:///", "", 1))
DB_PATH.parent.mkdir(parents=True, exist_ok=True)


@contextmanager
def get_db():
    connection = sqlite3.connect(DB_PATH, timeout=10)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")

    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def init_db():
    with get_db() as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        db.execute("""
            CREATE TABLE IF NOT EXISTS vps_instances (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                provider TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id)
                    REFERENCES users(id)
                    ON DELETE CASCADE
            )
        """)


if __name__ == "__main__":
    init_db()
    print("CJH FREE VPS database initialized.")
