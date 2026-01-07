#!/usr/bin/env python3
"""Script para debuggear el conteo de Route53"""

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

route53_dir = latest_run / 'raw' / 'route53' / 'us-east-1'

# Verificar qué operaciones hay
if route53_dir.exists():
    files = list(route53_dir.glob('*.json.gz'))
    print(f"Archivos de Route53 encontrados: {len(files)}")
    for f in files[:15]:
        print(f"  - {f.stem}")
else:
    print("No se encontró directorio de Route53")
    exit(1)

print("\n" + "="*60)

# Verificar ListHostedZones (la operación principal)
hosted_zones_file = route53_dir / 'ListHostedZones.json.gz'
if hosted_zones_file.exists():
    with gzip.open(hosted_zones_file, 'rt') as f:
        data = json.load(f)
    
    print("\n=== ListHostedZones ===")
    print(f"Success: {data.get('metadata', {}).get('success', False)}")
    print(f"Paginated: {data.get('metadata', {}).get('paginated', False)}")
    
    data_content = data.get('data', {})
    if isinstance(data_content, dict) and 'data' in data_content:
        pages = data_content.get('data', [])
        print(f"Total páginas: {len(pages)}")
        
        seen_zones = set()
        all_zones = []
        
        for i, page in enumerate(pages):
            print(f"\n--- Página {i+1} ---")
            # Route53 puede tener HostedZones o HostedZoneSummaries
            page_zones = page.get('HostedZones', []) or page.get('HostedZoneSummaries', [])
            print(f"Hosted zones en esta página: {len(page_zones)}")
            
            for zone in page_zones:
                zone_id = zone.get('Id', 'N/A')
                zone_name = zone.get('Name', 'N/A')
                
                # Normalizar ID (puede venir con /hostedzone/ prefix)
                if zone_id and '/hostedzone/' in zone_id:
                    zone_id = zone_id.split('/hostedzone/')[-1]
                
                if zone_id not in seen_zones and zone_id != 'N/A':
                    seen_zones.add(zone_id)
                    all_zones.append({
                        'id': zone_id,
                        'name': zone_name
                    })
                    print(f"  Zone: {zone_name} (ID: {zone_id})")
                elif zone_id != 'N/A':
                    print(f"  [DUPLICADO] Zone: {zone_name} (ID: {zone_id})")
        
        print(f"\nTotal hosted zones únicos: {len(all_zones)}")
        
        if all_zones:
            print("\nHosted zones encontradas:")
            for zone in all_zones:
                print(f"  - {zone['name']} (ID: {zone['id']})")
    elif isinstance(data_content, dict):
        # Puede ser datos directos sin paginación
        zones = data_content.get('HostedZones', []) or data_content.get('HostedZoneSummaries', [])
        print(f"Hosted zones (datos directos): {len(zones)}")
        for zone in zones:
            zone_id = zone.get('Id', 'N/A')
            zone_name = zone.get('Name', 'N/A')
            print(f"  - {zone_name} (ID: {zone_id})")
    else:
        print("Estructura de datos inesperada")
        print(f"Tipo de data_content: {type(data_content)}")
        if isinstance(data_content, dict):
            print(f"Keys: {list(data_content.keys())}")

print("\n" + "="*60)

# Verificar el índice
index_file = latest_run / 'index' / 'index.json'
if index_file.exists():
    with open(index_file, 'r', encoding='utf-8') as f:
        idx = json.load(f)
    
    route53 = idx.get('services', {}).get('route53', {})
    regions = route53.get('regions', {})
    us_east_1 = regions.get('us-east-1', {})
    ops = us_east_1.get('operations', [])
    
    print("\nOperaciones de Route53 en el índice:")
    for op in ops:
        op_name = op.get('operation', 'N/A')
        success = op.get('success', False)
        count = op.get('resource_count', 0)
        print(f"  {op_name}: success={success}, count={count}")

