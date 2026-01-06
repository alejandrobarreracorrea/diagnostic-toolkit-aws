#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para depurar el contador de recursos.
"""

import json
import gzip
import sys
from pathlib import Path

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
sys.path.insert(0, str(project_root))

from analyzer.indexer import DataIndexer

def test_count(service, operation, resource_key):
    """Probar el contador para un recurso específico."""
    runs_dir = project_root / "runs"
    runs = sorted([d for d in runs_dir.iterdir() if d.is_dir()], reverse=True)
    run = runs[0] if runs else None
    
    if not run:
        print("No se encontraron runs")
        return
    
    file_path = run / "raw" / service / "us-east-1" / f"{operation}.json.gz"
    
    if not file_path.exists():
        print(f"Archivo no existe: {file_path}")
        return
    
    print(f"\n{'='*60}")
    print(f"Probando: {service}.{operation}")
    print(f"{'='*60}")
    
    with gzip.open(file_path, 'rt', encoding='utf-8') as f:
        data = json.load(f)
    
    inner_data = data.get('data', {})
    
    # Contar manualmente
    pages_data = inner_data.get('data', []) if isinstance(inner_data, dict) and 'data' in inner_data else []
    manual_count = 0
    seen_manual = set()
    
    for page in pages_data:
        if isinstance(page, dict) and resource_key in page:
            resources = page.get(resource_key, [])
            if isinstance(resources, list):
                for item in resources:
                    if isinstance(item, dict):
                        # Buscar ID
                        item_id = item.get('DBClusterSnapshotIdentifier') or item.get('GroupId') or item.get('deploymentConfigName') or item.get('repositoryName')
                        if item_id:
                            if item_id not in seen_manual:
                                seen_manual.add(item_id)
                                manual_count += 1
                    elif isinstance(item, str):
                        if item not in seen_manual:
                            seen_manual.add(item)
                            manual_count += 1
    
    print(f"Conteo manual: {manual_count} (únicos: {len(seen_manual)})")
    
    # Contar con el indexer
    indexer = DataIndexer(run / "raw", run / "index")
    indexer_count = indexer._count_resources(inner_data, service_name=service, operation_name=operation)
    
    print(f"Conteo del indexer: {indexer_count}")
    
    if manual_count != indexer_count:
        print(f"⚠️  DIFERENCIA: Manual={manual_count}, Indexer={indexer_count}")
    else:
        print(f"✅ Coinciden")

if __name__ == "__main__":
    test_count('rds', 'DescribeDBClusterSnapshots', 'DBClusterSnapshots')
    test_count('ec2', 'DescribeSecurityGroups', 'SecurityGroups')
    test_count('codedeploy', 'ListDeploymentConfigs', 'deploymentConfigsList')

