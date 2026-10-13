import os
import secrets
import sqlite3
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from passlib.context import CryptContext
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BASE_DIR.parent

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    f"sqlite:///{PROJECT_DIR / 'cjh.db'}"
)

if not DATABASE_URL.startswith("sqlite:///"):
    raise RuntimeError("This starter version requires SQLite.")

DB_PATH = Path(DATABASE_URL.replace("sqlite:///", "", 1))
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

SECRET_KEY = os.getenv("SECRET_KEY", "")

if os.getenv("APP_ENV") == "production":
    if len(SECRET_KEY) < 32 or SECRET_KEY.startswith("REPLACE_"):
        raise RuntimeError("Configure a secure SECRET_KEY before startup.")

pwd_context = CryptContext(
    schemes=["pbkdf2_sha256"],
    deprecated="auto"
)


def connect_db():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_db():
    with connect_db() as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
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
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        """)


@asynccontextmanager
async def lifespan(app: FastAPI):
    initialize_db()
    yield


app = FastAPI(
    title="CJH FREE VPS",
    version="0.1.0",
    lifespan=lifespan
)

# No wildcard CORS access is enabled.
# Configure trusted origins if a separate frontend is deployed.


class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=32)
    password: str = Field(min_length=10, max_length=128)
    confirm_password: str = Field(min_length=10, max_length=128)


class LoginRequest(BaseModel):
    username: str
    password: str


@app.get("/", response_class=HTMLResponse)
def home():
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8">
      <meta name="viewport" content="width=device-width, initial-scale=1">
      <title>CJH FREE VPS</title>
      <style>
        body {
          margin: 0;
          min-height: 100vh;
          display: grid;
          place-items: center;
          font-family: Arial, sans-serif;
          color: #edf5ff;
          background: #07111f;
        }
        main {
          width: min(85%, 420px);
          padding: 28px;
          border: 1px solid #1f3c59;
          border-radius: 18px;
          background: #0d1b2d;
          text-align: center;
        }
        h1 { color: #38bdf8; }
        p { color: #a9bfd5; }
        a {
          display: inline-block;
          margin-top: 12px;
          padding: 12px 20px;
          color: #07111f;
          background: #38bdf8;
          border-radius: 9px;
          text-decoration: none;
          font-weight: bold;
        }
      </style>
    </head>
    <body>
      <main>
        <h1>CJH FREE VPS</h1>
        <p>Chachaji Hosting</p>
        <p>Backend starter is running.</p>
        <a href="/docs">API Documentation</a>
      </main>
    </body>
    </html>
    """


@app.get("/health")
def health():
    return {"status": "ok", "panel": "CJH FREE VPS"}


@app.post("/api/register")
def register(data: RegisterRequest):
    username = data.username.strip()

    if not username.replace("_", "").isalnum():
        raise HTTPException(
            status_code=400,
            detail="Username can contain letters, numbers and underscores."
        )

    if data.password != data.confirm_password:
        raise HTTPException(
            status_code=400,
            detail="Passwords do not match."
        )

    password_hash = pwd_context.hash(data.password)

    try:
        with connect_db() as db:
            cursor = db.execute(
                "INSERT INTO users (username, password_hash) VALUES (?, ?)",
                (username, password_hash)
            )
            user_id = cursor.lastrowid

        return {
            "message": "Account created.",
            "user_id": user_id
        }

    except sqlite3.IntegrityError:
        raise HTTPException(
            status_code=409,
            detail="Username already exists."
        )


@app.get("/api/vps")
def vps_info():
    return {
        "available_types": [
            {
                "id": "docker",
                "name": "Docker Environment"
            },
            {
                "id": "kvm",
                "name": "KVM Virtual Machine"
            },
            {
                "id": "sshx",
                "name": "SSHX Terminal"
            }
        ],
        "message": "Provisioning is not configured yet."
}
