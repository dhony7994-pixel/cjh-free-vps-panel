import shutil

SUPPORTED_PROVIDERS = {
    "docker",
    "kvm",
    "sshx",
}


def get_available_providers():
    """Return provider information and host availability."""

    return [
        {
            "id": "docker",
            "name": "Docker VPS",
            "description": "Isolated container environment; not a full VM.",
            "available": shutil.which("docker") is not None,
            "status": (
                "detected"
                if shutil.which("docker")
                else "not_installed"
            ),
        },
        {
            "id": "kvm",
            "name": "KVM Virtual Machine",
            "description": "Full virtual machine requiring host virtualization.",
            "available": (
                shutil.which("virsh") is not None
                and shutil.which("qemu-system-x86_64") is not None
            ),
            "status": (
                "detected"
                if (
                    shutil.which("virsh") is not None
                    and shutil.which("qemu-system-x86_64") is not None
                )
                else "not_configured"
            ),
        },
        {
            "id": "sshx",
            "name": "SSHX Environment",
            "description": "Terminal environment, not a full VPS.",
            "available": shutil.which("sshx") is not None,
            "status": (
                "detected"
                if shutil.which("sshx")
                else "not_installed"
            ),
        },
    ]


def create_vps(user_id: int, provider: str):
    """
    Provisioning remains disabled until a secure provider adapter
    with resource limits and lifecycle management is configured.
    """

    if provider not in SUPPORTED_PROVIDERS:
        raise ValueError("Unsupported provider.")

    if not isinstance(user_id, int) or user_id <= 0:
        raise ValueError("Invalid user ID.")

    raise NotImplementedError(
        f"{provider} provisioning is not configured. "
        "No VPS has been created."
    )
