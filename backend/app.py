import os
import sqlite3
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from starlette.middleware.sessions import SessionMiddleware

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"

# Load environment variables before reading settings or importing backend modules.
load_dotenv(BASE_DIR / ".env")

SECRET_KEY = os.getenv("SECRET_KEY", "")
APP_PORT = int(os.getenv("APP_PORT", "6769"))
COOKIE_SECURE = os.getenv("COOKIE_SECURE", "true").lower() == "true"

if len(SECRET_KEY) < 32 or SECRET_KEY == "REPLACE_WITH_A_RANDOM_SECRET":
    raise RuntimeError(
        "Set a secure, random SECRET_KEY of at least 32 characters in .env."
    )

if not FRONTEND_DIR.is_dir():
    raise RuntimeError("Frontend directory not found.")

from .database import init_db, get_db
from .auth import register_user, authenticate_user

app = FastAPI(title="CJH FREE VPS")

app.add_middleware(
    SessionMiddleware,
    secret_key=SECRET_KEY,
    same_site="lax",
    https_only=COOKIE_SECURE,
    max_age=60 * 60 * 12,
)

app.mount(
    "/static",
    StaticFiles(directory=str(FRONTEND_DIR)),
    name="static",
)


class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=32)
    password: str = Field(min_length=10, max_length=128)
    confirm_password: str = Field(min_length=10, max_length=128)


class LoginRequest(BaseModel):
    username: str = Field(min_length=3, max_length=32)
    password: str = Field(min_length=1, max_length=128)


class CreateVPSRequest(BaseModel):
    provider: str


def current_user(request: Request):
    user = request.session.get("user")

    if not isinstance(user, dict):
        raise HTTPException(
            status_code=401,
            detail="Please log in first.",
        )

    if not isinstance(user.get("id"), int):
        raise HTTPException(
            status_code=401,
            detail="Invalid session. Please log in again.",
        )

    return user


@app.on_event("startup")
def startup():
    init_db()


@app.get("/")
def home():
    return FileResponse(FRONTEND_DIR / "index.html")


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "CJH FREE VPS",
        "port": APP_PORT,
    }


@app.post("/api/register")
def register(data: RegisterRequest):
    try:
        user = register_user(
            data.username,
            data.password,
            data.confirm_password,
        )

        return {
            "message": "Account created. Please log in.",
            "user": user,
        }

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

    except sqlite3.IntegrityError:
        raise HTTPException(
            status_code=409,
            detail="Username already exists.",
        )


@app.post("/api/login")
def login(data: LoginRequest, request: Request):
    try:
        user = authenticate_user(
            data.username,
            data.password,
        )
    except ValueError:
        user = None

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password.",
        )

    request.session.clear()
    request.session["user"] = user

    return {
        "message": "Login successful.",
        "user": user,
    }


@app.post("/api/logout")
def logout(request: Request):
    request.session.clear()
    return {"message": "Logged out."}


@app.get("/api/vps")
def list_vps(request: Request):
    user = current_user(request)

    with get_db() as db:
        rows = db.execute(
            """
            SELECT id, provider, status, created_at
            FROM vps_instances
            WHERE user_id = ?
            ORDER BY id DESC
            """,
            (user["id"],),
        ).fetchall()

    return {
        "instances": [
            {
                "id": row["id"],
                "provider": row["provider"],
                "status": row["status"],
                "created_at": row["created_at"],
            }
            for row in rows
        ]
    }


@app.post("/api/vps/create")
def create_vps(data: CreateVPSRequest, request: Request):
    user = current_user(request)

    provider = data.provider.strip().lower()

    if provider not in {"docker", "kvm", "sshx"}:
        raise HTTPException(
            status_code=400,
            detail="Unsupported VPS provider.",
        )

    # Fail safely: real VPS provisioning is not implemented yet.
    # Do not insert a fake VPS record or claim that one was created.
    with get_db() as db:
        existing = db.execute(
            """
            SELECT id
            FROM vps_instances
            WHERE user_id = ?
            LIMIT 1
            """,
            (user["id"],),
        ).fetchone()

    if existing:
        raise HTTPException(
            status_code=409,
            detail="Your account already has a VPS.",
        )

    raise HTTPException(
        status_code=501,
        detail=(
            f"{provider.upper()} provisioning is not configured yet. "
            "No VPS has been created."
        ),
)
