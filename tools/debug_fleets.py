#!/usr/bin/env python3
"""
Script de depuración para EC2 DescribeFleets
"""

import json
import gzip
from pathlib import Path
import sys

def find_latest_run():
    """Encontrar el run más reciente."""
    runs_dir = Path("runs")
    if not runs_dir.exists():
        return None
    
    runs = sorted([d for d in runs_dir.iterdir() if d.is_dir()], reverse=True)
    return runs[0] if runs else None

def debug_fleets():
    """Depurar datos de DescribeFleets."""
    run_dir = find_latest_run()
    if not run_dir:
        print("ERROR: No se encontraron runs disponibles")
        return
    
    print(f"Analizando run: {run_dir.name}")
    print("="*80)
    
    # Buscar archivos de DescribeFleets
    raw_dir = run_dir / "raw" / "ec2"
    if not raw_dir.exists():
        print("ERROR: No existe el directorio raw/ec2")
        return
    
    # Buscar en todas las regiones
    fleet_files = []
    for region_dir in raw_dir.iterdir():
        if not region_dir.is_dir():
            continue
        
        for op_file in region_dir.glob("*fleet*.json.gz"):
            fleet_files.append((region_dir.name, op_file))
    
    if not fleet_files:
        print("ERROR: No se encontraron archivos de DescribeFleets")
        print(f"   Buscando en: {raw_dir}")
        # Listar archivos disponibles
        print("\nArchivos disponibles en ec2:")
        for region_dir in raw_dir.iterdir():
            if region_dir.is_dir():
                files = list(region_dir.glob("*.json.gz"))
                if files:
                    print(f"   {region_dir.name}: {len(files)} archivos")
                    for f in files[:5]:  # Mostrar primeros 5
                        print(f"      - {f.name}")
    
    for region, file_path in fleet_files:
        print(f"\n{'='*80}")
        print(f"Analizando: {region} / {file_path.name}")
        print(f"{'='*80}\n")
        
        try:
            with gzip.open(file_path, 'rt', encoding='utf-8') as f:
                data = json.load(f)
            
            # Mostrar metadata
            metadata = data.get("metadata", {})
            print("Metadata:")
            print(f"   Operation: {metadata.get('operation', 'N/A')}")
            print(f"   Success: {metadata.get('success', 'N/A')}")
            print(f"   Paginated: {metadata.get('paginated', 'N/A')}")
            print()
            
            # Analizar estructura de datos
            data_content = data.get("data", {})
            
            # Si es paginado
            if "pages" in data_content and "data" in data_content:
                print("Estructura: PAGINADO")
                pages = data_content.get("data", [])
                print(f"   Número de páginas: {len(pages)}")
                
                total_fleets = 0
                for i, page in enumerate(pages):
                    print(f"\n   Pagina {i+1}:")
                    print(f"      Keys en pagina: {list(page.keys()) if isinstance(page, dict) else 'No es dict'}")
                    
                    # Buscar fleets
                    fleets = None
                    for key in ["Fleets", "fleets", "FleetList", "fleetList"]:
                        if isinstance(page, dict) and key in page:
                            fleets = page.get(key)
                            print(f"      OK - Encontrado campo: {key}")
                            break
                    
                    if fleets:
                        if isinstance(fleets, list):
                            print(f"      Fleets encontrados: {len(fleets)}")
                            total_fleets += len(fleets)
                            
                            if len(fleets) > 0:
                                # Mostrar IDs de todos los fleets
                                for j, fleet in enumerate(fleets):
                                    if isinstance(fleet, dict):
                                        fleet_id = (fleet.get("FleetId") or 
                                                   fleet.get("fleetId") or 
                                                   fleet.get("FleetID") or
                                                   fleet.get("Id") or
                                                   fleet.get("id"))
                                        print(f"         Fleet {j+1}: ID = {fleet_id}")
                                        if not fleet_id:
                                            print(f"            WARNING: No se encontro FleetId. Keys disponibles: {list(fleet.keys())[:10]}")
                                            # Mostrar todas las keys del fleet
                                            print(f"            Todas las keys: {list(fleet.keys())}")
                                    else:
                                        print(f"         Fleet {j+1}: No es un dict, es {type(fleet)}: {fleet}")
                            else:
                                print(f"      INFO: La lista Fleets existe pero esta vacia")
                                # Verificar si hay datos en la pagina que no se estan procesando
                                print(f"      DEBUG: Contenido completo de la pagina (primeros 500 chars):")
                                page_str = json.dumps(page, indent=2, default=str)[:500]
                                print(f"         {page_str}...")
                        else:
                            print(f"      WARNING: Fleets no es una lista: {type(fleets)}, valor: {fleets}")
                    else:
                        print(f"      ERROR: No se encontro campo Fleets en esta pagina")
                        if isinstance(page, dict):
                            # Buscar recursivamente
                            def find_fleets_recursive(obj, path="", depth=0):
                                if depth > 3:
                                    return []
                                results = []
                                if isinstance(obj, dict):
                                    for k, v in obj.items():
                                        if 'fleet' in k.lower() and isinstance(v, list):
                                            results.append((f"{path}.{k}", v))
                                        if isinstance(v, (dict, list)):
                                            results.extend(find_fleets_recursive(v, f"{path}.{k}", depth+1))
                                elif isinstance(obj, list):
                                    for i, item in enumerate(obj):
                                        results.extend(find_fleets_recursive(item, f"{path}[{i}]", depth+1))
                                return results
                            
                            found = find_fleets_recursive(page)
                            if found:
                                print(f"      Campos relacionados con 'fleet' encontrados:")
                                for path, value in found:
                                    print(f"         {path}: {type(value).__name__} con {len(value) if isinstance(value, list) else 'N/A'} items")
                
                print(f"\n   TOTAL de fleets en todas las paginas: {total_fleets}")
                
            else:
                print("Estructura: NO PAGINADO")
                print(f"   Keys en data: {list(data_content.keys()) if isinstance(data_content, dict) else 'No es dict'}")
                
                # Buscar fleets directamente
                fleets = None
                for key in ["Fleets", "fleets", "FleetList", "fleetList"]:
                    if isinstance(data_content, dict) and key in data_content:
                        fleets = data_content.get(key)
                        print(f"   OK - Encontrado campo: {key}")
                        break
                
                if fleets:
                    if isinstance(fleets, list):
                        print(f"   Fleets encontrados: {len(fleets)}")
                        for j, fleet in enumerate(fleets[:3]):
                            if isinstance(fleet, dict):
                                fleet_id = (fleet.get("FleetId") or 
                                           fleet.get("fleetId") or 
                                           fleet.get("FleetID") or
                                           fleet.get("Id") or
                                           fleet.get("id"))
                                print(f"      Fleet {j+1}: ID = {fleet_id}")
                                if not fleet_id:
                                    print(f"         WARNING: No se encontro FleetId. Keys disponibles: {list(fleet.keys())[:10]}")
                    else:
                        print(f"   WARNING: Fleets no es una lista: {type(fleets)}")
                else:
                    print(f"   ERROR: No se encontro campo Fleets")
                    # Mostrar estructura completa (limitada)
                    if isinstance(data_content, dict):
                        print(f"   Estructura completa (primeros niveles):")
                        def print_structure(obj, indent=0, max_depth=2):
                            if indent > max_depth:
                                return
                            prefix = "   " * (indent + 1)
                            if isinstance(obj, dict):
                                for k, v in list(obj.items())[:5]:  # Primeros 5
                                    if isinstance(v, (dict, list)):
                                        print(f"{prefix}{k}: {type(v).__name__}")
                                        print_structure(v, indent+1, max_depth)
                                    else:
                                        print(f"{prefix}{k}: {type(v).__name__}")
                            elif isinstance(obj, list) and len(obj) > 0:
                                print(f"{prefix}[0]: {type(obj[0]).__name__}")
                                if isinstance(obj[0], dict):
                                    print_structure(obj[0], indent+1, max_depth)
                        
                        print_structure(data_content)
            
            # Verificar error
            error = data.get("error")
            if error:
                print(f"\nERROR en el archivo:")
                print(f"   {error}")
        
        except Exception as e:
            print(f"ERROR leyendo archivo: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    debug_fleets()

