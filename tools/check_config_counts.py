#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para verificar GetDiscoveredResourceCounts de Config.
"""

import json
import gzip
from pathlib import Path
import sys

# Configurar codificación UTF-8 para Windows
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

project_root = Path(__file__).parent.parent

# Encontrar último run
runs_dir = project_root / "runs"
runs = sorted([d for d in runs_dir.iterdir() if d.is_dir()], reverse=True)
run = runs[0] if runs else None

if not run:
    print("No se encontraron runs")
    exit(1)

print(f"Run: {run.name}")

# Buscar archivo GetDiscoveredResourceCounts
file_path = run / "raw" / "config" / "us-east-1" / "GetDiscoveredResourceCounts.json.gz"

if not file_path.exists():
    print(f"❌ Archivo no existe: {file_path}")
    print("\nEsto significa que GetDiscoveredResourceCounts no se ejecutó.")
    print("Aunque es 'safe to call', puede que haya fallado o no se haya intentado.")
    exit(1)

print(f"✅ Archivo encontrado: {file_path.name}")

# Leer datos
with gzip.open(file_path, 'rt', encoding='utf-8') as f:
    data = json.load(f)

inner_data = data.get('data', {})
pages_data = inner_data.get('data', []) if isinstance(inner_data, dict) and 'data' in inner_data else []

print(f"\nPáginas: {len(pages_data)}")

if pages_data:
    first_page = pages_data[0]
    resource_counts = first_page.get('resourceCounts', [])
    
    print(f"\nTipos de recursos encontrados: {len(resource_counts)}")
    print(f"\n{'='*80}")
    print("RECURSOS DE CONFIG POR TIPO")
    print(f"{'='*80}")
    
    total_resources = 0
    for r in resource_counts:
        resource_type = r.get('resourceType', 'N/A')
        count = r.get('count', 0)
        total_resources += count
        print(f"  {resource_type}: {count}")
    
    print(f"\n{'='*80}")
    print(f"TOTAL DE RECURSOS EN CONFIG: {total_resources}")
    print(f"{'='*80}")
    
    print(f"\n💡 Estos son los recursos que deberían aparecer en el inventario.")
    print(f"   Para obtener los detalles de cada recurso, necesitamos ejecutar")
    print(f"   ListDiscoveredResources para cada tipo de recurso.")
else:
    print("\n⚠️  No se encontraron datos en el archivo")

