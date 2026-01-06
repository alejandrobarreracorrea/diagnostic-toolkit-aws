#!/usr/bin/env python3
"""Script para verificar el inventario"""

import json
from pathlib import Path

# Encontrar el último run
runs = sorted([d for d in Path('runs').iterdir() if d.is_dir()], 
              key=lambda x: x.stat().st_mtime, reverse=True)
if not runs:
    print("No se encontraron runs")
    exit(1)

latest_run = runs[0]
print(f"Verificando inventario del run: {latest_run.name}\n")

inv_file = latest_run / 'outputs' / 'inventory' / 'inventory.json'
if not inv_file.exists():
    print("No se encontró el archivo de inventario")
    exit(1)

with open(inv_file, 'r', encoding='utf-8') as f:
    inv = json.load(f)

# Verificar Neptune
neptune = inv.get('services', {}).get('neptune', {})
print(f"Neptune en inventario: {neptune.get('resource_count', 0)} recursos")
print(f"Regiones: {neptune.get('regions', [])}")

# Verificar DocumentDB
docdb = inv.get('services', {}).get('docdb', {})
print(f"\nDocumentDB en inventario: {docdb.get('resource_count', 0)} recursos")
print(f"Regiones: {docdb.get('regions', [])}")

