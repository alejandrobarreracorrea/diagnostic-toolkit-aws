#!/usr/bin/env python3
"""Script para verificar detalladamente Neptune en el índice"""

import json
from pathlib import Path

# Encontrar el último run
runs = sorted([d for d in Path('runs').iterdir() if d.is_dir()], 
              key=lambda x: x.stat().st_mtime, reverse=True)
if not runs:
    print("No se encontraron runs")
    exit(1)

latest_run = runs[0]
print(f"Verificando índice del run: {latest_run.name}\n")

index_file = latest_run / 'index' / 'index.json'
if not index_file.exists():
    print("No se encontró el archivo de índice")
    exit(1)

with open(index_file, 'r', encoding='utf-8') as f:
    idx = json.load(f)

neptune = idx.get('services', {}).get('neptune', {})
regions = neptune.get('regions', {})
us_east_1 = regions.get('us-east-1', {})
ops = us_east_1.get('operations', [])

print("Todas las operaciones de Neptune en el índice:")
total_count = 0
for op in ops:
    op_name = op.get('operation', 'N/A')
    success = op.get('success', False)
    count = op.get('resource_count', 0)
    not_avail = op.get('not_available', False)
    print(f"  {op_name}: success={success}, count={count}, not_available={not_avail}")
    if count > 0:
        total_count += count

print(f"\nTotal recursos contados en el índice: {total_count}")

# Verificar qué operaciones están en primary_operations
print("\nOperaciones que DEBERÍAN contarse (según primary_operations):")
print("  - DescribeDBClusters")

# Verificar si DescribeDBClusters está en el índice
describe_clusters = [op for op in ops if 'describedbclusters' in op.get('operation', '').lower()]
if describe_clusters:
    print("\nDescribeDBClusters en el índice:")
    for op in describe_clusters:
        print(f"  {op.get('operation')}: count={op.get('resource_count', 0)}")
else:
    print("\n⚠️  DescribeDBClusters NO encontrado en el índice")

