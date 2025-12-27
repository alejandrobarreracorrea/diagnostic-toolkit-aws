#!/bin/bash
# Script para desplegar el stack de CloudFormation de ECAD IAM Role
# Uso: ./scripts/deploy-iam-role.sh [opciones]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
TEMPLATE_FILE="$PROJECT_ROOT/policies/ecad-iam-role-cloudformation.yaml"
STACK_NAME="${STACK_NAME:-ECAD-IAM-Role}"
ROLE_NAME="${ROLE_NAME:-ECAD-ReadOnly-Role}"

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

function print_usage() {
    echo "Uso: $0 [opciones]"
    echo ""
    echo "Opciones:"
    echo "  --stack-name NAME       Nombre del stack CloudFormation (default: ECAD-IAM-Role)"
    echo "  --role-name NAME        Nombre del rol IAM (default: ECAD-ReadOnly-Role)"
    echo "  --account-id ID         ID de cuenta para cross-account"
    echo "  --external-id ID         External ID para seguridad"
    echo "  --principal-arn ARN     ARN específico de usuario/rol"
    echo "  --no-same-account       No permitir acceso desde la misma cuenta"
    echo "  --update                 Actualizar stack existente"
    echo "  --delete                 Eliminar stack"
    echo "  --status                 Ver estado del stack"
    echo "  --outputs                Ver outputs del stack"
    echo "  --help                   Mostrar esta ayuda"
    echo ""
    echo "Ejemplos:"
    echo "  # Desplegar stack básico (misma cuenta)"
    echo "  $0"
    echo ""
    echo "  # Desplegar con External ID"
    echo "  $0 --external-id mi-secret-id"
    echo ""
    echo "  # Desplegar cross-account"
    echo "  $0 --account-id 123456789012 --external-id mi-secret-id --no-same-account"
    echo ""
    echo "  # Ver estado"
    echo "  $0 --status"
}

function check_aws_cli() {
    if ! command -v aws &> /dev/null; then
        echo -e "${RED}Error: AWS CLI no está instalado${NC}"
        echo "Instala con: pip install awscli"
        exit 1
    fi
}

function check_template() {
    if [ ! -f "$TEMPLATE_FILE" ]; then
        echo -e "${RED}Error: Template no encontrado: $TEMPLATE_FILE${NC}"
        exit 1
    fi
}

function deploy_stack() {
    local params=()
    params+=("ParameterKey=RoleName,ParameterValue=$ROLE_NAME")
    
    if [ "$ENABLE_SAME_ACCOUNT" = "false" ]; then
        params+=("ParameterKey=EnableSameAccountAccess,ParameterValue=false")
    else
        params+=("ParameterKey=EnableSameAccountAccess,ParameterValue=true")
    fi
    
    if [ -n "$PRINCIPAL_ACCOUNT_ID" ]; then
        params+=("ParameterKey=PrincipalAccountId,ParameterValue=$PRINCIPAL_ACCOUNT_ID")
    fi
    
    if [ -n "$EXTERNAL_ID" ]; then
        params+=("ParameterKey=ExternalId,ParameterValue=$EXTERNAL_ID")
    fi
    
    if [ -n "$PRINCIPAL_ARN" ]; then
        params+=("ParameterKey=PrincipalArn,ParameterValue=$PRINCIPAL_ARN")
    fi
    
    echo -e "${GREEN}Desplegando stack: $STACK_NAME${NC}"
    echo -e "${YELLOW}Template: $TEMPLATE_FILE${NC}"
    echo ""
    
    if [ "$UPDATE" = "true" ]; then
        echo "Actualizando stack existente..."
        aws cloudformation update-stack \
            --stack-name "$STACK_NAME" \
            --template-body "file://$TEMPLATE_FILE" \
            --capabilities CAPABILITY_NAMED_IAM \
            --parameters "${params[@]}"
        
        echo -e "${YELLOW}Esperando actualización del stack...${NC}"
        aws cloudformation wait stack-update-complete --stack-name "$STACK_NAME"
    else
        echo "Creando nuevo stack..."
        aws cloudformation create-stack \
            --stack-name "$STACK_NAME" \
            --template-body "file://$TEMPLATE_FILE" \
            --capabilities CAPABILITY_NAMED_IAM \
            --parameters "${params[@]}"
        
        echo -e "${YELLOW}Esperando creación del stack (esto puede tardar 1-2 minutos)...${NC}"
        aws cloudformation wait stack-create-complete --stack-name "$STACK_NAME"
    fi
    
    echo -e "${GREEN}✅ Stack desplegado exitosamente!${NC}"
    echo ""
    show_outputs
}

function show_status() {
    echo -e "${YELLOW}Estado del stack: $STACK_NAME${NC}"
    aws cloudformation describe-stacks \
        --stack-name "$STACK_NAME" \
        --query 'Stacks[0].[StackName,StackStatus,CreationTime]' \
        --output table 2>/dev/null || echo -e "${RED}Stack no encontrado${NC}"
}

function show_outputs() {
    echo -e "${GREEN}Outputs del stack:${NC}"
    aws cloudformation describe-stacks \
        --stack-name "$STACK_NAME" \
        --query 'Stacks[0].Outputs' \
        --output table 2>/dev/null || echo -e "${RED}No se pudieron obtener outputs${NC}"
}

function delete_stack() {
    echo -e "${YELLOW}⚠️  ¿Estás seguro de que quieres eliminar el stack $STACK_NAME?${NC}"
    read -p "Escribe 'yes' para confirmar: " confirm
    if [ "$confirm" = "yes" ]; then
        echo "Eliminando stack..."
        aws cloudformation delete-stack --stack-name "$STACK_NAME"
        echo -e "${YELLOW}Esperando eliminación...${NC}"
        aws cloudformation wait stack-delete-complete --stack-name "$STACK_NAME"
        echo -e "${GREEN}✅ Stack eliminado${NC}"
    else
        echo "Cancelado"
    fi
}

# Parse arguments
ENABLE_SAME_ACCOUNT="true"
UPDATE="false"

while [[ $# -gt 0 ]]; do
    case $1 in
        --stack-name)
            STACK_NAME="$2"
            shift 2
            ;;
        --role-name)
            ROLE_NAME="$2"
            shift 2
            ;;
        --account-id)
            PRINCIPAL_ACCOUNT_ID="$2"
            shift 2
            ;;
        --external-id)
            EXTERNAL_ID="$2"
            shift 2
            ;;
        --principal-arn)
            PRINCIPAL_ARN="$2"
            shift 2
            ;;
        --no-same-account)
            ENABLE_SAME_ACCOUNT="false"
            shift
            ;;
        --update)
            UPDATE="true"
            shift
            ;;
        --delete)
            check_aws_cli
            delete_stack
            exit 0
            ;;
        --status)
            check_aws_cli
            show_status
            exit 0
            ;;
        --outputs)
            check_aws_cli
            show_outputs
            exit 0
            ;;
        --help)
            print_usage
            exit 0
            ;;
        *)
            echo -e "${RED}Opción desconocida: $1${NC}"
            print_usage
            exit 1
            ;;
    esac
done

# Main execution
check_aws_cli
check_template
deploy_stack

