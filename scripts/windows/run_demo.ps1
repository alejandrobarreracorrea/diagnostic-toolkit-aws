# Script de demo para ECAD (Windows PowerShell)
# Ejecuta análisis completo con fixtures sin necesidad de AWS

$ErrorActionPreference = "Stop"

$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent (Split-Path -Parent $scriptPath)
Set-Location $projectRoot

$FIXTURES_DIR = "fixtures"
$OUTPUT_DIR = Join-Path $FIXTURES_DIR "outputs"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "ECAD Demo - AWS Cloud Architecture Diagnostic" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Verificar que fixtures existan
if (-not (Test-Path $FIXTURES_DIR)) {
    Write-Host "Error: Directorio fixtures no encontrado: $FIXTURES_DIR" -ForegroundColor Red
    Write-Host "Por favor, crea fixtures mínimos antes de ejecutar el demo." -ForegroundColor Yellow
    exit 1
}

# Verificar que Python esté instalado
try {
    $pythonVersion = python --version 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "Python no encontrado"
    }
} catch {
    Write-Host "Error: Python 3 no encontrado" -ForegroundColor Red
    exit 1
}

# Verificar dependencias
Write-Host "Verificando dependencias..." -ForegroundColor Yellow
try {
    python -c "import boto3, botocore, yaml, jinja2" 2>&1 | Out-Null
    if ($LASTEXITCODE -ne 0) {
        throw "Faltan dependencias"
    }
} catch {
    Write-Host "Error: Faltan dependencias. Ejecuta: pip install -r requirements.txt" -ForegroundColor Red
    exit 1
}

Write-Host "✓ Dependencias OK" -ForegroundColor Green
Write-Host ""

# Crear estructura de directorios si no existe
$dirs = @(
    (Join-Path $FIXTURES_DIR "index"),
    (Join-Path $OUTPUT_DIR "inventory"),
    (Join-Path $OUTPUT_DIR "evidence"),
    (Join-Path $OUTPUT_DIR "reports")
)

foreach ($dir in $dirs) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
    }
}

# Paso 1: Análisis
Write-Host "Paso 1/3: Analizando datos..." -ForegroundColor Yellow
try {
    python -m analyzer.main --run-dir $FIXTURES_DIR
    if ($LASTEXITCODE -ne 0) {
        throw "Error en análisis"
    }
} catch {
    Write-Host "Error en análisis" -ForegroundColor Red
    exit 1
}
Write-Host "✓ Análisis completado" -ForegroundColor Green
Write-Host ""

# Paso 2: Evidence Pack
Write-Host "Paso 2/3: Generando evidence pack..." -ForegroundColor Yellow
try {
    python -m evidence.generator --run-dir $FIXTURES_DIR
    if ($LASTEXITCODE -ne 0) {
        throw "Error generando evidence pack"
    }
} catch {
    Write-Host "Error generando evidence pack" -ForegroundColor Red
    exit 1
}
Write-Host "✓ Evidence pack generado" -ForegroundColor Green
Write-Host ""

# Paso 3: Reportes
Write-Host "Paso 3/3: Generando reportes..." -ForegroundColor Yellow
try {
    python -m analyzer.report_generator --run-dir $FIXTURES_DIR
    if ($LASTEXITCODE -ne 0) {
        throw "Error generando reportes"
    }
} catch {
    Write-Host "Error generando reportes" -ForegroundColor Red
    exit 1
}
Write-Host "✓ Reportes generados" -ForegroundColor Green
Write-Host ""

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Demo completado exitosamente!" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Outputs disponibles en:" -ForegroundColor Cyan
Write-Host "  - Inventarios: $OUTPUT_DIR\inventory\" -ForegroundColor Yellow
Write-Host "  - Evidence Pack: $OUTPUT_DIR\evidence\" -ForegroundColor Yellow
Write-Host "  - Reportes: $OUTPUT_DIR\reports\" -ForegroundColor Yellow
Write-Host ""
Write-Host "Revisa los archivos generados para ver los resultados del demo." -ForegroundColor Cyan


