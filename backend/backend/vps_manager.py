SUPPORTED_PROVIDERS = {"docker", "kvm", "sshx"}


def get_available_providers():
    """
    Lists supported provider types.
    This function does not claim they are installed or operational.
    """
    return [
        {
            "id": "docker",
            "name": "Docker Environment",
            "status": "not_configured"
        },
        {
            "id": "kvm",
            "name": "KVM Virtual Machine",
            "status": "not_configured"
        },
        {
            "id": "sshx",
            "name": "SSHX Terminal",
            "status": "not_configured"
        }
    ]


def create_vps(user_id: int, provider: str):
    """
    Safe placeholder until real provisioning adapters are configured.
    """
    if provider not in SUPPORTED_PROVIDERS:
        raise ValueError("Unsupported VPS provider.")

    raise NotImplementedError(
        "Real provisioning is not configured. "
        "No VPS has been created."
  )
