import shutil
import re


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
    if not isinstance(host, str) or not host:
        raise ValueError("Invalid host.")

    if any(char.isspace() for char in host):
        raise ValueError("Invalid host.")

    if not isinstance(port, int) or isinstance(port, bool):
        raise ValueError("Invalid SSH port.")

    if not 1 <= port <= 65535:
        raise ValueError("Invalid SSH port.")

    if not isinstance(username, str):
        raise ValueError("Invalid SSH username.")

    if not re.fullmatch(r"[A-Za-z0-9_][A-Za-z0-9_.-]{0,31}", username):
        raise ValueError("Invalid SSH username.")

    return {
        "host": host,
        "port": port,
        "username": username,
        "command": f"ssh -p {port} {username}@{host}",
        "ssh_client_available": check_ssh_available(),
        "sshx_available": check_sshx_available(),
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
        ),
    }
