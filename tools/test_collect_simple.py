#!/usr/bin/env python3
"""
Test simple para diagnosticar por qué no se recolectan datos.
"""

import sys
from pathlib import Path

# Agregar el directorio raíz al path para imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import boto3
import json
import gzip
from datetime import datetime

print("=" * 60)
print("Test Simple de Recolección")
print("=" * 60)
print()

# Crear sesión
try:
    session = boto3.Session()
    print("✅ Sesión AWS creada")
except Exception as e:
    print(f"❌ Error creando sesión: {e}")
    exit(1)

# Probar con EC2 (servicio común)
service_name = "ec2"
region = "us-east-1"

print(f"\nProbando servicio: {service_name} en región: {region}")
print()

try:
    # Crear cliente
    client = session.client(service_name, region_name=region)
    print(f"✅ Cliente {service_name} creado")
    
    # Probar operaciones comunes
    test_operations = [
        "describe_regions",
        "describe_instances",
        "describe_vpcs",
        "describe_security_groups"
    ]
    
    print(f"\nProbando {len(test_operations)} operaciones comunes:")
    print()
    
    results = {}
    
    for op_name in test_operations:
        print(f"  Probando {op_name}...", end=" ")
        
        # Verificar que existe
        if not hasattr(client, op_name):
            print("❌ NO EXISTE en cliente")
            continue
        
        # Intentar ejecutar
        try:
            op_func = getattr(client, op_name)
            result = op_func()
            print(f"✅ EXITOSO - {type(result)}")
            results[op_name] = {
                "success": True,
                "result_type": str(type(result)),
                "has_data": isinstance(result, dict) and len(result) > 0
            }
            
            # Mostrar keys si es dict
            if isinstance(result, dict):
                keys = list(result.keys())[:5]
                print(f"      Keys: {keys}")
        
        except Exception as e:
            error_code = getattr(e, 'response', {}).get('Error', {}).get('Code', 'Unknown')
            print(f"❌ ERROR: {error_code}")
            results[op_name] = {
                "success": False,
                "error": error_code,
                "message": str(e)
            }
    
    print()
    print("=" * 60)
    print("Resumen:")
    print("=" * 60)
    
    successful = [op for op, res in results.items() if res.get("success")]
    failed = [op for op, res in results.items() if not res.get("success")]
    
    print(f"✅ Exitosas: {len(successful)}")
    if successful:
        for op in successful:
            print(f"   - {op}")
    
    print(f"❌ Fallidas: {len(failed)}")
    if failed:
        for op in failed:
            error = results[op].get("error", "Unknown")
            print(f"   - {op}: {error}")
    
    # Si hay al menos una exitosa, guardar resultado de ejemplo
    if successful:
        test_op = successful[0]
        print(f"\n💾 Guardando resultado de ejemplo: {test_op}")
        
        output_dir = project_root / "test_output"
        output_dir.mkdir(exist_ok=True)
        
        op_func = getattr(client, test_op)
        result = op_func()
        
        output = {
            "metadata": {
                "service": service_name,
                "region": region,
                "operation": test_op,
                "timestamp": datetime.utcnow().isoformat(),
                "success": True
            },
            "data": result
        }
        
        filepath = output_dir / f"{service_name}_{region}_{test_op}.json.gz"
        with gzip.open(filepath, 'wt', encoding='utf-8') as f:
            json.dump(output, f, indent=2, default=str)
        
        print(f"✅ Guardado en: {filepath}")
        print(f"\n💡 Si esto funciona, el problema está en el collector.")
        print(f"   Si no funciona, el problema es de permisos/credenciales.")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

print()
print("=" * 60)


