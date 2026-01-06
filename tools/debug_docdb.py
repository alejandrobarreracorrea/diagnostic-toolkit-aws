#!/usr/bin/env python3
"""Script para debuggear el conteo de DocumentDB"""

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

docdb_dir = latest_run / 'raw' / 'docdb' / 'us-east-1'

# Obtener clusters con TODOS los detalles
clusters = []
clusters_file = docdb_dir / 'DescribeDBClusters.json.gz'
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
                
                if cluster_id not in seen_clusters:
                    seen_clusters.add(cluster_id)
                    clusters.append({
                        'id': cluster_id,
                        'status': status,
                        'engine': engine,
                        'version': engine_version,
                        'arn': cluster_arn
                    })
                    print(f"  Cluster: {cluster_id}")
                    print(f"    Status: {status}")
                    print(f"    Engine: {engine}")
                    print(f"    Version: {engine_version}")
                    print(f"    ARN: {cluster_arn}")
                else:
                    print(f"  [DUPLICADO] Cluster: {cluster_id}")
        
        print(f"\nTotal clusters únicos: {len(clusters)}")
        
        # Verificar estados
        deleted = [c for c in clusters if 'deleted' in c['status'].lower() or 'deleting' in c['status'].lower() or 'failed' in c['status'].lower()]
        valid = [c for c in clusters if c not in deleted]
        
        print(f"Clusters válidos (no deleted/deleting/failed): {len(valid)}")
        print(f"Clusters eliminados/fallidos: {len(deleted)}")
        
        if deleted:
            print("\nClusters eliminados:")
            for c in deleted:
                print(f"  - {c['id']}: {c['status']}")
        
        if valid:
            print("\nClusters válidos:")
            for c in valid:
                print(f"  - {c['id']}: {c['status']}")
    else:
        print("Estructura de datos inesperada")
        print(f"Tipo de data_content: {type(data_content)}")
        if isinstance(data_content, dict):
            print(f"Keys: {list(data_content.keys())}")

print("\n" + "="*60)

# Verificar también las instancias
instances_file = docdb_dir / 'DescribeDBInstances.json.gz'
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
                    cluster_id = inst.get('DBClusterIdentifier', 'N/A')
                    all_instances.append({
                        'id': inst_id,
                        'status': status,
                        'cluster': cluster_id
                    })
        
        print(f"Total instancias únicas: {len(all_instances)}")
        
        # Verificar si las instancias tienen clusters asociados que existen
        cluster_ids = {c['id'] for c in clusters}
        instances_with_valid_cluster = [i for i in all_instances if i['cluster'] in cluster_ids]
        instances_without_cluster = [i for i in all_instances if i['cluster'] not in cluster_ids and i['cluster'] != 'N/A']
        
        print(f"Instancias con cluster válido: {len(instances_with_valid_cluster)}")
        print(f"Instancias sin cluster válido: {len(instances_without_cluster)}")
        
        if instances_without_cluster:
            print("\nInstancias sin cluster válido:")
            for i in instances_without_cluster:
                print(f"  - {i['id']}: cluster={i['cluster']}, status={i['status']}")
