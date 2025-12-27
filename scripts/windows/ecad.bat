@echo off
REM ECAD - Script Batch para Windows
REM Equivalente al Makefile para sistemas Windows

setlocal enabledelayedexpansion

if "%1"=="" (
    echo.
    echo ========================================
    echo   ECAD - Comandos Disponibles
    echo ========================================
    echo.
    echo Uso: ecad.bat [comando] [opciones]
    echo.
    echo Comandos disponibles:
    echo   install          - Instalar dependencias Python
    echo   collect          - Recolectar datos desde AWS
    echo   analyze          - Analizar un run existente
    echo   evidence         - Generar evidence pack
    echo   reports          - Generar todos los reportes
    echo   demo             - Ejecutar demo con fixtures
    echo   clean            - Limpiar archivos temporales
    echo   help             - Mostrar esta ayuda
    echo.
    echo Ejemplos:
    echo   ecad.bat install
    echo   ecad.bat collect
    echo   ecad.bat analyze RUN_DIR=runs\run-20240101-120000
    echo.
    goto :end
)

if "%1"=="install" goto :install
if "%1"=="collect" goto :collect
if "%1"=="analyze" goto :analyze
if "%1"=="evidence" goto :evidence
if "%1"=="reports" goto :reports
if "%1"=="demo" goto :demo
if "%1"=="clean" goto :clean
if "%1"=="help" goto :help

echo Error: Comando desconocido "%1"
echo Ejecuta "ecad.bat help" para ver comandos disponibles
goto :end

:install
echo Instalando dependencias Python...
cd /d %~dp0\..\..
python -m pip install -r requirements.txt
if errorlevel 1 (
    echo Error: No se pudieron instalar las dependencias
    echo Asegurate de tener Python 3.9+ instalado
    exit /b 1
)
echo Dependencias instaladas correctamente
goto :end

:collect
echo Iniciando recoleccion de datos AWS...
cd /d %~dp0\..\..
if "%RUN_DIR%"=="" (
    for /f "tokens=2 delims==" %%I in ('wmic os get localdatetime /value') do set datetime=%%I
    set RUN_DIR=runs\run-!datetime:~0,8!-!datetime:~8,6!
)
echo Run directory: %RUN_DIR%
if not exist "%RUN_DIR%\raw" mkdir "%RUN_DIR%\raw"
if "%ECAD_MAX_THREADS%"=="" set ECAD_MAX_THREADS=20
if "%ECAD_MAX_PAGES%"=="" set ECAD_MAX_PAGES=100
python -m collector.main --output-dir "%RUN_DIR%" --max-threads %ECAD_MAX_THREADS% --max-pages %ECAD_MAX_PAGES%
goto :end

:analyze
cd /d %~dp0\..\..
if "%RUN_DIR%"=="" (
    echo Error: RUN_DIR no especificado
    echo Uso: ecad.bat analyze RUN_DIR=runs\run-YYYYMMDD-HHMMSS
    exit /b 1
)
echo Analizando run: %RUN_DIR%
python -m analyzer.main --run-dir "%RUN_DIR%"
goto :end

:evidence
cd /d %~dp0\..\..
if "%RUN_DIR%"=="" (
    echo Error: RUN_DIR no especificado
    echo Uso: ecad.bat evidence RUN_DIR=runs\run-YYYYMMDD-HHMMSS
    exit /b 1
)
echo Generando evidence pack para: %RUN_DIR%
python -m evidence.generator --run-dir "%RUN_DIR%"
goto :end

:reports
cd /d %~dp0\..\..
if "%RUN_DIR%"=="" (
    echo Error: RUN_DIR no especificado
    echo Uso: ecad.bat reports RUN_DIR=runs\run-YYYYMMDD-HHMMSS
    exit /b 1
)
echo Generando reportes para: %RUN_DIR%
python -m analyzer.report_generator --run-dir "%RUN_DIR%"
goto :end

:demo
cd /d %~dp0\..\..
echo Ejecutando demo con fixtures...
if not exist "fixtures\outputs" mkdir "fixtures\outputs"
python -m analyzer.main --run-dir fixtures
python -m evidence.generator --run-dir fixtures
python -m analyzer.report_generator --run-dir fixtures
echo Demo completado. Revisa fixtures\outputs\
goto :end

:clean
cd /d %~dp0\..\..
echo Limpiando archivos temporales...
for /d /r . %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d" 2>nul
for /r . %%f in (*.pyc) do @if exist "%%f" del /q "%%f" 2>nul
for /r . %%f in (*.pyo) do @if exist "%%f" del /q "%%f" 2>nul
for /d /r . %%d in (*.egg-info) do @if exist "%%d" rd /s /q "%%d" 2>nul
echo Limpieza completada
goto :end

:help
echo.
echo ========================================
echo   ECAD - Comandos Disponibles
echo ========================================
echo.
echo   install          - Instalar dependencias Python
echo   collect          - Recolectar datos desde AWS
echo   analyze          - Analizar un run existente
echo   evidence         - Generar evidence pack
echo   reports          - Generar todos los reportes
echo   demo             - Ejecutar demo con fixtures
echo   clean            - Limpiar archivos temporales
echo.
echo Variables de entorno opcionales:
echo   ECAD_MAX_THREADS - Numero de threads (default: 20)
echo   ECAD_MAX_PAGES   - Maximo de paginas (default: 100)
echo   RUN_DIR          - Directorio del run para analizar
echo.
goto :end

:end
endlocal


