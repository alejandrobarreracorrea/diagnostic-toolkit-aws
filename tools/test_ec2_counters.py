#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test de contadores para recursos EC2."""

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

tests = [
    ('ec2', 'DescribeRouteTables'),
    ('ec2', 'DescribeSubnets'),
    ('ec2', 'DescribeLaunchTemplates'),
]

for service, operation in tests:
    file_path = run / "raw" / service / "us-east-1" / f"{operation}.json.gz"
    if file_path.exists():
        with gzip.open(file_path, 'rt', encoding='utf-8') as f:
            data = json.load(f)
        count = indexer._count_resources(data.get('data', {}), service_name=service, operation_name=operation)
        print(f"{service}.{operation}: {count} recursos")

