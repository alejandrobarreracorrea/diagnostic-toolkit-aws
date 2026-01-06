#!/usr/bin/env python3
"""Script para debuggear el conteo de Neptune"""

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

neptune_dir = latest_run / 'raw' / 'neptune' / 'us-east-1'

# Obtener clusters con TODOS los detalles
clusters = []
clusters_file = neptune_dir / 'DescribeDBClusters.json.gz'
if clusters_file.exists():
    with gzip.open(clusters_file, 'rt') as f:
        data = json.load(f)
    
    print("=== DescribeDBClusters ===")
    print(f"Success: {data.get('metadata', {}).get('success', False)}")
    print(f"Paginated: {data.get('metadata', {}).get('paginated', False)}")
    
    data_content = data.get('data', {})
    if isinstance(data_content, dict) and 'data' in data_content:
        pages = data_content.get('data', [])
        print(f"Total páginas: {len(pages)}")
        
        seen_clusters = set()
        for i, page in enumerate(pages):
            print(f"\n--- Página {i+1} ---")
            page_clusters = page.get('DBClusters', [])
            print(f"Clusters en esta página: {len(page_clusters)}")
            
            for cluster in page_clusters:
                cluster_id = cluster.get('DBClusterIdentifier', 'N/A')
                status = cluster.get('Status', 'N/A')
                engine = cluster.get('Engine', 'N/A')
                engine_version = cluster.get('EngineVersion', 'N/A')
                cluster_arn = cluster.get('DBClusterArn', 'N/A')
                
                is_neptune = engine and 'neptune' in engine.lower()
                marker = "[NEPTUNE]" if is_neptune else "[NO NEPTUNE]"
                
                if cluster_id not in seen_clusters:
                    seen_clusters.add(cluster_id)
                    clusters.append({
                        'id': cluster_id,
                        'status': status,
                        'engine': engine,
                        'version': engine_version,
                        'arn': cluster_arn,
                        'is_neptune': is_neptune
                    })
                    print(f"  {marker} Cluster: {cluster_id}")
                    print(f"    Status: {status}")
                    print(f"    Engine: {engine}")
                    print(f"    Version: {engine_version}")
                    print(f"    ARN: {cluster_arn}")
                else:
                    print(f"  [DUPLICADO] Cluster: {cluster_id}")
        
        print(f"\nTotal clusters únicos: {len(clusters)}")
        
        neptune_clusters = [c for c in clusters if c['is_neptune']]
        non_neptune_clusters = [c for c in clusters if not c['is_neptune']]
        
        print(f"Clusters de Neptune: {len(neptune_clusters)}")
        print(f"Clusters NO de Neptune: {len(non_neptune_clusters)}")
        
        if non_neptune_clusters:
            print("\nClusters que NO son de Neptune (serán excluidos):")
            for c in non_neptune_clusters:
                print(f"  - {c['id']}: Engine={c['engine']}")
        
        if neptune_clusters:
            print("\nClusters de Neptune (serán contados):")
            for c in neptune_clusters:
                print(f"  - {c['id']}: Status={c['status']}")
    else:
        print("Estructura de datos inesperada")
        print(f"Tipo de data_content: {type(data_content)}")
        if isinstance(data_content, dict):
            print(f"Keys: {list(data_content.keys())}")

print("\n" + "="*60)

# Verificar también las instancias
instances_file = neptune_dir / 'DescribeDBInstances.json.gz'
if instances_file.exists():
    with gzip.open(instances_file, 'rt') as f:
        data = json.load(f)
    
    print("\n=== DescribeDBInstances ===")
    data_content = data.get('data', {})
    
    if isinstance(data_content, dict) and 'data' in data_content:
        pages = data_content.get('data', [])
        seen_instances = set()
        all_instances = []
        
        for page in pages:
            for inst in page.get('DBInstances', []):
                inst_id = inst.get('DBInstanceIdentifier', 'N/A')
                if inst_id not in seen_instances:
                    seen_instances.add(inst_id)
                    status = inst.get('DBInstanceStatus', 'N/A')
                    engine = inst.get('Engine', 'N/A')
                    cluster_id = inst.get('DBClusterIdentifier', 'N/A')
                    is_neptune = engine and 'neptune' in engine.lower()
                    all_instances.append({
                        'id': inst_id,
                        'status': status,
                        'engine': engine,
                        'cluster': cluster_id,
                        'is_neptune': is_neptune
                    })
        
        print(f"Total instancias únicas: {len(all_instances)}")
        
        neptune_instances = [i for i in all_instances if i['is_neptune']]
        non_neptune_instances = [i for i in all_instances if not i['is_neptune']]
        
        print(f"Instancias de Neptune: {len(neptune_instances)}")
        print(f"Instancias NO de Neptune: {len(non_neptune_instances)}")
        
        if non_neptune_instances:
            print("\nInstancias que NO son de Neptune (serán excluidas):")
            for i in non_neptune_instances:
                print(f"  - {i['id']}: Engine={i['engine']}, Status={i['status']}")

