function handleCredentialResponse(response) {
    const id_token = response.credential;

    fetch('http://127.0.0.1:5000/auth/google', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ token: id_token })
    })
    .then(res => {
        if (!res.ok) throw new Error("Error en backend");
        return res.json();
    })
    .then(data => {
        if (data.status === "success") {

            localStorage.setItem("session_token", data.access_token);
            localStorage.setItem("user_name", data.user.name);
            localStorage.setItem("user_email", data.user.email);
            localStorage.setItem("user_picture", data.user.picture);

            window.location.href = "dash.html";

        } else {
            alert("Error: " + data.message);
        }
    })
    .catch(err => {
        console.error(err);
        alert("Error conectando con el servidor");
    });
}


// 🔒 logout
function logout() {
    localStorage.clear();
    window.location.href = "log.html";
}