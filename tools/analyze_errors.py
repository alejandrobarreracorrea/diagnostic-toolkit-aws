#!/usr/bin/env python3
"""
Script para analizar errores en la recolección de datos AWS
"""

import json
import sys
from pathlib import Path
from collections import Counter, defaultdict

def analyze_errors(run_dir: str):
    """Analizar errores en un run."""
    run_path = Path(run_dir)
    index_file = run_path / "index" / "index.json"
    
    if not index_file.exists():
        print(f"❌ No se encontró el índice en {run_dir}")
        return
    
    with open(index_file, 'r') as f:
        idx = json.load(f)
    
    # Analizar errores
    error_codes = Counter()
    error_by_service = defaultdict(list)
    total_errors = 0
    total_operations = 0
    
    permission_errors = []
    throttling_errors = []
    validation_errors = []
    other_errors = []
    
    permission_codes = ['AccessDenied', 'UnauthorizedOperation', 'Forbidden', 'AccessDeniedException']
    throttling_codes = ['Throttling', 'ThrottlingException', 'TooManyRequestsException', 'RateExceeded']
    validation_codes = ['ValidationException', 'InvalidParameterValue', 'MissingParameter']
    
    services_with_permission_errors = {}
    
    for service_name, service_data in idx.get("services", {}).items():
        service_perm_errors = 0
        service_total_errors = 0
        
        for region_name, region_data in service_data.get("regions", {}).items():
            for op_info in region_data.get("operations", []):
                total_operations += 1
                if not op_info.get("success", True) and not op_info.get("not_available", False):
                    total_errors += 1
                    service_total_errors += 1
                    error = op_info.get("error", {})
                    if isinstance(error, dict):
                        error_code = error.get("code", "Unknown")
                        error_message = error.get("message", "")
                        error_codes[error_code] += 1
                        
                        entry = {
                            "service": service_name,
                            "operation": op_info.get("operation"),
                            "code": error_code,
                            "message": error_message[:150]
                        }
                        
                        error_by_service[error_code].append(entry)
                        
                        if error_code in permission_codes:
                            permission_errors.append(entry)
                            service_perm_errors += 1
                        elif error_code in throttling_codes:
                            throttling_errors.append(entry)
                        elif error_code in validation_codes:
                            validation_errors.append(entry)
                        else:
                            other_errors.append(entry)
        
        if service_perm_errors > 0:
            services_with_permission_errors[service_name] = {
                "permission_errors": service_perm_errors,
                "total_errors": service_total_errors
            }
    
    # Mostrar resultados
    print("="*80)
    print("ANÁLISIS DE ERRORES - AWS Cloud Architecture Diagnostic")
    print("="*80)
    print(f"\n📊 ESTADÍSTICAS GENERALES")
    print(f"   Total de operaciones: {total_operations}")
    print(f"   Total de errores: {total_errors}")
    if total_operations > 0:
        print(f"   Tasa de error: {(total_errors/total_operations*100):.1f}%")
    
    print("\n" + "="*80)
    print("🔒 ERRORES DE PERMISOS (Falta de permisos IAM)")
    print("="*80)
    print(f"   Total: {len(permission_errors)} errores")
    if permission_errors:
        print("\n   Estos errores indican que la política IAM no tiene permisos suficientes.")
        print("   Necesitas agregar permisos para estas operaciones en tu política IAM.\n")
        print("   Top 10 servicios con más errores de permisos:")
        service_counts = Counter([e['service'] for e in permission_errors])
        for i, (service, count) in enumerate(service_counts.most_common(10), 1):
            print(f"   {i:2d}. {service:30s} - {count:3d} operaciones sin permisos")
        
        print("\n   Ejemplos de errores:")
        for err in permission_errors[:5]:
            print(f"   - {err['service']}.{err['operation']}: {err['code']}")
            print(f"     {err['message'][:100]}")
    else:
        print("   ✅ No hay errores de permisos")
    
    print("\n" + "="*80)
    print("⏱️  ERRORES DE THROTTLING (Límites de tasa de API)")
    print("="*80)
    print(f"   Total: {len(throttling_errors)} errores")
    if throttling_errors:
        print("\n   Estos errores son NORMALES y no indican un problema.")
        print("   AWS limita la cantidad de llamadas por segundo. El collector")
        print("   tiene retry automático, pero algunos pueden fallar.\n")
        print("   Ejemplos:")
        for err in throttling_errors[:5]:
            print(f"   - {err['service']}.{err['operation']}: {err['code']}")
    else:
        print("   ✅ No hay errores de throttling")
    
    print("\n" + "="*80)
    print("❌ ERRORES DE VALIDACIÓN (Parámetros inválidos)")
    print("="*80)
    print(f"   Total: {len(validation_errors)} errores")
    if validation_errors:
        print("\n   Estos errores indican que la operación requiere parámetros")
        print("   que no se pudieron inferir automáticamente.\n")
        print("   Ejemplos:")
        for err in validation_errors[:5]:
            print(f"   - {err['service']}.{err['operation']}: {err['code']}")
            print(f"     {err['message'][:100]}")
    else:
        print("   ✅ No hay errores de validación")
    
    print("\n" + "="*80)
    print("⚠️  OTROS ERRORES")
    print("="*80)
    print(f"   Total: {len(other_errors)} errores")
    if other_errors:
        error_types = Counter([e['code'] for e in other_errors])
        print("\n   Tipos de errores encontrados:")
        for code, count in error_types.most_common(10):
            print(f"   - {code}: {count} ocurrencias")
            example = next((e for e in other_errors if e['code'] == code), None)
            if example:
                print(f"     Ejemplo: {example['service']}.{example['operation']}")
    
    print("\n" + "="*80)
    print("📋 TOP 15 CÓDIGOS DE ERROR MÁS COMUNES")
    print("="*80)
    for i, (error_code, count) in enumerate(error_codes.most_common(15), 1):
        pct = (count / total_errors * 100) if total_errors > 0 else 0
        print(f"   {i:2d}. {error_code:40s} - {count:4d} ocurrencias ({pct:5.1f}%)")
        if error_by_service.get(error_code):
            example = error_by_service[error_code][0]
            print(f"       Ejemplo: {example['service']}.{example['operation']}")
    
    print("\n" + "="*80)
    print("💡 RECOMENDACIONES")
    print("="*80)
    
    if len(permission_errors) > 0:
        print("\n   1. ERRORES DE PERMISOS:")
        print("      - Revisa la política IAM y agrega permisos para los servicios")
        print("        que muestran errores de AccessDenied")
        print("      - Puedes usar la política recomendada en policies/iam-policy-ecad-part*.json")
        print("      - Algunos servicios pueden requerir permisos adicionales")
    
    if len(throttling_errors) > 0:
        print("\n   2. ERRORES DE THROTTLING:")
        print("      - Estos son normales y no requieren acción")
        print("      - El collector tiene retry automático")
        print("      - Puedes reducir ECAD_MAX_THREADS si hay muchos throttling")
    
    if len(validation_errors) > 0:
        print("\n   3. ERRORES DE VALIDACIÓN:")
        print("      - Algunas operaciones requieren parámetros específicos")
        print("      - El collector intenta inferirlos, pero no siempre es posible")
        print("      - Estos errores son esperados y no afectan el inventario principal")
    
    print("\n" + "="*80)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python3 tools/analyze_errors.py <run_dir>")
        print("Ejemplo: python3 tools/analyze_errors.py runs/run-20251226-111101")
        sys.exit(1)
    
    analyze_errors(sys.argv[1])


