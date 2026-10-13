import shutil

SUPPORTED_PROVIDERS = {
    "docker",
    "kvm",
    "sshx",
}


def _check_command(command: str) -> bool:
    """Check whether a required executable exists."""
    return shutil.which(command) is not None


def get_available_providers():
    """Detect installed provider tools on the host."""

    docker_available = _check_command("docker")

    kvm_available = (
        _check_command("virsh")
        and _check_command("qemu-system-x86_64")
    )

    sshx_available = _check_command("sshx")

    return [
        {
            "id": "docker",
            "name": "Docker Environment",
            "description": "Container environment; not a full virtual machine.",
            "available": docker_available,
            "status": (
                "detected" if docker_available else "not_installed"
            ),
        },
        {
            "id": "kvm",
            "name": "KVM Virtual Machine",
            "description": (
                "Virtual machine requiring host virtualization "
                "and additional configuration."
            ),
            "available": kvm_available,
            "status": (
                "detected" if kvm_available else "not_configured"
            ),
        },
        {
            "id": "sshx",
            "name": "SSHX Terminal",
            "description": "Terminal session; not a standalone VPS.",
            "available": sshx_available,
            "status": (
                "detected" if sshx_available else "not_installed"
            ),
        },
    ]


def get_provider(provider: str):
    """Return information about a supported provider."""

    if not isinstance(provider, str):
        raise ValueError("Invalid provider.")

    provider = provider.strip().lower()

    if provider not in SUPPORTED_PROVIDERS:
        raise ValueError("Unsupported provider.")

    for item in get_available_providers():
        if item["id"] == provider:
            return item

    raise ValueError("Provider information unavailable.")


def create_vps(user_id: int, provider: str):
    """
    Provisioning is disabled until secure infrastructure
    configuration and instance isolation are implemented.
    """

    if not isinstance(user_id, int) or isinstance(user_id, bool) or user_id <= 0:
        raise ValueError("Invalid user ID.")

    info = get_provider(provider)

    if not info["available"]:
        raise RuntimeError(
            f"{info['name']} is not installed or configured."
        )

    raise NotImplementedError(
        f"{info['name']} provisioning is not configured. "
        "No VPS has been created."
    )
