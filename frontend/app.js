const API = "/api";

let isRegisterMode = false;
let currentUser = null;
let isAuthenticating = false;
let isCreatingVPS = false;

const $ = (id) => document.getElementById(id);

function showMessage(id, message, error = false) {
    const element = $(id);
    if (!element) return;

    element.textContent = message;
    element.style.color = error ? "#fca5a5" : "#6ee7b7";
}

function setAuthMode(registerMode) {
    isRegisterMode = registerMode;

    const title = $("auth-title");
    const authButton = $("auth-button");
    const switchText = $("switch-text");
    const switchButton = $("switch-button");
    const registerFields = $("register-fields");
    const password = $("password");

    if (title) {
        title.textContent = registerMode ? "Create Account" : "Welcome Back";
    }

    if (authButton) {
        authButton.textContent = registerMode ? "Register" : "Login";
    }

    if (switchText) {
        switchText.textContent = registerMode
            ? "Already have an account?"
            : "Don't have an account?";
    }

    if (switchButton) {
        switchButton.textContent = registerMode ? "Login" : "Register";
    }

    if (registerFields) {
        registerFields.hidden = !registerMode;
    }

    if (password) {
        password.autocomplete = registerMode
            ? "new-password"
            : "current-password";
    }

    showMessage("auth-message", "");
}

function toggleAuth() {
    setAuthMode(!isRegisterMode);
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
        throw new Error(
            typeof data.detail === "string"
                ? data.detail
                : "Request failed. Please try again."
        );
    }

    return data;
}

function setDashboardVisible(visible) {
    const authSection = $("auth-section");
    const dashboard = $("dashboard");

    if (authSection) authSection.hidden = visible;
    if (dashboard) dashboard.hidden = !visible;
}

async function authenticate() {
    if (isAuthenticating) return;

    const button = $("auth-button");
    const usernameField = $("username");
    const passwordField = $("password");

    if (!usernameField || !passwordField) {
        showMessage("auth-message", "Login form is incomplete.", true);
        return;
    }

    const username = usernameField.value.trim();
    const password = passwordField.value;

    if (!/^[A-Za-z0-9_]{3,32}$/.test(username)) {
        showMessage(
            "auth-message",
            "Username must be 3–32 characters using letters, numbers or underscores.",
            true
        );
        return;
    }

    if (!password) {
        showMessage("auth-message", "Password is required.", true);
        return;
    }

    const confirmField = $("confirm-password");

    if (isRegisterMode) {
        if (password.length < 10 || password.length > 128) {
            showMessage(
                "auth-message",
                "Password must contain 10–128 characters.",
                true
            );
            return;
        }

        if (!confirmField) {
            showMessage(
                "auth-message",
                "Registration form is incomplete.",
                true
            );
            return;
        }

        if (password !== confirmField.value) {
            showMessage("auth-message", "Passwords do not match.", true);
            return;
        }
    }

    isAuthenticating = true;
    if (button) button.disabled = true;

    try {
        if (isRegisterMode) {
            await request("/register", {
                method: "POST",
                body: JSON.stringify({
                    username,
                    password,
                    confirm_password: confirmField.value
                })
            });

            setAuthMode(false);
            passwordField.value = "";
            if (confirmField) confirmField.value = "";

            showMessage(
                "auth-message",
                "Account created successfully. Please log in."
            );
            return;
        }

        const result = await request("/login", {
            method: "POST",
            body: JSON.stringify({ username, password })
        });

        if (
            !result.user ||
            typeof result.user.id !== "number" ||
            typeof result.user.username !== "string"
        ) {
            throw new Error("Invalid login response.");
        }

        currentUser = result.user;
        setDashboardVisible(true);

        const welcome = $("welcome-user");
        if (welcome) {
            welcome.textContent = "Welcome, " + currentUser.username;
        }

        passwordField.value = "";
        if (confirmField) confirmField.value = "";

        await loadVPS();

    } catch (error) {
        showMessage(
            "auth-message",
            error.message || "Something went wrong.",
            true
        );
    } finally {
        isAuthenticating = false;
        if (button) button.disabled = false;
    }
}

async function loadVPS() {
    const list = $("vps-list");
    if (!list) {
        showMessage("vps-message", "VPS list element is missing.", true);
        return;
    }

    list.replaceChildren();

    try {
        const result = await request("/vps");
        const instances = Array.isArray(result.instances)
            ? result.instances
            : [];

        const emptyMessage = $("empty-message");
        if (emptyMessage) {
            emptyMessage.hidden = instances.length > 0;
        }

        const createButton = $("create-vps-button");
        if (createButton) {
            createButton.disabled = instances.length > 0 || isCreatingVPS;
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

async function createVPS() {
    if (isCreatingVPS) return;

    const providerField = $("provider");
    const button = $("create-vps-button");

    if (!providerField) {
        showMessage("vps-message", "Select a provider first.", true);
        return;
    }

    isCreatingVPS = true;
    if (button) button.disabled = true;

    showMessage("vps-message", "Sending request...");

    try {
        const result = await request("/vps/create", {
            method: "POST",
            body: JSON.stringify({
                provider: providerField.value
            })
        });

        showMessage(
            "vps-message",
            result.message || "Request completed."
        );

        await loadVPS();

    } catch (error) {
        showMessage(
            "vps-message",
            error.message || "VPS creation failed.",
            true
        );
    } finally {
        isCreatingVPS = false;
        if (button) button.disabled = false;
        await loadVPS();
    }
}

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
        setDashboardVisible(false);

        if ($("username")) $("username").value = "";
        if ($("password")) $("password").value = "";
        if ($("confirm-password")) $("confirm-password").value = "";

        setAuthMode(false);
        if (button) button.disabled = false;
    }
}

async function restoreSession() {
    try {
        const result = await request("/vps");

        // The VPS endpoint requires authentication.
        // A successful response confirms the session is active.
        currentUser = { username: "User" };

        setDashboardVisible(true);

        // The API currently does not expose a separate session endpoint.
        // Avoid inventing a username; show a generic welcome message.
        const welcome = $("welcome-user");
        if (welcome) welcome.textContent = "Welcome back";

        const list = $("vps-list");
        if (list) {
            const instances = Array.isArray(result.instances)
                ? result.instances
                : [];

            list.replaceChildren();

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

            const emptyMessage = $("empty-message");
            if (emptyMessage) {
                emptyMessage.hidden = instances.length > 0;
            }

            const createButton = $("create-vps-button");
            if (createButton) {
                createButton.disabled = instances.length > 0;
                createButton.textContent = instances.length > 0
                    ? "VPS Limit Reached"
                    : "Create VPS";
            }
        }
    } catch {
        currentUser = null;
        setDashboardVisible(false);
    }
}

document.addEventListener("DOMContentLoaded", () => {
    const authForm = $("auth-form");

    if (authForm) {
        authForm.addEventListener("submit", (event) => {
            event.preventDefault();
            authenticate();
        });
    }

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

    setAuthMode(false);
    restoreSession();
});
