/**
 * Lógica del Dashboard - PyA Programadores
 */

// 1. Configuración Inicial y Saludo
document.addEventListener("DOMContentLoaded", () => {
    const userName = localStorage.getItem("user_name") || "Programador";
    const userGreeting = document.getElementById("user-greeting");
    
    if (userGreeting) {
        userGreeting.innerText = `Hola, ${userName}. Contenido protegido para miembros.`;
    }

    // Cargar la sección de inicio al entrar
    showSection('home');
});

// 2. Navegación entre secciones
function showSection(id) {
    const articles = document.querySelectorAll('article');
    
    articles.forEach(art => {
        art.style.display = 'none';
    });

    const target = document.getElementById(id);
    if (target) {
        target.style.display = 'block';
        
        // Carga automática si entramos al tablón
        if (id === 'tablon') {
            loadProjects();
        }
    }
}

// 3. Gestión de Sesión
function logout() {
    localStorage.clear(); 
    window.location.href = "log.html";
}

// 4. Lógica del Tablón (Comunicación con el Backend)
async function loadProjects() {
    const container = document.getElementById('projects-container');
    if (!container) return;

    // Feedback visual de carga
    container.innerHTML = `
        <div style="text-align:center; padding: 20px;">
            <p style="color: #38bdf8; font-weight: bold;">Cargando retos...</p>
        </div>
    `;

    try {
        // Usamos 127.0.0.1 para evitar problemas de resolución de nombres
        const response = await fetch('http://127.0.0.1:8000/api/challenges');
        
        if (!response.ok) throw new Error("Error en la respuesta del servidor");
        
        const projects = await response.json();
        
        container.innerHTML = ""; 

        if (projects.length === 0) {
            container.innerHTML = `
                <div style="background: #1e293b; padding: 20px; border-radius: 12px; text-align: center;">
                    <p style="color: #64748b;">No hay retos publicados aún. ¡Sé el primero!</p>
                </div>
            `;
            return;
        }

        projects.forEach(p => {
            const card = document.createElement('div');
            card.style = `
                background: #1e293b; 
                padding: 20px; 
                border-radius: 12px; 
                border-left: 4px solid #38bdf8;
                margin-bottom: 15px;
                text-align: left;
                box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
            `;
            
            card.innerHTML = `
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                    <h4 style="margin: 0; color: #38bdf8; font-size: 1.1rem;">${p.title}</h4>
                    <span style="font-size: 0.7rem; color: #64748b;">${p.created_at ? new Date(p.created_at).toLocaleDateString() : 'Reciente'}</span>
                </div>
                <p style="font-size: 0.95rem; color: #cbd5e1; margin-bottom: 12px;">${p.description}</p>
                <div style="display: flex; align-items: center; gap: 8px;">
                    <div style="width: 24px; height: 24px; background: #334155; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 0.6rem; color: #38bdf8;">👤</div>
                    <small style="color: #94a3b8;">${p.author_email || p.user_email || 'Anónimo'}</small>
                </div>
            `;
            container.appendChild(card);
        });
    } catch (err) {
        console.error("Error al cargar proyectos:", err);
        container.innerHTML = `
            <div style="background: #451a1a; padding: 15px; border-radius: 8px; border: 1px solid #ef4444;">
                <p style="color: #f87171; margin: 0;">❌ Error al conectar con el servidor.</p>
                <small style="color: #fca5a5;">Asegúrate de que Python está corriendo en el puerto 8000.</small>
            </div>
        `;
    }
}

// 5. Subida de Retos
async function uploadProject() {
    const titleInput = document.getElementById('proj-title');
    const descInput = document.getElementById('proj-desc');
    const email = localStorage.getItem("user_email") || "invitado@pya.com"; 

    if (!titleInput.value.trim() || !descInput.value.trim()) {
        return alert("Bro, no puedes dejar campos vacíos.");
    }

    const projectData = {
        title: titleInput.value,
        description: descInput.value
    };

    try {
        const response = await fetch(`http://127.0.0.1:8000/api/challenges?email=${email}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(projectData)
        });

        if (response.ok) {
            alert("¡Proyecto subido con éxito!");
            titleInput.value = "";
            descInput.value = "";
            
            // Cerrar modal si existe
            const modal = document.getElementById('modal-upload');
            if (modal) modal.style.display = 'none';
            
            loadProjects(); // Refrescar el tablón automáticamente
        } else {
            const error = await response.json();
            alert("Error: " + (error.detail || "No se pudo subir el proyecto"));
        }
    } catch (err) {
        console.error("Error en la petición:", err);
        alert("El servidor no responde. Verifica tu terminal de Python.");
    }
}