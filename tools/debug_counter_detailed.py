#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Debug counter with detailed logging."""

import json
import gzip
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Importar y modificar temporalmente para debug
import analyzer.indexer as indexer_module

# Guardar el método original
original_count = indexer_module.DataIndexer._count_resources

def debug_count_resources(self, data, service_name=None, operation_name=None):
    """Versión con debug del método _count_resources."""
    print(f"\n=== DEBUG: _count_resources ===")
    print(f"Service: {service_name}, Operation: {operation_name}")
    print(f"Data type: {type(data)}")
    
    if isinstance(data, dict):
        print(f"Data keys: {list(data.keys())[:10]}")
        
        if "pages" in data and "data" in data:
            print("Found paginated data")
            seen_ids = set()
            pages_list = data["data"]
            print(f"Pages count: {len(pages_list)}")
            
            for i, page in enumerate(pages_list):
                if isinstance(page, dict):
                    print(f"\nProcessing page {i+1}")
                    print(f"  Page keys: {list(page.keys())[:10]}")
                    
                    # Buscar listas de recursos
                    common_list_keys = [
                        'Items', 'items', 'Results', 'results', 'Resources', 'resources',
                        'Instances', 'instances', 'Certificates', 'certificates',
                        'CertificateSummaryList', 'certificateSummaryList',
                        'RestApis', 'restApis', 'Buckets', 'buckets', 'BucketsList', 'Users', 'users',
                        'Roles', 'roles', 'Policies', 'policies', 'Groups', 'groups',
                        'Vpcs', 'vpcs', 'Subnets', 'subnets', 'SecurityGroups', 'securityGroups',
                        'RouteTables', 'routeTables',
                    ]
                    
                    found_any = False
                    for key in common_list_keys:
                        if key in page and isinstance(page[key], list):
                            print(f"  Found key: {key}, items: {len(page[key])}")
                            found_any = True
                            
                            for j, item in enumerate(page[key][:5]):  # Solo primeros 5
                                if isinstance(item, dict):
                                    item_id = item.get('RouteTableId') or item.get('SubnetId')
                                    if item_id:
                                        if item_id in seen_ids:
                                            print(f"    Item {j}: DUPLICADO {item_id}")
                                        else:
                                            seen_ids.add(item_id)
                                            print(f"    Item {j}: NUEVO {item_id}")
                            break  # Solo procesar la primera clave encontrada
                    
                    if not found_any:
                        print(f"  No se encontró ninguna clave de lista conocida")
            
            print(f"\nTotal seen_ids: {len(seen_ids)}")
            if len(seen_ids) > 0:
                return len(seen_ids)
    
    # Llamar al método original como fallback
    return original_count(self, data, service_name, operation_name)

# Reemplazar temporalmente
indexer_module.DataIndexer._count_resources = debug_count_resources

from analyzer.indexer import DataIndexer

runs_dir = project_root / "runs"
runs = sorted([d for d in runs_dir.iterdir() if d.is_dir()], reverse=True)
run = runs[0] if runs else None

if not run:
    print("No runs found")
    exit(1)

indexer = DataIndexer(run / "raw", run / "index")

file_path = run / "raw" / "ec2" / "us-east-1" / "DescribeRouteTables.json.gz"
with gzip.open(file_path, 'rt', encoding='utf-8') as f:
    data = json.load(f)

inner_data = data.get('data', {})
count = indexer._count_resources(inner_data, service_name='ec2', operation_name='DescribeRouteTables')
print(f"\n=== RESULTADO FINAL: {count} ===")

