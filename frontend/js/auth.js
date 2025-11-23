async function login() {
    const username = document.getElementById("username").value;
    const password = document.getElementById("password").value;

    try {
        const data = await api("/auth/login", "POST", { username, password });
        localStorage.setItem("token", data.access_token);
        window.location.href = "dashboard.html";
    } catch (err) {
        document.getElementById("status").innerText = "Invalid credentials";
    }
}

function logout() {
    localStorage.removeItem("token");
    window.location.href = "login.html";
}
