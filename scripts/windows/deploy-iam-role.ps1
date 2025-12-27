# Script PowerShell para desplegar el stack de CloudFormation de ECAD IAM Role
# Uso: .\scripts\windows\deploy-iam-role.ps1 [opciones]

param(
    [string]$StackName = "ECAD-IAM-Role",
    [string]$RoleName = "ECAD-ReadOnly-Role",
    [string]$AccountId = "",
    [string]$ExternalId = "",
    [string]$PrincipalArn = "",
    [switch]$NoSameAccount,
    [switch]$Update,
    [switch]$Delete,
    [switch]$Status,
    [switch]$Outputs,
    [switch]$Help
)

$ErrorActionPreference = "Stop"

$ScriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent (Split-Path -Parent $ScriptPath)
$TemplateFile = Join-Path $ProjectRoot "policies\ecad-iam-role-cloudformation.yaml"

function Show-Usage {
    Write-Host "Uso: .\deploy-iam-role.ps1 [opciones]" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Opciones:"
    Write-Host "  -StackName NAME       Nombre del stack CloudFormation (default: ECAD-IAM-Role)"
    Write-Host "  -RoleName NAME        Nombre del rol IAM (default: ECAD-ReadOnly-Role)"
    Write-Host "  -AccountId ID         ID de cuenta para cross-account"
    Write-Host "  -ExternalId ID       External ID para seguridad"
    Write-Host "  -PrincipalArn ARN    ARN específico de usuario/rol"
    Write-Host "  -NoSameAccount        No permitir acceso desde la misma cuenta"
    Write-Host "  -Update               Actualizar stack existente"
    Write-Host "  -Delete               Eliminar stack"
    Write-Host "  -Status               Ver estado del stack"
    Write-Host "  -Outputs              Ver outputs del stack"
    Write-Host "  -Help                 Mostrar esta ayuda"
    Write-Host ""
    Write-Host "Ejemplos:"
    Write-Host "  # Desplegar stack básico (misma cuenta)"
    Write-Host "  .\deploy-iam-role.ps1"
    Write-Host ""
    Write-Host "  # Desplegar con External ID"
    Write-Host "  .\deploy-iam-role.ps1 -ExternalId 'mi-secret-id'"
    Write-Host ""
    Write-Host "  # Desplegar cross-account"
    Write-Host "  .\deploy-iam-role.ps1 -AccountId '123456789012' -ExternalId 'mi-secret-id' -NoSameAccount"
}

function Test-AwsCli {
    try {
        $null = aws --version
    } catch {
        Write-Host "Error: AWS CLI no está instalado" -ForegroundColor Red
        Write-Host "Instala con: pip install awscli" -ForegroundColor Yellow
        exit 1
    }
}

function Test-Template {
    if (-not (Test-Path $TemplateFile)) {
        Write-Host "Error: Template no encontrado: $TemplateFile" -ForegroundColor Red
        exit 1
    }
}

function Deploy-Stack {
    $params = @(
        "ParameterKey=RoleName,ParameterValue=$RoleName"
    )
    
    if ($NoSameAccount) {
        $params += "ParameterKey=EnableSameAccountAccess,ParameterValue=false"
    } else {
        $params += "ParameterKey=EnableSameAccountAccess,ParameterValue=true"
    }
    
    if ($AccountId) {
        $params += "ParameterKey=PrincipalAccountId,ParameterValue=$AccountId"
    }
    
    if ($ExternalId) {
        $params += "ParameterKey=ExternalId,ParameterValue=$ExternalId"
    }
    
    if ($PrincipalArn) {
        $params += "ParameterKey=PrincipalArn,ParameterValue=$PrincipalArn"
    }
    
    Write-Host "Desplegando stack: $StackName" -ForegroundColor Green
    Write-Host "Template: $TemplateFile" -ForegroundColor Yellow
    Write-Host ""
    
    if ($Update) {
        Write-Host "Actualizando stack existente..." -ForegroundColor Yellow
        aws cloudformation update-stack `
            --stack-name $StackName `
            --template-body "file://$TemplateFile" `
            --capabilities CAPABILITY_NAMED_IAM `
            --parameters $params
        
        Write-Host "Esperando actualización del stack..." -ForegroundColor Yellow
        aws cloudformation wait stack-update-complete --stack-name $StackName
    } else {
        Write-Host "Creando nuevo stack..." -ForegroundColor Yellow
        aws cloudformation create-stack `
            --stack-name $StackName `
            --template-body "file://$TemplateFile" `
            --capabilities CAPABILITY_NAMED_IAM `
            --parameters $params
        
        Write-Host "Esperando creación del stack (esto puede tardar 1-2 minutos)..." -ForegroundColor Yellow
        aws cloudformation wait stack-create-complete --stack-name $StackName
    }
    
    Write-Host "✅ Stack desplegado exitosamente!" -ForegroundColor Green
    Write-Host ""
    Show-Outputs
}

function Show-Status {
    Write-Host "Estado del stack: $StackName" -ForegroundColor Yellow
    try {
        aws cloudformation describe-stacks `
            --stack-name $StackName `
            --query 'Stacks[0].[StackName,StackStatus,CreationTime]' `
            --output table
    } catch {
        Write-Host "Stack no encontrado" -ForegroundColor Red
    }
}

function Show-Outputs {
    Write-Host "Outputs del stack:" -ForegroundColor Green
    try {
        aws cloudformation describe-stacks `
            --stack-name $StackName `
            --query 'Stacks[0].Outputs' `
            --output table
    } catch {
        Write-Host "No se pudieron obtener outputs" -ForegroundColor Red
    }
}

function Remove-Stack {
    Write-Host "⚠️  ¿Estás seguro de que quieres eliminar el stack $StackName?" -ForegroundColor Yellow
    $confirm = Read-Host "Escribe 'yes' para confirmar"
    if ($confirm -eq "yes") {
        Write-Host "Eliminando stack..." -ForegroundColor Yellow
        aws cloudformation delete-stack --stack-name $StackName
        Write-Host "Esperando eliminación..." -ForegroundColor Yellow
        aws cloudformation wait stack-delete-complete --stack-name $StackName
        Write-Host "✅ Stack eliminado" -ForegroundColor Green
    } else {
        Write-Host "Cancelado" -ForegroundColor Yellow
    }
}

# Main execution
if ($Help) {
    Show-Usage
    exit 0
}

if ($Delete) {
    Test-AwsCli
    Remove-Stack
    exit 0
}

if ($Status) {
    Test-AwsCli
    Show-Status
    exit 0
}

if ($Outputs) {
    Test-AwsCli
    Show-Outputs
    exit 0
}

Test-AwsCli
Test-Template
Deploy-Stack

