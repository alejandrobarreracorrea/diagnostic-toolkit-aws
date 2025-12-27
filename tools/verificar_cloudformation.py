#!/usr/bin/env python3
"""Script para verificar si CloudFormation tiene stacks activos"""
import json
import gzip
from pathlib import Path

# Buscar el run más reciente
runs_dir = Path('runs')
runs = sorted([d for d in runs_dir.iterdir() if d.is_dir()], reverse=True)
if not runs:
    print('❌ No se encontraron runs')
    exit(1)

latest_run = runs[0]
print(f'📁 Analizando: {latest_run.name}\n')

# Buscar archivos de CloudFormation
cf_dir = latest_run / 'raw' / 'cloudformation'
if not cf_dir.exists():
    print('❌ No se encontró directorio CloudFormation')
    exit(1)

# Buscar todas las regiones
regions = [d for d in cf_dir.iterdir() if d.is_dir()]
if not regions:
    print('❌ No se encontraron regiones')
    exit(1)

print('='*80)
print('CLOUDFORMATION - VERIFICACIÓN DE STACKS ACTIVOS')
print('='*80)

total_stacks = 0
active_stacks = 0
deleted_stacks = 0

for region_dir in regions:
    region_name = region_dir.name
    print(f'\n📍 Región: {region_name}')
    print('-'*80)
    
    # Buscar ListStacks o DescribeStacks
    for op_file in sorted(region_dir.glob('*.json.gz')):
        op_name = op_file.stem.replace('.json', '')
        
        if op_name.lower() not in ['liststacks', 'describestacks']:
            continue
        
        try:
            with gzip.open(op_file, 'rt') as f:
                data = json.load(f)
            
            metadata = data.get('metadata', {})
            success = metadata.get('success', False)
            response_data = data.get('data', {})
            
            if success and response_data:
                # Buscar stacks en diferentes formatos de respuesta
                stacks = []
                if isinstance(response_data, dict):
                    stacks = response_data.get('Stacks', []) or response_data.get('StackSummaries', [])
                elif isinstance(response_data, list):
                    stacks = response_data
                
                if isinstance(stacks, list):
                    print(f'\n  Operación: {op_name}')
                    print(f'  Total stacks encontrados: {len(stacks)}')
                    
                    for stack in stacks:
                        stack_name = stack.get('StackName', 'N/A')
                        stack_status = stack.get('StackStatus', 'N/A')
                        total_stacks += 1
                        
                        if stack_status == 'DELETE_COMPLETE':
                            deleted_stacks += 1
                            print(f'    ❌ {stack_name}: {stack_status} (eliminado)')
                        else:
                            active_stacks += 1
                            print(f'    ✅ {stack_name}: {stack_status} (activo)')
                    
                    if len(stacks) == 0:
                        print(f'    ⚠️  No hay stacks en esta región')
            else:
                error = data.get('error', {})
                error_code = error.get('code', 'Unknown') if isinstance(error, dict) else 'Unknown'
                print(f'  ❌ {op_name}: Error ({error_code})')
        except Exception as e:
            print(f'  ❌ {op_name}: Error leyendo archivo: {e}')

print('\n' + '='*80)
print('RESUMEN:')
print('='*80)
print(f'Total stacks encontrados: {total_stacks}')
print(f'✅ Stacks activos: {active_stacks}')
print(f'❌ Stacks eliminados (DELETE_COMPLETE): {deleted_stacks}')

if active_stacks > 0:
    print(f'\n✅ CloudFormation ESTÁ EN USO con {active_stacks} stack(s) activo(s)')
else:
    print(f'\n❌ CloudFormation NO ESTÁ EN USO (no hay stacks activos)')


