#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para analizar específicamente los errores de EC2.
"""

import json
import sys
from pathlib import Path
from collections import Counter, defaultdict

# Configurar codificación UTF-8 para Windows
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from tools.validate_iam_policies import (
    is_read_operation, 
    operation_to_iam_permission,
    find_latest_run,
    load_json_file,
    check_permission_covered
)

def main():
    print("="*80)
    print("🔍 ANÁLISIS DETALLADO: ERRORES DE EC2")
    print("="*80)
    
    # Cargar políticas
    policy1_file = project_root / "policies" / "iam-policy-ecad-part1.json"
    policy2_file = project_root / "policies" / "iam-policy-ecad-part2.json"
    policy3_file = project_root / "policies" / "iam-policy-ecad-part3.json"
    
    policy1 = load_json_file(policy1_file) if policy1_file.exists() else None
    policy2 = load_json_file(policy2_file) if policy2_file.exists() else None
    policy3 = load_json_file(policy3_file) if policy3_file.exists() else None
    
    all_policy_permissions = set()
    if policy1:
        for stmt in policy1.get("Statement", []):
            actions = stmt.get("Action", [])
            if isinstance(actions, str):
                all_policy_permissions.add(actions)
            else:
                all_policy_permissions.update(actions)
    
    if policy2:
        for stmt in policy2.get("Statement", []):
            actions = stmt.get("Action", [])
            if isinstance(actions, str):
                all_policy_permissions.add(actions)
            else:
                all_policy_permissions.update(actions)
    
    if policy3:
        for stmt in policy3.get("Statement", []):
            actions = stmt.get("Action", [])
            if isinstance(actions, str):
                all_policy_permissions.add(actions)
            else:
                all_policy_permissions.update(actions)
    
    # Verificar permisos de EC2 en políticas
    ec2_perms = [p for p in all_policy_permissions if p.startswith('ec2:')]
    print(f"\n📋 Permisos de EC2 en políticas: {len(ec2_perms)}")
    for perm in sorted(ec2_perms):
        print(f"   - {perm}")
    
    # Encontrar último run
    run_dir = find_latest_run()
    if not run_dir:
        print("\n❌ No se encontraron runs disponibles")
        return
    
    index_file = run_dir / "index" / "index.json"
    if not index_file.exists():
        print(f"\n❌ No se encontró índice en {run_dir.name}")
        return
    
    idx = load_json_file(index_file)
    if not idx:
        return
    
    service_name = 'ec2'
    if service_name not in idx.get("services", {}):
        print(f"\n❌ Servicio {service_name} no encontrado en el índice")
        return
    
    print(f"\n{'='*80}")
    print(f"🔸 ANÁLISIS DE {service_name.upper()}")
    print(f"{'='*80}")
    
    service_data = idx.get("services", {}).get(service_name, {})
    
    # Analizar todas las operaciones
    total_ops = 0
    successful_ops = 0
    failed_ops = 0
    permission_errors = []
    other_errors = []
    write_operation_errors = []
    
    permission_codes = ['AccessDenied', 'UnauthorizedOperation', 'Forbidden', 'AccessDeniedException']
    
    for region_name, region_data in service_data.get("regions", {}).items():
        for op_info in region_data.get("operations", []):
            total_ops += 1
            op_name = op_info.get("operation", "")
            
            if op_info.get("success", True):
                successful_ops += 1
            else:
                failed_ops += 1
                if not op_info.get("not_available", False):
                    error = op_info.get("error", {})
                    if isinstance(error, dict):
                        error_code = error.get("code", "")
                        error_message = error.get("message", "")
                        
                        # Verificar si es operación de escritura
                        if not is_read_operation(op_name):
                            write_operation_errors.append({
                                "operation": op_name,
                                "error_code": error_code,
                                "error_message": error_message[:150]
                            })
                        elif error_code in permission_codes:
                            perm = operation_to_iam_permission(service_name, op_name)
                            is_covered = check_permission_covered(perm, all_policy_permissions)
                            
                            permission_errors.append({
                                "operation": op_name,
                                "permission": perm,
                                "covered": is_covered,
                                "error_code": error_code,
                                "error_message": error_message[:150],
                                "region": region_name
                            })
                        else:
                            other_errors.append({
                                "operation": op_name,
                                "error_code": error_code,
                                "error_message": error_message[:150],
                                "region": region_name
                            })
    
    print(f"\n📊 ESTADÍSTICAS:")
    print(f"   Total de operaciones: {total_ops}")
    print(f"   Operaciones exitosas: {successful_ops} ({successful_ops/total_ops*100:.1f}%)" if total_ops > 0 else "   Operaciones exitosas: 0")
    print(f"   Operaciones fallidas: {failed_ops} ({failed_ops/total_ops*100:.1f}%)" if total_ops > 0 else "   Operaciones fallidas: 0")
    print(f"   ⚠️  Errores de operaciones de ESCRITURA: {len(write_operation_errors)}")
    print(f"   🔒 Errores de permisos en operaciones de LECTURA: {len(permission_errors)}")
    print(f"   ⚠️  Otros errores: {len(other_errors)}")
    
    if write_operation_errors:
        print(f"\n{'='*80}")
        print(f"⚠️  OPERACIONES DE ESCRITURA (NO DEBERÍAN EJECUTARSE)")
        print(f"{'='*80}")
        print(f"   Total: {len(write_operation_errors)}")
        print(f"   Estas operaciones NO deberían ejecutarse en un diagnóstico de solo lectura.")
        
        # Agrupar por tipo de operación
        write_types = Counter()
        for err in write_operation_errors:
            op_lower = err['operation'].lower()
            if op_lower.startswith('create'):
                write_types['Create*'] += 1
            elif op_lower.startswith('delete'):
                write_types['Delete*'] += 1
            elif op_lower.startswith('update'):
                write_types['Update*'] += 1
            elif op_lower.startswith('modify'):
                write_types['Modify*'] += 1
            else:
                write_types['Otros'] += 1
        
        print(f"\n   Tipos de operaciones de escritura:")
        for op_type, count in write_types.most_common():
            print(f"      - {op_type}: {count}")
        
        print(f"\n   Primeras 10 operaciones de escritura:")
        for err in write_operation_errors[:10]:
            print(f"      - {err['operation']} ({err['error_code']})")
    
    if permission_errors:
        print(f"\n{'='*80}")
        print(f"🔒 ERRORES DE PERMISOS EN OPERACIONES DE LECTURA")
        print(f"{'='*80}")
        
        covered_errors = [e for e in permission_errors if e['covered']]
        not_covered_errors = [e for e in permission_errors if not e['covered']]
        
        print(f"\n   Total de errores de permisos: {len(permission_errors)}")
        print(f"   ✅ Permisos cubiertos pero que fallan: {len(covered_errors)}")
        print(f"   ❌ Permisos NO cubiertos: {len(not_covered_errors)}")
        
        if covered_errors:
            print(f"\n   ⚠️  OPERACIONES CON PERMISOS CUBIERTOS PERO QUE FALLAN:")
            print(f"      (Los permisos están en las políticas pero aún fallan)")
            
            # Agrupar por operación
            op_counts = Counter([e['operation'] for e in covered_errors])
            print(f"\n      Top 15 operaciones más comunes:")
            for i, (op, count) in enumerate(op_counts.most_common(15), 1):
                example = next(e for e in covered_errors if e['operation'] == op)
                print(f"      {i:2d}. {op:40s} - {count:3d} errores")
                print(f"          Permiso: {example['permission']}")
                print(f"          Error: {example['error_code']}")
        
        if not_covered_errors:
            print(f"\n   ❌ OPERACIONES CON PERMISOS NO CUBIERTOS:")
            op_counts = Counter([e['operation'] for e in not_covered_errors])
            print(f"\n      Top 15 operaciones más comunes:")
            for i, (op, count) in enumerate(op_counts.most_common(15), 1):
                example = next(e for e in not_covered_errors if e['operation'] == op)
                print(f"      {i:2d}. {op:40s} - {count:3d} errores")
                print(f"          Permiso necesario: {example['permission']}")
    
    if other_errors:
        print(f"\n{'='*80}")
        print(f"⚠️  OTROS ERRORES")
        print(f"{'='*80}")
        
        error_types = Counter([e['error_code'] for e in other_errors])
        print(f"\n   Tipos de errores:")
        for error_code, count in error_types.most_common(10):
            print(f"      - {error_code}: {count}")
    
    print(f"\n{'='*80}")
    print(f"💡 DIAGNÓSTICO")
    print(f"{'='*80}")
    
    if len(write_operation_errors) > 0:
        print(f"\n   1. ⚠️  Se detectaron {len(write_operation_errors)} errores de operaciones de escritura")
        print(f"      - Estas operaciones NO deberían ejecutarse en un diagnóstico")
        print(f"      - El filtro de operaciones de escritura debería prevenir esto en futuras recolecciones")
    
    if len(covered_errors) > 0:
        print(f"\n   2. 🔴 PRIORIDAD ALTA: {len(covered_errors)} operaciones tienen permisos cubiertos pero fallan")
        print(f"      - Los permisos están en las políticas JSON pero no funcionan")
        print(f"      - Posibles causas:")
        print(f"        • Las políticas no están adjuntas al rol/usuario en AWS")
        print(f"        • Hay un 'explicit deny' en otra política")
        print(f"        • El servicio requiere permisos adicionales específicos")
        print(f"      - ACCIÓN: Verifica en AWS Console que las políticas estén adjuntas")
    
    if len(not_covered_errors) > 0:
        print(f"\n   3. ⚠️  {len(not_covered_errors)} operaciones tienen permisos NO cubiertos")
        print(f"      - Estos permisos faltan en las políticas")
        print(f"      - ACCIÓN: Agrega estos permisos a las políticas")
    
    if successful_ops == 0:
        print(f"\n   4. ❌ CRÍTICO: No hay operaciones exitosas")
        print(f"      - EC2 no está trayendo ninguna información")
        print(f"      - Esto indica un problema grave de permisos o configuración")
        print(f"      - ACCIÓN: Verifica las credenciales y políticas en AWS")
    
    print(f"\n{'='*80}")

if __name__ == "__main__":
    main()

