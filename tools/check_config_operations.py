#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para verificar operaciones de Config y cómo ejecutarlas.
"""

import sys
from pathlib import Path

# Agregar el directorio raíz al path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import boto3
from collector.discovery import ServiceDiscovery

# Configurar codificación UTF-8 para Windows
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

def main():
    print("="*80)
    print("🔍 VERIFICACIÓN DE OPERACIONES DE CONFIG")
    print("="*80)
    
    session = boto3.Session()
    discovery = ServiceDiscovery(session)
    
    # Descubrir operaciones
    ops = discovery.discover_operations('config', 'us-east-1')
    
    # Operaciones importantes para recursos
    important_ops = [
        'ListDiscoveredResources',
        'ListAggregateDiscoveredResources',
        'SelectResourceConfig',
        'GetDiscoveredResourceCounts',
        'GetAggregateDiscoveredResourceCounts'
    ]
    
    print(f"\nOperaciones importantes de Config:")
    print(f"{'='*80}")
    
    for op_name in important_ops:
        if op_name in ops:
            op_info = ops[op_name]
            print(f"\n🔸 {op_name}")
            print(f"   Safe to call: {op_info.get('safe_to_call', False)}")
            print(f"   Required params: {len(op_info.get('required_params', []))}")
            for param in op_info.get('required_params', []):
                print(f"      - {param.get('name')} ({param.get('type')})")
            print(f"   Optional params: {len(op_info.get('optional_params', []))}")
            print(f"   Paginated: {op_info.get('paginated', False)}")
        else:
            print(f"\n❌ {op_name} - NO ENCONTRADA")
    
    print(f"\n{'='*80}")
    print("💡 SOLUCIÓN")
    print(f"{'='*80}")
    print(f"""
    Las operaciones de Config que listan recursos requieren parámetros:
    
    1. ListDiscoveredResources requiere:
       - resourceType (obligatorio)
    
    2. SelectResourceConfig requiere:
       - Expression (obligatorio) - una query SQL
    
    3. GetDiscoveredResourceCounts puede ejecutarse sin parámetros
    
    Para obtener los recursos de Config, necesitamos:
    
    OPCIÓN 1: Usar GetDiscoveredResourceCounts (sin parámetros)
      - Devuelve conteos por tipo de recurso
      - No devuelve los recursos individuales
    
    OPCIÓN 2: Ejecutar ListDiscoveredResources para cada tipo de recurso
      - Requiere conocer los tipos de recursos (EC2::Instance, EC2::Volume, etc.)
      - Puede ser costoso si hay muchos tipos
    
    OPCIÓN 3: Usar SelectResourceConfig con una query genérica
      - Requiere construir una query SQL
      - Más flexible pero más complejo
    
    RECOMENDACIÓN: Agregar soporte especial para Config que:
    1. Primero ejecute GetDiscoveredResourceCounts para obtener tipos
    2. Luego ejecute ListDiscoveredResources para cada tipo encontrado
    """)
    
    print(f"{'='*80}")

if __name__ == "__main__":
    main()

