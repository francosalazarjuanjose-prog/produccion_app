# produccion_app/backend_api/app/routers/auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
import mysql.connector
from typing import Optional
import traceback

from .. import schemas
from .. import security
from ..database import obtener_conexion_db_directa

router = APIRouter(
    tags=["Autenticación"]
)

def get_user_data_from_db(db_conn: mysql.connector.MySQLConnection, user_id: str) -> Optional[dict]:
    print(f"DEBUG AUTH (get_user_data_from_db): Buscando usuario '{user_id}'")
    cursor = None
    try:
        if not db_conn or not db_conn.is_connected():
            print("DEBUG AUTH ERROR (get_user_data_from_db): Conexión a BD no válida al inicio.")
            return None 
        cursor = db_conn.cursor(dictionary=True)
        # Asegúrate de seleccionar todos los campos que necesitas para UsuarioInDB y el token
        query = "SELECT ID_Usuario, Nombre, Rol, Estado, Contraseña, Cedula, Telefono, Correo FROM Usuario WHERE ID_Usuario = %s"
        cursor.execute(query, (user_id,))
        user_data_dict = cursor.fetchone()
        if user_data_dict:
            print(f"DEBUG AUTH (get_user_data_from_db): Usuario '{user_id}' encontrado.")
            return user_data_dict
        print(f"DEBUG AUTH (get_user_data_from_db): Usuario '{user_id}' NO encontrado.")
        return None
    except Exception as e:
        print(f"DEBUG AUTH ERROR (get_user_data_from_db): Excepción al buscar usuario '{user_id}': {type(e).__name__} - {e}")
        traceback.print_exc()
        return None
    finally:
        if cursor:
            cursor.close()
            print(f"DEBUG AUTH (get_user_data_from_db): Cursor cerrado para usuario '{user_id}'.")

@router.post("/token", response_model=schemas.Token, summary="Obtener Token de Acceso")
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends()
):
    print(f"DEBUG AUTH (login_for_access_token): Intento de login para ID_Usuario: {form_data.username}")
    db_conn = None
    try:
        db_conn = obtener_conexion_db_directa()
        if db_conn is None or not db_conn.is_connected():
            print("DEBUG AUTH ERROR (login_for_access_token): Conexión a BD nula o no conectada.")
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Servicio no disponible (BD).")

        user_data_dict = get_user_data_from_db(db_conn, form_data.username)
        
        if not user_data_dict:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="ID de Usuario o Contraseña (Cédula) incorrectos.", headers={"WWW-Authenticate": "Bearer"})
        
        # Crear instancia de UsuarioInDB para fácil acceso y validación (aunque no la usemos mucho aquí)
        user_in_db = schemas.UsuarioInDB(**user_data_dict) 

        try:
            provided_password_as_int = int(form_data.password)
        except ValueError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="El formato de la Contraseña (Cédula) es incorrecto.", headers={"WWW-Authenticate": "Bearer"})

        if user_in_db.Contraseña != provided_password_as_int: # Compara con la columna Contraseña de la BD
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="ID de Usuario o Contraseña (Cédula) incorrectos.", headers={"WWW-Authenticate": "Bearer"})
        
        if user_in_db.Estado != 'Activo':
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="El usuario no está activo.", headers={"WWW-Authenticate": "Bearer"})
        
        # Crear el token con 'sub' (ID_Usuario), 'rol' y 'nombre_usuario'
        access_token_data = {
            "sub": user_in_db.ID_Usuario, 
            "rol": user_in_db.Rol,
            "nombre_usuario": user_in_db.Nombre # <--- AÑADIDO NOMBRE AL TOKEN PAYLOAD
        }
        access_token = security.create_access_token(data=access_token_data)
        
        print(f"DEBUG AUTH (login_for_access_token): Token JWT creado para ID_Usuario: {user_in_db.ID_Usuario} con nombre: {user_in_db.Nombre}")
        return {"access_token": access_token, "token_type": "bearer"}
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"DEBUG AUTH ERROR INESPERADO (login_for_access_token): {type(e).__name__} - {e}")
        traceback.print_exc()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error interno del servidor durante el login.")
    finally: 
        if db_conn and db_conn.is_connected():
            print("DEBUG AUTH (login_for_access_token): Cerrando conexión de BD.")
            db_conn.close()

async def get_current_active_user(
    current_user_id: str = Depends(security.get_current_user_id_from_token) # Solo necesitamos el ID del token aquí
) -> schemas.UsuarioInDB: # Devolvemos el objeto UsuarioInDB para tener todos los datos del usuario
    print(f"DEBUG AUTH (get_current_active_user): Verificando usuario con ID del token: {current_user_id}")
    db_conn = None
    try:
        db_conn = obtener_conexion_db_directa()
        if db_conn is None or not db_conn.is_connected():
            print(f"DEBUG AUTH ERROR (get_current_active_user): Conexión a BD nula o no conectada para ID: {current_user_id}")
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Servicio BD no disponible en get_current_active_user.")
        
        user_data_dict = get_user_data_from_db(db_conn, current_user_id)
            
        if not user_data_dict:
            print(f"DEBUG AUTH ERROR (get_current_active_user): Usuario del token (ID: {current_user_id}) no encontrado en BD.")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario del token no encontrado.", headers={"WWW-Authenticate": "Bearer"})
        
        user_in_db = schemas.UsuarioInDB(**user_data_dict) # Crear el objeto Pydantic

        if user_in_db.Estado != "Activo":
            print(f"DEBUG AUTH (get_current_active_user): Usuario del token (ID: {current_user_id}) no está activo. Estado: {user_in_db.Estado}")
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Usuario del token inactivo.", headers={"WWW-Authenticate": "Bearer"})
        
        print(f"DEBUG AUTH (get_current_active_user): Usuario {user_in_db.ID_Usuario} ('{user_in_db.Nombre}') verificado y activo.")
        return user_in_db
    except HTTPException:
        raise
    except Exception as e:
        print(f"DEBUG AUTH ERROR INESPERADO (get_current_active_user): {type(e).__name__} - {e}")
        traceback.print_exc()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error al verificar el usuario.")
    finally: 
        if db_conn and db_conn.is_connected():
            print(f"DEBUG AUTH (get_current_active_user): Cerrando conexión de BD para ID: {current_user_id}.")
            db_conn.close()