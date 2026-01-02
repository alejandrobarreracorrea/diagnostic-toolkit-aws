#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para actualizar las políticas IAM agregando permisos faltantes de lectura.
Respeta el límite de 6144 caracteres por statement de AWS.
"""

import json
import sys
import os
from pathlib import Path
from collections import defaultdict

# Configurar codificación UTF-8 para Windows
if sys.platform == 'win32':
    import io
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        # Python < 3.7
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Importar funciones del script de validación
from tools.validate_iam_policies import (
    is_read_operation, 
    operation_to_iam_permission,
    find_latest_run,
    load_json_file,
    check_permission_covered
)

def get_missing_permissions():
    """Obtener lista de permisos faltantes desde el run más reciente."""
    run_dir = find_latest_run()
    if not run_dir:
        print("❌ No se encontraron runs disponibles")
        return set()
    
    index_file = run_dir / "index" / "index.json"
    if not index_file.exists():
        print(f"❌ No se encontró índice en {run_dir.name}")
        return set()
    
    idx = load_json_file(index_file)
    if not idx:
        return set()
    
    # Cargar políticas actuales
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
    
    # Analizar errores de permisos - SOLO operaciones de lectura
    permission_errors = []
    permission_codes = ['AccessDenied', 'UnauthorizedOperation', 'Forbidden', 'AccessDeniedException']
    
    for service_name, service_data in idx.get("services", {}).items():
        for region_name, region_data in service_data.get("regions", {}).items():
            for op_info in region_data.get("operations", []):
                if not op_info.get("success", True) and not op_info.get("not_available", False):
                    error = op_info.get("error", {})
                    if isinstance(error, dict):
                        error_code = error.get("code", "")
                        op_name = op_info.get("operation", "")
                        
                        # FILTRAR: Solo considerar errores de operaciones de LECTURA
                        if error_code in permission_codes and is_read_operation(op_name):
                            permission_errors.append({
                                "service": service_name,
                                "operation": op_name,
                                "code": error_code
                            })
    
    # Obtener permisos faltantes
    missing_perms = set()
    for error in permission_errors:
        service = error['service']
        operation = error['operation']
        perm = operation_to_iam_permission(service, operation)
        
        # Verificar si está cubierto
        if not check_permission_covered(perm, all_policy_permissions):
            missing_perms.add(perm)
    
    return missing_perms

def calculate_statement_size(statement):
    """Calcular el tamaño aproximado de un statement en caracteres."""
    # Serializar a JSON sin espacios extra para calcular tamaño real
    json_str = json.dumps(statement, separators=(',', ':'))
    return len(json_str)

def add_permissions_to_policy(policy_file, new_permissions, max_size=6000):
    """Agregar permisos a una política respetando el límite de tamaño."""
    policy = load_json_file(policy_file)
    if not policy:
        return set()  # Retornar set vacío en lugar de False
    
    # Obtener permisos existentes
    existing_permissions = set()
    for stmt in policy.get("Statement", []):
        actions = stmt.get("Action", [])
        if isinstance(actions, str):
            existing_permissions.add(actions)
        else:
            existing_permissions.update(actions)
    
    # Filtrar permisos que ya existen
    permissions_to_add = sorted(new_permissions - existing_permissions)
    
    if not permissions_to_add:
        print(f"   ✅ {policy_file.name}: Todos los permisos ya están presentes")
        return True
    
    # Intentar agregar a la primera statement (ECADReadOnlyAccess)
    main_statement = None
    for stmt in policy.get("Statement", []):
        if stmt.get("Sid", "").startswith("ECADReadOnlyAccess"):
            main_statement = stmt
            break
    
    if not main_statement:
        # Si no hay statement principal, usar la primera
        main_statement = policy.get("Statement", [{}])[0]
        if "Action" not in main_statement:
            main_statement["Action"] = []
    
    # Obtener acciones actuales
    current_actions = main_statement.get("Action", [])
    if isinstance(current_actions, str):
        current_actions = [current_actions]
    
    # Agregar nuevos permisos
    added_count = 0
    for perm in permissions_to_add:
        # Crear statement temporal para verificar tamaño
        test_actions = current_actions + [perm]
        test_statement = main_statement.copy()
        test_statement["Action"] = sorted(test_actions)
        
        size = calculate_statement_size(test_statement)
        
        if size <= max_size:
            current_actions.append(perm)
            added_count += 1
        else:
            # Si excede el límite, no agregar más
            print(f"   ⚠️  {policy_file.name}: Límite de tamaño alcanzado. No se pueden agregar más permisos.")
            break
    
    # Actualizar statement
    main_statement["Action"] = sorted(current_actions)
    
    # Guardar política actualizada
    try:
        with open(policy_file, 'w', encoding='utf-8') as f:
            json.dump(policy, f, indent=2, ensure_ascii=False)
        print(f"   ✅ {policy_file.name}: Agregados {added_count} permisos nuevos")
    except Exception as e:
        print(f"   ❌ Error guardando {policy_file.name}: {e}")
        return set(permissions_to_add)  # Retornar todos si hay error
    
    # Retornar permisos que no se pudieron agregar
    remaining = set(permissions_to_add[added_count:])
    return remaining

def main():
    print("="*80)
    print("🔧 ACTUALIZACIÓN DE POLÍTICAS IAM ECAD")
    print("="*80)
    
    # Obtener permisos faltantes
    print("\n📋 Obteniendo permisos faltantes del run más reciente...")
    missing_perms = get_missing_permissions()
    
    if not missing_perms:
        print("\n✅ No hay permisos faltantes. Las políticas están completas.")
        return
    
    print(f"\n📊 Permisos faltantes encontrados: {len(missing_perms)}")
    
    # Archivos de políticas
    policy1_file = project_root / "policies" / "iam-policy-ecad-part1.json"
    policy2_file = project_root / "policies" / "iam-policy-ecad-part2.json"
    
    # Distribuir permisos entre las dos políticas
    # Dividir aproximadamente por la mitad
    perms_list = sorted(missing_perms)
    mid_point = len(perms_list) // 2
    
    perms_part1 = set(perms_list[:mid_point])
    perms_part2 = set(perms_list[mid_point:])
    
    print(f"\n📦 Distribuyendo permisos:")
    print(f"   Part1: {len(perms_part1)} permisos")
    print(f"   Part2: {len(perms_part2)} permisos")
    
    # Agregar a part1
    print(f"\n📝 Actualizando {policy1_file.name}...")
    remaining_part1 = add_permissions_to_policy(policy1_file, perms_part1)
    
    # Si quedaron permisos sin agregar en part1, intentar agregarlos a part2
    if remaining_part1:
        print(f"\n   ⚠️  {len(remaining_part1)} permisos no se pudieron agregar a part1, intentando en part2...")
        perms_part2.update(remaining_part1)
    
    # Agregar a part2
    print(f"\n📝 Actualizando {policy2_file.name}...")
    remaining_part2 = add_permissions_to_policy(policy2_file, perms_part2)
    
    # Resumen
    print("\n" + "="*80)
    print("📊 RESUMEN")
    print("="*80)
    
    if remaining_part2:
        print(f"\n⚠️  {len(remaining_part2)} permisos no se pudieron agregar debido al límite de tamaño:")
        for perm in sorted(remaining_part2):
            print(f"      - {perm}")
        print("\n   💡 RECOMENDACIÓN: Considera crear una part3 o revisar los permisos duplicados.")
    else:
        print("\n✅ Todos los permisos faltantes han sido agregados exitosamente.")
    
    print("\n💡 PRÓXIMOS PASOS:")
    print("   1. Revisa las políticas actualizadas")
    print("   2. Actualiza el template de CloudFormation si es necesario")
    print("   3. Aplica las políticas actualizadas al rol/usuario en AWS")
    print("   4. Ejecuta una nueva recolección para verificar")
    
    print("\n" + "="*80)

if __name__ == "__main__":
    main()

