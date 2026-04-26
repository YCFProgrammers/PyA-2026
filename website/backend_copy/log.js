function handleCredentialResponse(response) {
    const id_token = response.credential;

    fetch('http://localhost:8000/auth/google', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ token: id_token })
    })
    .then(res => {
        if (!res.ok) {
            // Esto nos dirá si el backend respondió 404, 405 o 500
            console.error("Respuesta del servidor no OK:", res.status);
            throw new Error("Error en el servidor");
        }
        return res.json();
    })
    .then(data => {
        if (data.status === "success") {
            localStorage.setItem("session_token", data.access_token);
            localStorage.setItem("user_name", data.user.name);
            localStorage.setItem("user_email", data.user.email);

            console.log("Sesión guardada. Redirigiendo...");
            window.location.href = "dash.html"; 
        } else {
            alert("Error: " + data.message);
        }
    })
    .catch(err => {
        console.error("DETALLE DEL ERROR:", err);
        alert("No se pudo conectar con el servidor de autenticación.");
    });
}


function logout() {
 
    localStorage.removeItem("session_token");
    localStorage.removeItem("user_name");
    localStorage.removeItem("user_email");



    console.log("Sesión cerrada.");

    window.location.href = "log.html";
}