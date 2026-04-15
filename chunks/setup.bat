@echo off
REM Script para configurar y ejecutar el semantic chunking en Windows

echo ========================================
echo Semantic Chunking Script Setup
echo ========================================

REM Verificar si Python está instalado
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python no está instalado o no está en PATH
    pause
    exit /b 1
)

echo.
echo [1] Ejecutando setup...
python setup.py

echo.
echo [2] Instalando dependencias (si es necesario)...
pip install -r requirements.txt

echo.
echo [3] Listo para ejecutar el script
echo.
echo Para procesar las lecciones, ejecuta:
echo   python chunk_transcripts.py
echo.
pause
