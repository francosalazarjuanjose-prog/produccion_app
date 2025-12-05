# produccion_app/backend_api/app/security.py
from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import jwt, JWTError # Asegúrate de haber hecho: pip install python-jose[cryptography]
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from . import schemas # Para schemas.TokenData (aunque no se use directamente en esta versión simplificada de get_current_user)

# --- Configuración de JWT ---
# ¡¡¡CAMBIA ESTA SECRET_KEY EN UN ENTORNO REAL Y GUÁRDALA DE FORMA SEGURA!!!
SECRET_KEY = "a3f7b2d8e1c90f47a6b3e2d7c8109f54e2d1c0b8a7f6e3d2a1b9c807f4e5d6c3" # Ejemplo, ¡DEBES CAMBIARLA!
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 720 # <--- ACTUALIZADO A 12 HORAS (12 * 60)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token") # Apunta al endpoint de login

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Crea un nuevo token de acceso JWT.
    'data' debe contener el 'sub' (subject/ID_Usuario) y cualquier otro dato a incluir (ej. rol).
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire}) # 'exp' es el tiempo de expiración estándar de JWT
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user_id_from_token(token: str = Depends(oauth2_scheme)) -> str:
    """
    Dependencia para decodificar el token JWT, verificar su validez 
    y extraer el ID de usuario (almacenado en el campo 'sub').
    Es usada por get_current_active_user.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudieron validar las credenciales del token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: Optional[str] = payload.get("sub") # "sub" es nuestro ID_Usuario
        if username is None:
            print("Error de token: 'sub' (ID de usuario) no encontrado en el payload.")
            raise credentials_exception
        # Aquí podríamos instanciar TokenData si quisiéramos validar más campos del payload
        # token_data = schemas.TokenData(username=username)
        return username # Devolvemos el ID_Usuario (str)
    except JWTError as e:
        print(f"Error de JWT al decodificar token: {e}")
        raise credentials_exception
    except Exception as e:
        print(f"Error inesperado durante la validación del token: {e}")
        raise credentials_exception