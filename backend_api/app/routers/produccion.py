# produccion_app/backend_api/app/routers/produccion.py (COMPLETO Y VERIFICADO)
from fastapi import APIRouter, HTTPException, Depends, status
import mysql.connector
import traceback
from datetime import datetime, time, timedelta 
from decimal import Decimal, ROUND_HALF_UP

from ..database import obtener_conexion_db_directa
from .. import schemas 
from ..routers.auth import get_current_active_user

router = APIRouter(
    prefix="/produccion",
    tags=["Gestión de Producción KPI"]
)

def calcular_y_actualizar_indicadores(db_conn: mysql.connector.MySQLConnection, cursor: mysql.connector.cursor.MySQLCursorDict, id_registro_kpi: int):
    print(f"DEBUG INDICADORES: Iniciando cálculo para ID_Registro_KPI = {id_registro_kpi}")
    
    cursor.execute("SELECT * FROM Registro_KPI WHERE ID_Registro = %s", (id_registro_kpi,))
    kpi = cursor.fetchone()

    if not kpi or kpi.get("Hora_Finalización") is None or kpi.get("Hora_Inicio") is None:
        print(f"DEBUG INDICADORES: No se calculan para KPI {id_registro_kpi}, datos insuficientes o no finalizado.")
        return

    hora_inicio_kpi_obj = kpi["Hora_Inicio"]
    hora_fin_kpi_obj = kpi["Hora_Finalización"]

    if isinstance(hora_inicio_kpi_obj, timedelta):
        total_seconds = int(hora_inicio_kpi_obj.total_seconds())
        h,m,s = (total_seconds // 3600) % 24, (total_seconds // 60) % 60, total_seconds % 60
        hora_inicio_kpi_obj = time(h,m,s)
    elif isinstance(hora_inicio_kpi_obj, str): 
        try: hora_inicio_kpi_obj = time.fromisoformat(hora_inicio_kpi_obj)
        except ValueError:
            print(f"Advertencia: Formato de Hora_Inicio inválido '{kpi['Hora_Inicio']}' para KPI {id_registro_kpi}. No se calcularán indicadores."); return

    if isinstance(hora_fin_kpi_obj, timedelta):
        total_seconds = int(hora_fin_kpi_obj.total_seconds())
        h,m,s = (total_seconds // 3600) % 24, (total_seconds // 60) % 60, total_seconds % 60
        hora_fin_kpi_obj = time(h,m,s)
    elif isinstance(hora_fin_kpi_obj, str):
        try: hora_fin_kpi_obj = time.fromisoformat(hora_fin_kpi_obj)
        except ValueError:
            print(f"Advertencia: Formato de Hora_Finalización inválido '{kpi['Hora_Finalización']}' para KPI {id_registro_kpi}. No se calcularán indicadores."); return

    fecha_kpi = kpi["Fecha"] 
    datetime_inicio = datetime.combine(fecha_kpi, hora_inicio_kpi_obj)
    datetime_fin = datetime.combine(fecha_kpi, hora_fin_kpi_obj)

    if datetime_fin < datetime_inicio: 
        datetime_fin += timedelta(days=1)
    
    diff_seconds = (datetime_fin - datetime_inicio).total_seconds()
    tiempo_bruto_registrado_min = Decimal(diff_seconds / 60) if diff_seconds >= 0 else Decimal(0)

    paros_programados_registrados_min = kpi.get("Paros_Programados", Decimal(0)) or Decimal(0)

    tiempo_disponible_para_producir_min = tiempo_bruto_registrado_min - paros_programados_registrados_min
    tiempo_disponible_para_producir_min = max(Decimal(0), tiempo_disponible_para_producir_min)

    paros_alistamiento = kpi.get("Paros_Alistamiento", Decimal(0)) or Decimal(0)
    paros_calidad = kpi.get("Paros_Calidad", Decimal(0)) or Decimal(0)
    paros_averias = kpi.get("Paros_Averias", Decimal(0)) or Decimal(0)
    paros_organizacion = kpi.get("Paros_Organizacion", Decimal(0)) or Decimal(0)
    tiempo_paros_noplaneados_min = paros_alistamiento + paros_calidad + paros_averias + paros_organizacion

    tiempo_operativo_real_min = tiempo_disponible_para_producir_min - tiempo_paros_noplaneados_min
    tiempo_operativo_real_min = max(Decimal(0), tiempo_operativo_real_min)

    disponibilidad_oee = None
    if tiempo_disponible_para_producir_min > 0:
        disponibilidad_oee = (tiempo_operativo_real_min / tiempo_disponible_para_producir_min)
        disponibilidad_oee = disponibilidad_oee.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
    elif tiempo_operativo_real_min == 0 and tiempo_disponible_para_producir_min == 0:
        disponibilidad_oee = Decimal("1.0000")

    cantidad_conforme = kpi.get("Cantidad_Conforme", Decimal(0)) or Decimal(0)
    retal_proceso = kpi.get("Retal_Proceso", Decimal(0)) or Decimal(0)
    
    total_piezas_evaluables_calidad = cantidad_conforme + retal_proceso 

    calidad_oee = None
    if total_piezas_evaluables_calidad > 0:
        calidad_oee = (cantidad_conforme / total_piezas_evaluables_calidad)
        calidad_oee = calidad_oee.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
    elif cantidad_conforme > 0 and retal_proceso == 0: 
        calidad_oee = Decimal("1.0000")

    rendimiento_oee = None
    oee_general = None
    
    if disponibilidad_oee is not None and calidad_oee is not None and rendimiento_oee is not None:
       oee_general = (disponibilidad_oee * rendimiento_oee * calidad_oee).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
    
    update_query = """
        UPDATE Registro_KPI
        SET 
            Tiempo_Bruto_Turno_Registrado_Min = %(tiempo_bruto)s,
            Tiempo_Disponible_Para_Producir_Min = %(tiempo_disp_prod)s,
            Tiempo_Paros_NoPlaneados_Min = %(paros_noplan)s,
            Tiempo_Operativo_Real_Min = %(tiempo_oper_real)s,
            Disponibilidad_OEE = %(disponibilidad)s,
            Calidad_OEE = %(calidad)s,
            Rendimiento_OEE = %(rendimiento)s,
            OEE_General = %(oee)s
        WHERE ID_Registro = %(id_kpi)s
    """
    params = {
        "tiempo_bruto": tiempo_bruto_registrado_min,
        "tiempo_disp_prod": tiempo_disponible_para_producir_min,
        "paros_noplan": tiempo_paros_noplaneados_min,
        "tiempo_oper_real": tiempo_operativo_real_min,
        "disponibilidad": disponibilidad_oee,
        "calidad": calidad_oee,
        "rendimiento": rendimiento_oee, 
        "oee": oee_general,             
        "id_kpi": id_registro_kpi
    }
    cursor.execute(update_query, params)
    print(f"DEBUG INDICADORES: KPI {id_registro_kpi} actualizado con: Bruto={tiempo_bruto_registrado_min}, DispProd={tiempo_disponible_para_producir_min}, ParosNoPlan={tiempo_paros_noplaneados_min}, OperReal={tiempo_operativo_real_min}, Disp={disponibilidad_oee}, Cal={calidad_oee}")

@router.post("/registros_kpi/iniciar", response_model=schemas.RegistroKPIResponse, status_code=status.HTTP_201_CREATED)
async def iniciar_registro_kpi(
    datos_inicio: schemas.RegistroKPIIniciar,
    current_user: schemas.UsuarioInDB = Depends(get_current_active_user),
    db_conexion: mysql.connector.MySQLConnection = Depends(obtener_conexion_db_directa)
):
    print(f"DEBUG KPI INICIO: Usuario {current_user.ID_Usuario}, Datos: {datos_inicio.dict()}")
    cursor = None
    try:
        if not db_conexion or not db_conexion.is_connected():
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Error de conexión a BD.")
        cursor = db_conexion.cursor(dictionary=True)

        query_verificar_maquina = """
            SELECT ID_Registro, ID_Usuario, Hora_Inicio 
            FROM Registro_KPI 
            WHERE ID_Maquina = %s AND Hora_Finalización IS NULL
        """
        cursor.execute(query_verificar_maquina, (datos_inicio.ID_Maquina,))
        registro_activo_existente = cursor.fetchone()

        if registro_activo_existente:
            nombre_usuario_activo = "Desconocido"
            id_usuario_activo = registro_activo_existente.get("ID_Usuario")
            if id_usuario_activo:
                cursor.execute("SELECT Nombre FROM Usuario WHERE ID_Usuario = %s", (id_usuario_activo,))
                usuario_info = cursor.fetchone()
                if usuario_info:
                    nombre_usuario_activo = usuario_info.get("Nombre", "Desconocido")
            
            hora_inicio_activa_td = registro_activo_existente.get("Hora_Inicio")
            hora_inicio_activa_str = ""
            if isinstance(hora_inicio_activa_td, timedelta):
                 total_seconds = int(hora_inicio_activa_td.total_seconds())
                 h,m,s = (total_seconds // 3600) % 24, (total_seconds // 60) % 60, total_seconds % 60
                 hora_inicio_activa_str = time(h, m, s).strftime("%H:%M:%S")
            elif isinstance(hora_inicio_activa_td, time):
                 hora_inicio_activa_str = hora_inicio_activa_td.strftime("%H:%M:%S")
            elif isinstance(hora_inicio_activa_td, str):
                try:
                    dt_obj = datetime.strptime(hora_inicio_activa_td, "%H:%M:%S")
                    hora_inicio_activa_str = dt_obj.strftime("%H:%M:%S")
                except ValueError:
                    hora_inicio_activa_str = str(hora_inicio_activa_td)
            mensaje_error = (
                f"La máquina {datos_inicio.ID_Maquina} ya tiene un turno activo (ID Reg: {registro_activo_existente['ID_Registro']}) "
                f"iniciado por {nombre_usuario_activo} a las {hora_inicio_activa_str}. "
                "Finalice el turno actual antes de iniciar uno nuevo."
            )
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=mensaje_error)
        
        query_turno = "SELECT Hora_Inicio FROM Turno WHERE ID_Turno = %s"
        cursor.execute(query_turno, (datos_inicio.ID_Turno,))
        turno_info = cursor.fetchone()

        if not turno_info:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Turno con ID '{datos_inicio.ID_Turno}' no encontrado.")
        
        hora_inicio_bd = turno_info['Hora_Inicio']
        
        hora_inicio_para_insertar = hora_inicio_bd
        if isinstance(hora_inicio_bd, timedelta):
            total_seconds = int(hora_inicio_bd.total_seconds())
            h,m,s = (total_seconds // 3600) % 24, (total_seconds // 60) % 60, total_seconds % 60
            hora_inicio_para_insertar = time(h, m, s)
        
        query_insert = """
            INSERT INTO Registro_KPI (
                Fecha, Referencia, ID_Usuario, ID_Maquina, ID_Proceso, Turno, Hora_Inicio, 
                Cantidad_Conforme, Cantidad_Unidades, Numero_Capas, 
                Retal_Proceso, Retal_Merma, 
                Paros_Alistamiento, Paros_Programados, Paros_Calidad, Paros_Averias, Paros_Organizacion
            ) VALUES (
                %(Fecha)s, %(Referencia)s, %(ID_Usuario)s, %(ID_Maquina)s, %(ID_Proceso)s, 
                %(ID_Turno)s, %(Hora_Inicio_Calculada)s, 
                0.0, 0, %(Numero_Capas)s, 
                0.0, 0.0, 
                0.0, 0.0, 0.0, 0.0, 0.0 
            )
        """
        datos_para_db = datos_inicio.dict()
        datos_para_db["ID_Usuario"] = current_user.ID_Usuario
        datos_para_db["Hora_Inicio_Calculada"] = hora_inicio_para_insertar
        
        if datos_para_db.get("Numero_Capas") is None:
            datos_para_db["Numero_Capas"] = 1 

        cursor.execute(query_insert, datos_para_db)
        db_conexion.commit()
        id_nuevo_registro = cursor.lastrowid
        print(f"DEBUG KPI INICIO: Registro KPI iniciado con ID: {id_nuevo_registro}. Hora_Finalización es NULL.")
        
        query_select = "SELECT * FROM Registro_KPI WHERE ID_Registro = %s"
        cursor.execute(query_select, (id_nuevo_registro,))
        registro_creado_dict = cursor.fetchone()
        if not registro_creado_dict:
            raise HTTPException(status_code=500, detail="No se pudo recuperar el registro KPI recién creado.")
        
        if registro_creado_dict.get('Hora_Finalización') is None:
            registro_creado_dict['Hora_Finalización'] = None 

        for time_field in ["Hora_Inicio", "Hora_Finalización"]: 
            if registro_creado_dict.get(time_field) and isinstance(registro_creado_dict[time_field], timedelta):
                total_seconds = int(registro_creado_dict[time_field].total_seconds())
                h,m,s = (total_seconds // 3600) % 24, (total_seconds // 60) % 60, total_seconds % 60
                registro_creado_dict[time_field] = time(h,m,s)
        
        return schemas.RegistroKPIResponse(**registro_creado_dict)

    except mysql.connector.Error as db_error:
        print(f"ERROR MYSQL (iniciar_registro_kpi): {db_error}"); traceback.print_exc()
        if db_conexion and db_conexion.is_connected(): db_conexion.rollback()
        if db_error.errno == 1452: raise HTTPException(status_code=409, detail=f"Error de FK: {db_error.msg}")
        raise HTTPException(status_code=500, detail=f"Error DB: {db_error.msg}")
    except HTTPException: 
        if db_conexion and db_conexion.is_connected() and hasattr(db_conexion, 'in_transaction') and db_conexion.in_transaction:
            print("DEBUG KPI INICIO: Rollback debido a HTTPException durante posible transacción.")
            db_conexion.rollback()
        raise
    except Exception as e:
        print(f"ERROR GENERAL (iniciar_registro_kpi): {e}"); traceback.print_exc()
        if db_conexion and db_conexion.is_connected(): db_conexion.rollback()
        raise HTTPException(status_code=500, detail="Error inesperado.")
    finally:
        if cursor: cursor.close()

@router.put("/registros_kpi/{id_registro_kpi}/agregar_rollo", response_model=schemas.RegistroKPIResponse)
async def agregar_rollo_a_kpi(
    id_registro_kpi: int,
    rollo_data: schemas.AgregarRolloData,
    current_user: schemas.UsuarioInDB = Depends(get_current_active_user),
    db_conexion: mysql.connector.MySQLConnection = Depends(obtener_conexion_db_directa)
):
    print(f"DEBUG KPI AGREGAR_ROLLO: ID_Registro={id_registro_kpi}, Usuario={current_user.ID_Usuario}, Peso={rollo_data.peso_rollo}")
    cursor = None
    try:
        if not db_conexion or not db_conexion.is_connected():
            raise HTTPException(status_code=503, detail="Error de conexión a BD.")
        cursor = db_conexion.cursor(dictionary=True)

        cursor.execute("SELECT Hora_Finalización FROM Registro_KPI WHERE ID_Registro = %s", (id_registro_kpi,))
        kpi_estado = cursor.fetchone()
        if not kpi_estado:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Registro KPI con ID {id_registro_kpi} no encontrado.")
        if kpi_estado['Hora_Finalización'] is not None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"No se puede agregar rollo. El Registro KPI ID {id_registro_kpi} ya está finalizado.")

        # --- INICIO DE LA MODIFICACIÓN ---
        # Se actualiza el nombre de la columna a Cantidad_Unidades
        query_update = """
            UPDATE Registro_KPI
            SET
                Cantidad_Conforme = Cantidad_Conforme + %(peso_rollo)s,
                Cantidad_Unidades = Cantidad_Unidades + 1 
            WHERE ID_Registro = %(id_registro_kpi)s; 
        """ 
        # --- FIN DE LA MODIFICACIÓN ---

        params_update = {"peso_rollo": rollo_data.peso_rollo, "id_registro_kpi": id_registro_kpi}
        cursor.execute(query_update, params_update)
        
        if cursor.rowcount == 0:
             db_conexion.rollback()
             raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Registro KPI con ID {id_registro_kpi} no encontrado durante la actualización (inesperado).")

        db_conexion.commit()
        print(f"DEBUG KPI AGREGAR_ROLLO: Rollo agregado a KPI ID: {id_registro_kpi}")
        
        query_select = "SELECT * FROM Registro_KPI WHERE ID_Registro = %s"
        cursor.execute(query_select, (id_registro_kpi,))
        registro_actualizado_dict = cursor.fetchone()
        if not registro_actualizado_dict:
            raise HTTPException(status_code=500, detail="No se pudo recuperar el registro KPI actualizado.")
        for time_field in ["Hora_Inicio", "Hora_Finalización"]:
            if registro_actualizado_dict.get(time_field) and isinstance(registro_actualizado_dict[time_field], timedelta):
                total_seconds = int(registro_actualizado_dict[time_field].total_seconds())
                h,m,s = (total_seconds // 3600) % 24, (total_seconds // 60) % 60, total_seconds % 60
                registro_actualizado_dict[time_field] = time(h,m,s)
        return schemas.RegistroKPIResponse(**registro_actualizado_dict)
    except mysql.connector.Error as db_error:
        print(f"ERROR MYSQL (agregar_rollo_a_kpi): {db_error}"); traceback.print_exc()
        if db_conexion and db_conexion.is_connected(): db_conexion.rollback()
        raise HTTPException(status_code=500, detail=f"Error DB: {db_error.msg}")
    except HTTPException:
        if db_conexion and db_conexion.is_connected() and hasattr(db_conexion, 'in_transaction') and db_conexion.in_transaction:
            db_conexion.rollback()
        raise
    except Exception as e:
        print(f"ERROR GENERAL (agregar_rollo_a_kpi): {e}"); traceback.print_exc()
        if db_conexion and db_conexion.is_connected(): db_conexion.rollback()
        raise HTTPException(status_code=500, detail="Error inesperado.")
    finally:
        if cursor: cursor.close()

@router.put("/registros_kpi/{id_registro_kpi}/registrar_paquetes", response_model=schemas.RegistroKPIResponse)
async def registrar_paquetes_a_kpi(
    id_registro_kpi: int,
    paquetes_data: schemas.RegistrarPaquetesData,
    current_user: schemas.UsuarioInDB = Depends(get_current_active_user),
    db_conexion: mysql.connector.MySQLConnection = Depends(obtener_conexion_db_directa)
):
    print(f"DEBUG KPI REGISTRAR_PAQUETES: ID_Registro={id_registro_kpi}, Usuario={current_user.ID_Usuario}, CantPaquetes={paquetes_data.cantidad_paquetes}")
    cursor = None
    try:
        if not db_conexion or not db_conexion.is_connected():
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Error de conexión a BD.")
        
        cursor = db_conexion.cursor(dictionary=True)

        cursor.execute("SELECT Referencia, Hora_Finalización FROM Registro_KPI WHERE ID_Registro = %s", (id_registro_kpi,))
        kpi_info = cursor.fetchone()
        if not kpi_info:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Registro KPI con ID {id_registro_kpi} no encontrado.")
        
        if kpi_info['Hora_Finalización'] is not None: 
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"No se pueden registrar paquetes. El Registro KPI ID {id_registro_kpi} ya está finalizado.")

        referencia_kpi = kpi_info["Referencia"]

        cursor.execute("SELECT Peso_Paquete FROM Producto WHERE Referencia = %s", (referencia_kpi,))
        producto_info = cursor.fetchone()
        if not producto_info or producto_info.get("Peso_Paquete") is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Producto con Referencia {referencia_kpi} o su Peso_Paquete no encontrado/válido en la tabla Producto.")
        
        peso_paquete_bd = producto_info["Peso_Paquete"]
        
        if not isinstance(peso_paquete_bd, Decimal) or peso_paquete_bd <= 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Peso_Paquete para la Referencia {referencia_kpi} no es válido ({peso_paquete_bd}).")

        cantidad_conforme_a_sumar = Decimal(paquetes_data.cantidad_paquetes) * peso_paquete_bd

        # --- MODIFICACIÓN AQUÍ ---
        query_update = """
            UPDATE Registro_KPI
            SET
                Cantidad_Conforme = Cantidad_Conforme + %(cantidad_conforme)s,
                Cantidad_Unidades = Cantidad_Unidades + %(cantidad_paquetes)s
            WHERE ID_Registro = %(id_registro_kpi)s; 
        """ 
        params_update = {
            "cantidad_conforme": cantidad_conforme_a_sumar,
            "cantidad_paquetes": paquetes_data.cantidad_paquetes,
            "id_registro_kpi": id_registro_kpi
        }
        
        cursor.execute(query_update, params_update)

        if cursor.rowcount == 0: 
            db_conexion.rollback()
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Registro KPI con ID {id_registro_kpi} no encontrado durante la actualización.")
        
        db_conexion.commit()
        print(f"DEBUG KPI REGISTRAR_PAQUETES: Paquetes registrados para KPI ID: {id_registro_kpi}. Sumado a conforme: {cantidad_conforme_a_sumar}. Sumado a conteo de unidades: {paquetes_data.cantidad_paquetes}")

        cursor.execute("SELECT * FROM Registro_KPI WHERE ID_Registro = %s", (id_registro_kpi,))
        registro_actualizado_dict = cursor.fetchone()
        if not registro_actualizado_dict:
            raise HTTPException(status_code=500, detail="No se pudo recuperar el registro KPI actualizado después de registrar paquetes.")
        
        for time_field in ["Hora_Inicio", "Hora_Finalización"]:
            if registro_actualizado_dict.get(time_field) and isinstance(registro_actualizado_dict[time_field], timedelta):
                total_seconds = int(registro_actualizado_dict[time_field].total_seconds())
                h,m,s = (total_seconds // 3600) % 24, (total_seconds // 60) % 60, total_seconds % 60
                registro_actualizado_dict[time_field] = time(h,m,s)
        
        return schemas.RegistroKPIResponse(**registro_actualizado_dict)

    except mysql.connector.Error as db_error:
        print(f"ERROR MYSQL (registrar_paquetes_a_kpi): {db_error}"); traceback.print_exc()
        if db_conexion and db_conexion.is_connected(): db_conexion.rollback()
        raise HTTPException(status_code=500, detail=f"Error DB al registrar paquetes: {db_error.msg}")
    except HTTPException: 
        if db_conexion and db_conexion.is_connected() and hasattr(db_conexion, 'in_transaction') and db_conexion.in_transaction:
            db_conexion.rollback()
        raise
    except Exception as e:
        print(f"ERROR GENERAL (registrar_paquetes_a_kpi): {type(e).__name__} - {e}"); traceback.print_exc()
        if db_conexion and db_conexion.is_connected(): db_conexion.rollback()
        raise HTTPException(status_code=500, detail="Error inesperado al registrar paquetes.")
    finally:
        if cursor: cursor.close()
        print("DEBUG KPI REGISTRAR_PAQUETES: Finalizando endpoint.")

@router.get("/registros_kpi/{id_registro_kpi}", response_model=schemas.RegistroKPIResponse)
async def obtener_registro_kpi(
    id_registro_kpi: int,
    current_user: schemas.UsuarioInDB = Depends(get_current_active_user), 
    db_conexion: mysql.connector.MySQLConnection = Depends(obtener_conexion_db_directa)
):
    print(f"DEBUG KPI OBTENER: Solicitando KPI ID: {id_registro_kpi} por Usuario: {current_user.ID_Usuario}")
    cursor = None
    try:
        if not db_conexion or not db_conexion.is_connected():
            raise HTTPException(status_code=503, detail="Error de conexión a BD.")
        cursor = db_conexion.cursor(dictionary=True)
        query_select = "SELECT * FROM Registro_KPI WHERE ID_Registro = %s"
        cursor.execute(query_select, (id_registro_kpi,))
        registro_dict = cursor.fetchone()
        if not registro_dict:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Registro KPI con ID {id_registro_kpi} no encontrado.")
        
        for time_field in ["Hora_Inicio", "Hora_Finalización"]:
            if registro_dict.get(time_field) and isinstance(registro_dict[time_field], timedelta):
                total_seconds = int(registro_dict[time_field].total_seconds())
                h,m,s = (total_seconds // 3600) % 24, (total_seconds // 60) % 60, total_seconds % 60
                registro_dict[time_field] = time(h,m,s)
        
        return schemas.RegistroKPIResponse(**registro_dict)
    except mysql.connector.Error as db_error: 
        print(f"ERROR MYSQL (obtener_registro_kpi): {db_error}"); traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error DB: {db_error.msg}")
    except HTTPException:
        raise
    except Exception as e:
        print(f"ERROR GENERAL (obtener_registro_kpi): {e}"); traceback.print_exc()
        raise HTTPException(status_code=500, detail="Error inesperado al obtener registro KPI.")
    finally:
        if cursor: cursor.close()

@router.put("/registros_kpi/{id_registro_kpi}/finalizar", response_model=schemas.RegistroKPIResponse)
async def finalizar_registro_kpi(
    id_registro_kpi: int,
    datos_finales: schemas.RegistroKPIFinalizarData, # Este schema ya no tiene 'Observaciones'
    current_user: schemas.UsuarioInDB = Depends(get_current_active_user),
    db_conexion: mysql.connector.MySQLConnection = Depends(obtener_conexion_db_directa)
):
    print(f"DEBUG KPI FINALIZAR (Operario): ID_Registro={id_registro_kpi}, Usuario={current_user.ID_Usuario}, Datos={datos_finales.dict()}")
    cursor = None
    try:
        if not db_conexion or not db_conexion.is_connected():
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Error de conexión a BD.")
        cursor = db_conexion.cursor(dictionary=True)
        
        cursor.execute("SELECT Hora_Finalización, Turno FROM Registro_KPI WHERE ID_Registro = %s", (id_registro_kpi,))
        kpi_estado = cursor.fetchone()
        
        if not kpi_estado:
             raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Registro KPI con ID {id_registro_kpi} no encontrado.")
        if kpi_estado['Hora_Finalización'] is not None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"El Registro KPI ID {id_registro_kpi} ya ha sido finalizado.")

        id_turno_del_kpi = kpi_estado['Turno']

        cursor.execute("SELECT Hora_Fin FROM Turno WHERE ID_Turno = %s", (id_turno_del_kpi,))
        turno_info = cursor.fetchone()
        if not turno_info or not turno_info.get('Hora_Fin'):
            raise HTTPException(status_code=404, detail=f"No se encontró la hora de finalización para el turno {id_turno_del_kpi}.")
        
        hora_finalizacion_automatica = turno_info['Hora_Fin']
        
        if isinstance(hora_finalizacion_automatica, timedelta):
            total_seconds = int(hora_finalizacion_automatica.total_seconds())
            h,m,s = (total_seconds // 3600) % 24, (total_seconds // 60) % 60, total_seconds % 60
            hora_finalizacion_automatica = time(h,m,s)

        # --- MODIFICACIÓN CLAVE ---
        set_parts = ["Hora_Finalización = %(Hora_Finalización)s"]
        update_params = {"Hora_Finalización": hora_finalizacion_automatica}

        # Se elimina el bloque 'if datos_finales.Observaciones is not None:'
        
        if datos_finales.Retal_Proceso is not None:
            set_parts.append("Retal_Proceso = %(Retal_Proceso)s")
            update_params["Retal_Proceso"] = datos_finales.Retal_Proceso
        if datos_finales.Retal_Merma is not None:
            set_parts.append("Retal_Merma = %(Retal_Merma)s")
            update_params["Retal_Merma"] = datos_finales.Retal_Merma
        
        query_update_final = f"UPDATE Registro_KPI SET {', '.join(set_parts)} WHERE ID_Registro = %(id_registro_kpi)s" 
        update_params["id_registro_kpi"] = id_registro_kpi
        # --- FIN DE LA MODIFICACIÓN ---
        
        cursor.execute(query_update_final, update_params)
        if cursor.rowcount == 0: 
            db_conexion.rollback()
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Registro KPI con ID {id_registro_kpi} no encontrado para finalizar (inesperado).")
        
        calcular_y_actualizar_indicadores(db_conexion, cursor, id_registro_kpi)

        db_conexion.commit()
        print(f"DEBUG KPI FINALIZAR: Registro KPI ID: {id_registro_kpi} finalizado e indicadores calculados.")
        
        query_select = "SELECT * FROM Registro_KPI WHERE ID_Registro = %s"
        cursor.execute(query_select, (id_registro_kpi,))
        registro_actualizado_dict = cursor.fetchone()
        if not registro_actualizado_dict:
            raise HTTPException(status_code=500, detail="No se pudo recuperar el registro KPI finalizado.")
        
        for time_field in ["Hora_Inicio", "Hora_Finalización"]:
            if registro_actualizado_dict.get(time_field) and isinstance(registro_actualizado_dict[time_field], timedelta):
                total_seconds = int(registro_actualizado_dict[time_field].total_seconds())
                h,m,s = (total_seconds // 3600) % 24, (total_seconds // 60) % 60, total_seconds % 60
                registro_actualizado_dict[time_field] = time(h,m,s)
                
        return schemas.RegistroKPIResponse(**registro_actualizado_dict)
    except mysql.connector.Error as db_error:
        print(f"ERROR MYSQL (finalizar_registro_kpi): {db_error}"); traceback.print_exc()
        if db_conexion and db_conexion.is_connected(): db_conexion.rollback()
        raise HTTPException(status_code=500, detail=f"Error DB: {db_error.msg}")
    except HTTPException:
        if db_conexion and db_conexion.is_connected() and hasattr(db_conexion, 'in_transaction') and db_conexion.in_transaction:
            db_conexion.rollback()
        raise
    except Exception as e:
        print(f"ERROR GENERAL (finalizar_registro_kpi): {e}"); traceback.print_exc()
        if db_conexion and db_conexion.is_connected(): db_conexion.rollback()
        raise HTTPException(status_code=500, detail="Error inesperado.")
    finally:
        if cursor: cursor.close()

@router.put("/registros_kpi/{id_registro_kpi}/forzar_finalizar", response_model=schemas.RegistroKPIResponse)
async def forzar_finalizar_registro_kpi(
    id_registro_kpi: int,
    finalizar_data: schemas.ForzarFinalizarData, # Este schema ahora debe ser 'pass' (vacío)
    current_user: schemas.UsuarioInDB = Depends(get_current_active_user), 
    db_conexion: mysql.connector.MySQLConnection = Depends(obtener_conexion_db_directa)
):
    print(f"DEBUG KPI FORZAR_FINALIZAR: ID_Registro={id_registro_kpi} por Admin={current_user.ID_Usuario}")

    if current_user.Rol.lower() != "administrador": 
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No tiene permisos para forzar la finalización de un turno.")

    cursor = None
    try:
        if not db_conexion or not db_conexion.is_connected():
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Error de conexión a BD.")
        
        cursor = db_conexion.cursor(dictionary=True)

        cursor.execute("SELECT Hora_Finalización FROM Registro_KPI WHERE ID_Registro = %s", (id_registro_kpi,))
        kpi_estado = cursor.fetchone()
        if not kpi_estado:
             raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Registro KPI con ID {id_registro_kpi} no encontrado.")
        
        if kpi_estado['Hora_Finalización'] is not None:
            print(f"INFO KPI FORZAR_FINALIZAR: El Registro KPI ID {id_registro_kpi} ya estaba finalizado. Re-calculando indicadores.")
            calcular_y_actualizar_indicadores(db_conexion, cursor, id_registro_kpi) 
            db_conexion.commit() 
            
            cursor.execute("SELECT * FROM Registro_KPI WHERE ID_Registro = %s", (id_registro_kpi,)) 
            registro_dict = cursor.fetchone()
            if not registro_dict: 
                 raise HTTPException(status_code=500, detail=f"No se pudo re-obtener el Registro KPI ID {id_registro_kpi} ya finalizado.")

            for time_field_loop in ["Hora_Inicio", "Hora_Finalización"]: 
                if registro_dict.get(time_field_loop) and isinstance(registro_dict[time_field_loop], timedelta):
                    total_seconds = int(registro_dict[time_field_loop].total_seconds())
                    h,m,s = (total_seconds // 3600) % 24, (total_seconds // 60) % 60, total_seconds % 60
                    registro_dict[time_field_loop] = time(h,m,s)
            return schemas.RegistroKPIResponse(**registro_dict)

        hora_finalizacion_actual = datetime.now().time() 

        # --- MODIFICACIÓN CLAVE ---
        # Se elimina la creación de 'observacion_final' y la referencia a 'Observaciones' en el UPDATE
        query_update = """
            UPDATE Registro_KPI
            SET Hora_Finalización = %(hora_fin)s
            WHERE ID_Registro = %(id_kpi)s;
        """
        params_update = {
            "hora_fin": hora_finalizacion_actual,
            "id_kpi": id_registro_kpi
        }
        # --- FIN DE LA MODIFICACIÓN ---
        
        cursor.execute(query_update, params_update)
        if cursor.rowcount == 0: 
            db_conexion.rollback()
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"No se pudo actualizar el Registro KPI ID {id_registro_kpi} (inesperado).")

        calcular_y_actualizar_indicadores(db_conexion, cursor, id_registro_kpi)

        db_conexion.commit()
        print(f"DEBUG KPI FORZAR_FINALIZAR: Registro KPI ID {id_registro_kpi} forzado a finalizar e indicadores calculados.")

        cursor.execute("SELECT * FROM Registro_KPI WHERE ID_Registro = %s", (id_registro_kpi,))
        registro_actualizado_dict = cursor.fetchone()
        if not registro_actualizado_dict:
            raise HTTPException(status_code=500, detail="No se pudo recuperar el registro KPI forzado a finalizar.")
        
        for time_field_loop in ["Hora_Inicio", "Hora_Finalización"]: 
            if registro_actualizado_dict.get(time_field_loop) and isinstance(registro_actualizado_dict[time_field_loop], timedelta):
                total_seconds = int(registro_actualizado_dict[time_field_loop].total_seconds())
                h,m,s = (total_seconds // 3600) % 24, (total_seconds // 60) % 60, total_seconds % 60
                registro_actualizado_dict[time_field_loop] = time(h,m,s)
        
        return schemas.RegistroKPIResponse(**registro_actualizado_dict)

    except mysql.connector.Error as db_error:
        print(f"ERROR MYSQL (forzar_finalizar_registro_kpi): {db_error}"); traceback.print_exc()
        if db_conexion and db_conexion.is_connected(): db_conexion.rollback()
        raise HTTPException(status_code=500, detail=f"Error DB: {db_error.msg}")
    except HTTPException:
        if db_conexion and db_conexion.is_connected() and hasattr(db_conexion, 'in_transaction') and db_conexion.in_transaction:
            db_conexion.rollback()
        raise
    except Exception as e:
        print(f"ERROR GENERAL (forzar_finalizar_registro_kpi): {e}"); traceback.print_exc()
        if db_conexion and db_conexion.is_connected(): db_conexion.rollback()
        raise HTTPException(status_code=500, detail="Error inesperado al forzar finalización.")
    finally:
        if cursor: cursor.close()

# Pega este código al final de tu archivo produccion.py

@router.get("/turno_activo_por_usuario/{id_usuario}", response_model=schemas.MaquinaEstadoResponse)
async def obtener_turno_activo_por_usuario(
    id_usuario: str,
    current_user: schemas.UsuarioInDB = Depends(get_current_active_user),
    db_conexion: mysql.connector.MySQLConnection = Depends(obtener_conexion_db_directa)
):
    if id_usuario != current_user.ID_Usuario:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No se puede consultar el estado de otro usuario.")
    
    cursor = None
    try:
        cursor = db_conexion.cursor(dictionary=True)
        # Usamos la misma consulta que el dashboard de administrador
        query = """
            SELECT 
                m.ID_Maquina, m.Maquina, p.Proceso,
                r.ID_Registro AS ID_Registro_KPI,
                r.ID_Usuario AS ID_Usuario_Activo,
                u.Nombre AS Nombre_Usuario_Activo,
                r.Hora_Inicio AS Hora_Inicio_Turno_Activo,
                r.Referencia AS Referencia_Actual
            FROM Maquina m
            JOIN Proceso p ON m.ID_Proceso = p.ID_Proceso
            LEFT JOIN Registro_KPI r ON m.ID_Maquina = r.ID_Maquina AND r.Hora_Finalización IS NULL
            LEFT JOIN Usuario u ON r.ID_Usuario = u.ID_Usuario
            WHERE r.ID_Usuario = %(id_usuario)s
            LIMIT 1;
        """
        cursor.execute(query, {"id_usuario": id_usuario})
        maquina_activa = cursor.fetchone()

        if not maquina_activa:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No se encontró un turno activo para este usuario.")
        
        # Convertir timedelta si es necesario (código de seguridad)
        if maquina_activa.get('Hora_Inicio_Turno_Activo') and isinstance(maquina_activa['Hora_Inicio_Turno_Activo'], timedelta):
            total_seconds = int(maquina_activa['Hora_Inicio_Turno_Activo'].total_seconds())
            h,m,s = (total_seconds // 3600) % 24, (total_seconds // 60) % 60, total_seconds % 60
            maquina_activa['Hora_Inicio_Turno_Activo'] = time(h,m,s)

        return maquina_activa

    except mysql.connector.Error as e:
        traceback.print_exc()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Error de base de datos: {e.msg}")
    finally:
        if cursor:
            cursor.close()

