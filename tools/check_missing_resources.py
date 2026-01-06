#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para verificar recursos faltantes del inventario.
"""

import json
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

def find_latest_run():
    """Encontrar el run más reciente."""
    runs_dir = project_root / "runs"
    if not runs_dir.exists():
        return None
    runs = sorted([d for d in runs_dir.iterdir() if d.is_dir()], reverse=True)
    return runs[0] if runs else None

def main():
    print("="*80)
    print("🔍 VERIFICACIÓN DE RECURSOS FALTANTES")
    print("="*80)
    
    # Valores esperados de AWS Config
    expected = {
        'EC2::EIP': 13,
        'ELBv2::LoadBalancer': 13,
        'S3::Bucket': 9,
        'KMS::Alias': 8,
        'KMS::Key': 8,
        'RDS::DBSnapshot': 8,
        'CloudFormation::Stack': 6,
        'EKS::Addon': 6,
        'Events::Rule': 6,
        'SQS::Queue': 6,
    }
    
    # Mapeo de recursos a operaciones
    resource_operations = {
        'EC2::EIP': {
            'service': 'ec2',
            'operations': ['DescribeAddresses']
        },
        'ELBv2::LoadBalancer': {
            'service': 'elbv2',
            'operations': ['DescribeLoadBalancers']
        },
        'S3::Bucket': {
            'service': 's3',
            'operations': ['ListBuckets']
        },
        'KMS::Alias': {
            'service': 'kms',
            'operations': ['ListAliases']
        },
        'KMS::Key': {
            'service': 'kms',
            'operations': ['ListKeys']
        },
        'RDS::DBSnapshot': {
            'service': 'rds',
            'operations': ['DescribeDBSnapshots']
        },
        'CloudFormation::Stack': {
            'service': 'cloudformation',
            'operations': ['ListStacks']
        },
        'EKS::Addon': {
            'service': 'eks',
            'operations': ['ListAddons']
        },
        'Events::Rule': {
            'service': 'events',
            'operations': ['ListRules']
        },
        'SQS::Queue': {
            'service': 'sqs',
            'operations': ['ListQueues']
        }
    }
    
    run_dir = find_latest_run()
    if not run_dir:
        print("\n❌ No se encontraron runs disponibles")
        return
    
    print(f"\n📁 Analizando run: {run_dir.name}")
    
    # Cargar índice
    index_file = run_dir / "index" / "index.json"
    if not index_file.exists():
        print(f"\n❌ No se encontró índice en {run_dir.name}")
        return
    
    with open(index_file, 'r', encoding='utf-8') as f:
        idx = json.load(f)
    
    print(f"\n{'Recurso':<40} {'Esperado':<10} {'Encontrado':<12} {'Estado':<15}")
    print("="*80)
    
    for resource_name, expected_count in expected.items():
        resource_info = resource_operations.get(resource_name, {})
        service_name = resource_info.get('service', '')
        expected_ops = resource_info.get('operations', [])
        
        if not service_name:
            print(f"{resource_name:<40} {expected_count:<10} {'N/A':<12} {'❌ No mapeado':<15}")
            continue
        
        service_data = idx.get("services", {}).get(service_name, {})
        
        if not service_data:
            print(f"{resource_name:<40} {expected_count:<10} {'0':<12} {'❌ Servicio no encontrado':<15}")
            continue
        
        found_count = 0
        found_ops = []
        
        for region_name, region_data in service_data.get("regions", {}).items():
            for op_info in region_data.get("operations", []):
                op_name = op_info.get("operation", "")
                op_normalized = op_name.replace('_', '').lower()
                
                for expected_op in expected_ops:
                    expected_normalized = expected_op.replace('_', '').lower()
                    if expected_normalized in op_normalized or op_normalized in expected_normalized:
                        success = op_info.get("success", False)
                        resource_count = op_info.get("resource_count", 0) or 0
                        if success:
                            found_count += resource_count
                            found_ops.append({
                                'operation': op_name,
                                'count': resource_count,
                                'region': region_name
                            })
        
        if found_count == expected_count:
            state = "✅ Correcto"
        elif found_count < expected_count:
            state = f"⚠️  Faltan {expected_count - found_count}"
        elif found_count > expected_count:
            state = f"⚠️  {found_count - expected_count} más"
        else:
            state = "❌ No encontrado"
        
        print(f"{resource_name:<40} {expected_count:<10} {found_count:<12} {state:<15}")
        if found_ops:
            for op in found_ops:
                print(f"  → {op['operation']} ({op['region']}): {op['count']} recursos")
    
    print("="*80)

if __name__ == "__main__":
    main()

