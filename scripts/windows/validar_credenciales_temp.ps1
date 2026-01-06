# Script para validar credenciales temporales de AWS (SSO/AssumeRole)
# NO guarda ninguna información en archivos

$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent (Split-Path -Parent $scriptPath)
Set-Location $projectRoot

Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host "🔍 VALIDACIÓN DE CREDENCIALES TEMPORALES AWS" -ForegroundColor Cyan
Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host ""

# Verificar variables de entorno
$accessKey = $env:AWS_ACCESS_KEY_ID
$secretKey = $env:AWS_SECRET_ACCESS_KEY
$sessionToken = $env:AWS_SESSION_TOKEN

if (-not $accessKey) {
    Write-Host "❌ AWS_ACCESS_KEY_ID no está configurada" -ForegroundColor Red
    Write-Host ""
    Write-Host "💡 Configura con:" -ForegroundColor Yellow
    Write-Host "   `$env:AWS_ACCESS_KEY_ID='tu-access-key'" -ForegroundColor Cyan
    exit 1
}

if (-not $secretKey) {
    Write-Host "❌ AWS_SECRET_ACCESS_KEY no está configurada" -ForegroundColor Red
    Write-Host ""
    Write-Host "💡 Configura con:" -ForegroundColor Yellow
    Write-Host "   `$env:AWS_SECRET_ACCESS_KEY='tu-secret-key'" -ForegroundColor Cyan
    exit 1
}

if (-not $sessionToken) {
    Write-Host "❌ AWS_SESSION_TOKEN no está configurada" -ForegroundColor Red
    Write-Host ""
    Write-Host "💡 Configura con:" -ForegroundColor Yellow
    Write-Host "   `$env:AWS_SESSION_TOKEN='tu-session-token'" -ForegroundColor Cyan
    exit 1
}

Write-Host "✅ Variables de entorno detectadas:" -ForegroundColor Green
Write-Host "   AWS_ACCESS_KEY_ID: $($accessKey.Substring(0, [Math]::Min(10, $accessKey.Length)))...$($accessKey.Substring($accessKey.Length - 4))" -ForegroundColor Gray
Write-Host "   AWS_SECRET_ACCESS_KEY: $('*' * $secretKey.Length)" -ForegroundColor Gray
Write-Host "   AWS_SESSION_TOKEN: $($sessionToken.Substring(0, [Math]::Min(20, $sessionToken.Length)))...$($sessionToken.Substring($sessionToken.Length - 20))" -ForegroundColor Gray
Write-Host ""

# Verificar con AWS CLI
Write-Host "🔍 Probando conexión con AWS (AWS CLI)..." -ForegroundColor Cyan
try {
    $identity = aws sts get-caller-identity 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ AWS CLI: Credenciales válidas" -ForegroundColor Green
        Write-Host ""
        Write-Host "📋 Información de la cuenta (AWS CLI):" -ForegroundColor Cyan
        Write-Host $identity
        Write-Host ""
    } else {
        Write-Host "❌ AWS CLI: Error validando credenciales" -ForegroundColor Red
        if ($identity) {
            Write-Host "   Detalles: $identity" -ForegroundColor Yellow
        }
        $awsCliOk = $false
    }
} catch {
    Write-Host "❌ AWS CLI: Error: $_" -ForegroundColor Red
    $awsCliOk = $false
}

# Verificar con boto3
Write-Host "🔍 Probando conexión con AWS (boto3)..." -ForegroundColor Cyan
try {
    $pythonScript = @"
import boto3
import os
import json

access_key = os.getenv('AWS_ACCESS_KEY_ID')
secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
session_token = os.getenv('AWS_SESSION_TOKEN')

if not all([access_key, secret_key, session_token]):
    print('ERROR: Variables de entorno no configuradas')
    exit(1)

try:
    session = boto3.Session(
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        aws_session_token=session_token
    )
    sts = session.client('sts')
    identity = sts.get_caller_identity()
    
    print('SUCCESS')
    print(json.dumps(identity, indent=2))
    
    # Verificación adicional
    try:
        ec2 = session.client('ec2', region_name='us-east-1')
        regions = ec2.describe_regions()
        print(f'REGIONS_AVAILABLE: {len(regions.get(\"Regions\", []))}')
    except Exception as e:
        print(f'WARNING: {str(e)}')
    
except Exception as e:
    print(f'ERROR: {str(e)}')
    exit(1)
"@
    
    $boto3Result = python -c $pythonScript 2>&1
    if ($LASTEXITCODE -eq 0 -and $boto3Result -match "SUCCESS") {
        Write-Host "✅ boto3: Credenciales válidas" -ForegroundColor Green
        Write-Host ""
        Write-Host "📋 Información de la cuenta (boto3):" -ForegroundColor Cyan
        # Extraer solo la parte JSON
        $jsonPart = ($boto3Result | Select-String -Pattern '\{.*\}' -AllMatches).Matches[0].Value
        if ($jsonPart) {
            $identityObj = $jsonPart | ConvertFrom-Json
            Write-Host "   Account ID: $($identityObj.Account)" -ForegroundColor White
            Write-Host "   User/Role ARN: $($identityObj.Arn)" -ForegroundColor White
            Write-Host "   User ID: $($identityObj.UserId)" -ForegroundColor White
        }
        
        if ($boto3Result -match "REGIONS_AVAILABLE: (\d+)") {
            $regionCount = $matches[1]
            Write-Host "   Regiones disponibles: $regionCount" -ForegroundColor White
        }
        
        Write-Host ""
        Write-Host "=" * 60 -ForegroundColor Cyan
        Write-Host "✅ VALIDACIÓN EXITOSA" -ForegroundColor Green
        Write-Host "=" * 60 -ForegroundColor Cyan
        Write-Host ""
        Write-Host "💡 Las credenciales están funcionando correctamente." -ForegroundColor Green
        Write-Host "   Puedes usar estas variables de entorno para ejecutar ECAD." -ForegroundColor Green
        Write-Host ""
        Write-Host "⚠️  IMPORTANTE: Estas credenciales son temporales." -ForegroundColor Yellow
        Write-Host "   Si expiran, necesitarás renovarlas (ej: aws sso login)" -ForegroundColor Yellow
        Write-Host ""
    } else {
        Write-Host "❌ boto3: Error validando credenciales" -ForegroundColor Red
        if ($boto3Result) {
            Write-Host "   Detalles: $boto3Result" -ForegroundColor Yellow
            
            if ($boto3Result -match "ExpiredToken|expired") {
                Write-Host ""
                Write-Host "💡 Las credenciales han expirado." -ForegroundColor Yellow
                Write-Host "   Renueva las credenciales (ej: aws sso login)" -ForegroundColor Cyan
            } elseif ($boto3Result -match "InvalidClientTokenId|SignatureDoesNotMatch") {
                Write-Host ""
                Write-Host "💡 Las credenciales son inválidas." -ForegroundColor Yellow
                Write-Host "   Verifica que las variables de entorno estén correctas" -ForegroundColor Cyan
            }
        }
        exit 1
    }
} catch {
    Write-Host "❌ boto3: Error: $_" -ForegroundColor Red
    Write-Host "   Asegúrate de que boto3 esté instalado: pip install boto3" -ForegroundColor Yellow
    exit 1
}

