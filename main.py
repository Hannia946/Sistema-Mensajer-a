from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import bcrypt
from cryptography.fernet import Fernet
from dotenv import load_dotenv
import os
import sqlite3
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()  # Carga las variables de entorno desde el archivo .env

app = FastAPI(title="Sistema de Mensajería")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Permite que cualquier pantalla local se conecte
    allow_credentials=True,
    allow_methods=["*"], # Permite todos los métodos (GET, POST, etc.)
    allow_headers=["*"],
)

LLAVE_SECRET_TEXTO = os.getenv("LLAVE_MAESTRA_SECRET")  # Lee la llave secreta desde el archivo .env
componente_cifrado = Fernet(LLAVE_SECRET_TEXTO.encode('utf-8'))

#config de bd

#archivo de la bd
db_archivo = "mensajeria.db"

def inicializacionBD():
    conexion = sqlite3.connect(db_archivo)
    cursor = conexion.cursor()

    #tabla usuarios
    cursor.execute("""
                   CREATE TABLE IF NOT EXISTS usuarios (
                   usuario TEXT PRIMARY KEY,
                   password TEXT NOT NULL
                     )
                   """)
    #tabla mensajes
    cursor.execute("""
                   CREATE TABLE IF NOT EXISTS mensajes (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   remitente TEXT NOT NULL,
                   destinatario TEXT NOT NULL,
                   contenido_oculto TEXT NOT NULL
                     )
                   """)
    conexion.commit()
    conexion.close()

inicializacionBD()

#modelo de datos

class RegistroUsuario(BaseModel):
    usuario: str
    password: str
class EnvíoMensaje(BaseModel):
    remitente: str
    destinatario: str
    contenido: str
class LoginUsuario(BaseModel):
    usuario: str
    password: str

#ENPOINTS
#saludo de bienvenida
@app.get("/")
def inicio():
    return {"mensaje": "¡Bienvenido al servidor de mensajería seguro!"}

# registrar usuario 
@app.post("/registrar")
def registrar_usuario(datos: RegistroUsuario):
    usuario_limpio = datos.usuario.strip()
    if not usuario_limpio:
        raise HTTPException(status_code=400, detail="Indique su usuario.")
    sal = bcrypt.gensalt()
    password_hasheada = bcrypt.hashpw(datos.password.encode('utf-8'), sal)
    
    conexion = sqlite3.connect(db_archivo)
    cursor = conexion.cursor()

    try:
        #insertar usuario
        cursor.execute("INSERT INTO usuarios (usuario, password) VALUES (?, ?)", (usuario_limpio, password_hasheada.decode('utf-8')))
        conexion.commit()
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="El usuario ya existe.")
    finally:
        conexion.close()
    return {"mensaje": f"Usuario {usuario_limpio} registrado con éxito."}
    
#login
@app.post("/login")
def login_usuario(datos: LoginUsuario):
    usuario_limpio = datos.usuario.strip()

    conexion = sqlite3.connect(db_archivo)
    cursor = conexion.cursor()

    cursor.execute("SELECT password FROM usuarios WHERE usuario = ?", (usuario_limpio,))
    resultado = cursor.fetchone()
    conexion.close()

    if resultado is None:
        raise HTTPException(status_code=400, detail="Usuario o contraseña incorrectos.")
    
    password_almacenada = resultado[0]
    
    coincide = bcrypt.checkpw(datos.password.encode('utf-8'), password_almacenada.encode('utf-8'))
    if coincide:
        return {"mensaje": f"Usuario {usuario_limpio} autenticado con éxito.",
                "usuario": usuario_limpio}
    else:
        raise HTTPException(status_code=400, detail="Usuario o contraseña incorrectos.")

# enviar mensajes 
@app.post("/enviar-mensaje")
def enviar_mensaje(datos: EnvíoMensaje):
    
    remitente_limpio = datos.remitente.strip()
    destinatario_limpio = datos.destinatario.strip()
    contenido_limpio = datos.contenido.strip() 

    if not destinatario_limpio or not contenido_limpio:
        raise HTTPException(status_code=400, detail="El destinatario o el mensaje no pueden estar vacíos.")
    
    # cifrar el mensaje con el componente Fernet (llave maestra)
    contenido_cifrado = componente_cifrado.encrypt(contenido_limpio.encode('utf-8')).decode('utf-8') 
    
    conexion = sqlite3.connect(db_archivo)
    cursor = conexion.cursor()
    #insertar mensaje en la tabla de mensajes
    cursor.execute("INSERT INTO mensajes (remitente, destinatario, contenido_oculto) VALUES (?, ?, ?)", (remitente_limpio, destinatario_limpio, contenido_cifrado))
    conexion.commit()
    conexion.close()
    
    return {"mensaje": "Mensaje cifrado y guardado en la Base de Datos con éxito."}

# leer mensajes)
@app.get("/leer-mensajes/{usuario_actual}/{usuario_amigo}")
def leer_mensajes(usuario_actual: str, usuario_amigo: str):
    usuario_limpio = usuario_actual.strip()
    amigo_limpio = usuario_amigo.strip()

    conexion = sqlite3.connect(db_archivo)
    cursor = conexion.cursor()

    #traer mensajes enviados que yo mande o que me mandaron
    cursor.execute("""
        SELECT remitente, destinatario, contenido_oculto 
        FROM mensajes 
        WHERE (remitente = ? AND destinatario = ?) 
           OR (remitente = ? AND destinatario = ?)
        ORDER BY id ASC
    """, (usuario_limpio, amigo_limpio, amigo_limpio, usuario_limpio))
    
    filas = cursor.fetchall()
    conexion.close()

    mensajes_del_chat = []
    
    # buscar en la bd
    for msg in filas:
        remitenteDB, destinatarioDB, contenidoCifradoDB = msg
        try:
            #se descifra el mensaje con la llave maestra
            contenidoDescifrado = componente_cifrado.decrypt(contenidoCifradoDB.encode('utf-8')).decode('utf-8')
            
            mensajes_del_chat.append({
                "remitente": remitenteDB,
                "destinatario": destinatarioDB,
                "contenido": contenidoDescifrado
            })
            
        except Exception:
            raise HTTPException(status_code=500, detail="Error al descifrar el historial.")
                
    return {"mensajes": mensajes_del_chat}

#obtener lista de usuarios registrados
@app.get("/usuarios/{usuario_actual}")
def obtener_usuarios(usuario_actual: str):
    usuario_limpio = usuario_actual.strip()
    conexion = sqlite3.connect(db_archivo)
    cursor = conexion.cursor()
    
    # trae todos los usuarios menos al que está logueado
    cursor.execute("SELECT usuario FROM usuarios WHERE usuario != ?", (usuario_limpio,))
    filas = cursor.fetchall()
    conexion.close()
    
    # se convierte la lista de tuplas [('pedro',), ('juan',)] a una lista simple ['pedro', 'juan']
    lista_usuarios = [u[0] for u in filas]
    return {"usuarios": lista_usuarios}

# ver la bd 
@app.get("/ver-base-de-datos")
def ver_bd():
    conexion = sqlite3.connect(db_archivo)
    cursor = conexion.cursor()

    #buscar los mensajes que le corresponden al destinatario
    cursor.execute("SELECT * FROM usuarios")
    usuarios = cursor.fetchall()

    cursor.execute("SELECT * FROM mensajes")
    mensajes = cursor.fetchall()
    
    conexion.close()
    
    return {
        "usuarios_en_base_de_datos": [{"usuario": u[0], "hash_password": u[1]} for u in usuarios],
        "mensajes_cifrados_en_base_de_datos": [{"id": m[0], "remitente": m[1], "destinatario": m[2], "texto_cifrado": m[3]} for m in mensajes]
    }