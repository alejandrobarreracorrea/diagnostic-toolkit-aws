# Script para verificar que las credenciales AWS están configuradas correctamente (Windows PowerShell)

$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent (Split-Path -Parent $scriptPath)
Set-Location $projectRoot

Write-Host "🔍 Verificando credenciales AWS..." -ForegroundColor Cyan
Write-Host ""

# Verificar AWS CLI
$awsCli = Get-Command aws -ErrorAction SilentlyContinue
if (-not $awsCli) {
    Write-Host "⚠️  AWS CLI no está instalado" -ForegroundColor Yellow
    Write-Host "   Instala con: pip install awscli" -ForegroundColor Yellow
    Write-Host ""
} else {
    Write-Host "✅ AWS CLI instalado" -ForegroundColor Green
}

# Verificar credenciales
Write-Host ""
Write-Host "Probando acceso a AWS..." -ForegroundColor Cyan
try {
    $identity = aws sts get-caller-identity 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Credenciales funcionando correctamente" -ForegroundColor Green
        Write-Host ""
        Write-Host "Información de la cuenta:" -ForegroundColor Cyan
        Write-Host $identity
        Write-Host ""
        Write-Host "✅ Puedes ejecutar: .\scripts\windows\ecad.ps1 collect" -ForegroundColor Green
    } else {
        throw "Error de credenciales"
    }
} catch {
    Write-Host "❌ Error: No se pueden acceder las credenciales AWS" -ForegroundColor Red
    Write-Host ""
    Write-Host "Opciones para configurar:" -ForegroundColor Yellow
    Write-Host "1. AWS CLI: aws configure"
    Write-Host "2. Variables de entorno:"
    Write-Host "   `$env:AWS_ACCESS_KEY_ID='tu-key'"
    Write-Host "   `$env:AWS_SECRET_ACCESS_KEY='tu-secret'"
    Write-Host "3. Archivo: `$env:USERPROFILE\.aws\credentials"
    Write-Host ""
    Write-Host "Ver más detalles en docs\guides\TROUBLESHOOTING.md" -ForegroundColor Yellow
}


