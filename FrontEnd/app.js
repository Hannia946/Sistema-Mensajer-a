// servidor FastAPI
const API_URL = "http://127.0.0.1:8000";

// variables globales para rastrear al usuario actual
let usuarioActual = "";

// elementos de la pantalla (DOM)
const authSection = document.getElementById("auth-section");
const chatSection = document.getElementById("chat-section");
const usernameInput = document.getElementById("username");
const passwordInput = document.getElementById("password");
const destinatarioInput = document.getElementById("destinatario");
const mensajeInput = document.getElementById("mensaje-texto");
const chatBox = document.getElementById("chat-box");
const welcomeUser = document.getElementById("welcome-user");

// Registrar usuario
document.getElementById("btn-register").addEventListener("click", async () => {
    const usuario = usernameInput.value.trim();
    const password = passwordInput.value;

    if (!usuario || !password) return alert("Por favor llena todos los campos");

    try {
        const respuesta = await fetch(`${API_URL}/registrar`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ usuario: usuario, password: password })
        });
        
        const data = await respuesta.json();
        if (respuesta.ok) {
            alert(data.mensaje);
        } else {
            alert(`Error: ${data.detail || data.error}`);
        }
    } catch (error) {
        alert("No se pudo conectar con el servidor Backend.");
    }
});

// Inciar sesión 
document.getElementById("btn-login").addEventListener("click", () => {
    const usuario = usernameInput.value.trim();
    const password = passwordInput.value;

    if (!usuario || !password) return alert("Escribe tu usuario y contraseña para ingresar");
    try{
        const respuesta = await fetch(`${API_URL}/login`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ usuario: usuario, password: password })
        });

        const data = await respuesta.json();
        if (respuesta.ok) {
            usuarioActual = data.usuario;
            welcomeUser.innerText = `Usuario: ${usuarioActual}`;
            
            authSection.classList.add("hidden");
            chatSection.classList.remove("hidden");

            cargarMensajes();
        }else{
            alert(`Error: ${data.detail || "Credenciales inválidas"}`);
        }
    }catch(error){
        alert("No se pudo conectar con el servidor para iniciar sesión.");
    }
});  

// Enviar mensaje
document.getElementById("btn-send").addEventListener("click", async () => {
    const destino = destinatarioInput.value.trim();
    const texto = mensajeInput.value.trim();

    if (!destino || !texto) return alert("Escribe el destinatario y el mensaje");

    try {
        const respuesta = await fetch(`${API_URL}/enviar-mensaje`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                remitente: usuarioActual,
                destinatario: destino,
                contenido: texto
            })
        });

        if (respuesta.ok) {
            mensajeInput.value = ""; // limpiar la caja de texto
            // se agrega el mensaje visualmente a nuestro chatbox como enviado por mí
            const msgDiv = document.createElement("div");
            msgDiv.className = "msg me";
            msgDiv.innerHTML = `<div class="msg-meta">Para: ${destino}</div>${texto}`;
            chatBox.appendChild(msgDiv);
            chatBox.scrollTop = chatBox.scrollHeight;
        }
    } catch (error) {
        alert("Error al enviar el mensaje.");
    }
});

// Leer mensajes desenmascarados
async function cargarMensajes() {
    if (!usuarioActual) return;
    
    try {
        const respuesta = await fetch(`${API_URL}/leer-mensajes/${usuarioActual}`);
        const data = await respuesta.json();
        
        // limpiar el contenedor de mensajes
        chatBox.innerHTML = "";
        
        if (data.mensajes && data.mensajes.length > 0) {
            data.mensajes.forEach(msg => {
                const msgDiv = document.createElement("div");
                msgDiv.className = "msg other";
                msgDiv.innerHTML = `<div class="msg-meta">De: ${msg.remitente}</div>${msg.contenido}`;
                chatBox.appendChild(msgDiv);
            });
        } else {
            chatBox.innerHTML = `<p style="text-align:center; color:#9ca3af; font-size:14px;">No tienes mensajes nuevos.</p>`;
        }
        chatBox.scrollTop = chatBox.scrollHeight;
    } catch (error) {
        console.error("Error al cargar mensajes:", error);
    }
}

// Botón para actualizar mensajes
document.getElementById("btn-refresh").addEventListener("click", cargarMensajes);

// Cerrar sesión
document.getElementById("btn-logout").addEventListener("click", () => {
    usuarioActual = "";
    authSection.classList.remove("hidden");
    chatSection.classList.add("hidden");
    passwordInput.value = "";
});