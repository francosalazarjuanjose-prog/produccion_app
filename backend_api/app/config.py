# produccion_app/backend_api/app/config.py
from pydantic_settings import BaseSettings
from pathlib import Path

# Define la ruta al archivo .env
env_path = Path('.') / '.env'

class Settings(BaseSettings):
    # Configuración de la base de datos (puedes mover la tuya aquí también)
    DB_HOST: str = "localhost"
    DB_PORT: int = 3306
    DB_USER: str = "root"
    DB_PASSWORD: str = "@Martin110619"
    DB_DATABASE: str = "bbdd_produccion"

    # Configuración del correo
    MAIL_USERNAME: str
    MAIL_PASSWORD: str
    MAIL_FROM: str
    MAIL_PORT: int
    MAIL_SERVER: str
    MAIL_STARTTLS: bool
    MAIL_SSL_TLS: bool

    # Correo del destinatario de mantenimiento
    MAINTENANCE_EMAIL_RECIPIENT: str

    class Config:
        env_file = env_path

settings = Settings()