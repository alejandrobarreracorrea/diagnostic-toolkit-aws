#!/usr/bin/env python3
"""Script para analizar alarmas de CloudWatch y sus acciones"""

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
alarms_file = cloudwatch_dir / 'DescribeAlarms.json.gz'

if alarms_file.exists():
    with gzip.open(alarms_file, 'rt', encoding='utf-8') as f:
        data = json.load(f)
    
    print("=== Análisis de Alarmas de CloudWatch ===\n")
    
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
        else:
            alarms = data_content.get("MetricAlarms", []) or data_content.get("CompositeAlarms", []) or data_content.get("Alarms", [])
            all_alarms = alarms
        
        print(f"Total alarmas: {len(all_alarms)}\n")
        
        # Analizar acciones
        alarms_with_actions = 0
        alarms_with_sns = 0
        alarms_with_sqs = 0
        alarms_without_actions = 0
        
        for alarm in all_alarms:
            alarm_actions = alarm.get("AlarmActions", [])
            ok_actions = alarm.get("OKActions", [])
            insufficient_data_actions = alarm.get("InsufficientDataActions", [])
            
            all_actions = alarm_actions + ok_actions + insufficient_data_actions
            
            if all_actions:
                alarms_with_actions += 1
                # Verificar si hay SNS o SQS
                for action in all_actions:
                    if "sns" in action.lower() or "arn:aws:sns" in action:
                        alarms_with_sns += 1
                        break
                    elif "sqs" in action.lower() or "arn:aws:sqs" in action:
                        alarms_with_sqs += 1
                        break
            else:
                alarms_without_actions += 0
        
        print(f"Alarmas con acciones: {alarms_with_actions}")
        print(f"Alarmas con SNS: {alarms_with_sns}")
        print(f"Alarmas con SQS: {alarms_with_sqs}")
        print(f"Alarmas sin acciones: {len(all_alarms) - alarms_with_actions}")
        
        # Mostrar ejemplos
        print("\n=== Ejemplos de alarmas con acciones ===")
        count = 0
        for alarm in all_alarms:
            alarm_actions = alarm.get("AlarmActions", [])
            if alarm_actions and count < 3:
                print(f"\nAlarma: {alarm.get('AlarmName')}")
                print(f"  Acciones: {alarm_actions}")
                count += 1

