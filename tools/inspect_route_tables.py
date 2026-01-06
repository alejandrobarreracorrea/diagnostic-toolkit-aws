#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Inspeccionar estructura de RouteTables."""

import json
import gzip
from pathlib import Path

runs_dir = Path("runs")
runs = sorted([d for d in runs_dir.iterdir() if d.is_dir()], reverse=True)
run = runs[0] if runs else None

if not run:
    print("No runs found")
    exit(1)

file = run / "raw" / "ec2" / "us-east-1" / "DescribeRouteTables.json.gz"
data = json.load(gzip.open(file, 'rt'))

print("Metadata success:", data.get('metadata', {}).get('success', False))
inner_data = data.get('data', {})
print("Has pages:", 'pages' in inner_data)
print("Has data:", 'data' in inner_data)

if 'data' in inner_data and isinstance(inner_data['data'], list) and len(inner_data['data']) > 0:
    first_page = inner_data['data'][0]
    if isinstance(first_page, dict):
        print("First page keys:", list(first_page.keys())[:10])
        if 'RouteTables' in first_page:
            print(f"RouteTables count: {len(first_page['RouteTables'])}")
            if len(first_page['RouteTables']) > 0:
                print("First RouteTable keys:", list(first_page['RouteTables'][0].keys())[:10])
                print("First RouteTableId:", first_page['RouteTables'][0].get('RouteTableId'))

