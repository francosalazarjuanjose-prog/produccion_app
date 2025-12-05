# produccion_app/backend_api/app/routers/calidad.py (VERSIÓN FINAL Y DEFINITIVA)

from fastapi import APIRouter, HTTPException, Depends, status
import mysql.connector
import traceback
import json
from decimal import Decimal, InvalidOperation
from typing import List

from ..database import obtener_conexion_db_directa
from .. import schemas
from ..routers.auth import get_current_active_user

router = APIRouter(
    prefix="/calidad",
    tags=["Gestión de Calidad"]
)

# =================================================================================
# FUNCIÓN AUXILIAR PARA CALCULAR RESULTADOS (SIN CAMBIOS)
# =================================================================================
def calcular_resultado_variable(valor_medido_str: str, variable_reglas: dict) -> str:
    tipo_dato = variable_reglas.get('Tipo_Dato')
    if tipo_dato == 'BOOLEANO': return 'CONFORME' if valor_medido_str in ['1', 'true', 'True'] else 'NO_CONFORME'
    if tipo_dato == 'TEXTO' or tipo_dato == 'LISTA': return 'CONFORME'
    if tipo_dato == 'NUMERICO':
        try:
            valor_medido = Decimal(valor_medido_str)
            l_esp_inf = variable_reglas.get('Limite_Especificacion_Inferior'); l_esp_sup = variable_reglas.get('Limite_Especificacion_Superior')
            l_con_inf = variable_reglas.get('Limite_Control_Inferior'); l_con_sup = variable_reglas.get('Limite_Control_Superior')
            
            if l_esp_inf is not None and valor_medido < l_esp_inf: return 'FUERA_ESPECIFICACION_INF'
            if l_esp_sup is not None and valor_medido > l_esp_sup: return 'FUERA_ESPECIFICACION_SUP'
            if l_con_inf is not None and valor_medido < l_con_inf: return 'FUERA_CONTROL_INF'
            if l_con_sup is not None and valor_medido > l_con_sup: return 'FUERA_CONTROL_SUP'
            return 'DENTRO_CONTROL'
        except (InvalidOperation, TypeError): return 'NO_CONFORME'
    return 'NO_CONFORME'


# =================================================================================
# ENDPOINT PARA OBTENER VARIABLES (LÓGICA FINAL Y SIMPLIFICADA)
# =================================================================================
@router.get("/variables_por_proceso/", response_model=schemas.ListaVariablesCalidadResponse, summary="Obtener variables de calidad para un proceso y referencia")
async def obtener_variables_de_calidad(
    id_proceso: str, 
    referencia: str, 
    current_user: schemas.UsuarioInDB = Depends(get_current_active_user), 
    db_conexion: mysql.connector.MySQLConnection = Depends(obtener_conexion_db_directa)
):
    if not db_conexion or not db_conexion.is_connected():
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Error de conexión a la base de datos.")
    
    cursor = None
    try:
        cursor = db_conexion.cursor(dictionary=True)
        
        # 1. Obtener TODAS las reglas candidatas: las específicas de la referencia Y las genéricas del proceso.
        query = """
            SELECT * FROM calidad_maestro_variables
            WHERE (ID_Proceso = %(id_proceso)s AND Referencia = %(referencia)s AND Activo = 1) 
               OR (ID_Proceso = %(id_proceso)s AND Referencia IS NULL AND Activo = 1);
        """
        params = {"id_proceso": id_proceso, "referencia": referencia}
        cursor.execute(query, params)
        todas_las_variables = cursor.fetchall()
        
        # 2. Lógica de "override": si una variable específica y una genérica tienen el mismo nombre, nos quedamos con la específica.
        variables_finales_dict = {}
        for var in todas_las_variables:
            nombre = var['Nombre_Variable']
            # Si el nombre no está en el diccionario, lo añadimos.
            # Si ya está, solo lo reemplazamos si la nueva variable es más específica (tiene Referencia).
            if nombre not in variables_finales_dict or var['Referencia'] is not None:
                variables_finales_dict[nombre] = var
        
        variables_candidatas = list(variables_finales_dict.values())

        # 3. Filtro de LIMPIEZA final y explícito para el caso de Sellado.
        if id_proceso == '06':
            cursor.execute("SELECT Tipo_Sellado FROM Producto WHERE Referencia = %s", (referencia,))
            producto_info = cursor.fetchone()
            tipo_sellado = producto_info.get('Tipo_Sellado') if producto_info else 'N/A'

            variables_filtradas = []
            if tipo_sellado == 'FONDO_CAMISETA':
                # Si es FONDO, nos quedamos con todo EXCEPTO la variable visual/booleana.
                for var in variables_candidatas:
                    if var['Nombre_Variable'] != 'Calidad del Sellado':
                        variables_filtradas.append(var)
                variables_candidatas = variables_filtradas
            
            elif tipo_sellado == 'LATERAL':
                # Si es LATERAL, nos quedamos con todo EXCEPTO la variable de prueba en Kg.
                for var in variables_candidatas:
                    if var['Nombre_Variable'] != 'Resistencia del Sellado':
                        variables_filtradas.append(var)
                variables_candidatas = variables_filtradas
        
        # 4. Procesamiento final
        variables_procesadas = []
        for variable in variables_candidatas:
            if variable.get('Opciones_Lista') and isinstance(variable['Opciones_Lista'], str):
                try: variable['Opciones_Lista'] = json.loads(variable['Opciones_Lista'])
                except json.JSONDecodeError: variable['Opciones_Lista'] = None
            variables_procesadas.append(variable)
            
        return {"data": sorted(variables_procesadas, key=lambda x: x['ID_Variable'])}
        
    finally:
        if cursor: cursor.close()
        if db_conexion and db_conexion.is_connected(): db_conexion.close()


# =================================================================================
# ENDPOINT PARA CREAR INSPECCIONES (SIN CAMBIOS FUNCIONALES)
# =================================================================================
@router.post("/inspecciones/", response_model=schemas.InspeccionResponse, status_code=status.HTTP_201_CREATED, summary="Crear una nueva inspección de calidad")
async def crear_inspeccion_calidad(inspeccion_data: schemas.InspeccionCreate, current_user: schemas.UsuarioInDB = Depends(get_current_active_user), db_conexion: mysql.connector.MySQLConnection = Depends(obtener_conexion_db_directa)):
    if not db_conexion or not db_conexion.is_connected(): raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Error de conexión a BD.")
    cursor = None
    try:
        db_conexion.start_transaction()
        cursor = db_conexion.cursor(dictionary=True)
        
        query_header = "INSERT INTO calidad_inspeccion_header (ID_Registro_KPI, Lote, ID_Usuario) VALUES (%(id_kpi)s, %(lote)s, %(id_usuario)s)"
        params_header = {"id_kpi": inspeccion_data.ID_Registro_KPI, "lote": inspeccion_data.Lote, "id_usuario": current_user.ID_Usuario}
        cursor.execute(query_header, params_header)
        id_nueva_inspeccion = cursor.lastrowid

        resultado_general = 'APROBADO'
        ids_variables = [d.ID_Variable_Calidad for d in inspeccion_data.detalles]
        if not ids_variables:
             raise HTTPException(status_code=400, detail="No se proporcionaron detalles para la inspección.")

        query_reglas = f"SELECT * FROM calidad_maestro_variables WHERE ID_Variable IN ({','.join(['%s'] * len(ids_variables))})"
        cursor.execute(query_reglas, ids_variables)
        reglas_map = {regla['ID_Variable']: regla for regla in cursor.fetchall()}

        for detalle in inspeccion_data.detalles:
            reglas_variable_actual = reglas_map.get(detalle.ID_Variable_Calidad)
            if not reglas_variable_actual: raise HTTPException(status_code=404, detail=f"No se encontraron reglas para ID_Variable {detalle.ID_Variable_Calidad}")
            
            resultado_variable = calcular_resultado_variable(detalle.Valor_Medido, reglas_variable_actual)
            
            query_detalle = "INSERT INTO calidad_inspeccion_detalle (ID_Inspeccion, ID_Variable_Calidad, Valor_Medido, Resultado_Variable) VALUES (%(id_ins)s, %(id_var)s, %(val_med)s, %(res_var)s)"
            params_detalle = {"id_ins": id_nueva_inspeccion, "id_var": detalle.ID_Variable_Calidad, "val_med": detalle.Valor_Medido, "res_var": resultado_variable}
            cursor.execute(query_detalle, params_detalle)

            if resultado_variable.startswith('FUERA_ESPECIFICACION'): resultado_general = 'RECHAZADO'
            elif resultado_variable.startswith('FUERA_CONTROL') and resultado_general != 'RECHAZADO': resultado_general = 'APROBADO_CON_DESVIACION'
            elif resultado_variable == 'NO_CONFORME' and resultado_general != 'RECHAZADO': resultado_general = 'RECHAZADO'

        query_update_header = "UPDATE calidad_inspeccion_header SET Resultado_General = %s WHERE ID_Inspeccion = %s"
        cursor.execute(query_update_header, (resultado_general, id_nueva_inspeccion))
        
        db_conexion.commit()

        cursor.execute("SELECT * FROM calidad_inspeccion_header WHERE ID_Inspeccion = %s", (id_nueva_inspeccion,))
        header_guardado = cursor.fetchone()
        cursor.execute("SELECT * FROM calidad_inspeccion_detalle WHERE ID_Inspeccion = %s", (id_nueva_inspeccion,))
        detalles_guardados = cursor.fetchall()
        
        response_data = header_guardado
        response_data['detalles'] = detalles_guardados
        return response_data
    except mysql.connector.Error as db_error:
        if db_conexion: db_conexion.rollback()
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error de base de datos: {db_error.msg}")
    except Exception as e:
        if db_conexion: db_conexion.rollback()
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error inesperado: {e}")
    finally:
        if cursor: cursor.close()
        if db_conexion and db_conexion.is_connected(): db_conexion.close()