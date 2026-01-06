#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para verificar los conteos de recursos y compararlos con AWS Config.
"""

import json
import gzip
import sys
from pathlib import Path
from collections import Counter

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

def count_resources_in_file(file_path, resource_key):
    """Contar recursos en un archivo."""
    if not file_path.exists():
        return None, "File not found"
    
    try:
        with gzip.open(file_path, 'rt', encoding='utf-8') as f:
            data = json.load(f)
        
        inner_data = data.get('data', {})
        if not inner_data:
            return 0, "No data"
        
        # Formato paginado
        if isinstance(inner_data, dict) and 'data' in inner_data:
            pages_data = inner_data.get('data', [])
            total = 0
            for page in pages_data:
                if isinstance(page, dict) and resource_key in page:
                    resources = page.get(resource_key, [])
                    if isinstance(resources, list):
                        total += len(resources)
            return total, "OK"
        
        # Formato directo
        if resource_key in inner_data:
            resources = inner_data.get(resource_key, [])
            if isinstance(resources, list):
                return len(resources), "OK"
        
        return 0, f"Key '{resource_key}' not found"
    except Exception as e:
        return None, str(e)

def main():
    print("="*80)
    print("🔍 VERIFICACIÓN DE CONTEOS DE RECURSOS")
    print("="*80)
    
    run_dir = find_latest_run()
    if not run_dir:
        print("\n❌ No se encontraron runs disponibles")
        return
    
    print(f"\n📁 Analizando run: {run_dir.name}")
    
    # Valores esperados de AWS Config
    expected = {
        'CloudWatch::Alarm': 66,
        'EC2::NetworkInterface': 66,
        'EC2::Volume': 25,
        'EC2::SecurityGroup': 21,
        'RDS::DBClusterSnapshot': 20,
        'CodeDeploy::DeploymentConfig': 17,
        'ELBv2::Listener': 17,
        'EC2::Instance': 14,
        'ECR::Repository': 14,
    }
    
    # Archivos a verificar
    checks = [
        ('CloudWatch::Alarm', 'cloudwatch', 'us-east-1', 'DescribeAlarms', 'MetricAlarms'),
        ('EC2::NetworkInterface', 'ec2', 'us-east-1', 'DescribeNetworkInterfaces', 'NetworkInterfaces'),
        ('EC2::Volume', 'ec2', 'us-east-1', 'DescribeVolumes', 'Volumes'),
        ('EC2::SecurityGroup', 'ec2', 'us-east-1', 'DescribeSecurityGroups', 'SecurityGroups'),
        ('RDS::DBClusterSnapshot', 'rds', 'us-east-1', 'DescribeDBClusterSnapshots', 'DBClusterSnapshots'),
        ('CodeDeploy::DeploymentConfig', 'codedeploy', 'us-east-1', 'ListDeploymentConfigs', 'deploymentConfigsList'),
        ('ELBv2::Listener', 'elbv2', 'us-east-1', 'DescribeListeners', 'Listeners'),
        ('EC2::Instance', 'ec2', 'us-east-1', 'DescribeInstances', 'Instances'),
        ('ECR::Repository', 'ecr', 'us-east-1', 'DescribeRepositories', 'repositories'),
    ]
    
    print(f"\n{'Recurso':<40} {'Esperado':<10} {'Encontrado':<12} {'Estado':<15} {'Detalles'}")
    print("="*80)
    
    # Cargar índice para ver qué dice el contador
    index_file = run_dir / "index" / "index.json"
    index = {}
    if index_file.exists():
        with open(index_file, 'r', encoding='utf-8') as f:
            index = json.load(f)
    
    for resource_name, service, region, operation, resource_key in checks:
        expected_count = expected.get(resource_name, 0)
        
        # Verificar archivo
        file_path = run_dir / "raw" / service / region / f"{operation}.json.gz"
        found_count, status = count_resources_in_file(file_path, resource_key)
        
        # Verificar índice
        index_count = 0
        service_data = index.get("services", {}).get(service, {})
        for region_name, region_data in service_data.get("regions", {}).items():
            if region_name == region:
                for op_info in region_data.get("operations", []):
                    op_name = op_info.get("operation", "")
                    if operation.lower() in op_name.lower() or op_name.lower() in operation.lower():
                        index_count = op_info.get("resource_count", 0) or 0
                        break
        
        # Determinar estado
        if found_count is None:
            state = "❌ Error"
            details = status
        elif found_count == expected_count:
            state = "✅ Correcto"
            details = "OK"
        elif found_count < expected_count:
            state = "⚠️  Faltan"
            details = f"Faltan {expected_count - found_count}"
        else:
            state = "⚠️  Más"
            details = f"{found_count - expected_count} más"
        
        # Si el índice tiene un valor diferente, mostrarlo
        if index_count != found_count and found_count is not None:
            details += f" (índice: {index_count})"
        
        print(f"{resource_name:<40} {expected_count:<10} {str(found_count) if found_count is not None else 'N/A':<12} {state:<15} {details}")
    
    print("="*80)
    print("\n💡 NOTAS:")
    print("   - CloudWatch Alarm: Puede fallar por permisos")
    print("   - ELBv2 Listener: Requiere parámetro LoadBalancerArn (se ejecuta como follow-up)")
    print("   - CodeDeploy DeploymentConfig: Verificar formato de respuesta")
    print("   - ECR Repository: Verificar si está en el inventario")
    print("="*80)

if __name__ == "__main__":
    main()

