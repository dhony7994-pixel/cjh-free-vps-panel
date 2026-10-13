#!/usr/bin/env bash
set -Eeuo pipefail

APP_NAME="CJH FREE VPS"
APP_DIR="/opt/cjh-free-vps"
APP_PORT="6769"
SERVICE_NAME="cjh-free-vps"

if [[ $EUID -ne 0 ]]; then
    echo "Please run as root: sudo bash install.sh"
    exit 1
fi

pause() {
    read -r -p "Press Enter to continue..."
}

install_dependencies() {
    if command -v apt-get >/dev/null 2>&1; then
        apt-get update
        apt-get install -y python3 python3-venv python3-pip \
            git curl ca-certificates
    elif command -v dnf >/dev/null 2>&1; then
        dnf install -y python3 python3-pip git curl
    else
        echo "Unsupported OS. Use a compatible Ubuntu/Debian or Fedora server."
        return 1
    fi
}

install_panel() {
    if [[ -f "$APP_DIR/backend/app.py" ]]; then
        echo "Existing panel detected."
        read -r -p "Preserve its configuration and continue? [y/N]: " confirm
        [[ "$confirm" =~ ^[Yy]$ ]] || return
    else
        echo "Panel application files are missing."
        echo "Upload the project files to $APP_DIR first."
        echo "This installer will not download unverified code."
        return 1
    fi

    install_dependencies

    python3 -m venv "$APP_DIR/.venv"
    "$APP_DIR/.venv/bin/pip" install --upgrade pip
    "$APP_DIR/.venv/bin/pip" install -r "$APP_DIR/requirements.txt"

    if [[ ! -f "$APP_DIR/.env" && -f "$APP_DIR/.env.example" ]]; then
        cp "$APP_DIR/.env.example" "$APP_DIR/.env"
        chmod 600 "$APP_DIR/.env"
        echo "Review $APP_DIR/.env before starting the panel."
    fi

    echo "Do not start the service until production secrets and"
    echo "the application's admin/bootstrap configuration are set."
    echo "The backend must bind to 127.0.0.1 behind an HTTPS proxy."
    echo "Configure a reverse proxy for public access on port 6769."
}

uninstall_panel() {
    echo "This removes the panel service and application files."
    echo "It does not automatically delete VPS environments or databases."
    read -r -p "Type UNINSTALL to continue: " confirm
    [[ "$confirm" == "UNINSTALL" ]] || return

    systemctl disable --now "$SERVICE_NAME" 2>/dev/null || true
    rm -f "/etc/systemd/system/${SERVICE_NAME}.service"
    systemctl daemon-reload

    if [[ -d "$APP_DIR" ]]; then
        read -r -p "Remove application files at $APP_DIR? [y/N]: " remove_files
        if [[ "$remove_files" =~ ^[Yy]$ ]]; then
            rm -rf -- "$APP_DIR"
        fi
    fi

    echo "Panel service removed. Review remaining data manually."
}

update_panel() {
    if [[ ! -d "$APP_DIR/.git" ]]; then
        echo "No Git repository found at $APP_DIR."
        echo "Set up a verified GitHub checkout before updating."
        return 1
    fi

    echo "Updating requires a verified repository and a tested backup."
    read -r -p "Continue with Git fast-forward update? [y/N]: " confirm
    [[ "$confirm" =~ ^[Yy]$ ]] || return

    cd "$APP_DIR"
    git diff --quiet || {
        echo "Working tree has changes. Commit or back them up first."
        return 1
    }

    git pull --ff-only
    "$APP_DIR/.venv/bin/pip" install -r "$APP_DIR/requirements.txt"

    echo "Update downloaded. Run database migrations and tests"
    echo "before restarting the production service."
}

while true; do
    clear || true

    echo "╔══════════════════════════════════════╗"
    echo "║          CJH FREE VPS PANEL          ║"
    echo "║          Chachaji Hosting            ║"
    echo "╠══════════════════════════════════════╣"
    echo "║  1. Install Free VPS Panel           ║"
    echo "║  2. Uninstall Panel                  ║"
    echo "║  3. Update Panel                     ║"
    echo "║  4. Exit                             ║"
    echo "╚══════════════════════════════════════╝"

    read -r -p "Select option [1-4]: " choice

    case "$choice" in
        1) install_panel; pause ;;
        2) uninstall_panel; pause ;;
        3) update_panel; pause ;;
        4) echo "Goodbye!"; exit 0 ;;
        *) echo "Invalid option."; pause ;;
    esac
done
