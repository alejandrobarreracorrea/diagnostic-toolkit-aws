@echo off
REM Script de demo para ECAD (Windows)
REM Ejecuta análisis completo con fixtures sin necesidad de AWS

cd /d %~dp0\..\..

setlocal enabledelayedexpansion

set FIXTURES_DIR=fixtures
set OUTPUT_DIR=%FIXTURES_DIR%\outputs

echo ==========================================
echo ECAD Demo - AWS Cloud Architecture Diagnostic
echo ==========================================
echo.

REM Verificar que fixtures existan
if not exist "%FIXTURES_DIR%" (
    echo Error: Directorio fixtures no encontrado: %FIXTURES_DIR%
    echo Por favor, crea fixtures mínimos antes de ejecutar el demo.
    exit /b 1
)

REM Verificar que Python esté instalado
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python 3 no encontrado
    exit /b 1
)

REM Verificar dependencias
echo Verificando dependencias...
python -c "import boto3, botocore, yaml, jinja2" 2>nul
if errorlevel 1 (
    echo Error: Faltan dependencias. Ejecuta: pip install -r requirements.txt
    exit /b 1
)

echo ✓ Dependencias OK
echo.

REM Crear estructura de directorios si no existe
if not exist "%FIXTURES_DIR%\index" mkdir "%FIXTURES_DIR%\index"
if not exist "%OUTPUT_DIR%\inventory" mkdir "%OUTPUT_DIR%\inventory"
if not exist "%OUTPUT_DIR%\evidence" mkdir "%OUTPUT_DIR%\evidence"
if not exist "%OUTPUT_DIR%\reports" mkdir "%OUTPUT_DIR%\reports"

REM Paso 1: Análisis
echo Paso 1/3: Analizando datos...
python -m analyzer.main --run-dir "%FIXTURES_DIR%"
if errorlevel 1 (
    echo Error en análisis
    exit /b 1
)
echo ✓ Análisis completado
echo.

REM Paso 2: Evidence Pack
echo Paso 2/3: Generando evidence pack...
python -m evidence.generator --run-dir "%FIXTURES_DIR%"
if errorlevel 1 (
    echo Error generando evidence pack
    exit /b 1
)
echo ✓ Evidence pack generado
echo.

REM Paso 3: Reportes
echo Paso 3/3: Generando reportes...
python -m analyzer.report_generator --run-dir "%FIXTURES_DIR%"
if errorlevel 1 (
    echo Error generando reportes
    exit /b 1
)
echo ✓ Reportes generados
echo.

echo ==========================================
echo Demo completado exitosamente!
echo ==========================================
echo.
echo Outputs disponibles en:
echo   - Inventarios: %OUTPUT_DIR%\inventory\
echo   - Evidence Pack: %OUTPUT_DIR%\evidence\
echo   - Reportes: %OUTPUT_DIR%\reports\
echo.
echo Revisa los archivos generados para ver los resultados del demo.

endlocal


