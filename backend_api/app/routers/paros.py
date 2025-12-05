# produccion_app/backend_api/app/routers/paros.py (VERSIÓN FINAL ACTUALIZADA)
from fastapi import APIRouter, HTTPException, Depends, status
import mysql.connector
import traceback
from datetime import datetime

from ..database import obtener_conexion_db_directa
from .. import schemas
from ..routers.auth import get_current_active_user
# --- 1. LÍNEAS NUEVAS: IMPORTAMOS NUESTRAS HERRAMIENTAS ---
from ..utils.email_utils import send_maintenance_alert_email
from ..config import settings

router = APIRouter(
    prefix="/paros",
    tags=["Registro de Paros"]
)

@router.post("/maquina_con_kpi/", response_model=schemas.ParoMaquinaResponse, status_code=status.HTTP_201_CREATED)
async def crear_paro_maquina_y_actualizar_kpi(
    paro_data: schemas.ParoMaquinaCreate,
    current_user: schemas.UsuarioInDB = Depends(get_current_active_user),
    db_conexion: mysql.connector.MySQLConnection = Depends(obtener_conexion_db_directa)
):
    cursor = None
    try:
        cursor = db_conexion.cursor(dictionary=True)
        
        # --- Lógica existente para guardar el paro (sin cambios) ---
        query_insert_paro = """
            INSERT INTO Paros_Maquina (
                ID_Registro_KPI, Fecha, Referencia, ID_Usuario, ID_Maquina, ID_Proceso, Turno,
                ID_TP, ID_Paro, Tiempo_Paro
            ) VALUES (
                %(ID_Registro_KPI)s, %(Fecha)s, %(Referencia)s, %(ID_Usuario)s, %(ID_Maquina)s, 
                %(ID_Proceso)s, %(Turno)s, %(ID_TP)s, %(ID_Paro)s, %(Tiempo_Paro)s
            )
        """
        datos_paro_db = paro_data.dict()
        datos_paro_db["ID_Usuario"] = current_user.ID_Usuario
        
        cursor.execute(query_insert_paro, datos_paro_db)
        id_nuevo_paro_maquina = cursor.lastrowid

        cursor.execute("SELECT Tipo_De_Paro FROM Tipo_Paro WHERE ID_TP = %s", (paro_data.ID_TP,))
        tipo_paro_row = cursor.fetchone()
        if tipo_paro_row:
            tipo_paro_nombre = tipo_paro_row['Tipo_De_Paro'].lower()
            columna_map = { "alistamiento": "Paros_Alistamiento", "programado": "Paros_Programados", "calidad": "Paros_Calidad", "averias": "Paros_Averias", "organizacional": "Paros_Organizacion" }
            columna_a_actualizar = next((v for k, v in columna_map.items() if k in tipo_paro_nombre), None)

            if columna_a_actualizar:
                query_update_kpi = f"UPDATE Registro_KPI SET {columna_a_actualizar} = COALESCE({columna_a_actualizar}, 0) + %s WHERE ID_Registro = %s"
                cursor.execute(query_update_kpi, (paro_data.Tiempo_Paro, paro_data.ID_Registro_KPI))

        # --- 2. NUEVA LÓGICA PARA ENVIAR CORREO DE ALERTA ---
        # El ID de tipo de paro para "Averías" es 'A4' según tu script de BD.
        if paro_data.ID_TP == 'A4':
            try:
                # Obtenemos los nombres legibles para el correo desde la BD
                cursor.execute("SELECT Maquina FROM Maquina WHERE ID_Maquina = %s", (paro_data.ID_Maquina,))
                machine_info = cursor.fetchone()
                
                cursor.execute("SELECT Proceso FROM Proceso WHERE ID_Proceso = %s", (paro_data.ID_Proceso,))
                process_info = cursor.fetchone()
                
                cursor.execute("SELECT Descripcion_Paro FROM Descripcion_Paro WHERE ID_Paro = %s", (paro_data.ID_Paro,))
                stop_info = cursor.fetchone()
                
                # Llamamos a nuestra función de envío de correo
                await send_maintenance_alert_email(
                    recipients=[settings.MAINTENANCE_EMAIL_RECIPIENT],
                    machine_name=machine_info['Maquina'] if machine_info else paro_data.ID_Maquina,
                    process_name=process_info['Proceso'] if process_info else paro_data.ID_Proceso,
                    operator_name=current_user.Nombre,
                    stop_description=stop_info['Descripcion_Paro'] if stop_info else "No especificada",
                    alert_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                )
            except Exception as e:
                # Si el envío de correo falla, no detenemos la operación.
                # Solo imprimimos una advertencia en la consola del servidor.
                print(f"!!! ADVERTENCIA: El registro de paro se guardó, pero falló el envío del correo de alerta: {e}")
                traceback.print_exc()
        # --- FIN DE LA NUEVA LÓGICA ---

        db_conexion.commit()

        respuesta_data = datos_paro_db.copy()
        respuesta_data["ID_Paro_Maquina"] = id_nuevo_paro_maquina
        return schemas.ParoMaquinaResponse(**respuesta_data)

    except mysql.connector.Error as db_error:
        if db_conexion and db_conexion.is_connected(): db_conexion.rollback()
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error de base de datos al registrar paro: {db_error.msg}")
    except Exception as e:
        if db_conexion and db_conexion.is_connected(): db_conexion.rollback()
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error inesperado al registrar paro: {e}")
    finally:
        if cursor: cursor.close()