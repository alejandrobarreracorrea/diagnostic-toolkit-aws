#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para verificar por qué servicios con permisos cubiertos aún fallan.
"""

import json
import sys
from pathlib import Path
from collections import defaultdict

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
    print("🔍 ANÁLISIS DETALLADO: PERMISOS CUBIERTOS PERO QUE FALLAN")
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
    
    # Servicios específicos a analizar
    target_services = ['codeguru-reviewer', 'comprehend', 'datapipeline', 'dax', 'devicefarm', 'discovery', 'ecr-public']
    
    print(f"\n📋 Analizando servicios específicos: {', '.join(target_services)}")
    
    permission_codes = ['AccessDenied', 'UnauthorizedOperation', 'Forbidden', 'AccessDeniedException']
    
    for service_name in target_services:
        if service_name not in idx.get("services", {}):
            continue
        
        print(f"\n{'='*80}")
        print(f"🔸 {service_name}")
        print(f"{'='*80}")
        
        service_data = idx.get("services", {}).get(service_name, {})
        covered_errors = []
        operations_with_errors = []
        
        for region_name, region_data in service_data.get("regions", {}).items():
            for op_info in region_data.get("operations", []):
                if not op_info.get("success", True) and not op_info.get("not_available", False):
                    error = op_info.get("error", {})
                    if isinstance(error, dict):
                        error_code = error.get("code", "")
                        op_name = op_info.get("operation", "")
                        
                        if error_code in permission_codes and is_read_operation(op_name):
                            perm = operation_to_iam_permission(service_name, op_name)
                            is_covered = check_permission_covered(perm, all_policy_permissions)
                            
                            operations_with_errors.append({
                                "operation": op_name,
                                "permission": perm,
                                "covered": is_covered,
                                "error_code": error_code,
                                "error_message": error.get("message", "")[:100]
                            })
                            
                            if is_covered:
                                covered_errors.append({
                                    "operation": op_name,
                                    "permission": perm,
                                    "error_code": error_code
                                })
        
        if not operations_with_errors:
            print(f"   ✅ No hay errores de permisos para {service_name}")
            continue
        
        print(f"\n   📊 Total de operaciones con errores: {len(operations_with_errors)}")
        print(f"   ✅ Permisos cubiertos pero que fallan: {len(covered_errors)}")
        print(f"   ❌ Permisos NO cubiertos: {len(operations_with_errors) - len(covered_errors)}")
        
        if covered_errors:
            print(f"\n   ⚠️  OPERACIONES CON PERMISOS CUBIERTOS PERO QUE FALLAN:")
            for err in covered_errors[:10]:  # Mostrar primeras 10
                print(f"      - {err['operation']}")
                print(f"        Permiso en política: {err['permission']}")
                print(f"        Error: {err['error_code']}")
                
                # Verificar si el permiso está realmente en las políticas
                matching_perms = [p for p in all_policy_permissions if err['permission'] in p or p in err['permission']]
                if matching_perms:
                    print(f"        Permisos relacionados en políticas: {', '.join(matching_perms[:3])}")
                print()
        
        if len(operations_with_errors) > len(covered_errors):
            print(f"\n   ❌ OPERACIONES CON PERMISOS NO CUBIERTOS:")
            for err in operations_with_errors:
                if not err['covered']:
                    print(f"      - {err['operation']}")
                    print(f"        Permiso necesario: {err['permission']}")
                    print(f"        Error: {err['error_code']}")
                    print()
    
    print("\n" + "="*80)
    print("💡 EXPLICACIÓN")
    print("="*80)
    print("""
   Si los permisos están en el JSON pero aún fallan, las causas más comunes son:

   1. 🔴 POLÍTICAS NO ADJUNTAS AL ROL/USUARIO
      - Las políticas JSON existen pero no están aplicadas en AWS
      - Verifica en AWS Console → IAM → Roles/Users que las políticas estén adjuntas
      - Las políticas deben estar adjuntas al rol/usuario que ejecuta ECAD

   2. 🔴 EXPLICIT DENY EN OTRA POLÍTICA
      - Puede haber otra política con "Effect": "Deny" que bloquea estos permisos
      - AWS evalúa primero los Deny, así que aunque tengas Allow, el Deny prevalece
      - Revisa todas las políticas adjuntas al rol/usuario

   3. 🔴 FORMATO DEL PERMISO NO COINCIDE
      - Algunos servicios requieren permisos específicos además de los wildcards
      - Ejemplo: codeguru-reviewer puede requerir permisos específicos además de Describe*/Get*/List*
      - Verifica la documentación del servicio para permisos adicionales

   4. 🔴 REGIÓN O SERVICIO NO HABILITADO
      - El servicio puede no estar habilitado en la cuenta AWS
      - El servicio puede no estar disponible en la región seleccionada
      - Algunos servicios requieren activación manual

   5. 🔴 PERMISOS ADICIONALES REQUERIDOS
      - Algunos servicios requieren permisos de otros servicios
      - Ejemplo: algunos servicios requieren permisos de IAM o CloudWatch
      - Revisa los requisitos previos del servicio

   📋 ACCIÓN RECOMENDADA:
      1. Verifica en AWS Console que las políticas estén adjuntas al rol/usuario
      2. Revisa si hay políticas con "Effect": "Deny" que puedan estar bloqueando
      3. Verifica que el servicio esté habilitado en la cuenta
      4. Ejecuta: aws iam simulate-principal-policy para verificar permisos
    """)
    print("="*80)

if __name__ == "__main__":
    main()

