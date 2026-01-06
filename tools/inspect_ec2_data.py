#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para inspeccionar la estructura de datos de EC2 DescribeInstances.
"""

import json
import gzip
from pathlib import Path

project_root = Path(__file__).parent.parent

# Encontrar último run
runs_dir = project_root / "runs"
runs = sorted([d for d in runs_dir.iterdir() if d.is_dir()], reverse=True)
run = runs[0] if runs else None

if not run:
    print("No se encontraron runs")
    exit(1)

print(f"Run: {run.name}")

# Leer archivo DescribeInstances
file_path = run / "raw" / "ec2" / "us-east-1" / "DescribeInstances.json.gz"

if not file_path.exists():
    print(f"Archivo no existe: {file_path}")
    exit(1)

with gzip.open(file_path, 'rt', encoding='utf-8') as f:
    data = json.load(f)

print("\nEstructura del archivo:")
print(f"  Keys principales: {list(data.keys())}")

# Nivel 1: data
inner_data = data.get("data", {})
print(f"\nNivel data:")
print(f"  Tipo: {type(inner_data).__name__}")
if isinstance(inner_data, dict):
    print(f"  Keys: {list(inner_data.keys())}")

# Nivel 2: data["data"] (páginas)
if isinstance(inner_data, dict) and "data" in inner_data:
    pages_data = inner_data.get("data", [])
    print(f"\nPáginas:")
    print(f"  Tipo: {type(pages_data).__name__}")
    print(f"  Cantidad: {len(pages_data)}")
    
    if pages_data and isinstance(pages_data, list):
        first_page = pages_data[0]
        print(f"\nPrimera página:")
        print(f"  Tipo: {type(first_page).__name__}")
        if isinstance(first_page, dict):
            print(f"  Keys: {list(first_page.keys())}")
            
            # Buscar Reservations
            reservations = first_page.get("Reservations", [])
            print(f"\nReservations:")
            print(f"  Cantidad: {len(reservations)}")
            
            if reservations:
                first_reservation = reservations[0]
                print(f"  Primera reservation keys: {list(first_reservation.keys()) if isinstance(first_reservation, dict) else 'N/A'}")
                
                instances = first_reservation.get("Instances", [])
                print(f"  Instancias en primera reservation: {len(instances)}")
                
                # Contar todas las instancias en todas las páginas
                total_instances = 0
                for page in pages_data:
                    if isinstance(page, dict):
                        page_reservations = page.get("Reservations", [])
                        for res in page_reservations:
                            if isinstance(res, dict):
                                page_instances = res.get("Instances", [])
                                total_instances += len(page_instances)
                
                print(f"\n{'='*60}")
                print(f"TOTAL DE INSTANCIAS EN TODAS LAS PÁGINAS: {total_instances}")
                print(f"{'='*60}")
                
                if total_instances > 0:
                    print(f"\nPrimeras instancias:")
                    instance_count = 0
                    for page in pages_data:
                        if isinstance(page, dict):
                            page_reservations = page.get("Reservations", [])
                            for res in page_reservations:
                                if isinstance(res, dict):
                                    page_instances = res.get("Instances", [])
                                    for inst in page_instances:
                                        if instance_count < 10:
                                            instance_id = inst.get("InstanceId", "N/A")
                                            instance_type = inst.get("InstanceType", "N/A")
                                            state = inst.get("State", {}).get("Name", "N/A") if isinstance(inst.get("State"), dict) else "N/A"
                                            print(f"  {instance_id} - {instance_type} - {state}")
                                            instance_count += 1
                                        else:
                                            break
                                    if instance_count >= 10:
                                        break
                            if instance_count >= 10:
                                break

