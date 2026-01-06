#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test counting logic step by step."""

import json
import gzip
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

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

# Simular el proceso paso a paso
common_list_keys = [
    'Items', 'items', 'Results', 'results', 'Resources', 'resources',
    'Instances', 'instances', 'Certificates', 'certificates',
    'CertificateSummaryList', 'certificateSummaryList',
    'RestApis', 'restApis', 'Buckets', 'buckets', 'BucketsList', 'Users', 'users',
    'Roles', 'roles', 'Policies', 'policies', 'Groups', 'groups',
    'Vpcs', 'vpcs', 'Subnets', 'subnets', 'SecurityGroups', 'securityGroups',
    'LoadBalancers', 'loadBalancers', 'TargetGroups', 'targetGroups',
    'Listeners', 'listeners',
    'NetworkInterfaces', 'networkInterfaces',
    'Volumes', 'volumes',
    'RouteTables', 'routeTables',  # Esta debería estar aquí
]

if 'data' in inner_data:
    pages = inner_data['data']
    seen_ids = set()
    
    print(f"Processing {len(pages)} pages")
    
    for i, page in enumerate(pages):
        if isinstance(page, dict):
            print(f"\nPage {i+1} keys: {list(page.keys())[:10]}")
            
            # Buscar en common_list_keys
            found_key = None
            for key in common_list_keys:
                if key in page and isinstance(page[key], list):
                    found_key = key
                    print(f"  Found key: {key}, count: {len(page[key])}")
                    break
            
            if found_key:
                items = page[found_key]
                for item in items:
                    if isinstance(item, dict):
                        item_id = item.get('RouteTableId')
                        if item_id:
                            if item_id in seen_ids:
                                print(f"    DUPLICADO: {item_id}")
                            else:
                                seen_ids.add(item_id)
                                print(f"    NUEVO: {item_id}")
    
    print(f"\nTotal unique IDs: {len(seen_ids)}")

