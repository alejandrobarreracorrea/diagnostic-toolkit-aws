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

# Verificar credenciales AWS CLI
Write-Host ""
Write-Host "Probando acceso a AWS (AWS CLI)..." -ForegroundColor Cyan
$awsCliOk = $false
try {
    $identity = aws sts get-caller-identity 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ AWS CLI: Credenciales funcionando correctamente" -ForegroundColor Green
        Write-Host ""
        Write-Host "Información de la cuenta (AWS CLI):" -ForegroundColor Cyan
        Write-Host $identity
        $awsCliOk = $true
    } else {
        Write-Host "❌ AWS CLI: Error de credenciales" -ForegroundColor Red
        if ($identity) {
            Write-Host "   Detalles: $identity" -ForegroundColor Yellow
        }
    }
} catch {
    Write-Host "❌ AWS CLI: Error verificando credenciales: $_" -ForegroundColor Red
}

# Verificar credenciales boto3
Write-Host ""
Write-Host "Probando acceso a AWS (boto3)..." -ForegroundColor Cyan
$boto3Ok = $false
try {
    $pythonCmd = "import boto3; session = boto3.Session(); sts = session.client('sts'); identity = sts.get_caller_identity(); print('Account:', identity.get('Account')); print('Arn:', identity.get('Arn'))"
    $boto3Result = python -c $pythonCmd 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ boto3: Credenciales funcionando correctamente" -ForegroundColor Green
        Write-Host ""
        Write-Host "Información de la cuenta (boto3):" -ForegroundColor Cyan
        Write-Host $boto3Result
        $boto3Ok = $true
    } else {
        Write-Host "❌ boto3: Error de credenciales" -ForegroundColor Red
        if ($boto3Result) {
            Write-Host "   Detalles: $boto3Result" -ForegroundColor Yellow
            if ($boto3Result -match "expired|ExpiredToken") {
                Write-Host ""
                Write-Host "💡 Las credenciales SSO han expirado. Ejecuta:" -ForegroundColor Yellow
                Write-Host "   aws sso login" -ForegroundColor Cyan
            }
        }
    }
} catch {
    Write-Host "❌ boto3: Error verificando credenciales: $_" -ForegroundColor Red
    Write-Host "   Asegúrate de que boto3 esté instalado: pip install boto3" -ForegroundColor Yellow
}

# Resumen
Write-Host ""
Write-Host "=" * 60 -ForegroundColor Cyan
if ($awsCliOk -and $boto3Ok) {
    Write-Host "✅ Todas las verificaciones pasaron - Listo para usar" -ForegroundColor Green
    Write-Host ""
    Write-Host "✅ Puedes ejecutar: .\scripts\windows\ecad.ps1 collect" -ForegroundColor Green
} elseif ($awsCliOk -and -not $boto3Ok) {
    Write-Host "⚠️  AWS CLI funciona pero boto3 no - Puede haber problemas" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "💡 Solución:" -ForegroundColor Yellow
    Write-Host "   1. Verifica que boto3 esté instalado: pip install boto3" -ForegroundColor Cyan
    Write-Host "   2. Si usas SSO, verifica que las credenciales no hayan expirado" -ForegroundColor Cyan
    Write-Host "   3. Si expiraron, ejecuta: aws sso login" -ForegroundColor Cyan
} elseif (-not $awsCliOk -and $boto3Ok) {
    Write-Host "⚠️  boto3 funciona pero AWS CLI no - Debería funcionar" -ForegroundColor Yellow
} else {
    Write-Host "❌ No se pudieron verificar las credenciales" -ForegroundColor Red
    Write-Host ""
    Write-Host "💡 Opciones para configurar:" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "   Para SSO:" -ForegroundColor Cyan
    Write-Host "   1. aws sso login" -ForegroundColor White
    Write-Host "   2. Verifica que ~/.aws/config tiene el perfil SSO configurado" -ForegroundColor White
    Write-Host ""
    Write-Host "   Para credenciales estáticas:" -ForegroundColor Cyan
    Write-Host "   1. AWS CLI: aws configure" -ForegroundColor White
    Write-Host "   2. Variables de entorno:" -ForegroundColor White
    Write-Host "      `$env:AWS_ACCESS_KEY_ID='tu-key'" -ForegroundColor Gray
    Write-Host "      `$env:AWS_SECRET_ACCESS_KEY='tu-secret'" -ForegroundColor Gray
    Write-Host "   3. Archivo: `$env:USERPROFILE\.aws\credentials" -ForegroundColor White
    Write-Host ""
    Write-Host "Ver más detalles en docs\guides\TROUBLESHOOTING.md" -ForegroundColor Yellow
}


