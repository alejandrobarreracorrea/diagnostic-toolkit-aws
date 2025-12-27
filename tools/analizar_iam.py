#!/usr/bin/env python3
"""Script para analizar qué recursos de IAM se están contando"""
import json
import gzip
from pathlib import Path
from collections import defaultdict

# Buscar el run más reciente
runs_dir = Path('runs')
runs = sorted([d for d in runs_dir.iterdir() if d.is_dir()], reverse=True)
if not runs:
    print('No se encontraron runs')
    exit(1)

latest_run = runs[0]
iam_dir = latest_run / 'raw' / 'iam'
if not iam_dir.exists():
    print(f'No se encontró directorio IAM en {latest_run.name}')
    exit(1)

# Buscar todas las regiones
regions = [d for d in iam_dir.iterdir() if d.is_dir()]
if not regions:
    print('No se encontraron regiones')
    exit(1)

print(f'Run: {latest_run.name}')
print('='*80)

total_resources = defaultdict(int)
operations_detail = defaultdict(dict)
primary_ops = ['ListUsers', 'ListRoles', 'ListGroups']

for region_dir in regions:
    region_name = region_dir.name
    print(f'\nRegión: {region_name}')
    print('-'*80)
    
    for op_file in sorted(region_dir.glob('*.json.gz')):
        op_name = op_file.stem.replace('.json', '')
        # Convertir snake_case a PascalCase para comparar
        op_pascal = ''.join(word.capitalize() for word in op_name.split('_'))
        
        try:
            with gzip.open(op_file, 'rt') as f:
                data = json.load(f)
            
            metadata = data.get('metadata', {})
            success = metadata.get('success', False)
            response_data = data.get('data', {})
            
            # Contar recursos según el tipo de operación
            resource_count = 0
            if success and response_data:
                if isinstance(response_data, dict):
                    # Buscar listas de recursos
                    for key in ['Users', 'Roles', 'Groups', 'Policies', 'AttachedPolicies', 
                               'UserDetailList', 'RoleDetailList', 'GroupDetailList']:
                        if key in response_data and isinstance(response_data[key], list):
                            count = len(response_data[key])
                            resource_count += count
                            is_primary = op_pascal in primary_ops or op_name in ['list_users', 'list_roles', 'list_groups']
                            marker = '✅' if is_primary else '⚠️ '
                            print(f'  {marker} {op_name} ({op_pascal}): {key} = {count}')
                            total_resources[key] += count
                            if op_name not in operations_detail:
                                operations_detail[op_name] = {}
                            operations_detail[op_name][key] = count
                elif isinstance(response_data, list):
                    resource_count = len(response_data)
                    is_primary = op_pascal in primary_ops or op_name in ['list_users', 'list_roles', 'list_groups']
                    marker = '✅' if is_primary else '⚠️ '
                    print(f'  {marker} {op_name} ({op_pascal}): lista directa = {resource_count}')
            
            if not success:
                error = data.get('error', {})
                error_code = error.get('code', 'Unknown') if isinstance(error, dict) else 'Unknown'
                print(f'  ❌ {op_name}: Error ({error_code})')
        except Exception as e:
            print(f'  ❌ {op_name}: Error leyendo archivo: {e}')

print('\n' + '='*80)
print('RESUMEN TOTAL:')
print('='*80)
for key, count in sorted(total_resources.items()):
    print(f'{key}: {count}')
print(f'\nTotal recursos IAM encontrados: {sum(total_resources.values())}')

print('\n' + '='*80)
print('OPERACIONES PRINCIPALES CONFIGURADAS:')
print('='*80)
print('Solo estas operaciones deberían contar recursos:')
print('- ListUsers (Users)')
print('- ListRoles (Roles)')
print('- ListGroups (Groups)')
print('\nSi hay más recursos, pueden venir de otras operaciones que se están contando incorrectamente.')


