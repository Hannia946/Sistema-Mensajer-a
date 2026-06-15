from fastapi import FastAPI
from pydantic import BaseModel
import bcrypt
from cryptography.fernet import Fernet
from dotenv import load_dotenv
import os

load_dotenv()  # Carga las variables de entorno desde el archivo .env

app = FastAPI(title="Sistema de Mensajería")

LLAVE_SECRET_TEXTO = os.getenv("LLAVE_MAESTRA_SECRET")  # Lee la llave secreta desde el archivo .env
componente_cifrado = Fernet(LLAVE_SECRET_TEXTO.encode('utf-8'))

# simulación de bd
tabla_usuarios = {}  
tabla_mensajes = []  


class RegistroUsuario(BaseModel):
    usuario: str
    password: str

class EnvíoMensaje(BaseModel):
    remitente: str
    destinatario: str
    contenido: str

#ENPOINTS
#1. saludo de bienvenida
@app.get("/")
def inicio():
    return {"mensaje": "¡Bienvenido al servidor de mensajería seguro!"}

# 2. registrar usuario 
@app.post("/registrar")
def registrar_usuario(datos: RegistroUsuario):
    # verificar si el usuario ya existe
    if datos.usuario in tabla_usuarios:
        return {"error": "El usuario ya existe"}
    
    # hashear la contraseña con bcrypt 
    sal = bcrypt.gensalt()
    password_hasheada = bcrypt.hashpw(datos.password.encode('utf-8'), sal)
    
    # guardar la contraseña hasheada en la bd simulada
    tabla_usuarios[datos.usuario] = password_hasheada.decode('utf-8')
    
    return {"mensaje": f"Usuario {datos.usuario} registrado con éxito con contraseña oculta."}

# 3. enviar mensajes 
@app.post("/enviar-mensaje")
def enviar_mensaje(datos: EnvíoMensaje):
    # cifrar el mensaje antes de guardarlo en la base de datos simulada
    contenido_cifrado = componente_cifrado.encrypt(datos.contenido.encode('utf-8'))
    
    nuevo_mensaje = {
        "remitente": datos.remitente,
        "destinatario": datos.destinatario,
        "contenido_oculto": contenido_cifrado.decode('utf-8') # se guarda como texto legible para JSON
    }
    
    tabla_mensajes.append(nuevo_mensaje)
    return {"mensaje": "Mensaje cifrado y guardado en el servidor con éxito."}

# 4. ver la bd 
@app.get("/ver-base-de-datos")
def ver_bd():
    return {
        "tabla_usuarios": tabla_usuarios,
        "tabla_mensajes_cifrados": tabla_mensajes
    }

# 5. leer mensajes (se descifran antes de mostrar al usuario)
@app.get("/leer-mensajes/{usuario_destinatario}")
def leer_mensajes(usuario_destinatario: str):
    mensajes_del_usuario = []
    
    # buscar en la bd
    for msg in tabla_mensajes:
        # si es el mismo usuario
        if msg["destinatario"] == usuario_destinatario:
            try:
                # tomar el contenido oculto y se convierte a bytes
                contenido_cifrado_bytes = msg["contenido_oculto"].encode('utf-8')
                
                # descrifrar con el componente cifrado con la llave del .env
                contenido_descifrado = componente_cifrado.decrypt(contenido_cifrado_bytes).decode('utf-8')
                
                # crear copia con el texto limpio para el usuario
                mensaje_limpio = {
                    "remitente": msg["remitente"],
                    "contenido": contenido_descifrado
                }
                mensajes_del_usuario.append(mensaje_limpio)
            except Exception as e:
                #avisar el error si no se pudo descifrar el mensaje
                return {"error": "No se pudieron descifrar los mensajes de forma segura."}
                
    # devolver lista vacía si no hay mensajes
    return {"mensajes": mensajes_del_usuario}