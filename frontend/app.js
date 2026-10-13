const API = "/api";

let isRegisterMode = false;
let currentUser = null;

const $ = (id) => document.getElementById(id);

function showMessage(id, message, error = false) {
    const element = $(id);
    element.textContent = message;
    element.style.color = error ? "#fca5a5" : "#6ee7b7";
}

function toggleAuth() {
    isRegisterMode = !isRegisterMode;

    $("auth-title").textContent = isRegisterMode
        ? "Create Account"
        : "Welcome Back";

    $("auth-button").textContent = isRegisterMode
        ? "Register"
        : "Login";

    $("switch-text").textContent = isRegisterMode
        ? "Already have an account?"
        : "Don't have an account?";

    $("switch-button").textContent = isRegisterMode
        ? "Login"
        : "Register";

    $("register-fields").hidden = !isRegisterMode;

    $("password").autocomplete = isRegisterMode
        ? "new-password"
        : "current-password";

    $("auth-message").textContent = "";
}

async function request(path, options = {}) {
    const response = await fetch(API + path, {
        ...options,
        credentials: "same-origin",
        headers: {
            "Content-Type": "application/json",
            ...options.headers
        }
    });

    const data = await response.json().catch(() => ({}));

    if (!response.ok) {
        throw new Error(data.detail || "Request failed.");
    }

    return data;
}

async function authenticate() {
    const button = $("auth-button");
    const username = $("username").value.trim();
    const password = $("password").value;

    if (!username || !password) {
        showMessage(
            "auth-message",
            "Username and password are required.",
            true
        );
        return;
    }

    if (isRegisterMode) {
        const confirmPassword = $("confirm-password").value;

        if (password.length < 10) {
            showMessage(
                "auth-message",
                "Password must contain at least 10 characters.",
                true
            );
            return;
        }

        if (password !== confirmPassword) {
            showMessage(
                "auth-message",
                "Passwords do not match.",
                true
            );
            return;
        }
    }

    button.disabled = true;

    try {
        if (isRegisterMode) {
            await request("/register", {
                method: "POST",
                body: JSON.stringify({
                    username,
                    password,
                    confirm_password: $("confirm-password").value
                })
            });

            isRegisterMode = false;
            toggleAuth();

            $("password").value = "";

            showMessage(
                "auth-message",
                "Account created. Please log in."
            );

            return;
        }

        const result = await request("/login", {
            method: "POST",
            body: JSON.stringify({ username, password })
        });

        currentUser = result.user;

        $("auth-section").hidden = true;
        $("dashboard").hidden = false;
        $("welcome-user").textContent =
            "Welcome, " + currentUser.username;

        await loadVPS();

    } catch (error) {
        showMessage("auth-message", error.message, true);
    } finally {
        button.disabled = false;
    }
}

async function loadVPS() {
    try {
        const result = await request("/vps");

        const list = $("vps-list");
        list.replaceChildren();

        const instances = result.instances || [];

        $("empty-state").hidden = instances.length > 0;

        for (const instance of instances) {
            const card = document.createElement("div");
            card.className = "card";

            const title = document.createElement("h2");
            title.textContent = "VPS #" + instance.id;

            const provider = document.createElement("p");
            provider.textContent =
                "Type: " + instance.provider;

            const status = document.createElement("p");
            status.textContent =
                "Status: " + instance.status;

            card.append(title, provider, status);
            list.appendChild(card);
        }
    } catch (error) {
        showMessage("vps-message", error.message, true);
    }
}

async function createVPS() {
    showMessage(
        "vps-message",
        "Checking VPS provisioning service..."
    );

    /*
     * The backend must implement authenticated VPS creation.
     * This request will fail safely until that API exists.
     */

    try {
        const result = await request("/vps/create", {
            method: "POST",
            body: JSON.stringify({
                provider: $("provider").value
            })
        });

        showMessage(
            "vps-message",
            result.message || "VPS creation request submitted."
        );

        await loadVPS();

    } catch (error) {
        showMessage("vps-message", error.message, true);
    }
}

async function logout() {
    try {
        await request("/logout", {
            method: "POST",
            body: JSON.stringify({})
        });
    } catch (error) {
        console.error("Logout request failed:", error);
    }

    currentUser = null;

    $("dashboard").hidden = true;
    $("auth-section").hidden = false;
    $("password").value = "";
    $("confirm-password").value = "";
      }
function showLogin() {
    $("dashboard").hidden = true;
    $("auth-section").hidden = false;
}

document.addEventListener("DOMContentLoaded", () => {
    $("auth-form").addEventListener("submit", (event) => {
        event.preventDefault();
        authenticate();
    });

    $("switch-button").addEventListener("click", toggleAuth);

    $("create-vps-button").addEventListener("click", createVPS);

    $("logout-button").addEventListener("click", logout);

    showLogin();
});
