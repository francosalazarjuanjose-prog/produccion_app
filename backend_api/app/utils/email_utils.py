# produccion_app/backend_api/app/utils/email_utils.py
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from ..config import settings
from typing import List

# Configuración de la conexión de correo usando los settings que creamos
conf = ConnectionConfig(
    MAIL_USERNAME = settings.MAIL_USERNAME,
    MAIL_PASSWORD = settings.MAIL_PASSWORD,
    MAIL_FROM = settings.MAIL_FROM,
    MAIL_PORT = settings.MAIL_PORT,
    MAIL_SERVER = settings.MAIL_SERVER,
    MAIL_STARTTLS = settings.MAIL_STARTTLS,
    MAIL_SSL_TLS = settings.MAIL_SSL_TLS,
    USE_CREDENTIALS = True,
    VALIDATE_CERTS = True
)

async def send_maintenance_alert_email(
    recipients: List[str],
    machine_name: str,
    process_name: str,
    operator_name: str,
    stop_description: str,
    alert_time: str
):
    """
    Envía un correo de alerta de avería al equipo de mantenimiento.
    """
    subject = f"¡Alerta de Avería Urgente! - Máquina: {machine_name}"
    
    # Este es el cuerpo del correo en formato HTML. Puedes personalizarlo si quieres.
    html_body = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ padding: 20px; border: 1px solid #ddd; border-radius: 5px; max-width: 600px; margin: auto; }}
            .header {{ background-color: #d9534f; color: white; padding: 10px; text-align: center; border-radius: 5px 5px 0 0; }}
            .content {{ padding: 20px; }}
            .content p {{ margin: 0 0 10px; }}
            strong {{ color: #d9534f; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h2>Alerta de Avería en Planta</h2>
            </div>
            <div class="content">
                <p>Se ha registrado una nueva avería que requiere atención inmediata del equipo de mantenimiento.</p>
                <hr>
                <p><strong>Máquina:</strong> {machine_name}</p>
                <p><strong>Proceso:</strong> {process_name}</p>
                <p><strong>Avería Reportada:</strong> {stop_description}</p>
                <p><strong>Operario que reporta:</strong> {operator_name}</p>
                <p><strong>Hora del reporte:</strong> {alert_time}</p>
                <hr>
                <p>Por favor, proceda a revisar el equipo a la brevedad posible.</p>
            </div>
        </div>
    </body>
    </html>
    """

    message = MessageSchema(
        subject=subject,
        recipients=recipients,
        body=html_body,
        subtype="html"
    )

    fm = FastMail(conf)
    await fm.send_message(message)
    print(f"Correo de alerta de avería enviado a {recipients}")