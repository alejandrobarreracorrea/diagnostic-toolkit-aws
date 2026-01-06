#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Inspeccionar todas las páginas de RouteTables y Subnets."""

import json
import gzip
from pathlib import Path

runs_dir = Path("runs")
runs = sorted([d for d in runs_dir.iterdir() if d.is_dir()], reverse=True)
run = runs[0] if runs else None

if not run:
    print("No runs found")
    exit(1)

for resource_type, filename in [('RouteTables', 'DescribeRouteTables'), ('Subnets', 'DescribeSubnets')]:
    file = run / "raw" / "ec2" / "us-east-1" / f"{filename}.json.gz"
    data = json.load(gzip.open(file, 'rt'))
    inner_data = data.get('data', {})
    
    if 'data' in inner_data and isinstance(inner_data['data'], list):
        pages = inner_data['data']
        print(f"\n{resource_type}:")
        print(f"  Total pages: {len(pages)}")
        
        all_items = []
        all_ids = set()
        
        for i, page in enumerate(pages):
            if isinstance(page, dict) and resource_type in page:
                items = page[resource_type]
                if isinstance(items, list):
                    print(f"  Page {i+1}: {len(items)} items")
                    all_items.extend(items)
                    for item in items:
                        if isinstance(item, dict):
                            if resource_type == 'RouteTables':
                                item_id = item.get('RouteTableId')
                            elif resource_type == 'Subnets':
                                item_id = item.get('SubnetId')
                            if item_id:
                                all_ids.add(item_id)
        
        print(f"  Total items across all pages: {len(all_items)}")
        print(f"  Unique IDs: {len(all_ids)}")
        print(f"  First 5 IDs: {list(all_ids)[:5]}")

