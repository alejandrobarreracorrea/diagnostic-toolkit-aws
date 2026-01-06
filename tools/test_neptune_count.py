#!/usr/bin/env python3
"""Script para simular el conteo de Neptune en show_inventory_console"""

import json
from pathlib import Path

# Encontrar el último run
runs = sorted([d for d in Path('runs').iterdir() if d.is_dir()], 
              key=lambda x: x.stat().st_mtime, reverse=True)
if not runs:
    print("No se encontraron runs")
    exit(1)

latest_run = runs[0]
print(f"Simulando conteo de Neptune para: {latest_run.name}\n")

index_file = latest_run / 'index' / 'index.json'
with open(index_file, 'r', encoding='utf-8') as f:
    index = json.load(f)

services = index.get("services", {})
service_name = 'neptune'
service_data = services.get(service_name, {})

# primary_operations como en ecad.py (actualizado)
primary_operations = {
    'neptune': ['DescribeDBClusters'],  # Solo clusters
}

resource_count = 0
successful_ops = 0
failed_ops = 0

for region_name, region_data in service_data.get("regions", {}).items():
    print(f"Región: {region_name}")
    for op_info in region_data.get("operations", []):
        op_name = op_info.get("operation", "")
        op_count = op_info.get("resource_count", 0) or 0
        
        if op_info.get("success"):
            successful_ops += 1
            # Solo contar recursos de operaciones principales
            if service_name in primary_operations:
                # Normalizar nombre de operación a PascalCase para comparar
                if '_' in op_name:
                    op_pascal = ''.join(word.capitalize() for word in op_name.split('_'))
                else:
                    op_pascal = op_name
                
                allowed_ops = primary_operations[service_name]
                print(f"  Operación: {op_name} (normalizada: {op_pascal})")
                print(f"    Allowed ops: {allowed_ops}")
                print(f"    Count en índice: {op_count}")
                
                # Comparar tanto el nombre original como el normalizado
                if op_name in allowed_ops or op_pascal in allowed_ops:
                    print(f"    [OK] COINCIDE - Se suma al conteo")
                    resource_count += op_count
                else:
                    print(f"    [NO] NO COINCIDE - NO se suma al conteo")
            else:
                print(f"  {op_name}: NO está en primary_operations, usaría heurística")
        elif not op_info.get("not_available", False):
            failed_ops += 1

print(f"\n{'='*60}")
print(f"Resultado final:")
print(f"  Recursos contados: {resource_count}")
print(f"  Operaciones exitosas: {successful_ops}")
print(f"  Operaciones fallidas: {failed_ops}")

