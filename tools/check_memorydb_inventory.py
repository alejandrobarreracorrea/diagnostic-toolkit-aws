#!/usr/bin/env python3
"""Script para verificar MemoryDB en el inventario"""

import json
from pathlib import Path

# Encontrar el último run
runs = sorted([d for d in Path('runs').iterdir() if d.is_dir()], 
              key=lambda x: x.stat().st_mtime, reverse=True)
if not runs:
    print("No se encontraron runs")
    exit(1)

latest_run = runs[0]
print(f"Verificando MemoryDB en inventario del run: {latest_run.name}\n")

# Verificar índice
index_file = latest_run / 'index' / 'index.json'
with open(index_file, 'r', encoding='utf-8') as f:
    idx = json.load(f)

memorydb = idx.get('services', {}).get('memorydb', {})
regions = memorydb.get('regions', {})
us_east_1 = regions.get('us-east-1', {})
ops = us_east_1.get('operations', [])

print("Operaciones de MemoryDB en el índice:")
total_count = 0
for op in ops:
    op_name = op.get('operation', 'N/A')
    success = op.get('success', False)
    count = op.get('resource_count', 0)
    print(f"  {op_name}: success={success}, count={count}")
    if count > 0:
        total_count += count

print(f"\nTotal recursos en índice: {total_count}")

# Verificar inventario
inv_file = latest_run / 'outputs' / 'inventory' / 'inventory.json'
if inv_file.exists():
    with open(inv_file, 'r', encoding='utf-8') as f:
        inv = json.load(f)
    
    memorydb_inv = inv.get('services', {}).get('memorydb', {})
    print(f"\nMemoryDB en inventario: {memorydb_inv.get('resource_count', 0)} recursos")
    print(f"Regiones: {memorydb_inv.get('regions', [])}")

