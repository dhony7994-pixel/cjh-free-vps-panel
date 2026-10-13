const API = "/api";

let isRegisterMode = false;
let currentUser = null;

const $ = (id) => document.getElementById(id);

// Show success or error messages
function showMessage(id, message, error = false) {
    const element = $(id);

    if (!element) return;

    element.textContent = message;
    element.style.color = error ? "#fca5a5" : "#6ee7b7";
}

// Set login or register mode
function setAuthMode(registerMode) {
    isRegisterMode = registerMode;

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

    showMessage("auth-message", "");
}

// Toggle login/register
function toggleAuth() {
    setAuthMode(!isRegisterMode);
}

// API request helper
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
        throw new Error(
            data.detail || "Request failed. Please try again."
        );
    }

    return data;
}

// Login and registration
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

    if (!/^[A-Za-z0-9_]{3,32}$/.test(username)) {
        showMessage(
            "auth-message",
            "Username must be 3–32 characters using letters, numbers or underscores.",
            true
        );
        return;
    }

    if (isRegisterMode) {
        const confirmPassword = $("confirm-password").value;

        if (password.length < 10 || password.length > 128) {
            showMessage(
                "auth-message",
                "Password must contain 10–128 characters.",
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
    showMessage("auth-message", "");

    try {
        // Registration
        if (isRegisterMode) {
            await request("/register", {
                method: "POST",
                body: JSON.stringify({
                    username: username,
                    password: password,
                    confirm_password: $("confirm-password").value
                })
            });

            // Switch back to login mode correctly
            setAuthMode(false);

            $("password").value = "";
            $("confirm-password").value = "";

            showMessage(
                "auth-message",
                "Account created successfully. Please log in."
            );

            return;
        }

        // Login
        const result = await request("/login", {
            method: "POST",
            body: JSON.stringify({
                username: username,
                password: password
            })
        });

        currentUser = result.user;

        if (!currentUser) {
            throw new Error("Login response was invalid.");
        }

        $("auth-section").hidden = true;
        $("dashboard").hidden = false;

        $("welcome-user").textContent =
            "Welcome, " + currentUser.username;

        $("password").value = "";
        $("confirm-password").value = "";

        await loadVPS();

    } catch (error) {
        showMessage(
            "auth-message",
            error.message || "Something went wrong.",
            true
        );
    } finally {
        button.disabled = false;
    }
}

// Load the logged-in user's VPS instances
async function loadVPS() {
    const list = $("vps-list");

    list.replaceChildren();

    try {
        const result = await request("/vps");
        const instances = result.instances || [];

        // Keep the VPS creation form visible.
        // Only hide the empty-state message when instances exist.
        const emptyMessage = $("empty-message");

        if (emptyMessage) {
            emptyMessage.hidden = instances.length > 0;
        }

        // Disable creation if the account already has a VPS.
        const createButton = $("create-vps-button");

        if (createButton) {
            createButton.disabled = instances.length > 0;
            createButton.textContent = instances.length > 0
                ? "VPS Limit Reached"
                : "Create VPS";
        }

        for (const instance of instances) {
            const card = document.createElement("div");
            card.className = "card vps-card";

            const title = document.createElement("h2");
            title.textContent = "VPS #" + instance.id;

            const provider = document.createElement("p");
            provider.textContent = "Type: " + instance.provider;

            const status = document.createElement("p");
            status.textContent = "Status: " + instance.status;

            card.append(title, provider, status);
            list.appendChild(card);
        }

        showMessage("vps-message", "");

    } catch (error) {
        showMessage(
            "vps-message",
            error.message || "Could not load VPS instances.",
            true
        );
    }
}

// Request VPS creation
async function createVPS() {
    const button = $("create-vps-button");

    if (button && button.disabled) return;

    showMessage("vps-message", "Checking VPS provisioning service...");

    if (button) button.disabled = true;

    try {
        const provider = $("provider").value;

        const result = await request("/vps/create", {
            method: "POST",
            body: JSON.stringify({ provider: provider })
        });

        showMessage(
            "vps-message",
            result.message || "VPS creation request submitted."
        );

        await loadVPS();

    } catch (error) {
        showMessage(
            "vps-message",
            error.message || "VPS creation failed.",
            true
        );
    } finally {
        if (button) button.disabled = false;
    }
}

// Logout
async function logout() {
    const button = $("logout-button");

    if (button) button.disabled = true;

    try {
        await request("/logout", {
            method: "POST",
            body: JSON.stringify({})
        });
    } catch (error) {
        console.error("Logout request failed:", error);
    } finally {
        currentUser = null;

        $("dashboard").hidden = true;
        $("auth-section").hidden = false;

        $("username").value = "";
        $("password").value = "";
        $("confirm-password").value = "";

        setAuthMode(false);

        if (button) button.disabled = false;
    }
}

// Show login page on initial load
function showLogin() {
    $("dashboard").hidden = true;
    $("auth-section").hidden = false;
}

// Connect the page buttons
document.addEventListener("DOMContentLoaded", () => {
    // Support both form submission and the existing HTML button.
    const authForm = $("auth-form");

    if (authForm) {
        authForm.addEventListener("submit", (event) => {
            event.preventDefault();
            authenticate();
        });
    }

    // The HTML currently uses inline onclick handlers.
    // Add listeners only if those handlers are not present.
    const switchButton = $("switch-button");

    if (switchButton && !switchButton.hasAttribute("onclick")) {
        switchButton.addEventListener("click", toggleAuth);
    }

    const createButton = $("create-vps-button");

    if (createButton && !createButton.hasAttribute("onclick")) {
        createButton.addEventListener("click", createVPS);
    }

    const logoutButton = $("logout-button");

    if (logoutButton && !logoutButton.hasAttribute("onclick")) {
        logoutButton.addEventListener("click", logout);
    }

    showLogin();
});
