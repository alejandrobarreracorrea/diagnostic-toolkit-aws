@echo off
REM Script para verificar que las credenciales AWS están configuradas correctamente (Windows)

cd /d %~dp0\..\..

echo 🔍 Verificando credenciales AWS...
echo.

REM Verificar AWS CLI
where aws >nul 2>&1
if errorlevel 1 (
    echo ⚠️  AWS CLI no está instalado
    echo    Instala con: pip install awscli
    echo.
) else (
    echo ✅ AWS CLI instalado
)

REM Verificar credenciales
echo.
echo Probando acceso a AWS...
aws sts get-caller-identity >nul 2>&1
if errorlevel 1 (
    echo ❌ Error: No se pueden acceder las credenciales AWS
    echo.
    echo Opciones para configurar:
    echo 1. AWS CLI: aws configure
    echo 2. Variables de entorno:
    echo    set AWS_ACCESS_KEY_ID=tu-key
    echo    set AWS_SECRET_ACCESS_KEY=tu-secret
    echo 3. Archivo: %%USERPROFILE%%\.aws\credentials
    echo.
    echo Ver más detalles en docs\guides\TROUBLESHOOTING.md
) else (
    echo ✅ Credenciales funcionando correctamente
    echo.
    echo Información de la cuenta:
    aws sts get-caller-identity
    echo.
    echo ✅ Puedes ejecutar: scripts\windows\ecad.bat collect
)


