#!/usr/bin/env python3
"""
Script de diagnóstico para entender por qué no se están recolectando datos.
"""

import sys
from pathlib import Path

# Agregar el directorio raíz al path para imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import boto3
from collector.discovery import ServiceDiscovery

# Crear sesión
session = boto3.Session()

# Crear discovery
discovery = ServiceDiscovery(session)

# Probar con EC2 en us-east-1 (servicio común)
print("=" * 60)
print("Diagnóstico de Recolección")
print("=" * 60)
print()

service_name = "ec2"
region = "us-east-1"

print(f"1. Probando servicio: {service_name} en región: {region}")
print()

# Descubrir operaciones
operations = discovery.discover_operations(service_name, region)
print(f"2. Operaciones descubiertas: {len(operations)}")
print()

if operations:
    print("3. Primeras 10 operaciones:")
    for i, (op_name, op_info) in enumerate(list(operations.items())[:10], 1):
        safe = op_info.get("safe_to_call", False)
        required = len(op_info.get("required_params", []))
        print(f"   {i}. {op_name}")
        print(f"      - safe_to_call: {safe}")
        print(f"      - required_params: {required}")
        print()
    
    # Contar operaciones safe_to_call
    safe_ops = [op for op, info in operations.items() if info.get("safe_to_call", False)]
    print(f"4. Operaciones safe_to_call: {len(safe_ops)} de {len(operations)}")
    if safe_ops:
        print(f"   Ejemplos: {', '.join(safe_ops[:5])}")
    print()
    
    # Probar ejecutar una operación safe_to_call
    if safe_ops:
        test_op = safe_ops[0]
        print(f"5. Probando ejecutar: {test_op}")
        try:
            client = session.client(service_name, region_name=region)
            if hasattr(client, test_op):
                op_func = getattr(client, test_op)
                print(f"   ✅ Operación existe en cliente")
                print(f"   Intentando ejecutar...")
                result = op_func()
                print(f"   ✅ Ejecución exitosa!")
                print(f"   Tipo de resultado: {type(result)}")
                if isinstance(result, dict):
                    print(f"   Keys: {list(result.keys())[:5]}")
            else:
                print(f"   ❌ Operación NO existe en cliente")
        except Exception as e:
            print(f"   ❌ Error: {e}")
else:
    print("3. ❌ No se encontraron operaciones")
    print()
    print("   Posibles causas:")
    print("   - El servicio no está disponible en esta región")
    print("   - Las operaciones no existen en el cliente boto3")
    print("   - Error en el descubrimiento")

print()
print("=" * 60)


