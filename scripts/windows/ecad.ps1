# ECAD - Script PowerShell para Windows
# Equivalente al Makefile para sistemas Windows (PowerShell)

param(
    [Parameter(Position=0)]
    [string]$Command = "",
    
    [Parameter()]
    [string]$RunDir = ""
)

$ErrorActionPreference = "Stop"

# Cambiar al directorio raíz del proyecto
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent (Split-Path -Parent $scriptPath)
Set-Location $projectRoot

function Show-Help {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "  ECAD - Comandos Disponibles" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Uso: .\ecad.ps1 [comando] [opciones]"
    Write-Host ""
    Write-Host "Comandos disponibles:"
    Write-Host "  install          - Instalar dependencias Python"
    Write-Host "  collect          - Recolectar datos desde AWS"
    Write-Host "  analyze          - Analizar un run existente"
    Write-Host "  evidence         - Generar evidence pack"
    Write-Host "  reports          - Generar todos los reportes"
    Write-Host "  demo             - Ejecutar demo con fixtures"
    Write-Host "  clean            - Limpiar archivos temporales"
    Write-Host "  help             - Mostrar esta ayuda"
    Write-Host ""
    Write-Host "Ejemplos:"
    Write-Host "  .\ecad.ps1 install"
    Write-Host "  .\ecad.ps1 collect"
    Write-Host "  .\ecad.ps1 analyze -RunDir runs\run-20240101-120000"
    Write-Host ""
}

function Install-Dependencies {
    Write-Host "Instalando dependencias Python..." -ForegroundColor Yellow
    python -m pip install -r requirements.txt
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Error: No se pudieron instalar las dependencias" -ForegroundColor Red
        Write-Host "Asegurate de tener Python 3.9+ instalado" -ForegroundColor Red
        exit 1
    }
    Write-Host "Dependencias instaladas correctamente" -ForegroundColor Green
}

function Start-Collection {
    Write-Host "Iniciando recolección de datos AWS..." -ForegroundColor Yellow
    
    if ([string]::IsNullOrEmpty($env:RUN_DIR)) {
        $runDir = python -c "from collector.run_dir import get_run_dir; print(get_run_dir())"
        if ($LASTEXITCODE -ne 0) {
            $timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
            $runDir = "runs\run-$timestamp"
        }
        $runDir = $runDir -replace "/", "\"
    } else {
        $runDir = $env:RUN_DIR
    }
    
    Write-Host "Run directory: $runDir" -ForegroundColor Cyan
    
    $rawDir = Join-Path $runDir "raw"
    if (-not (Test-Path $rawDir)) {
        New-Item -ItemType Directory -Path $rawDir -Force | Out-Null
    }
    
    $maxThreads = if ($env:ECAD_MAX_THREADS) { $env:ECAD_MAX_THREADS } else { "20" }
    $maxPages = if ($env:ECAD_MAX_PAGES) { $env:ECAD_MAX_PAGES } else { "100" }
    
    python -m collector.main --output-dir $runDir --max-threads $maxThreads --max-pages $maxPages
}

function Start-Analysis {
    $runDir = if ($RunDir) { $RunDir } elseif ($env:RUN_DIR) { $env:RUN_DIR } else { "" }
    
    if ([string]::IsNullOrEmpty($runDir)) {
        Write-Host "Error: RUN_DIR no especificado" -ForegroundColor Red
        Write-Host "Uso: .\ecad.ps1 analyze -RunDir runs\run-YYYYMMDD-HHMMSS" -ForegroundColor Yellow
        exit 1
    }
    
    Write-Host "Analizando run: $runDir" -ForegroundColor Yellow
    python -m analyzer.main --run-dir $runDir
}

function Start-Evidence {
    $runDir = if ($RunDir) { $RunDir } elseif ($env:RUN_DIR) { $env:RUN_DIR } else { "" }
    
    if ([string]::IsNullOrEmpty($runDir)) {
        Write-Host "Error: RUN_DIR no especificado" -ForegroundColor Red
        Write-Host "Uso: .\ecad.ps1 evidence -RunDir runs\run-YYYYMMDD-HHMMSS" -ForegroundColor Yellow
        exit 1
    }
    
    Write-Host "Generando evidence pack para: $runDir" -ForegroundColor Yellow
    python -m evidence.generator --run-dir $runDir
}

function Start-Reports {
    $runDir = if ($RunDir) { $RunDir } elseif ($env:RUN_DIR) { $env:RUN_DIR } else { "" }
    
    if ([string]::IsNullOrEmpty($runDir)) {
        Write-Host "Error: RUN_DIR no especificado" -ForegroundColor Red
        Write-Host "Uso: .\ecad.ps1 reports -RunDir runs\run-YYYYMMDD-HHMMSS" -ForegroundColor Yellow
        exit 1
    }
    
    Write-Host "Generando reportes para: $runDir" -ForegroundColor Yellow
    python -m analyzer.report_generator --run-dir $runDir
}

function Start-Demo {
    Write-Host "Ejecutando demo con fixtures..." -ForegroundColor Yellow
    
    $outputDir = "fixtures\outputs"
    if (-not (Test-Path $outputDir)) {
        New-Item -ItemType Directory -Path $outputDir -Force | Out-Null
    }
    
    python -m analyzer.main --run-dir fixtures
    python -m evidence.generator --run-dir fixtures
    python -m analyzer.report_generator --run-dir fixtures
    
    Write-Host "Demo completado. Revisa fixtures\outputs\" -ForegroundColor Green
}

function Start-Clean {
    Write-Host "Limpiando archivos temporales..." -ForegroundColor Yellow
    
    Get-ChildItem -Path . -Recurse -Directory -Filter "__pycache__" | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
    Get-ChildItem -Path . -Recurse -File -Filter "*.pyc" | Remove-Item -Force -ErrorAction SilentlyContinue
    Get-ChildItem -Path . -Recurse -File -Filter "*.pyo" | Remove-Item -Force -ErrorAction SilentlyContinue
    Get-ChildItem -Path . -Recurse -Directory -Filter "*.egg-info" | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
    
    Write-Host "Limpieza completada" -ForegroundColor Green
}

# Main
if ([string]::IsNullOrEmpty($Command)) {
    Show-Help
    exit 0
}

switch ($Command.ToLower()) {
    "install" { Install-Dependencies }
    "collect" { Start-Collection }
    "analyze" { Start-Analysis }
    "evidence" { Start-Evidence }
    "reports" { Start-Reports }
    "demo" { Start-Demo }
    "clean" { Start-Clean }
    "help" { Show-Help }
    default {
        Write-Host "Error: Comando desconocido '$Command'" -ForegroundColor Red
        Write-Host "Ejecuta '.\ecad.ps1 help' para ver comandos disponibles" -ForegroundColor Yellow
        exit 1
    }
}


