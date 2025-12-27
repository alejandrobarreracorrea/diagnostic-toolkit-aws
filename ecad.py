#!/usr/bin/env python3
"""
ECAD - Script Interactivo Principal
Ejecuta el kit completo con menú interactivo
"""

import os
import sys
import subprocess
import json
from pathlib import Path
from datetime import datetime
import platform

def print_header():
    """Imprimir encabezado."""
    print("\n" + "="*60)
    print("  AWS Cloud Architecture Diagnostic (ECAD)")
    print("="*60 + "\n")

def print_menu():
    """Mostrar menú principal."""
    print("Selecciona una opción:")
    print()
    print("  1. 🎯 DEMO - Ejecutar con datos de ejemplo (sin AWS)")
    print("  2. 📥 RECOLECTAR TODO - Recolectar TODOS los servicios y regiones")
    print("  3. 📊 ANALIZAR - Analizar un run existente")
    print("  4. 📋 EVIDENCE - Generar evidence pack Well-Architected")
    print("  5. 📄 REPORTES - Generar reportes ejecutivos")
    print("  6. 🔄 COMPLETO - Recolectar + Analizar + Reportes (todo)")
    print("  7. 🔍 VERIFICAR - Verificar credenciales AWS")
    print("  8. 📦 INSTALAR - Instalar/verificar dependencias Python")
    print("  9. 📁 LISTAR - Listar runs disponibles")
    print(" 10. 📊 INVENTARIO - Mostrar inventario consolidado en consola")
    print(" 11. 🧹 LIMPIAR - Limpiar archivos temporales")
    print("  0. ❌ SALIR")
    print()

def get_user_choice():
    """Obtener selección del usuario."""
    while True:
        try:
            choice = input("Tu opción (0-11): ").strip()
            if choice in ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11']:
                return choice
            else:
                print("❌ Opción inválida. Selecciona 0-11\n")
        except KeyboardInterrupt:
            print("\n\n👋 ¡Hasta luego!")
            sys.exit(0)

def get_make_command(base_cmd, run_dir=None):
    """Obtener el comando correcto según el sistema operativo."""
    is_windows = platform.system() == 'Windows'
    
    if not is_windows:
        # Linux/macOS - usar make directamente
        return base_cmd
    
    # Windows - usar scripts de Windows
    # Extraer el comando (install, collect, analyze, etc.)
    parts = base_cmd.split()
    if len(parts) < 2:
        return base_cmd
    
    cmd_name = parts[1]
    script_bat = Path("scripts/windows/ecad.bat")
    script_ps1 = Path("scripts/windows/ecad.ps1")
    
    # Preferir PowerShell si está disponible
    if script_ps1.exists():
        script_path = script_ps1.resolve()
        if cmd_name in ["analyze", "evidence", "reports"] and run_dir:
            run_dir_str = str(run_dir).replace('\\', '/')
            return f'powershell -ExecutionPolicy Bypass -File "{script_path}" {cmd_name} -RunDir "{run_dir_str}"'
        else:
            return f'powershell -ExecutionPolicy Bypass -File "{script_path}" {cmd_name}'
    
    # Usar batch file
    if script_bat.exists():
        script_path = script_bat.resolve()
        # La variable RUN_DIR se pasa como variable de entorno en run_command
        return f'"{script_path}" {cmd_name}'
    
    # Si no hay scripts, intentar usar make si está disponible (chocolatey, etc)
    return base_cmd

def run_command(cmd, description, run_dir=None):
    """Ejecutar comando y mostrar resultado."""
    print(f"\n{'='*60}")
    print(f"  {description}")
    print(f"{'='*60}\n")
    
    # Convertir comando make a comando del sistema
    if cmd.startswith("make "):
        actual_cmd = get_make_command(cmd, run_dir)
    else:
        actual_cmd = cmd
    
    # Preparar variables de entorno si hay run_dir
    env = os.environ.copy()
    if run_dir:
        env['RUN_DIR'] = str(run_dir)
    
    try:
        result = subprocess.run(actual_cmd, shell=True, check=True, env=env)
        print(f"\n✅ {description} completado exitosamente")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Error ejecutando: {description}")
        print(f"   Código de error: {e.returncode}")
        return False
    except KeyboardInterrupt:
        print("\n\n⚠️  Operación cancelada por el usuario")
        return False

def verify_aws_credentials():
    """Verificar credenciales AWS."""
    print("\n🔍 Verificando credenciales AWS...\n")
    
    try:
        result = subprocess.run(
            ["aws", "sts", "get-caller-identity"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            print("✅ Credenciales AWS funcionando correctamente")
            print("\nInformación de la cuenta:")
            print(result.stdout)
            return True
        else:
            print("❌ No se pueden acceder las credenciales AWS")
            print("\nOpciones para configurar:")
            print("  1. Ejecutar: aws configure")
            print("  2. Variables de entorno:")
            if os.name == 'nt':  # Windows
                print("     set AWS_ACCESS_KEY_ID=tu-key")
                print("     set AWS_SECRET_ACCESS_KEY=tu-secret")
                print("  3. Archivo: %USERPROFILE%\\.aws\\credentials")
            else:  # Linux/macOS
                print("     export AWS_ACCESS_KEY_ID=tu-key")
                print("     export AWS_SECRET_ACCESS_KEY=tu-secret")
                print("  3. Archivo: ~/.aws/credentials")
            return False
    except FileNotFoundError:
        print("❌ AWS CLI no está instalado")
        print("\nInstala con:")
        if os.name == 'nt':  # Windows
            print("  Windows: pip install awscli")
        else:
            print("  macOS: brew install awscli")
            print("  Linux: pip install awscli")
        return False
    except Exception as e:
        print(f"❌ Error verificando credenciales: {e}")
        return False

def check_dependencies():
    """Verificar e instalar dependencias."""
    print("\n📦 Verificando dependencias Python...\n")
    
    required_modules = ['boto3', 'botocore', 'yaml', 'jinja2', 'tqdm']
    missing = []
    
    for module in required_modules:
        try:
            __import__(module)
            print(f"  ✅ {module}")
        except ImportError:
            print(f"  ❌ {module} - NO INSTALADO")
            missing.append(module)
    
    if not missing:
        print("\n✅ Todas las dependencias están instaladas")
        return True
    
    print(f"\n⚠️  Faltan {len(missing)} dependencias: {', '.join(missing)}")
    print("\nInstalando dependencias...")
    
    # Detectar comando pip según sistema operativo
    if os.name == 'nt':  # Windows
        pip_cmd = ["python", "-m", "pip", "install", "-r", "requirements.txt"]
        manual_cmd = "python -m pip install -r requirements.txt"
    else:  # Linux/macOS
        pip_cmd = ["pip3", "install", "-r", "requirements.txt"]
        manual_cmd = "pip3 install -r requirements.txt"
    
    try:
        result = subprocess.run(pip_cmd, check=True)
        print("\n✅ Dependencias instaladas exitosamente")
        return True
    except subprocess.CalledProcessError:
        print("\n❌ Error instalando dependencias")
        print("\nIntenta manualmente:")
        print(f"  {manual_cmd}")
        return False
    except FileNotFoundError:
        print("\n❌ pip no encontrado")
        if os.name == 'nt':  # Windows
            print("Instala pip o usa: python -m pip install -r requirements.txt")
        else:
            print("Instala pip3 o usa: python3 -m pip install -r requirements.txt")
        return False

def list_runs():
    """Listar runs disponibles."""
    runs_dir = Path("./runs")
    
    if not runs_dir.exists():
        print("\n📁 No hay runs disponibles aún")
        print("   Ejecuta primero la opción 2 (RECOLECTAR)")
        return []
    
    runs = sorted([d for d in runs_dir.iterdir() if d.is_dir()], reverse=True)
    
    if not runs:
        print("\n📁 No hay runs disponibles aún")
        print("   Ejecuta primero la opción 2 (RECOLECTAR)")
        return []
    
    print("\n📁 Runs disponibles:\n")
    for i, run_dir in enumerate(runs, 1):
        print(f"  {i}. {run_dir.name}")
    
    return runs

def select_run():
    """Seleccionar un run interactivamente."""
    runs = list_runs()
    
    if not runs:
        return None
    
    while True:
        try:
            choice = input(f"\nSelecciona un run (1-{len(runs)}) o 0 para cancelar: ").strip()
            
            if choice == '0':
                return None
            
            idx = int(choice) - 1
            if 0 <= idx < len(runs):
                return runs[idx]
            else:
                print(f"❌ Opción inválida. Selecciona 1-{len(runs)}")
        except ValueError:
            print("❌ Por favor ingresa un número")
        except KeyboardInterrupt:
            return None

def run_demo():
    """Ejecutar demo."""
    print("\n🎯 Ejecutando DEMO con datos de ejemplo...")
    print("   (No se requiere conexión a AWS)\n")
    
    # Verificar dependencias primero
    if not check_dependencies():
        print("\n❌ Faltan dependencias. Instálalas primero (opción 8)")
        return False
    
    return run_command("make demo", "Demo con fixtures", None)

def run_collect():
    """Recolectar datos desde AWS."""
    print("\n📥 Recolectando datos desde AWS...")
    print("   Esto puede tardar varias horas en entornos grandes\n")
    
    # Verificar dependencias primero
    if not check_dependencies():
        print("\n❌ Faltan dependencias. Instálalas primero (opción 8)")
        return False
    
    # Verificar credenciales
    if not verify_aws_credentials():
        print("\n⚠️  No se pueden verificar las credenciales")
        proceed = input("¿Continuar de todas formas? (s/N): ").strip().lower()
        if proceed != 's':
            return False
    
    # Preguntar por configuración
    print("\n⚙️  Configuración de Recolección:")
    print()
    
    # Región
    print("1. Regiones a recolectar:")
    print("   a) Una región específica (ej: us-east-1)")
    print("   b) Múltiples regiones (ej: us-east-1,us-west-2,eu-west-1)")
    print("   c) Todas las regiones disponibles (puede tardar mucho)")
    region_choice = input("   Opción (a/b/c, default: a): ").strip().lower() or "a"
    
    if region_choice == "a":
        region = input("   Región (default: us-east-1): ").strip() or "us-east-1"
        regions_str = region
    elif region_choice == "b":
        regions_str = input("   Regiones separadas por coma: ").strip()
        if not regions_str:
            regions_str = "us-east-1"
    else:  # c
        regions_str = "all"
        print("   ⚠️  Recolectar todas las regiones puede tardar MUCHO tiempo")
        confirm = input("   ¿Continuar? (s/N): ").strip().lower()
        if confirm != 's':
            print("   ❌ Cancelado")
            return False
    
    # Threads
    threads = input("\n2. Threads paralelos (default: 20, más = más rápido pero más carga): ").strip() or "20"
    
    # Servicios
    print("\n3. Servicios a recolectar:")
    print("   a) Todos los servicios (recomendado)")
    print("   b) Solo servicios específicos (ej: ec2,s3,rds,lambda)")
    print("   c) Excluir servicios específicos")
    service_choice = input("   Opción (a/b/c, default: a): ").strip().lower() or "a"
    
    service_allowlist = None
    service_denylist = None
    
    if service_choice == "b":
        allowlist_str = input("   Servicios separados por coma: ").strip()
        if allowlist_str:
            service_allowlist = allowlist_str
    elif service_choice == "c":
        denylist_str = input("   Servicios a excluir separados por coma: ").strip()
        if denylist_str:
            service_denylist = denylist_str
    
    # AssumeRole (opcional)
    print("\n4. AssumeRole (opcional):")
    use_role = input("   ¿Usar AssumeRole? (s/N): ").strip().lower()
    role_arn = None
    external_id = None
    
    if use_role == 's':
        role_arn = input("   AWS_ROLE_ARN: ").strip()
        external_id = input("   AWS_EXTERNAL_ID: ").strip()
    
    # Construir comando
    print("\n🚀 Iniciando recolección...")
    print("   (Esto puede tardar. Puedes cancelar con Ctrl+C)\n")
    
    # Preparar variables de entorno
    if regions_str != "all":
        os.environ['AWS_REGIONS'] = regions_str
    if role_arn:
        os.environ['AWS_ROLE_ARN'] = role_arn
    if external_id:
        os.environ['AWS_EXTERNAL_ID'] = external_id
    os.environ['ECAD_MAX_THREADS'] = threads
    
    if service_allowlist:
        os.environ['ECAD_SERVICE_ALLOWLIST'] = service_allowlist
    if service_denylist:
        os.environ['ECAD_SERVICE_DENYLIST'] = service_denylist
    
    # Ejecutar
    return run_command("make collect", "Recolección completa de datos AWS", None)

def run_analyze():
    """Analizar un run."""
    run_dir = select_run()
    
    if not run_dir:
        print("\n❌ No se seleccionó ningún run")
        return False
    
    print(f"\n📊 Analizando: {run_dir.name}")
    
    cmd = f"make analyze RUN_DIR={run_dir}"
    return run_command(cmd, f"Análisis de {run_dir.name}", run_dir)

def run_evidence():
    """Generar evidence pack."""
    run_dir = select_run()
    
    if not run_dir:
        print("\n❌ No se seleccionó ningún run")
        return False
    
    print(f"\n📋 Generando evidence pack: {run_dir.name}")
    
    cmd = f"make evidence RUN_DIR={run_dir}"
    return run_command(cmd, f"Evidence pack de {run_dir.name}", run_dir)

def run_reports():
    """Generar reportes."""
    run_dir = select_run()
    
    if not run_dir:
        print("\n❌ No se seleccionó ningún run")
        return False
    
    print(f"\n📄 Generando reportes: {run_dir.name}")
    
    cmd = f"make reports RUN_DIR={run_dir}"
    return run_command(cmd, f"Reportes de {run_dir.name}", run_dir)

def show_inventory_console():
    """Mostrar inventario consolidado en consola."""
    run_dir = select_run()
    
    if not run_dir:
        print("\n❌ No se seleccionó ningún run")
        return False
    
    # Cargar índice
    index_file = run_dir / "index" / "index.json"
    if not index_file.exists():
        print(f"\n❌ No se encontró el índice en {run_dir.name}")
        print("   Ejecuta primero la opción 3 (ANALIZAR) para generar el índice")
        return False
    
    try:
        with open(index_file, 'r') as f:
            index = json.load(f)
    except Exception as e:
        print(f"\n❌ Error leyendo índice: {e}")
        return False
    
    services = index.get("services", {})
    if not services:
        print(f"\n⚠️  No hay servicios en el índice de {run_dir.name}")
        return False
    
    print("\n" + "="*100)
    print(f"  INVENTARIO CONSOLIDADO - {run_dir.name}")
    print("="*100 + "\n")
    
    # Preparar datos para tabla
    table_data = []
    for service_name, service_data in sorted(services.items()):
        total_ops = service_data.get("total_operations", 0)
        successful_ops = 0
        failed_ops = 0
        resource_count = 0
        
        # Usar el mismo filtro de operaciones principales que el inventory generator
        # Importar la misma lógica del inventory generator
        primary_operations = {
            'acm': ['ListCertificates'],
            'apigateway': ['GetRestApis', 'GetApis'],  # Solo APIs principales, no GetSdkTypes
            'apigatewayv2': ['GetApis'],
            's3': ['ListBuckets'],
            'ec2': ['DescribeInstances'],  # Solo instancias, no VPCs ni Security Groups
            'iam': ['ListUsers', 'ListRoles', 'ListGroups'],
            'rds': ['DescribeDBInstances', 'DescribeDBClusters'],
            'docdb': ['DescribeDBClusters', 'DescribeDBInstances'],  # Solo clusters e instancias, no snapshots ni parámetros
            'lambda': ['ListFunctions'],
            'cloudformation': ['ListStacks'],
            'ecs': ['ListClusters', 'ListServices'],
            'eks': ['ListClusters'],
            'dynamodb': ['ListTables'],
            'sns': ['ListTopics'],
            'sqs': ['ListQueues'],
            'kinesis': ['ListStreams'],
            'redshift': ['DescribeClusters'],
            'elasticache': ['DescribeCacheClusters'],
            'elbv2': ['DescribeLoadBalancers'],
            'route53': ['ListHostedZones'],
            'cloudfront': ['ListDistributions'],
            # Servicios de consulta/información que NO tienen recursos gestionables
            'pricing': [],  # Servicio de consulta de precios, no tiene recursos
            'ce': [],  # Cost Explorer - servicio de consulta, no tiene recursos
            'cur': [],  # Cost and Usage Report - servicio de reportes, no tiene recursos
        }
        
        for region_name, region_data in service_data.get("regions", {}).items():
            for op_info in region_data.get("operations", []):
                op_name = op_info.get("operation", "")
                
                if op_info.get("success"):
                    successful_ops += 1
                    # Solo contar recursos de operaciones principales
                    if service_name in primary_operations:
                        # Normalizar nombre de operación a PascalCase para comparar
                        # Puede venir en PascalCase (ListStacks) o snake_case (list_stacks)
                        if '_' in op_name:
                            # Es snake_case: list_stacks -> ListStacks
                            op_pascal = ''.join(word.capitalize() for word in op_name.split('_'))
                        else:
                            # Ya está en PascalCase: ListStacks -> ListStacks
                            op_pascal = op_name
                        
                        allowed_ops = primary_operations[service_name]
                        # Comparar tanto el nombre original como el normalizado
                        if op_name in allowed_ops or op_pascal in allowed_ops:
                            resource_count += op_info.get("resource_count", 0) or 0
                    else:
                        # Heurística: solo contar operaciones List/Describe principales
                        op_lower = op_name.lower()
                        if (op_lower.startswith("list") or 
                            op_lower.startswith("describe") or
                            (op_lower.startswith("get") and any(x in op_lower for x in ["apis", "tables", "instances", "clusters", "functions", "buckets", "users", "roles"]))):
                            resource_count += op_info.get("resource_count", 0) or 0
                elif not op_info.get("not_available", False):  # Solo contar como fallida si no es "no disponible"
                    failed_ops += 1
        
        # Determinar estado
        if successful_ops > 0:
            status = "✅ Activo"
        elif failed_ops > 0:
            # Verificar si los errores son reales o solo operaciones/endpoints no disponibles
            has_real_errors = False
            for region_name, region_data in service_data.get("regions", {}).items():
                for op_info in region_data.get("operations", []):
                    # Si está marcado como "not_available", no es un error real
                    if op_info.get("not_available", False):
                        continue
                    
                    # Si no fue exitosa, verificar el tipo de error
                    if not op_info.get("success", False):
                        error = op_info.get("error", {})
                        error_code = error.get("code", "") if isinstance(error, dict) else ""
                        
                        # Códigos de error que NO son errores reales (son esperados):
                        # - OperationNotFound: operación no existe en el cliente
                        # - EndpointNotAvailable: endpoint no disponible (servicio no habilitado/región no soportada)
                        expected_error_codes = [
                            "OperationNotFound",
                            "EndpointNotAvailable"
                        ]
                        
                        # Si el código de error NO está en la lista de esperados, es un error real
                        if error_code and error_code not in expected_error_codes:
                            has_real_errors = True
                            break
                if has_real_errors:
                    break
            
            if has_real_errors:
                status = "⚠️  Con Errores"
            else:
                status = "ℹ️  No Disponible"  # Operaciones/endpoints no disponibles
        else:
            status = "❌ Sin Datos"
        
        table_data.append({
            "servicio": service_name,
            "regiones": len(service_data.get("regions", {})),
            "ops_totales": total_ops,
            "ops_exitosas": successful_ops,
            "ops_fallidas": failed_ops,
            "recursos": resource_count,
            "estado": status
        })
    
    # Mostrar tabla
    print(f"{'#':<4} {'Servicio':<30} {'Reg':<4} {'Ops Tot':<8} {'Ops OK':<8} {'Ops Err':<8} {'Recursos':<10} {'Estado':<15}")
    print("-" * 100)
    
    for idx, row in enumerate(table_data, 1):
        print(f"{idx:<4} {row['servicio']:<30} {row['regiones']:<4} {row['ops_totales']:<8} "
              f"{row['ops_exitosas']:<8} {row['ops_fallidas']:<8} {row['recursos']:<10} {row['estado']:<15}")
    
    print("-" * 100)
    print(f"\nTotal: {len(table_data)} servicios")
    print(f"Operaciones totales: {sum(r['ops_totales'] for r in table_data)}")
    print(f"Operaciones exitosas: {sum(r['ops_exitosas'] for r in table_data)}")
    print(f"Operaciones fallidas: {sum(r['ops_fallidas'] for r in table_data)}")
    print(f"Recursos estimados: {sum(r['recursos'] for r in table_data)}")
    
    # Opción para exportar
    print("\n" + "="*100)
    export = input("\n¿Exportar a CSV? (s/N): ").strip().lower()
    if export == 's':
        csv_file = run_dir / "inventory_console.csv"
        try:
            import csv
            with open(csv_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=['servicio', 'regiones', 'ops_totales', 
                                                       'ops_exitosas', 'ops_fallidas', 'recursos', 'estado'])
                writer.writeheader()
                writer.writerows(table_data)
            print(f"✅ Inventario exportado a: {csv_file}")
        except Exception as e:
            print(f"❌ Error exportando CSV: {e}")
    
    return True

def run_complete():
    """Ejecutar flujo completo."""
    print("\n🔄 Ejecutando flujo COMPLETO...")
    print("   1. Recolectar datos")
    print("   2. Analizar")
    print("   3. Generar evidence pack")
    print("   4. Generar reportes\n")
    
    confirm = input("⚠️  Esto puede tardar varias horas. ¿Continuar? (s/N): ").strip().lower()
    if confirm != 's':
        print("❌ Cancelado")
        return False
    
    # Paso 1: Recolectar
    if not run_collect():
        print("\n❌ Error en recolección. Abortando.")
        return False
    
    # Encontrar el último run creado
    runs_dir = Path("./runs")
    if not runs_dir.exists():
        print("\n❌ No se encontró el run creado")
        return False
    
    runs = sorted([d for d in runs_dir.iterdir() if d.is_dir()], reverse=True)
    if not runs:
        print("\n❌ No se encontró el run creado")
        return False
    
    latest_run = runs[0]
    print(f"\n✅ Run creado: {latest_run.name}")
    
    # Paso 2: Analizar
    if not run_command(f"make analyze RUN_DIR={latest_run}", "Análisis", latest_run):
        print("\n⚠️  Error en análisis, continuando...")
    
    # Paso 3: Evidence
    if not run_command(f"make evidence RUN_DIR={latest_run}", "Evidence pack", latest_run):
        print("\n⚠️  Error en evidence pack, continuando...")
    
    # Paso 4: Reportes
    if not run_command(f"make reports RUN_DIR={latest_run}", "Reportes", latest_run):
        print("\n⚠️  Error en reportes, continuando...")
    
    print(f"\n✅ Flujo completo finalizado!")
    print(f"   Revisa los resultados en: {latest_run}/outputs/")
    
    return True

def main():
    """Función principal."""
    print_header()
    
    while True:
        print_menu()
        choice = get_user_choice()
        
        if choice == '0':
            print("\n👋 ¡Hasta luego!\n")
            break
        
        elif choice == '1':
            run_demo()
        
        elif choice == '2':
            run_collect()
        
        elif choice == '3':
            run_analyze()
        
        elif choice == '4':
            run_evidence()
        
        elif choice == '5':
            run_reports()
        
        elif choice == '6':
            run_complete()
        
        elif choice == '7':
            verify_aws_credentials()
        
        elif choice == '8':
            check_dependencies()
        
        elif choice == '9':
            list_runs()
        
        elif choice == '10':
            show_inventory_console()
        
        elif choice == '11':
            run_command("make clean", "Limpieza de archivos temporales", None)
        
        # Pausa antes de volver al menú
        if choice != '0':
            input("\n⏎ Presiona Enter para continuar...")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 ¡Hasta luego!\n")
        sys.exit(0)

