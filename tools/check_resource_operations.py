#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para verificar qué operaciones se están ejecutando para los recursos que mencionas.
"""

import json
import sys
from pathlib import Path
from collections import defaultdict

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
    print("🔍 VERIFICACIÓN DE OPERACIONES PARA RECURSOS")
    print("="*80)
    
    # Mapeo de recursos a operaciones
    resource_operations = {
        'Config ResourceCompliance': {
            'service': 'config',
            'operations': ['GetComplianceSummaryByResourceType', 'DescribeComplianceByResource']
        },
        'EC2 NetworkInterface': {
            'service': 'ec2',
            'operations': ['DescribeNetworkInterfaces']
        },
        'CloudWatch Alarm': {
            'service': 'cloudwatch',
            'operations': ['DescribeAlarms']
        },
        'EC2 Volume': {
            'service': 'ec2',
            'operations': ['DescribeVolumes']
        },
        'ElasticLoadBalancingV2 TargetGroup': {
            'service': 'elbv2',
            'operations': ['DescribeTargetGroups']
        },
        'EC2 SecurityGroup': {
            'service': 'ec2',
            'operations': ['DescribeSecurityGroups']
        },
        'RDS DBClusterSnapshot': {
            'service': 'rds',
            'operations': ['DescribeDBClusterSnapshots']
        },
        'ElasticLoadBalancingV2 Listener': {
            'service': 'elbv2',
            'operations': ['DescribeListeners']
        },
        'CodeDeploy DeploymentConfig': {
            'service': 'codedeploy',
            'operations': ['ListDeploymentConfigs']
        },
        'EC2 Instance': {
            'service': 'ec2',
            'operations': ['DescribeInstances']
        }
    }
    
    # Encontrar último run
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
    
    print(f"\n{'='*80}")
    print("📊 ESTADO DE OPERACIONES")
    print(f"{'='*80}")
    
    results = defaultdict(dict)
    
    for resource_name, resource_info in resource_operations.items():
        service_name = resource_info['service']
        expected_ops = resource_operations[resource_name]['operations']
        
        service_data = idx.get("services", {}).get(service_name, {})
        
        if not service_data:
            results[resource_name] = {
                'status': '❌ Servicio no encontrado',
                'operations': []
            }
            continue
        
        found_ops = []
        for region_name, region_data in service_data.get("regions", {}).items():
            for op_info in region_data.get("operations", []):
                op_name = op_info.get("operation", "")
                # Normalizar nombre (puede estar en PascalCase o snake_case)
                op_normalized = op_name.replace('_', '').lower()
                
                for expected_op in expected_ops:
                    expected_normalized = expected_op.replace('_', '').lower()
                    if expected_normalized in op_normalized or op_normalized in expected_normalized:
                        success = op_info.get("success", False)
                        resource_count = op_info.get("resource_count", 0) or 0
                        found_ops.append({
                            'operation': op_name,
                            'success': success,
                            'resource_count': resource_count,
                            'region': region_name
                        })
        
        if found_ops:
            total_resources = sum(op['resource_count'] for op in found_ops if op['success'])
            successful_ops = sum(1 for op in found_ops if op['success'])
            results[resource_name] = {
                'status': f'✅ {successful_ops}/{len(found_ops)} operaciones exitosas',
                'operations': found_ops,
                'total_resources': total_resources
            }
        else:
            results[resource_name] = {
                'status': '❌ Operaciones no encontradas',
                'operations': [],
                'expected_operations': expected_ops
            }
    
    # Mostrar resultados
    print(f"\n{'Recurso':<40} {'Estado':<30} {'Recursos'}")
    print("="*80)
    
    for resource_name, result in results.items():
        status = result['status']
        total = result.get('total_resources', 0)
        print(f"{resource_name:<40} {status:<30} {total}")
        
        if result.get('operations'):
            for op in result['operations']:
                op_status = '✅' if op['success'] else '❌'
                print(f"  {op_status} {op['operation']} ({op['region']}): {op['resource_count']} recursos")
        elif result.get('expected_operations'):
            print(f"  Operaciones esperadas: {', '.join(result['expected_operations'])}")
    
    print(f"\n{'='*80}")
    print("💡 RECOMENDACIONES")
    print(f"{'='*80}")
    
    missing = [name for name, result in results.items() if 'no encontradas' in result['status'] or 'no encontrado' in result['status']]
    if missing:
        print(f"\n⚠️  Recursos sin operaciones encontradas:")
        for name in missing:
            print(f"   - {name}")
        print(f"\n   Estas operaciones deberían ejecutarse pero no se están encontrando.")
        print(f"   Verifica que las operaciones se estén ejecutando en el collector.")
    
    zero_resources = [name for name, result in results.items() if result.get('total_resources', 0) == 0 and 'exitosas' in result.get('status', '')]
    if zero_resources:
        print(f"\n⚠️  Recursos con operaciones exitosas pero sin recursos contados:")
        for name in zero_resources:
            print(f"   - {name}")
        print(f"\n   Las operaciones se ejecutan correctamente pero no se están contando recursos.")
        print(f"   Esto puede indicar un problema en el contador de recursos.")
    
    print(f"\n{'='*80}")

if __name__ == "__main__":
    main()

