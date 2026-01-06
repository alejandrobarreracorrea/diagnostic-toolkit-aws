#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Debug RouteTables counting."""

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
print("Data structure:")
print(f"  Has 'pages': {'pages' in inner_data}")
print(f"  Has 'data': {'data' in inner_data}")

if 'data' in inner_data:
    pages = inner_data['data']
    print(f"  Pages count: {len(pages)}")
    
    seen_ids = set()
    for i, page in enumerate(pages):
        if isinstance(page, dict) and 'RouteTables' in page:
            route_tables = page.get('RouteTables', [])
            print(f"\nPage {i+1}:")
            print(f"  RouteTables count: {len(route_tables)}")
            for rt in route_tables:
                if isinstance(rt, dict):
                    rt_id = rt.get('RouteTableId')
                    if rt_id:
                        if rt_id in seen_ids:
                            print(f"    DUPLICADO: {rt_id}")
                        else:
                            seen_ids.add(rt_id)
                            print(f"    NUEVO: {rt_id}")
    
    print(f"\nTotal unique IDs: {len(seen_ids)}")
    print(f"Expected: 4")

# Test the actual counter
count = indexer._count_resources(inner_data, service_name='ec2', operation_name='DescribeRouteTables')
print(f"\nCounter result: {count}")

