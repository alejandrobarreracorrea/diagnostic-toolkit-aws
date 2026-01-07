#!/usr/bin/env python3
"""Script para debuggear CloudWatch"""

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

cloudwatch_dir = latest_run / 'raw' / 'cloudwatch' / 'us-east-1'

# Verificar qué operaciones hay
if cloudwatch_dir.exists():
    files = list(cloudwatch_dir.glob('*.json.gz'))
    print(f"Archivos de CloudWatch encontrados: {len(files)}")
    for f in files[:15]:
        print(f"  - {f.stem}")
else:
    print("No se encontró directorio de CloudWatch")
    exit(1)

print("\n" + "="*60)

# Verificar DescribeAlarms (alarmas)
alarms_file = cloudwatch_dir / 'DescribeAlarms.json.gz'
if alarms_file.exists():
    with gzip.open(alarms_file, 'rt', encoding='utf-8') as f:
        data = json.load(f)
    
    print("\n=== DescribeAlarms ===")
    print(f"Success: {data.get('metadata', {}).get('success', False)}")
    print(f"Paginated: {data.get('metadata', {}).get('paginated', False)}")
    
    data_content = data.get('data', {})
    if isinstance(data_content, dict):
        # Manejar datos paginados
        if "pages" in data_content and "data" in data_content:
            pages = data_content.get("data", [])
            all_alarms = []
            seen_alarm_names = set()
            for page in pages:
                alarms = page.get("MetricAlarms", []) or page.get("CompositeAlarms", []) or page.get("Alarms", [])
                for alarm in alarms:
                    alarm_name = alarm.get("AlarmName")
                    if alarm_name and alarm_name not in seen_alarm_names:
                        seen_alarm_names.add(alarm_name)
                        all_alarms.append(alarm)
            print(f"Total alarmas únicas (paginado): {len(all_alarms)}")
        else:
            alarms = data_content.get("MetricAlarms", []) or data_content.get("CompositeAlarms", []) or data_content.get("Alarms", [])
            print(f"Total alarmas: {len(alarms)}")
            all_alarms = alarms
        
        if all_alarms:
            print(f"\nAlarmas encontradas: {len(all_alarms)}")
            for i, alarm in enumerate(all_alarms[:5], 1):
                name = alarm.get("AlarmName", "N/A")
                state = alarm.get("StateValue", "N/A")
                print(f"  {i}. {name}: State={state}")
        else:
            print("No se encontraron alarmas")

print("\n" + "="*60)

# Verificar ListDashboards
dashboards_file = cloudwatch_dir / 'ListDashboards.json.gz'
if dashboards_file.exists():
    with gzip.open(dashboards_file, 'rt', encoding='utf-8') as f:
        data = json.load(f)
    
    print("\n=== ListDashboards ===")
    print(f"Success: {data.get('metadata', {}).get('success', False)}")
    
    data_content = data.get('data', {})
    if isinstance(data_content, dict):
        dashboards = data_content.get("DashboardEntries", []) or data_content.get("Dashboards", [])
        print(f"Total dashboards: {len(dashboards)}")
        if dashboards:
            for i, dashboard in enumerate(dashboards[:5], 1):
                name = dashboard.get("DashboardName", "N/A")
                print(f"  {i}. {name}")

print("\n" + "="*60)

# Verificar logs (CloudWatch Logs es un servicio separado)
logs_dir = latest_run / 'raw' / 'logs' / 'us-east-1'
if logs_dir.exists():
    files = list(logs_dir.glob('*.json.gz'))
    print(f"\nArchivos de CloudWatch Logs encontrados: {len(files)}")
    for f in files[:10]:
        print(f"  - {f.stem}")
    
    # Verificar DescribeLogGroups
    log_groups_file = logs_dir / 'DescribeLogGroups.json.gz'
    if log_groups_file.exists():
        with gzip.open(log_groups_file, 'rt', encoding='utf-8') as f:
            data = json.load(f)
        
        print("\n=== DescribeLogGroups ===")
        print(f"Success: {data.get('metadata', {}).get('success', False)}")
        
        data_content = data.get('data', {})
        if isinstance(data_content, dict):
            if "pages" in data_content and "data" in data_content:
                pages = data_content.get("data", [])
                all_groups = []
                for page in pages:
                    groups = page.get("logGroups", []) or page.get("LogGroups", [])
                    all_groups.extend(groups)
                print(f"Total log groups (paginado): {len(all_groups)}")
            else:
                groups = data_content.get("logGroups", []) or data_content.get("LogGroups", [])
                print(f"Total log groups: {len(groups)}")
                all_groups = groups
            
            if all_groups:
                print(f"Log groups encontrados: {len(all_groups)}")
                for i, group in enumerate(all_groups[:5], 1):
                    name = group.get("logGroupName", group.get("LogGroupName", "N/A"))
                    print(f"  {i}. {name}")

