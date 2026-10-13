import os
import shutil
import subprocess


def check_ssh_available():
    """Check whether the SSH client is installed."""
    return shutil.which("ssh") is not None


def check_sshx_available():
    """Check whether the SSHX command is installed."""
    return shutil.which("sshx") is not None


def get_connection_info(host: str, port: int, username: str):
    """
    Return SSH connection details.
    This does not create a VPS or start an SSH server.
    """
    if not host or any(char.isspace() for char in host):
        raise ValueError("Invalid host.")

    if not 1 <= port <= 65535:
        raise ValueError("Invalid SSH port.")

    if not username or not username.replace("_", "").isalnum():
        raise ValueError("Invalid SSH username.")

    return {
        "host": host,
        "port": port,
        "username": username,
        "command": f"ssh -p {port} {username}@{host}",
        "ssh_client_available": check_ssh_available(),
        "sshx_available": check_sshx_available()
    }


def get_sshx_status():
    """Report SSHX availability without launching a session."""
    executable = shutil.which("sshx")

    return {
        "installed": executable is not None,
        "message": (
            "SSHX executable detected."
            if executable
            else "SSHX is not installed."
        )
  }
