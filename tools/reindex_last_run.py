#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para reindexar el último run y verificar el contador de instancias EC2.
"""

import sys
from pathlib import Path

# Configurar codificación UTF-8 para Windows
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from analyzer.indexer import DataIndexer

def main():
    # Encontrar último run
    runs_dir = project_root / "runs"
    if not runs_dir.exists():
        print("No se encontraron runs")
        return
    
    runs = sorted([d for d in runs_dir.iterdir() if d.is_dir()], reverse=True)
    if not runs:
        print("No se encontraron runs")
        return
    
    run_dir = runs[0]
    print(f"Reindexando run: {run_dir.name}")
    
    # Reindexar
    raw_dir = run_dir / "raw"
    index_dir = run_dir / "index"
    
    indexer = DataIndexer(raw_dir, index_dir)
    index = indexer.index_all()
    
    # Verificar EC2
    ec2_data = index.get("services", {}).get("ec2", {})
    if ec2_data:
        print(f"\n{'='*60}")
        print("RESULTADOS EC2")
        print(f"{'='*60}")
        
        total_instances = 0
        total_vpcs = 0
        total_subnets = 0
        
        for region_name, region_data in ec2_data.get("regions", {}).items():
            print(f"\nRegión: {region_name}")
            for op_info in region_data.get("operations", []):
                op_name = op_info.get("operation", "")
                resource_count = op_info.get("resource_count", 0) or 0
                success = op_info.get("success", False)
                
                # Mostrar todas las operaciones principales de EC2
                if any(x in op_name.lower() for x in ["describeinstances", "describevpcs", "describesubnets", 
                                                       "describeroutetables", "describelaunchtemplates", 
                                                       "describenetworkacls", "describesecuritygroups",
                                                       "describevolumes", "describenetworkinterfaces"]):
                    print(f"  {op_name}: success={success}, resources={resource_count}")
                    
                    if success:
                        if "describeinstances" in op_name.lower():
                            total_instances += resource_count
                        elif "describevpcs" in op_name.lower():
                            total_vpcs += resource_count
                        elif "describesubnets" in op_name.lower():
                            total_subnets += resource_count
        
        print(f"\n{'='*60}")
        print(f"RESUMEN EC2:")
        print(f"  Instancias: {total_instances}")
        print(f"  VPCs: {total_vpcs}")
        print(f"  Subnets: {total_subnets}")
        print(f"{'='*60}")
    else:
        print("No se encontraron datos de EC2")

if __name__ == "__main__":
    main()

