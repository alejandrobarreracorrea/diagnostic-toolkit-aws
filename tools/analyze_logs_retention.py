#!/usr/bin/env python3
"""Script para analizar retención de logs y metric filters"""

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

logs_dir = latest_run / 'raw' / 'logs' / 'us-east-1'

# Verificar DescribeLogGroups
log_groups_file = logs_dir / 'DescribeLogGroups.json.gz'
if log_groups_file.exists():
    with gzip.open(log_groups_file, 'rt', encoding='utf-8') as f:
        data = json.load(f)
    
    print("=== Análisis de Log Groups ===\n")
    
    data_content = data.get('data', {})
    if isinstance(data_content, dict):
        # Manejar datos paginados
        if "pages" in data_content and "data" in data_content:
            pages = data_content.get("data", [])
            all_groups = []
            for page in pages:
                groups = page.get("logGroups", []) or page.get("LogGroups", [])
                all_groups.extend(groups)
        else:
            groups = data_content.get("logGroups", []) or data_content.get("LogGroups", [])
            all_groups = groups
        
        print(f"Total log groups: {len(all_groups)}\n")
        
        # Analizar retención
        groups_with_retention = 0
        groups_without_retention = 0
        retention_periods = {}
        
        for group in all_groups:
            retention = group.get("retentionInDays")
            if retention:
                groups_with_retention += 1
                retention_periods[retention] = retention_periods.get(retention, 0) + 1
            else:
                groups_without_retention += 1
        
        print(f"Log groups con retención configurada: {groups_with_retention}")
        print(f"Log groups sin retención (retención indefinida): {groups_without_retention}")
        print(f"\nDistribución de períodos de retención:")
        for days, count in sorted(retention_periods.items()):
            print(f"  {days} días: {count} log groups")

# Verificar DescribeMetricFilters
metric_filters_file = logs_dir / 'DescribeMetricFilters.json.gz'
if metric_filters_file.exists():
    with gzip.open(metric_filters_file, 'rt', encoding='utf-8') as f:
        data = json.load(f)
    
    print("\n=== Análisis de Metric Filters ===\n")
    
    data_content = data.get('data', {})
    if isinstance(data_content, dict):
        # Manejar datos paginados
        if "pages" in data_content and "data" in data_content:
            pages = data_content.get("data", [])
            all_filters = []
            for page in pages:
                filters = page.get("metricFilters", []) or page.get("MetricFilters", [])
                all_filters.extend(filters)
        else:
            filters = data_content.get("metricFilters", []) or data_content.get("MetricFilters", [])
            all_filters = filters
        
        print(f"Total metric filters: {len(all_filters)}")
        if all_filters:
            print("\nMetric filters encontrados:")
            for i, filter_item in enumerate(all_filters[:5], 1):
                name = filter_item.get("filterName", "N/A")
                log_group = filter_item.get("logGroupName", "N/A")
                print(f"  {i}. {name} (log group: {log_group})")

