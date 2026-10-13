# CJH FREE VPS

CJH FREE VPS is a VPS management panel project
by Chachaji Hosting.

## Features

- FastAPI backend
- SQLite database
- Account registration
- Password hashing
- VPS provider integration structure
- Configurable panel port: 6769

## Supported provider integrations

- Docker containers
- KVM virtual machines
- SSHX terminal environments

These integrations require separate implementation
and host compatibility checks.

## Requirements

- Compatible Linux server
- Python 3.10 or newer
- Python virtual environment support

## Installation

Configure the environment variables before running
the application.

Never publish production secrets in GitHub.

Install dependencies:

    python3 -m venv .venv
    .venv/bin/pip install -r requirements.txt

Run the development server:

    .venv/bin/uvicorn backend.app:app \
      --host 127.0.0.1 --port 6769

Visit:

    http://127.0.0.1:6769

Do not expose this starter application publicly
until authentication, session security, provisioning,
and HTTPS deployment have been implemented and tested.

## Security

Never expose host credentials or private keys.
Never assume a VPS exists until provisioning succeeds.
