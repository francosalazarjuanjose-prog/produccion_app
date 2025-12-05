# produccion_app/backend_api/app/schemas.py (VERSIÓN FINAL SIN OBSERVACIONES)
from pydantic import BaseModel, Field
from datetime import date, time, datetime 
from decimal import Decimal
from typing import Optional, List 

# --- Schemas para Registro_KPI ---
class RegistroKPIIniciar(BaseModel):
    Fecha: date; Referencia: str; ID_Maquina: str; ID_Proceso: str; ID_Turno: str; Numero_Capas: Optional[int] = 1
    class Config: from_attributes = True

class RegistroKPIResponse(BaseModel):
    ID_Registro: int; Fecha: date; Referencia: str; ID_Usuario: str; ID_Maquina: str; ID_Proceso: str; Turno: str; Hora_Inicio: time; Hora_Finalización: Optional[time] = None; Cantidad_Conforme: Decimal; Cantidad_Unidades: int; Numero_Capas: int; Retal_Proceso: Decimal; Retal_Merma: Decimal
    Paros_Alistamiento: Optional[Decimal] = None; Paros_Programados: Optional[Decimal] = None; Paros_Calidad: Optional[Decimal] = None; Paros_Averias: Optional[Decimal] = None; Paros_Organizacion: Optional[Decimal] = None
    # 'Observaciones' ha sido eliminado de aquí.
    Tiempo_Bruto_Turno_Registrado_Min: Optional[Decimal] = None; Tiempo_Disponible_Para_Producir_Min: Optional[Decimal] = None; Tiempo_Paros_NoPlaneados_Min: Optional[Decimal] = None; Tiempo_Operativo_Real_Min: Optional[Decimal] = None
    Disponibilidad_OEE: Optional[Decimal] = None; Calidad_OEE: Optional[Decimal] = None; Rendimiento_OEE: Optional[Decimal] = None; OEE_General: Optional[Decimal] = None
    class Config: from_attributes = True

class AgregarRolloData(BaseModel):
    peso_rollo: Decimal = Field(..., gt=0)

class RegistrarPaquetesData(BaseModel):
    cantidad_paquetes: int = Field(..., ge=1)

class RegistroKPIFinalizarData(BaseModel): 
    # 'Observaciones' ha sido eliminado de aquí.
    Retal_Proceso: Optional[Decimal] = None
    Retal_Merma: Optional[Decimal] = None

class ForzarFinalizarData(BaseModel):
    # 'Observaciones' ha sido eliminado de aquí. Pasa a ser un modelo vacío si no se necesita nada más.
    pass
        
# --- Schemas para Paros_Maquina ---
class ParoMaquinaCreate(BaseModel):
    ID_Registro_KPI: int; Fecha: date; Referencia: str; ID_Maquina: str; ID_Proceso: str; Turno: str; ID_TP: str; ID_Paro: str; Tiempo_Paro: Decimal

class ParoMaquinaResponse(ParoMaquinaCreate): 
    ID_Paro_Maquina: int; ID_Usuario: str 

# --- Schemas para Usuario y Autenticación ---
class UsuarioInDB(BaseModel): 
    ID_Usuario: str; Nombre: str; Rol: str; Estado: str; Contraseña: int; Cedula: int; Telefono: str; Correo: Optional[str] = None
    class Config: from_attributes = True

class UsuarioResponse(BaseModel): 
    ID_Usuario: str; Nombre: str; Rol: str; Estado: Optional[str] = None
    class Config: from_attributes = True
    
class Token(BaseModel):
    access_token: str; token_type: str

class TokenData(BaseModel): 
    username: Optional[str] = None; rol: Optional[str] = None; nombre_usuario: Optional[str] = None
    
# --- Schemas de Respuesta para Datos Maestros ---
class ProcesoResponse(BaseModel):
    ID_Proceso: str; Proceso: str
    class Config: from_attributes = True

class MaquinaResponse(BaseModel): 
    ID_Maquina: str; Maquina: str; ID_Proceso: str 
    class Config: from_attributes = True

class MaquinaEstadoResponse(BaseModel):
    ID_Maquina: str; Maquina: str; Proceso: str; ID_Registro_KPI: Optional[int] = None; ID_Usuario_Activo: Optional[str] = None; Nombre_Usuario_Activo: Optional[str] = None; Hora_Inicio_Turno_Activo: Optional[time] = None; Referencia_Actual: Optional[str] = None
    class Config: from_attributes = True

class ListaMaquinasEstadoResponse(BaseModel):
    data: List[MaquinaEstadoResponse]

class ProductoResponse(BaseModel): 
    Referencia: str; Largo: Decimal; Ancho: Decimal; Calibre: Decimal; Diseño_Perforado: str; Linea_Producto: str; Peso_Paquete: Decimal
    Tratamiento: str
    Tipo_Sellado: str # Añadido para que esté disponible en la API
    Tipo_Producto: str # Añadido para que esté disponible en la API
    class Config: from_attributes = True

class LineaProductoResponse(BaseModel):
    Linea_Producto: str
    class Config: from_attributes = True

class ListaLineasProductoResponse(BaseModel):
    data: List[LineaProductoResponse]

class TipoParoResponse(BaseModel): 
    ID_TP: str; Tipo_De_Paro: str 
    class Config: from_attributes = True

class DescripcionParoResponse(BaseModel): 
    ID_Paro: str; ID_Proceso: str; Descripcion_Paro: str; ID_TP: str
    class Config: from_attributes = True

class TurnoResponse(BaseModel):
    ID_Turno: str; Nombre_Turno: str; Hora_Inicio: time; Hora_Fin: time
    class Config: from_attributes = True

# --- Schemas para Listas de Datos Maestros ---
class ListaProcesosResponse(BaseModel): data: List[ProcesoResponse]
class ListaMaquinasResponse(BaseModel): data: List[MaquinaResponse]
class ListaProductosResponse(BaseModel): data: List[ProductoResponse]
class ListaTiposParoResponse(BaseModel): data: List[TipoParoResponse]
class ListaDescripcionesParoResponse(BaseModel): data: List[DescripcionParoResponse]
class ListaTurnosResponse(BaseModel): data: List[TurnoResponse]
class ListaUsuariosResponse(BaseModel): data: List[UsuarioResponse]

# --- Schemas para Inspección de Calidad (SIN OBSERVACIONES) ---
class VariableCalidadResponse(BaseModel):
    ID_Variable: int; ID_Proceso: str; Referencia: Optional[str] = None; Nombre_Variable: str; Tipo_Dato: str; Unidad_Medida: Optional[str] = None; Valor_Esperado: Optional[Decimal] = None; Limite_Control_Inferior: Optional[Decimal] = None; Limite_Control_Superior: Optional[Decimal] = None; Limite_Especificacion_Inferior: Optional[Decimal] = None; Limite_Especificacion_Superior: Optional[Decimal] = None; Opciones_Lista: Optional[List[str]] = None
    class Config: from_attributes = True

class DetalleInspeccionCreate(BaseModel):
    ID_Variable_Calidad: int
    Valor_Medido: str

class InspeccionCreate(BaseModel):
    ID_Registro_KPI: int
    Lote: str
    Observaciones_Generales: Optional[str] = None # Mantenemos observaciones para Calidad
    detalles: List[DetalleInspeccionCreate]

class DetalleInspeccionResponse(DetalleInspeccionCreate):
    ID_Detalle: int; ID_Inspeccion: int; Resultado_Variable: Optional[str] = None
    class Config: from_attributes = True

class InspeccionResponse(BaseModel):
    ID_Inspeccion: int; ID_Registro_KPI: int; Lote: str; ID_Usuario: str; Fecha_Hora_Inspeccion: datetime; Resultado_General: str
    Observaciones_Generales: Optional[str] = None # Mantenemos observaciones para Calidad
    detalles: List[DetalleInspeccionResponse]
    class Config: from_attributes = True

class ListaVariablesCalidadResponse(BaseModel): data: List[VariableCalidadResponse]
class ListaInspeccionesResponse(BaseModel): data: List[InspeccionResponse]