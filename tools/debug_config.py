#!/usr/bin/env python3
"""Script para debuggear AWS Config en el evidence pack"""

import json
import gzip
from pathlib import Path

# Encontrar el último run
runs = sorted([d for d in Path('runs').iterdir() if d.is_dir()], 
              key=lambda x: x.stat().st_mtime, reverse=True)
if not runs:
    print("No se encontraron runs")
    exit(1)

latest_run = runs[0]
print(f"Analizando run: {latest_run.name}\n")

config_dir = latest_run / 'raw' / 'config' / 'us-east-1'

# Verificar qué operaciones hay
if config_dir.exists():
    files = list(config_dir.glob('*.json.gz'))
    print(f"Archivos de Config encontrados: {len(files)}")
    for f in files[:15]:
        print(f"  - {f.stem}")
else:
    print("No se encontró directorio de Config")
    exit(1)

print("\n" + "="*60)

# Verificar DescribeConfigurationRecorders (la operación principal)
recorders_file = config_dir / 'DescribeConfigurationRecorders.json.gz'
if recorders_file.exists():
    with gzip.open(recorders_file, 'rt', encoding='utf-8') as f:
        data = json.load(f)
    
    print("\n=== DescribeConfigurationRecorders ===")
    print(f"Success: {data.get('metadata', {}).get('success', False)}")
    print(f"Paginated: {data.get('metadata', {}).get('paginated', False)}")
    
    data_content = data.get('data', {})
    print(f"Tipo de data_content: {type(data_content)}")
    
    if isinstance(data_content, dict):
        print(f"Keys en data_content: {list(data_content.keys())}")
        
        # Buscar recorders en diferentes lugares
        recorders = None
        if 'ConfigurationRecorders' in data_content:
            recorders = data_content.get('ConfigurationRecorders', [])
            print(f"ConfigurationRecorders encontrados en data.ConfigurationRecorders: {len(recorders)}")
        elif 'data' in data_content:
            # Puede ser paginado
            pages = data_content.get('data', [])
            print(f"Es paginado, total páginas: {len(pages)}")
            all_recorders = []
            for i, page in enumerate(pages):
                page_recorders = page.get('ConfigurationRecorders', [])
                print(f"  Página {i+1}: {len(page_recorders)} recorders")
                if page_recorders:
                    all_recorders.extend(page_recorders)
            recorders = all_recorders
            print(f"Total recorders únicos: {len(recorders)}")
        
        if recorders:
            print(f"\nConfigurationRecorders encontrados: {len(recorders)}")
            for i, recorder in enumerate(recorders, 1):
                name = recorder.get('name', recorder.get('Name', 'N/A'))
                role_arn = recorder.get('roleARN', recorder.get('RoleARN', 'N/A'))
                recording = recorder.get('recording', recorder.get('recordingGroup', {}))
                print(f"\n  Recorder {i}: {name}")
                print(f"    RoleARN: {role_arn}")
                print(f"    Recording: {recording}")
                print(f"    Keys: {list(recorder.keys())[:10]}")
        else:
            print("No se encontraron ConfigurationRecorders")
    else:
        print("Estructura inesperada")

print("\n" + "="*60)

# Verificar también GetDiscoveredResourceCounts
counts_file = config_dir / 'GetDiscoveredResourceCounts.json.gz'
if counts_file.exists():
    with gzip.open(counts_file, 'rt', encoding='utf-8') as f:
        data = json.load(f)
    
    print("\n=== GetDiscoveredResourceCounts ===")
    print(f"Success: {data.get('metadata', {}).get('success', False)}")
    
    data_content = data.get('data', {})
    if isinstance(data_content, dict):
        total_resources = data_content.get('totalDiscoveredResources', 0)
        print(f"Total recursos descubiertos: {total_resources}")
        if total_resources > 0:
            print("  -> Config está activo (hay recursos descubiertos)")

