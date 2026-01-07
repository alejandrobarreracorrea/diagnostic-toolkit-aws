#!/usr/bin/env python3
"""Script para verificar Route53 en el inventario"""

import json
from pathlib import Path

# Encontrar el último run
runs = sorted([d for d in Path('runs').iterdir() if d.is_dir()], 
              key=lambda x: x.stat().st_mtime, reverse=True)
if not runs:
    print("No se encontraron runs")
    exit(1)

latest_run = runs[0]
print(f"Verificando Route53 en inventario del run: {latest_run.name}\n")

# Verificar índice
index_file = latest_run / 'index' / 'index.json'
with open(index_file, 'r', encoding='utf-8') as f:
    idx = json.load(f)

route53 = idx.get('services', {}).get('route53', {})
regions = route53.get('regions', {})
us_east_1 = regions.get('us-east-1', {})
ops = us_east_1.get('operations', [])

print("Operaciones de Route53 en el índice:")
total_count = 0
for op in ops:
    op_name = op.get('operation', 'N/A')
    success = op.get('success', False)
    count = op.get('resource_count', 0)
    if count > 0 or op_name == 'ListHostedZones':
        print(f"  {op_name}: success={success}, count={count}")
    if count > 0:
        total_count += count

print(f"\nTotal recursos en índice: {total_count}")

# Verificar inventario
inv_file = latest_run / 'outputs' / 'inventory' / 'inventory.json'
if inv_file.exists():
    with open(inv_file, 'r', encoding='utf-8') as f:
        inv = json.load(f)
    
    route53_inv = inv.get('services', {}).get('route53', {})
    print(f"\nRoute53 en inventario: {route53_inv.get('resource_count', 0)} recursos")
    print(f"Regiones: {route53_inv.get('regions', [])}")

