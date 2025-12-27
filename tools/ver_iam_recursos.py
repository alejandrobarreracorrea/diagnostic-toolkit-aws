#!/usr/bin/env python3
"""Ver qué recursos de IAM se están contando"""
import json
from pathlib import Path

# Buscar el run más reciente
runs_dir = Path('runs')
runs = sorted([d for d in runs_dir.iterdir() if d.is_dir()], reverse=True)
if not runs:
    print('❌ No se encontraron runs')
    exit(1)

latest_run = runs[0]
print(f'📁 Analizando: {latest_run.name}\n')

# Cargar índice
index_file = latest_run / 'index' / 'index.json'
if not index_file.exists():
    print('❌ No se encontró el índice. Ejecuta primero: make analyze')
    exit(1)

with open(index_file, 'r') as f:
    index = json.load(f)

iam_data = index.get('services', {}).get('iam', {})
if not iam_data:
    print('❌ No se encontraron datos de IAM')
    exit(1)

print('='*80)
print('RECURSOS DE IAM POR OPERACIÓN')
print('='*80)

primary_ops = ['ListUsers', 'ListRoles', 'ListGroups']
total_primary = 0
total_other = 0

for region_name, region_data in iam_data.get('regions', {}).items():
    print(f'\n📍 Región: {region_name}')
    print('-'*80)
    
    for op_info in region_data.get('operations', []):
        op_name = op_info.get('operation', '')
        success = op_info.get('success', False)
        resource_count = op_info.get('resource_count', 0) or 0
        
        # Convertir a PascalCase para comparar
        op_pascal = ''.join(word.capitalize() for word in op_name.split('_'))
        is_primary = op_pascal in primary_ops or op_name in ['list_users', 'list_roles', 'list_groups']
        
        if success and resource_count > 0:
            marker = '✅' if is_primary else '⚠️ '
            status = 'PRINCIPAL' if is_primary else 'AUXILIAR'
            print(f'{marker} {op_name:30} → {resource_count:3} recursos ({status})')
            
            if is_primary:
                total_primary += resource_count
            else:
                total_other += resource_count
        elif not success:
            error = op_info.get('error', {})
            error_code = error.get('code', 'Unknown') if isinstance(error, dict) else 'Unknown'
            print(f'❌ {op_name:30} → Error: {error_code}')

print('\n' + '='*80)
print('RESUMEN:')
print('='*80)
print(f'✅ Recursos de operaciones PRINCIPALES (ListUsers, ListRoles, ListGroups): {total_primary}')
print(f'⚠️  Recursos de operaciones AUXILIARES (otras): {total_other}')
print(f'📊 TOTAL mostrado en inventario: {total_primary + total_other}')
print(f'\n💡 Si el total es mayor a {total_primary}, se están contando operaciones auxiliares.')


