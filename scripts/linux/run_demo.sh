#!/bin/bash
# Script de demo para ECAD
# Ejecuta análisis completo con fixtures sin necesidad de AWS

# Cambiar al directorio raíz del proyecto
cd "$(dirname "$0")/../.."

set -e

FIXTURES_DIR="./fixtures"
OUTPUT_DIR="${FIXTURES_DIR}/outputs"

echo "=========================================="
echo "ECAD Demo - AWS Cloud Architecture Diagnostic"
echo "=========================================="
echo ""

# Verificar que fixtures existan
if [ ! -d "$FIXTURES_DIR" ]; then
    echo "Error: Directorio fixtures no encontrado: $FIXTURES_DIR"
    echo "Por favor, crea fixtures mínimos antes de ejecutar el demo."
    exit 1
fi

# Verificar que Python esté instalado
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 no encontrado"
    exit 1
fi

# Verificar dependencias
echo "Verificando dependencias..."
python3 -c "import boto3, botocore, yaml, jinja2" 2>/dev/null || {
    echo "Error: Faltan dependencias. Ejecuta: pip install -r requirements.txt"
    exit 1
}

echo "✓ Dependencias OK"
echo ""

# Crear estructura de directorios si no existe
mkdir -p "${FIXTURES_DIR}/index"
mkdir -p "${OUTPUT_DIR}/inventory"
mkdir -p "${OUTPUT_DIR}/evidence"
mkdir -p "${OUTPUT_DIR}/reports"

# Paso 1: Análisis
echo "Paso 1/3: Analizando datos..."
python3 -m analyzer.main --run-dir "${FIXTURES_DIR}" || {
    echo "Error en análisis"
    exit 1
}
echo "✓ Análisis completado"
echo ""

# Paso 2: Evidence Pack
echo "Paso 2/3: Generando evidence pack..."
python3 -m evidence.generator --run-dir "${FIXTURES_DIR}" || {
    echo "Error generando evidence pack"
    exit 1
}
echo "✓ Evidence pack generado"
echo ""

# Paso 3: Reportes
echo "Paso 3/3: Generando reportes..."
python3 -m analyzer.report_generator --run-dir "${FIXTURES_DIR}" || {
    echo "Error generando reportes"
    exit 1
}
echo "✓ Reportes generados"
echo ""

echo "=========================================="
echo "Demo completado exitosamente!"
echo "=========================================="
echo ""
echo "Outputs disponibles en:"
echo "  - Inventarios: ${OUTPUT_DIR}/inventory/"
echo "  - Evidence Pack: ${OUTPUT_DIR}/evidence/"
echo "  - Reportes: ${OUTPUT_DIR}/reports/"
echo ""
echo "Revisa los archivos generados para ver los resultados del demo."


