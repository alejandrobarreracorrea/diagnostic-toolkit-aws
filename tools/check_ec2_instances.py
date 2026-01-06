#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para verificar por qué no se están contando las instancias de EC2.
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
    print("🔍 VERIFICACIÓN DE INSTANCIAS EC2")
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
    
    # Analizar EC2
    ec2_data = idx.get("services", {}).get("ec2", {})
    if not ec2_data:
        print("\n❌ No se encontraron datos de EC2 en el índice")
        return
    
    print(f"\n{'='*80}")
    print("📊 ESTADÍSTICAS DE EC2")
    print(f"{'='*80}")
    
    total_ops = ec2_data.get("total_operations", 0)
    successful_ops = ec2_data.get("successful_operations", 0)
    failed_ops = ec2_data.get("failed_operations", 0)
    
    print(f"\n   Total de operaciones: {total_ops}")
    print(f"   Operaciones exitosas: {successful_ops}")
    print(f"   Operaciones fallidas: {failed_ops}")
    
    # Buscar operación DescribeInstances
    print(f"\n{'='*80}")
    print("🔍 BUSCANDO OPERACIÓN DescribeInstances")
    print(f"{'='*80}")
    
    describe_instances_found = False
    total_instances = 0
    
    for region_name, region_data in ec2_data.get("regions", {}).items():
        print(f"\n📍 Región: {region_name}")
        
        for op_info in region_data.get("operations", []):
            op_name = op_info.get("operation", "")
            
            # Buscar DescribeInstances (puede estar en diferentes formatos)
            if (op_name.lower() == "describeinstances" or 
                op_name.lower() == "describe_instances" or
                "describeinstances" in op_name.lower()):
                
                describe_instances_found = True
                success = op_info.get("success", False)
                resource_count = op_info.get("resource_count", 0) or 0
                file_path = op_info.get("file", "")
                
                print(f"\n   🔸 Operación: {op_name}")
                print(f"      ✅ Éxito: {success}")
                print(f"      📊 Recursos contados: {resource_count}")
                print(f"      📁 Archivo: {file_path}")
                
                if success and file_path:
                    # Leer el archivo para contar instancias reales
                    raw_file = run_dir / "raw" / file_path
                    if raw_file.exists():
                        try:
                            with gzip.open(raw_file, 'rt', encoding='utf-8') as f:
                                file_data = json.load(f)
                            
                            # Buscar instancias en los datos
                            data = file_data.get("data", {})
                            if isinstance(data, dict):
                                # Puede estar en diferentes formatos
                                instances = None
                                
                                # Formato directo
                                if "Instances" in data:
                                    instances = data["Instances"]
                                elif "instances" in data:
                                    instances = data["instances"]
                                elif "Reservations" in data:
                                    # EC2 DescribeInstances devuelve Reservations
                                    reservations = data["Reservations"]
                                    instances = []
                                    for res in reservations:
                                        if isinstance(res, dict) and "Instances" in res:
                                            instances.extend(res["Instances"])
                                
                                if instances:
                                    instance_count = len(instances)
                                    total_instances += instance_count
                                    print(f"\n      ✅ INSTANCIAS ENCONTRADAS EN EL ARCHIVO: {instance_count}")
                                    
                                    # Mostrar algunas instancias
                                    if instance_count > 0:
                                        print(f"\n      Primeras instancias:")
                                        for i, inst in enumerate(instances[:5], 1):
                                            instance_id = inst.get("InstanceId", "N/A")
                                            state = inst.get("State", {}).get("Name", "N/A") if isinstance(inst.get("State"), dict) else "N/A"
                                            instance_type = inst.get("InstanceType", "N/A")
                                            print(f"         {i}. {instance_id} - {instance_type} - Estado: {state}")
                                        
                                        if instance_count > 5:
                                            print(f"         ... y {instance_count - 5} más")
                                    
                                    # Verificar por qué no se contaron
                                    if instance_count > 0 and resource_count == 0:
                                        print(f"\n      ⚠️  PROBLEMA DETECTADO:")
                                        print(f"         - Hay {instance_count} instancias en el archivo")
                                        print(f"         - Pero resource_count es {resource_count}")
                                        print(f"         - El contador no está funcionando correctamente")
                                else:
                                    print(f"\n      ⚠️  No se encontraron instancias en el formato esperado")
                                    print(f"      Estructura de datos:")
                                    print(f"      {json.dumps(list(data.keys())[:10], indent=2)}")
                            elif isinstance(data, list):
                                # Puede ser una lista de páginas
                                print(f"\n      📋 Datos en formato de lista ({len(data)} elementos)")
                                for i, page in enumerate(data[:3], 1):
                                    if isinstance(page, dict) and "Instances" in page:
                                        page_instances = page["Instances"]
                                        print(f"         Página {i}: {len(page_instances)} instancias")
                        except Exception as e:
                            print(f"\n      ❌ Error leyendo archivo: {e}")
                elif not success:
                    error = op_info.get("error", {})
                    error_code = error.get("code", "") if isinstance(error, dict) else ""
                    print(f"\n      ❌ Error: {error_code}")
    
    print(f"\n{'='*80}")
    print("📊 RESUMEN")
    print(f"{'='*80}")
    
    if not describe_instances_found:
        print("\n   ❌ No se encontró la operación DescribeInstances")
        print("   Esto puede indicar que la operación no se ejecutó o falló")
    else:
        print(f"\n   ✅ Operación DescribeInstances encontrada")
        print(f"   📊 Total de instancias encontradas en archivos: {total_instances}")
        
        if total_instances > 0:
            print(f"\n   ✅ Se encontraron {total_instances} instancias en los archivos")
            print(f"   ⚠️  Si el inventario muestra 0, el problema está en el contador de recursos")
        else:
            print(f"\n   ⚠️  No se encontraron instancias en los archivos")
            print(f"   Esto puede indicar que:")
            print(f"   - No hay instancias en la cuenta/región")
            print(f"   - Los datos no se guardaron correctamente")
            print(f"   - El formato de los datos es diferente al esperado")
    
    print(f"\n{'='*80}")

if __name__ == "__main__":
    main()

