#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para verificar recursos de AWS Config.
"""

import json
import sys
import gzip
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

def main():
    print("="*80)
    print("🔍 VERIFICACIÓN DE RECURSOS DE AWS CONFIG")
    print("="*80)
    
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
    
    # Analizar Config
    config_data = idx.get("services", {}).get("config", {})
    if not config_data:
        print("\n❌ No se encontraron datos de Config en el índice")
        return
    
    print(f"\n{'='*80}")
    print("📊 ESTADÍSTICAS DE CONFIG")
    print(f"{'='*80}")
    
    total_ops = config_data.get("total_operations", 0)
    successful_ops = config_data.get("successful_operations", 0)
    failed_ops = config_data.get("failed_operations", 0)
    
    print(f"\n   Total de operaciones: {total_ops}")
    print(f"   Operaciones exitosas: {successful_ops}")
    print(f"   Operaciones fallidas: {failed_ops}")
    
    # Buscar operaciones relacionadas con recursos
    print(f"\n{'='*80}")
    print("🔍 OPERACIONES DE CONFIG")
    print(f"{'='*80}")
    
    resource_operations = [
        'ListDiscoveredResources',
        'ListResourceEvaluations',
        'ListAggregateDiscoveredResources',
        'GetAggregateResourceConfig',
        'GetResourceConfigHistory',
        'BatchGetResourceConfig',
        'SelectResourceConfig'
    ]
    
    all_resources = Counter()
    
    for region_name, region_data in config_data.get("regions", {}).items():
        print(f"\n📍 Región: {region_name}")
        
        for op_info in region_data.get("operations", []):
            op_name = op_info.get("operation", "")
            success = op_info.get("success", False)
            resource_count = op_info.get("resource_count", 0) or 0
            file_path = op_info.get("file", "")
            
            # Mostrar todas las operaciones
            print(f"\n   🔸 {op_name}")
            print(f"      ✅ Éxito: {success}")
            print(f"      📊 Recursos contados: {resource_count}")
            
            # Si es una operación de recursos y fue exitosa, intentar leer el archivo
            if success and file_path and any(res_op.lower() in op_name.lower() for res_op in resource_operations):
                raw_file = run_dir / "raw" / file_path
                if raw_file.exists():
                    try:
                        with gzip.open(raw_file, 'rt', encoding='utf-8') as f:
                            file_data = json.load(f)
                        
                        data = file_data.get("data", {})
                        
                        # Buscar recursos en diferentes formatos
                        resources_found = []
                        
                        # Formato con páginas
                        if isinstance(data, dict) and "pages" in data and "data" in data:
                            pages_list = data.get("data", [])
                            for page in pages_list:
                                if isinstance(page, dict):
                                    # Buscar diferentes campos que pueden contener recursos
                                    for key in ['ResourceIdentifiers', 'resourceIdentifiers', 
                                               'ResourceEvaluations', 'resourceEvaluations',
                                               'Results', 'results', 'Items', 'items']:
                                        if key in page and isinstance(page[key], list):
                                            resources_found.extend(page[key])
                        
                        # Formato directo
                        elif isinstance(data, dict):
                            for key in ['ResourceIdentifiers', 'resourceIdentifiers', 
                                       'ResourceEvaluations', 'resourceEvaluations',
                                       'Results', 'results', 'Items', 'items']:
                                if key in data and isinstance(data[key], list):
                                    resources_found.extend(data[key])
                        
                        if resources_found:
                            print(f"      ✅ Recursos encontrados en archivo: {len(resources_found)}")
                            
                            # Analizar tipos de recursos
                            for res in resources_found[:10]:
                                if isinstance(res, dict):
                                    resource_type = res.get("ResourceType", res.get("resourceType", "Unknown"))
                                    resource_id = res.get("ResourceId", res.get("resourceId", "Unknown"))
                                    all_resources[resource_type] += 1
                                    print(f"         - {resource_type}: {resource_id}")
                    except Exception as e:
                        print(f"      ❌ Error leyendo archivo: {e}")
    
    print(f"\n{'='*80}")
    print("📊 RESUMEN DE RECURSOS POR TIPO")
    print(f"{'='*80}")
    
    if all_resources:
        print(f"\n   Total de recursos encontrados: {sum(all_resources.values())}")
        print(f"\n   Recursos por tipo:")
        for resource_type, count in all_resources.most_common():
            print(f"      - {resource_type}: {count}")
    else:
        print(f"\n   ⚠️  No se encontraron recursos en los archivos")
        print(f"   Esto puede indicar que:")
        print(f"   - Las operaciones de recursos no se ejecutaron")
        print(f"   - Los datos no se guardaron correctamente")
        print(f"   - El formato de los datos es diferente al esperado")
    
    print(f"\n{'='*80}")
    print("💡 NOTA")
    print(f"{'='*80}")
    print(f"\n   Los recursos de Config que mencionas (ResourceCompliance, NetworkInterface, etc.)")
    print(f"   se obtienen típicamente con operaciones como:")
    print(f"   - ListDiscoveredResources")
    print(f"   - ListAggregateDiscoveredResources")
    print(f"   - SelectResourceConfig")
    print(f"\n   Verifica que estas operaciones se estén ejecutando y que tengan permisos.")
    print(f"{'='*80}")

if __name__ == "__main__":
    main()

