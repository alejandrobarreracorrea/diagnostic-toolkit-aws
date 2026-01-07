#!/usr/bin/env python3
"""Script para debuggear CloudTrail en el evidence pack"""

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

cloudtrail_dir = latest_run / 'raw' / 'cloudtrail' / 'us-east-1'

# Verificar ListTrails
trails_file = cloudtrail_dir / 'ListTrails.json.gz'
if trails_file.exists():
    with gzip.open(trails_file, 'rt', encoding='utf-8') as f:
        data = json.load(f)
    
    print("=== ListTrails ===")
    print(f"Success: {data.get('metadata', {}).get('success', False)}")
    print(f"Paginated: {data.get('metadata', {}).get('paginated', False)}")
    
    data_content = data.get('data', {})
    print(f"Tipo de data_content: {type(data_content)}")
    
    if isinstance(data_content, dict):
        print(f"Keys en data_content: {list(data_content.keys())}")
        
        # Buscar trails en diferentes lugares
        trails = None
        if 'Trails' in data_content:
            trails = data_content.get('Trails', [])
            print(f"Trails encontrados en data.Trails: {len(trails)}")
        elif 'trailList' in data_content:
            trails = data_content.get('trailList', [])
            print(f"Trails encontrados en data.trailList: {len(trails)}")
        elif 'data' in data_content:
            # Puede ser paginado
            pages = data_content.get('data', [])
            print(f"Es paginado, total páginas: {len(pages)}")
            all_trails = []
            for i, page in enumerate(pages):
                page_trails = page.get('Trails', []) or page.get('trailList', [])
                print(f"  Página {i+1}: {len(page_trails)} trails")
                if page_trails:
                    all_trails.extend(page_trails)
            trails = all_trails
            print(f"Total trails únicos: {len(trails)}")
        
        if trails:
            print(f"\nTrails encontrados: {len(trails)}")
            for i, trail in enumerate(trails, 1):
                name = trail.get('Name', 'N/A')
                is_logging = trail.get('IsLogging', False)
                is_multi_region = trail.get('IsMultiRegionTrail', False)
                status = trail.get('Status', 'N/A')
                print(f"\n  Trail {i}: {name}")
                print(f"    IsLogging: {is_logging}")
                print(f"    IsMultiRegionTrail: {is_multi_region}")
                print(f"    Status: {status}")
                print(f"    Keys: {list(trail.keys())[:10]}")
        else:
            print("No se encontraron trails")
    else:
        print("Estructura inesperada")

