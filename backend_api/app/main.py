# produccion_app/backend_api/app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles # <-- LÍNEA AÑADIDA

# --- Importación de los diferentes módulos de routers ---
from .routers import maestros
from .routers import produccion
from .routers import paros
from .routers import auth 
from .routers import calidad # <-- LÍNEA NUEVA AÑADIDA

# --- Creación de la Aplicación FastAPI Principal ---
app = FastAPI(
    title="API de Registro de Producción Industrial",
    description="Esta API maneja el registro de datos de producción, paros operativos, inspecciones de calidad y desperdicios para los procesos industriales de la planta, incluyendo autenticación de usuarios.",
    version="0.3.0" # Incrementé la versión para reflejar la adición del módulo de calidad
)

# --- Montar el directorio de archivos estáticos (Frontend) ---
# Esta es la instrucción clave que le dice a FastAPI cómo servir tu index.html
# IMPORTANTE: Esto debe hacerse antes de incluir los routers si hay rutas que puedan solaparse.
# Y Uvicorn debe ejecutarse desde la carpeta raíz del proyecto (produccion_app)
app.mount("/static", StaticFiles(directory="frontend_raspberry_pi"), name="static")


# --- CONFIGURACIÓN DE CORS (MUY PERMISIVA PARA DESARROLLO) ---
origins = [
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# --- FIN DE CONFIGURACIÓN DE CORS ---


# --- Inclusión de los Routers en la Aplicación Principal ---
app.include_router(auth.router) 
app.include_router(maestros.router)
app.include_router(produccion.router)
app.include_router(paros.router)
app.include_router(calidad.router) # <-- LÍNEA NUEVA AÑADIDA


# --- Endpoint Raíz ---
# ¡ATENCIÓN! La ruta raíz ahora debe ir al final, después de montar los archivos estáticos.
# Si la pones antes, a veces puede capturar todas las peticiones a "/"
@app.get("/", tags=["Raíz"])
async def ruta_raiz():
    """
    Endpoint raíz de la API.
    Devuelve un mensaje de bienvenida para confirmar que el servicio está en línea.
    """
    return {"mensaje": "¡Bienvenido a la API de Registro de Producción Industrial (v0.3.0 con Módulo de Calidad)! "}