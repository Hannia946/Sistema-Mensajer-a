const API_URL = "http://127.0.0.1:8000";

let usuarioActual = sessionStorage.getItem("usuario_seguro") || "";
let chatActivo = ""; // con quien se esta hablando actualmente

const authSection = document.getElementById("auth-section");
const chatSection = document.getElementById("chat-section");
const usernameInput = document.getElementById("username");
const passwordInput = document.getElementById("password");
const mensajeInput = document.getElementById("mensaje-texto");
const chatBox = document.getElementById("chat-box");
const welcomeUser = document.getElementById("welcome-user");
const listaUsuariosDiv = document.getElementById("lista-usuarios");
const chatConTitulo = document.getElementById("chat-con-titulo");
const btnSend = document.getElementById("btn-send");

// registrar usuario
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
        alert(data.mensaje || `Error: ${data.detail}`);
    } catch (error) {
        alert("No se pudo conectar con el servidor Backend.");
    }
});

// iniciar sesión
document.getElementById("btn-login").addEventListener("click", async () => {
    const usuario = usernameInput.value.trim();
    const password = passwordInput.value;
    if (!usuario || !password) return alert("Escribe tu usuario y contraseña");
    
    try {
        const respuesta = await fetch(`${API_URL}/login`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ usuario: usuario, password: password })
        });

        const data = await respuesta.json();
        if (respuesta.ok) {
            usuarioActual = usuario;
            sessionStorage.setItem("usuario_seguro", usuarioActual); 
            entrarAlChat();
        } else {
            alert(`Error: ${data.detail || "Credenciales inválidas"}`);
        }
    } catch(error) {
        alert("No se pudo conectar con el servidor.");
    }
});  

// configurar la interfaz para mostrar el chat
function entrarAlChat() {
    welcomeUser.innerText = `Usuario: ${usuarioActual}`;
    authSection.classList.add("hidden");
    chatSection.classList.remove("hidden");
    cargarListaContactos();
}

// cargar contactos en la barra lateral
async function cargarListaContactos() {
    try {
        const respuesta = await fetch(`${API_URL}/usuarios/${usuarioActual}`);
        const data = await respuesta.json();
        
        listaUsuariosDiv.innerHTML = "";
        
        if (data.usuarios.length === 0) {
            listaUsuariosDiv.innerHTML = '<p style="font-size:12px;color:#6b7280;text-align:center;">No hay más usuarios registrados.</p>';
            return;
        }

        data.usuarios.forEach(username => {
            const userDiv = document.createElement("div");
            userDiv.className = `user-item ${chatActivo === username ? 'active' : ''}`;
            userDiv.textContent = username;
            
            // evento cuando se hace click en un usuario
            userDiv.addEventListener("click", () => {
                // se desactiva el botón anterior y se activa este
                document.querySelectorAll(".user-item").forEach(el => el.classList.remove("active"));
                userDiv.classList.add("active");
                
                chatActivo = username;
                chatConTitulo.textContent = `Chateando con: ${chatActivo}`;
                
                mensajeInput.disabled = false;
                btnSend.disabled = false;
                
                cargarMensajes();
            });
            
            listaUsuariosDiv.appendChild(userDiv);
        });
    } catch (error) {
        console.error("Error al cargar contactos:", error);
    }
}

// Enviar mensaje
btnSend.addEventListener("click", async () => {
    const texto = mensajeInput.value.trim();
    if (!chatActivo || !texto) return;

    try {
        const respuesta = await fetch(`${API_URL}/enviar-mensaje`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                remitente: usuarioActual,
                destinatario: chatActivo, 
                contenido: texto
            })
        });

        if (respuesta.ok) {
            mensajeInput.value = ""; 
            cargarMensajes(); //recarga para ver le mensaje en el historial 
        }
    } catch (error) {
        alert("Error al enviar el mensaje.");
    }
});

// leer mensajes
async function cargarMensajes() {
    if (!usuarioActual || !chatActivo) return;
    
    try {
        // historial entre usuario y yo
        const respuesta = await fetch(`${API_URL}/leer-mensajes/${usuarioActual}/${chatActivo}`);
        const data = await respuesta.json();
        
        chatBox.innerHTML = "";
        
        if (data.mensajes && data.mensajes.length > 0) {
            data.mensajes.forEach(msg => {
                const msgDiv = document.createElement("div");
                
                msgDiv.className = msg.remitente === usuarioActual ? "msg me" : "msg other";
                
                const metaDiv = document.createElement("div");
                metaDiv.className = "msg-meta";
                metaDiv.textContent = msg.remitente === usuarioActual ? "Tú" : msg.remitente;
                
                const textSpan = document.createElement("span");
                textSpan.textContent = msg.contenido;
                
                msgDiv.appendChild(metaDiv);
                msgDiv.appendChild(textSpan);
                chatBox.appendChild(msgDiv);
            });
        } else {
            chatBox.innerHTML = `<p style="text-align:center; color:#9ca3af; font-size:14px;">No hay mensajes previos. ¡Escribe algo seguro!</p>`;
        }
        chatBox.scrollTop = chatBox.scrollHeight;
    } catch (error) {
        console.error("Error al cargar mensajes:", error);
    }
}

// cerrar sesión
document.getElementById("btn-logout").addEventListener("click", () => {
    usuarioActual = "";
    chatActivo = "";
    sessionStorage.removeItem("usuario_seguro"); 
    authSection.classList.remove("hidden");
    chatSection.classList.add("hidden");
    passwordInput.value = "";
    usernameInput.value = "";
    mensajeInput.disabled = true;
    btnSend.disabled = true;
    chatConTitulo.textContent = "Selecciona un contacto para chatear";
    chatBox.innerHTML = `<p style="text-align:center; color:#9ca3af; font-size:14px;">Haz clic en un usuario de la izquierda.</p>`;
});

// verificar sesión al cargar
if (usuarioActual) {
    entrarAlChat();
}

setInterval(() => {
    // si el usuario inicio sesion Y tiene un chat abierto con alguien, actualiza
    if (usuarioActual && chatActivo) {
        cargarMensajes();
    }
}, 3000);