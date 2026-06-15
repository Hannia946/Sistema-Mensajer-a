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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # cualquier pantalla local se conecte
    allow_credentials=True,
    allow_methods=["*"], # permite todos los métodos (GET, POST, etc.)
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

#ENPOINTS
#1. saludo de bienvenida
@app.get("/")
def inicio():
    return {"mensaje": "¡Bienvenido al servidor de mensajería seguro!"}

# 2. registrar usuario 
@app.post("/registrar")
def registrar_usuario(datos: RegistroUsuario):
    sal = bcrypt.gensalt()
    password_hasheada = bcrypt.hashpw(datos.password.encode('utf-8'), sal)
    
    conexion = sqlite3.connect(db_archivo)
    cursor = conexion.cursor()

    try:
        #insertar usuario
        cursor.execute("INSERT INTO usuarios (usuario, password) VALUES (?, ?)", (datos.usuario, password_hasheada.decode('utf-8')))
        conexion.commit()
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="El usuario ya existe.")
    finally:
        conexion.close()
    return {"mensaje": f"Usuario {datos.usuario} registrado con éxito en la Base de Datos."}
    

# 3. enviar mensajes 
@app.post("/enviar-mensaje")
def enviar_mensaje(datos: EnvíoMensaje):
    # cifrar el mensaje con el componente Fernet (llave maestra)
    contenido_cifrado = componente_cifrado.encrypt(datos.contenido.encode('utf-8')).decode('utf-8') 
    
    conexion = sqlite3.connect(db_archivo)
    cursor = conexion.cursor()
    #insertar mensaje en la tabla de mensajes
    cursor.execute("INSERT INTO mensajes (remitente, destinatario, contenido_oculto) VALUES (?, ?, ?)", (datos.remitente, datos.destinatario, contenido_cifrado))
    conexion.commit()
    conexion.close()
    
    return {"mensaje": "Mensaje cifrado y guardado en la Base de Datos con éxito."}

# 4. leer mensajes)
@app.get("/leer-mensajes/{usuario_destinatario}")
def leer_mensajes(usuario_destinatario: str):
    conexion = sqlite3.connect(db_archivo)
    cursor = conexion.cursor()

    #buscar los mensajes que le corresponden al destinatario
    cursor.execute("SELECT remitente, contenido_oculto FROM mensajes WHERE destinatario = ?", (usuario_destinatario,))
    filas = cursor.fetchall()
    conexion.close()
    mensajes_del_usuario = []
    
    # buscar en la bd
    for msg in filas:
        remitenteDB, contenidoCifradoDB = msg
        try:
            #se descifra el mensaje con la llave maestra
            contenidoDescifrado = componente_cifrado.decrypt(contenidoCifradoDB.encode('utf-8')).decode('utf-8')
            
            mensajes_del_usuario.append({
                "remitente": remitenteDB,
                "contenido": contenidoDescifrado
            })
            
        except Exception:
            raise HTTPException(status_code=500, detail="Error al descifrar el historial.")
                
    return {"mensajes": mensajes_del_usuario}

# 5. ver la bd 
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