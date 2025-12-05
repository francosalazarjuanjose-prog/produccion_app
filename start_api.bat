@echo off
REM --- Script de arranque para el servicio de la API de Produccion ---

REM Establece la unidad de disco y navega a la carpeta del proyecto
C:
cd C:\proyectos\produccion_app

REM Activa el entorno virtual. 'call' es crucial.
call .\.venv\Scripts\activate.bat

REM Inicia el servidor Uvicorn.
echo Iniciando servidor Uvicorn...
uvicorn backend_api.app.main:app --host 0.0.0.0 --port 8000