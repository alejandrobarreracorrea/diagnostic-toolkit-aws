#!/usr/bin/env python3
"""Script para debuggear el conteo de MemoryDB"""

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

memorydb_dir = latest_run / 'raw' / 'memorydb' / 'us-east-1'

# Verificar qué operaciones hay
if memorydb_dir.exists():
    files = list(memorydb_dir.glob('*.json.gz'))
    print(f"Archivos de MemoryDB encontrados: {len(files)}")
    for f in files[:10]:
        print(f"  - {f.stem}")
else:
    print("No se encontró directorio de MemoryDB")
    exit(1)

print("\n" + "="*60)

# Verificar DescribeClusters
clusters_file = memorydb_dir / 'DescribeClusters.json.gz'
if clusters_file.exists():
    with gzip.open(clusters_file, 'rt') as f:
        data = json.load(f)
    
    print("\n=== DescribeClusters ===")
    print(f"Success: {data.get('metadata', {}).get('success', False)}")
    print(f"Paginated: {data.get('metadata', {}).get('paginated', False)}")
    
    data_content = data.get('data', {})
    if isinstance(data_content, dict) and 'data' in data_content:
        pages = data_content.get('data', [])
        print(f"Total páginas: {len(pages)}")
        
        seen_clusters = set()
        all_clusters = []
        
        for i, page in enumerate(pages):
            print(f"\n--- Página {i+1} ---")
            page_clusters = page.get('Clusters', [])
            print(f"Clusters en esta página: {len(page_clusters)}")
            
            for cluster in page_clusters:
                cluster_id = cluster.get('Name', 'N/A')
                status = cluster.get('Status', 'N/A')
                engine = cluster.get('Engine', 'N/A')
                
                is_memorydb = engine and 'memorydb' in engine.lower()
                marker = "[MEMORYDB]" if is_memorydb else "[NO MEMORYDB]"
                
                if cluster_id not in seen_clusters:
                    seen_clusters.add(cluster_id)
                    all_clusters.append({
                        'id': cluster_id,
                        'status': status,
                        'engine': engine,
                        'is_memorydb': is_memorydb
                    })
                    print(f"  {marker} Cluster: {cluster_id}")
                    print(f"    Status: {status}")
                    print(f"    Engine: {engine}")
                else:
                    print(f"  [DUPLICADO] Cluster: {cluster_id}")
        
        print(f"\nTotal clusters únicos: {len(all_clusters)}")
        
        memorydb_clusters = [c for c in all_clusters if c['is_memorydb']]
        non_memorydb_clusters = [c for c in all_clusters if not c['is_memorydb']]
        
        print(f"Clusters de MemoryDB: {len(memorydb_clusters)}")
        print(f"Clusters NO de MemoryDB: {len(non_memorydb_clusters)}")
        
        if non_memorydb_clusters:
            print("\nClusters que NO son de MemoryDB (serán excluidos):")
            for c in non_memorydb_clusters:
                print(f"  - {c['id']}: Engine={c['engine']}")
        
        if memorydb_clusters:
            print("\nClusters de MemoryDB (serán contados):")
            for c in memorydb_clusters:
                print(f"  - {c['id']}: Status={c['status']}")
    else:
        print("Estructura de datos inesperada")
        print(f"Tipo de data_content: {type(data_content)}")
        if isinstance(data_content, dict):
            print(f"Keys: {list(data_content.keys())}")

