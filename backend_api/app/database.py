# produccion_app/backend_api/app/database.py
import mysql.connector
import traceback # Para imprimir tracebacks de errores de conexión

# --- Información para conectar a tu Base de Datos ---
DB_CONFIG = {
    "host": "localhost",
    "port": 3306,
    "user": "root",
    "password": "@Martin110619", # ¡TU CONTRASEÑA REAL DE MYSQL!
    "database": "bbdd_produccion"
}

# --- Función Auxiliar para Conectar a la Base de Datos ---
def obtener_conexion_db_directa(): # <--- ESTE ES EL NOMBRE CORRECTO DE LA FUNCIÓN
    """
    Intenta conectar a la base de datos usando la configuración DB_CONFIG.
    Imprime mensajes de debug sobre el estado de la conexión.
    Devuelve un objeto de conexión si tiene éxito, o None si falla.
    QUIEN LLAMA A ESTA FUNCIÓN ES RESPONSABLE DE CERRAR LA CONEXIÓN.
    """
    print("DEBUG DATABASE (directa): Intentando llamar a obtener_conexion_db_directa()...")
    try:
        print(f"DEBUG DATABASE (directa): Usando config: user={DB_CONFIG['user']}, host={DB_CONFIG['host']}, db={DB_CONFIG['database']}")
        conexion = mysql.connector.connect(**DB_CONFIG)
        
        if conexion and conexion.is_connected(): # Doble verificación
            print("DEBUG DATABASE (directa): mysql.connector.connect() tuvo éxito Y conexion.is_connected() es True.")
            return conexion
        elif conexion: # Si se creó el objeto conexión pero no está activo
            print("DEBUG DATABASE ERROR (directa): mysql.connector.connect() NO lanzó excepción, PERO conexion.is_connected() es False.")
            conexion.close() # Intenta cerrar si se creó el objeto pero no está conectado
            return None
        else: # Si mysql.connector.connect() devolvió None (muy raro)
             print("DEBUG DATABASE ERROR (directa): mysql.connector.connect() devolvió None.")
             return None

    except mysql.connector.Error as err:
        print(f"!!! DEBUG DATABASE ERROR CRÍTICO (directa mysql.connector.Error): {type(err).__name__} - {err}")
        print("--- Traceback del error de conexión MySQL ---")
        traceback.print_exc() # Imprime el traceback del error de conexión
        print("--- Fin del Traceback ---")
        return None
    except Exception as e: # Para cualquier otra excepción durante la conexión
        print(f"!!! DEBUG DATABASE ERROR INESPERADO (directa Exception): {type(e).__name__} - {e}")
        print("--- Traceback del error de conexión General ---")
        traceback.print_exc() # Imprime el traceback del error de conexión
        print("--- Fin del Traceback ---")
        return None
