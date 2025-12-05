# produccion_app/backend_api/routers/maestros.py (VERSIÓN FINAL Y COMPLETA)
from fastapi import APIRouter, HTTPException, Query, Depends, status
from typing import Optional, List
import mysql.connector, traceback
from datetime import timedelta, time as dt_time 

from ..database import obtener_conexion_db_directa
from .. import schemas
from ..routers.auth import get_current_active_user 

router = APIRouter(prefix="/maestros", tags=["Datos Maestros"])

def convert_timedelta_to_time(data_list: List[dict], fields_to_convert: List[str]) -> List[dict]:
    for item in data_list:
        for field in fields_to_convert:
            if field in item and item.get(field) and isinstance(item.get(field), timedelta):
                total_seconds = int(item[field].total_seconds())
                item[field] = dt_time((total_seconds // 3600) % 24, (total_seconds // 60) % 60, total_seconds % 60)
    return data_list

@router.get("/estado_maquinas/", response_model=schemas.ListaMaquinasEstadoResponse)
def listar_estado_maquinas(
    current_user: schemas.UsuarioInDB = Depends(get_current_active_user),
    db_conexion: mysql.connector.MySQLConnection = Depends(obtener_conexion_db_directa)
):
    if current_user.Rol.lower() != "administrador":
        raise HTTPException(status_code=403, detail="Acceso denegado. Se requiere rol de administrador.")
    
    try:
        with db_conexion.cursor(dictionary=True) as cursor:
            query = """
                SELECT 
                    m.ID_Maquina, 
                    m.Maquina, 
                    p.Proceso,
                    r.ID_Registro AS ID_Registro_KPI,
                    r.ID_Usuario AS ID_Usuario_Activo,
                    u.Nombre AS Nombre_Usuario_Activo,
                    r.Hora_Inicio AS Hora_Inicio_Turno_Activo,
                    r.Referencia AS Referencia_Actual
                FROM Maquina m
                JOIN Proceso p ON m.ID_Proceso = p.ID_Proceso
                LEFT JOIN Registro_KPI r ON m.ID_Maquina = r.ID_Maquina AND r.Hora_Finalización IS NULL
                LEFT JOIN Usuario u ON r.ID_Usuario = u.ID_Usuario
                ORDER BY m.ID_Maquina;
            """
            cursor.execute(query)
            resultados = cursor.fetchall()
            resultados_convertidos = convert_timedelta_to_time(resultados, ['Hora_Inicio_Turno_Activo'])
            return {"data": resultados_convertidos}
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error al consultar el estado de las máquinas: {e}")

@router.get("/procesos/", response_model=schemas.ListaProcesosResponse)
def listar_procesos_endpoint(db_conexion: mysql.connector.MySQLConnection = Depends(obtener_conexion_db_directa)):
    try:
        with db_conexion.cursor(dictionary=True) as cursor:
            cursor.execute("SELECT ID_Proceso, Proceso FROM Proceso ORDER BY ID_Proceso")
            return {"data": cursor.fetchall()}
    except Exception: raise HTTPException(status_code=500, detail="Error al consultar procesos")

@router.get("/maquinas/", response_model=schemas.ListaMaquinasResponse)
def listar_maquinas_endpoint(id_proceso: Optional[str] = None, db_conexion: mysql.connector.MySQLConnection = Depends(obtener_conexion_db_directa)):
    try:
        with db_conexion.cursor(dictionary=True) as cursor:
            query, params = "SELECT * FROM Maquina", []
            if id_proceso:
                query += " WHERE ID_Proceso = %s"
                params.append(id_proceso)
            query += " ORDER BY ID_Maquina"
            cursor.execute(query, tuple(params))
            return {"data": cursor.fetchall()}
    except Exception: raise HTTPException(status_code=500, detail="Error al consultar máquinas")


# ===================================================================
# ===== MODIFICACIÓN #1: AÑADIDO NUEVO ENDPOINT Y SUS SCHEMAS =====
# ===================================================================
class TipoProductoResponse(schemas.BaseModel):
    Tipo_Producto: str
    class Config: from_attributes = True

class ListaTiposProductoResponse(schemas.BaseModel):
    data: List[TipoProductoResponse]
    
@router.get("/tipos_producto/", response_model=ListaTiposProductoResponse)
def listar_tipos_producto_endpoint(db_conexion: mysql.connector.MySQLConnection = Depends(obtener_conexion_db_directa)):
    try:
        with db_conexion.cursor(dictionary=True) as cursor:
            cursor.execute("SELECT DISTINCT Tipo_Producto FROM Producto ORDER BY Tipo_Producto")
            return {"data": cursor.fetchall()}
    except Exception:
        raise HTTPException(status_code=500, detail="Error al consultar los tipos de producto")
# ===================================================================


# ===================================================================
# ===== MODIFICACIÓN #2: AÑADIDO FILTRO A /lineas_producto/ =====
# ===================================================================
@router.get("/lineas_producto/", response_model=schemas.ListaLineasProductoResponse)
def listar_lineas_producto_endpoint(
    tipo_producto: Optional[str] = None, # <-- NUEVO FILTRO OPCIONAL
    db_conexion: mysql.connector.MySQLConnection = Depends(obtener_conexion_db_directa)
):
    try:
        with db_conexion.cursor(dictionary=True) as cursor:
            query = "SELECT DISTINCT Linea_Producto FROM Producto"
            params = []
            if tipo_producto:
                query += " WHERE Tipo_Producto = %s"
                params.append(tipo_producto)
            query += " ORDER BY Linea_Producto"
            cursor.execute(query, tuple(params))
            return {"data": cursor.fetchall()}
    except Exception:
        raise HTTPException(status_code=500, detail="Error al consultar las líneas de producto")
# ===================================================================


# ===================================================================
# ===== MODIFICACIÓN #3: AÑADIDO FILTRO A /productos/ =====
# ===================================================================
@router.get("/productos/", response_model=schemas.ListaProductosResponse)
def listar_productos_endpoint(
    tipo_producto: Optional[str] = None, # <-- NUEVO FILTRO OPCIONAL
    linea_producto: Optional[str] = None,
    tratamiento: Optional[str] = None,
    db_conexion: mysql.connector.MySQLConnection = Depends(obtener_conexion_db_directa)
):
    try:
        with db_conexion.cursor(dictionary=True) as cursor:
            query = "SELECT * FROM Producto"
            params = []
            conditions = []
            
            if tipo_producto:
                conditions.append("Tipo_Producto = %s")
                params.append(tipo_producto)
            
            if linea_producto:
                conditions.append("Linea_Producto = %s")
                params.append(linea_producto)
            
            if tratamiento:
                conditions.append("Tratamiento = %s")
                params.append(tratamiento)
            
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
                
            query += " ORDER BY Referencia"
            cursor.execute(query, tuple(params))
            return {"data": cursor.fetchall()}
    except Exception:
        raise HTTPException(status_code=500, detail="Error al consultar productos")
# ===================================================================

@router.get("/tipos_paro/", response_model=schemas.ListaTiposParoResponse)
def listar_tipos_paro_endpoint(db_conexion: mysql.connector.MySQLConnection = Depends(obtener_conexion_db_directa)):
    try:
        with db_conexion.cursor(dictionary=True) as cursor:
            cursor.execute("SELECT ID_TP, Tipo_De_Paro FROM Tipo_Paro ORDER BY ID_TP")
            return {"data": cursor.fetchall()}
    except Exception: raise HTTPException(status_code=500, detail="Error al consultar tipos de paro")

@router.get("/descripciones_paro/", response_model=schemas.ListaDescripcionesParoResponse)
def listar_descripciones_paro_endpoint(id_proceso: str, id_tipo_paro: str, db_conexion: mysql.connector.MySQLConnection = Depends(obtener_conexion_db_directa)):
    try:
        with db_conexion.cursor(dictionary=True) as cursor:
            query = "SELECT * FROM Descripcion_Paro WHERE (ID_Proceso = %s OR ID_Proceso = '08') AND ID_TP = %s ORDER BY ID_Paro"
            cursor.execute(query, (id_proceso, id_tipo_paro))
            return {"data": cursor.fetchall()}
    except Exception: raise HTTPException(status_code=500, detail="Error al consultar descripciones de paro")

@router.get("/usuarios/", response_model=schemas.ListaUsuariosResponse)
def listar_usuarios_endpoint(db_conexion: mysql.connector.MySQLConnection = Depends(obtener_conexion_db_directa)):
    try:
        with db_conexion.cursor(dictionary=True) as cursor:
            cursor.execute("SELECT ID_Usuario, Nombre, Rol, Estado FROM Usuario WHERE Estado = 'Activo' ORDER BY Nombre")
            return {"data": cursor.fetchall()}
    except Exception: raise HTTPException(status_code=500, detail="Error al consultar usuarios")

@router.get("/turnos/", response_model=schemas.ListaTurnosResponse)
def listar_turnos_endpoint(db_conexion: mysql.connector.MySQLConnection = Depends(obtener_conexion_db_directa)):
    try:
        with db_conexion.cursor(dictionary=True) as cursor:
            cursor.execute("SELECT ID_Turno, Nombre_Turno, Hora_Inicio, Hora_Fin FROM Turno ORDER BY ID_Turno")
            return {"data": convert_timedelta_to_time(cursor.fetchall(), ['Hora_Inicio', 'Hora_Fin'])}
    except Exception: raise HTTPException(status_code=500, detail="Error al consultar turnos")