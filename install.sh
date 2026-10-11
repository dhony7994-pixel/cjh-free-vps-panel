#!/bin/bash

# Check if user is root
if [ "$EUID" -ne 0 ]; then
  echo "Please run as root (use sudo)."
  exit 1
fi

INSTALL_DIR="/opt/my-vps-panel"

show_menu() {
    clear
    echo "========================================"
    echo "         VPS CONTROL PANEL MENU         "
    echo "========================================"
    echo "1. Install Panel"
    echo "2. Uninstall Panel"
    echo "3. Update Panel"
    echo "4. Exit"
    echo "========================================"
    read -p "Choose an option [1-4]: " choice
}

install_panel() {
    echo "[-] Installing dependencies..."
    apt update && apt install -y python3 python3-pip python3-venv git curl

    echo "[-] Setting up directory at $INSTALL_DIR..."
    mkdir -p $INSTALL_DIR
    cd $INSTALL_DIR

    # Create virtual environment
    python3 -m venv venv
    source venv/bin/activate

    # Create app files (or pull from GitHub repository if published)
    cat << 'EOF' > app.py
from flask import Flask, render_template_string, request, redirect, url_for, session
import time

app = Flask(__name__)
app.secret_key = 'super_secret_key_change_this'

users = {}  # Simple in-memory user store for demonstration
vms = []

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>VPS Panel</title>
    <style>
        body { font-family: Arial, sans-serif; background: #f4f4f9; margin: 0; padding: 50px; }
        .container { max-width: 500px; background: white; padding: 30px; border-radius: 8px; box-shadow: 0px 0px 10px rgba(0,0,0,0.1); margin: auto; }
        input, button { width: 100%; padding: 10px; margin: 10px 0; border: 1px solid #ccc; border-radius: 4px; box-sizing: border-box; }
        button { background: #007BFF; color: white; border: none; font-weight: bold; cursor: pointer; }
        button:hover { background: #0056b3; }
        .error { color: red; font-size: 14px; }
    </style>
</head>
<body>
    <div class="container">
        {% if not session.get('logged_in') %}
            <h2>{{ title }}</h2>
            {% if error %}<div class="error">{{ error }}</div>{% endif %}
            <form method="POST">
                <input type="text" name="username" placeholder="Username" required><br>
                <input type="password" name="password" placeholder="Password" required><br>
                <button type="submit">{{ btn }}</button>
            </form>
            <p><a href="{{ switch_url }}">{{ switch_text }}</a></p>
        {% else %}
            <h2>Dashboard</h2>
            <p>Welcome, <b>{{ session.get('username') }}</b>!</p>
            <h3>Your 4GB VMs</h3>
            <ul>
                {% for vm in vms %}
                    <li>{{ vm.name }} - <a href="{{ vm.ssh_link }}" target="_blank">Connect via SSH</a></li>
                {% endfor %}
            </ul>
            <form action="/create_vm" method="POST">
                <button type="submit">Create 4GB VM (Takes ~1 min)</button>
            </form>
            <br>
            <a href="/logout"><button style="background: #dc3545;">Logout</button></a>
        {% endif %}
    </div>
</body>
</html>
"""

@app.route('/', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username in users and users[username] == password:
            session['logged_in'] = True
            session['username'] = username
            return redirect(url_for('dashboard'))
        error = 'Invalid Credentials'
    return render_template_string(HTML_TEMPLATE, title="Login", btn="Login", switch_url="/register", switch_text="Don't have an account? Register", error=error)

@app.route('/register', methods=['GET', 'POST'])
def register():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username in users:
            error = 'Username already exists'
        else:
            users[username] = password
            return redirect(url_for('login'))
    return render_template_string(HTML_TEMPLATE, title="Register", btn="Register", switch_url="/", switch_text="Already have an account? Login", error=error)

@app.route('/dashboard')
def dashboard():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    user_vms = [v for v in vms if v['owner'] == session.get('username')]
    return render_template_string(HTML_TEMPLATE, vms=user_vms)

@app.route('/create_vm', methods=['POST'])
def create_vm():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    
    # Simulate VM creation time delay (e.g., 60 seconds or shorter for testing)
    time.sleep(2) 
    
    vm_name = f"VM-4GB-{len(vms)+1}"
    ssh_link = f"ssh://root@vps-node-{len(vms)+1}.local:22"
    
    vms.append({'name': vm_name, 'ssh_link': ssh_link, 'owner': session.get('username')})
    return redirect(url_for('dashboard'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
EOF

    cat << 'EOF' > requirements.txt
flask
EOF

    pip install -r requirements.txt

    # Setup systemd service for auto-start and background execution
    cat << 'EOF' > /etc/systemd/system/vps-panel.service
[Unit]
Description=VPS Control Panel Flask App
After=network.target

[Service]
User=root
WorkingDirectory=/opt/my-vps-panel
ExecStart=/opt/my-vps-panel/venv/bin/python app.py
Restart=always

[Install]
WantedBy=multi-user.target
EOF

    systemctl daemon-reload
    systemctl enable vps-panel
    systemctl start vps-panel

    echo "[-] Panel installed successfully and running on port 5000!"
    read -p "Press Enter to return to menu..."
}

uninstall_panel() {
    echo "[-] Stopping and removing panel..."
    systemctl stop vps-panel
    systemctl disable vps-panel
    rm -f /etc/systemd/system/vps-panel.service
    systemctl daemon-reload
    rm -rf $INSTALL_DIR
    echo "[-] Panel uninstalled successfully."
    read -p "Press Enter to return to menu..."
}

update_panel() {
    echo "[-] Updating panel..."
    systemctl stop vps-panel
    cd $INSTALL_DIR
    # If using git repository: git pull
    systemctl start vps-panel
    echo "[-] Panel updated successfully."
    read -p "Press Enter to return to menu..."
}

while true; do
    show_menu
    case $choice in
        1) install_panel ;;
        2) uninstall_panel ;;
        3) update_panel ;;
        4) echo "Exiting..."; exit 0 ;;
        *) echo "Invalid option, please choose 1-4."; sleep 2 ;;
    esac
done
