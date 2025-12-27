#!/bin/bash
# Script para verificar que las credenciales AWS están configuradas correctamente

# Cambiar al directorio raíz del proyecto
cd "$(dirname "$0")/../.."

echo "🔍 Verificando credenciales AWS..."
echo ""

# Verificar AWS CLI
if ! command -v aws &> /dev/null; then
    echo "⚠️  AWS CLI no está instalado"
    echo "   Instala con: brew install awscli (macOS) o pip install awscli"
    echo ""
else
    echo "✅ AWS CLI instalado"
fi

# Verificar credenciales
echo ""
echo "Probando acceso a AWS..."
if aws sts get-caller-identity &> /dev/null; then
    echo "✅ Credenciales funcionando correctamente"
    echo ""
    echo "Información de la cuenta:"
    aws sts get-caller-identity
    echo ""
    echo "✅ Puedes ejecutar: make collect"
else
    echo "❌ Error: No se pueden acceder las credenciales AWS"
    echo ""
    echo "Opciones para configurar:"
    echo "1. AWS CLI: aws configure"
    echo "2. Variables de entorno:"
    echo "   export AWS_ACCESS_KEY_ID=tu-key"
    echo "   export AWS_SECRET_ACCESS_KEY=tu-secret"
    echo "3. Archivo: ~/.aws/credentials"
    echo ""
    echo "Ver más detalles en docs/guides/TROUBLESHOOTING.md"
fi


