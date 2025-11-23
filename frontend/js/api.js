const BASE_URL = "http://127.0.0.1:8000";

async function api(path, method = "GET", body = null, isForm = false) {
    const token = localStorage.getItem("token");

    const options = {
        method,
        headers: {
            ...(isForm ? {} : { "Content-Type": "application/json" }),
            ...(token ? { Authorization: `Bearer ${token}` } : {})
        },
        body: isForm ? body : (body ? JSON.stringify(body) : null)
    };

    const res = await fetch(`${BASE_URL}${path}`, options);
    if (!res.ok) throw new Error(await res.text());
    return res.json();
}
