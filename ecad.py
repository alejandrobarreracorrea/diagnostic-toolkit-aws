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
from collections import Counter, defaultdict

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
    print(" 11. 🔍 VALIDAR - Validar run y analizar errores")
    print(" 12. 🧹 LIMPIAR - Limpiar archivos temporales")
    print("  0. ❌ SALIR")
    print()

def get_user_choice():
    """Obtener selección del usuario."""
    while True:
        try:
            choice = input("Tu opción (0-12): ").strip()
            if choice in ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12']:
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

def operation_to_iam_permission(service_name: str, operation_name: str) -> str:
    """Convertir una operación AWS a permiso IAM necesario."""
    # Normalizar nombres de servicio (algunos tienen guiones)
    service_normalized = service_name.replace('-', '')
    
    # Casos especiales
    special_cases = {
        'apigateway': {
            'GetRestApis': 'apigateway:GET',
            'GetApis': 'apigateway:GET',
            'GetSdkTypes': 'apigateway:GET',
            'GetAccount': 'apigateway:GET',
        },
        'apigatewayv2': {
            'GetApis': 'apigatewayv2:Get*',
            'GetApi': 'apigatewayv2:Get*',
        },
        's3': {
            'ListBuckets': 's3:ListAllMyBuckets',
            'GetBucketLocation': 's3:GetBucketLocation',
        },
        'iam': {
            'GenerateServiceLastAccessedDetails': 'iam:GenerateServiceLastAccessedDetails',
            'GetServiceLastAccessedDetails': 'iam:GetServiceLastAccessedDetails',
        },
        'sts': {
            'GetCallerIdentity': 'sts:GetCallerIdentity',
        },
        'cloudtrail': {
            'LookupEvents': 'cloudtrail:LookupEvents',
        },
    }
    
    # Verificar casos especiales primero
    if service_name in special_cases:
        if operation_name in special_cases[service_name]:
            return special_cases[service_name][operation_name]
    
    # Mapeo estándar basado en prefijos de operación
    op_lower = operation_name.lower()
    
    if op_lower.startswith('list'):
        return f"{service_name}:List*"
    elif op_lower.startswith('describe'):
        return f"{service_name}:Describe*"
    elif op_lower.startswith('get'):
        return f"{service_name}:Get*"
    elif op_lower.startswith('batchget') or op_lower.startswith('batchdescribe'):
        return f"{service_name}:Get*"
    elif op_lower.startswith('scan') or op_lower.startswith('query'):
        # DynamoDB y otros servicios
        return f"{service_name}:List*"
    else:
        # Por defecto, intentar inferir
        # Si tiene "List" en el nombre, usar List*
        if 'list' in op_lower:
            return f"{service_name}:List*"
        # Si tiene "Describe" o "Get", usar Describe* o Get*
        elif 'describe' in op_lower:
            return f"{service_name}:Describe*"
        elif 'get' in op_lower:
            return f"{service_name}:Get*"
        else:
            # Fallback: usar el nombre de la operación directamente
            return f"{service_name}:{operation_name}"

def generate_missing_permissions(permission_errors: list) -> dict:
    """Generar lista de permisos IAM faltantes basados en errores."""
    missing_permissions = {}
    
    for error in permission_errors:
        service = error['service']
        operation = error['operation']
        permission = operation_to_iam_permission(service, operation)
        
        if service not in missing_permissions:
            missing_permissions[service] = {
                'permissions': set(),
                'operations': [],
                'count': 0
            }
        
        missing_permissions[service]['permissions'].add(permission)
        missing_permissions[service]['operations'].append(operation)
        missing_permissions[service]['count'] += 1
    
    # Convertir sets a listas para JSON
    for service in missing_permissions:
        missing_permissions[service]['permissions'] = sorted(list(missing_permissions[service]['permissions']))
        missing_permissions[service]['operations'] = sorted(list(set(missing_permissions[service]['operations'])))
    
    return missing_permissions

def generate_iam_policy_json(missing_permissions: dict) -> dict:
    """Generar política IAM JSON con los permisos faltantes."""
    all_permissions = set()
    
    for service_data in missing_permissions.values():
        all_permissions.update(service_data['permissions'])
    
    policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "ECADMissingPermissions",
                "Effect": "Allow",
                "Action": sorted(list(all_permissions)),
                "Resource": "*"
            }
        ]
    }
    
    return policy

def validate_run():
    """Validar un run y analizar errores."""
    run_dir = select_run()
    
    if not run_dir:
        print("\n❌ No se seleccionó ningún run")
        return False
    
    print(f"\n🔍 Validando run: {run_dir.name}")
    print("="*80)
    
    # Verificar estructura del run
    index_file = run_dir / "index" / "index.json"
    metadata_file = run_dir / "metadata.json"
    stats_file = run_dir / "collection_stats.json"
    
    print("\n📁 Verificando estructura del run...")
    issues = []
    
    if not index_file.exists():
        issues.append("❌ No se encontró index/index.json - El run no ha sido analizado")
        print("   ⚠️  Ejecuta primero la opción 3 (ANALIZAR) para generar el índice")
    else:
        print("   ✅ Índice encontrado")
    
    if not metadata_file.exists():
        issues.append("⚠️  No se encontró metadata.json")
    else:
        print("   ✅ Metadatos encontrados")
    
    if not stats_file.exists():
        issues.append("⚠️  No se encontró collection_stats.json")
    else:
        print("   ✅ Estadísticas de recolección encontradas")
    
    # Verificar archivos raw
    raw_dir = run_dir / "raw"
    if raw_dir.exists():
        raw_files = list(raw_dir.rglob("*.gz"))
        print(f"   ✅ {len(raw_files)} archivos raw encontrados")
    else:
        issues.append("❌ No se encontró directorio raw/ - No hay datos recolectados")
    
    if issues:
        print("\n⚠️  PROBLEMAS ENCONTRADOS:")
        for issue in issues:
            print(f"   {issue}")
    
    # Si no hay índice, no podemos analizar errores
    if not index_file.exists():
        print("\n💡 RECOMENDACIÓN: Ejecuta la opción 3 (ANALIZAR) primero para generar el índice")
        return False
    
    # Analizar errores
    print("\n" + "="*80)
    print("📊 ANALIZANDO ERRORES Y ESTADÍSTICAS")
    print("="*80)
    
    try:
        with open(index_file, 'r', encoding='utf-8') as f:
            idx = json.load(f)
    except Exception as e:
        print(f"\n❌ Error leyendo índice: {e}")
        return False
    
    # Analizar errores
    error_codes = Counter()
    error_by_service = defaultdict(list)
    total_errors = 0
    total_operations = 0
    successful_operations = 0
    
    permission_errors = []
    throttling_errors = []
    validation_errors = []
    other_errors = []
    
    permission_codes = ['AccessDenied', 'UnauthorizedOperation', 'Forbidden', 'AccessDeniedException']
    throttling_codes = ['Throttling', 'ThrottlingException', 'TooManyRequestsException', 'RateExceeded']
    validation_codes = ['ValidationException', 'InvalidParameterValue', 'MissingParameter']
    
    services_with_permission_errors = {}
    services_successful = {}
    total_resources = 0
    
    for service_name, service_data in idx.get("services", {}).items():
        service_perm_errors = 0
        service_total_errors = 0
        service_success = 0
        service_resources = 0
        
        for region_name, region_data in service_data.get("regions", {}).items():
            for op_info in region_data.get("operations", []):
                total_operations += 1
                
                if op_info.get("success", True):
                    successful_operations += 1
                    service_success += 1
                    # Contar recursos si están disponibles
                    resource_count = op_info.get("resource_count", 0) or 0
                    total_resources += resource_count
                    service_resources += resource_count
                elif not op_info.get("not_available", False):
                    total_errors += 1
                    service_total_errors += 1
                    error = op_info.get("error", {})
                    if isinstance(error, dict):
                        error_code = error.get("code", "Unknown")
                        error_message = error.get("message", "")
                        error_codes[error_code] += 1
                        
                        entry = {
                            "service": service_name,
                            "operation": op_info.get("operation"),
                            "code": error_code,
                            "message": error_message[:150]
                        }
                        
                        error_by_service[error_code].append(entry)
                        
                        if error_code in permission_codes:
                            permission_errors.append(entry)
                            service_perm_errors += 1
                        elif error_code in throttling_codes:
                            throttling_errors.append(entry)
                        elif error_code in validation_codes:
                            validation_errors.append(entry)
                        else:
                            other_errors.append(entry)
        
        if service_perm_errors > 0:
            services_with_permission_errors[service_name] = {
                "permission_errors": service_perm_errors,
                "total_errors": service_total_errors
            }
        
        if service_success > 0:
            services_successful[service_name] = {
                "successful_ops": service_success,
                "resources": service_resources
            }
    
    # Mostrar estadísticas generales
    print(f"\n📈 ESTADÍSTICAS GENERALES")
    print(f"   Total de operaciones: {total_operations:,}")
    print(f"   Operaciones exitosas: {successful_operations:,} ({successful_operations/total_operations*100:.1f}%)" if total_operations > 0 else "   Operaciones exitosas: 0")
    print(f"   Operaciones con errores: {total_errors:,} ({total_errors/total_operations*100:.1f}%)" if total_operations > 0 else "   Operaciones con errores: 0")
    print(f"   Recursos encontrados: {total_resources:,}")
    print(f"   Servicios con datos exitosos: {len(services_successful)}")
    print(f"   Servicios con errores de permisos: {len(services_with_permission_errors)}")
    
    # Evaluar calidad del run
    print("\n" + "="*80)
    print("📊 EVALUACIÓN DE CALIDAD DEL RUN")
    print("="*80)
    
    if total_operations == 0:
        print("\n❌ CRÍTICO: No se encontraron operaciones en el run")
        print("   El run está vacío o no se recolectó información")
        return False
    
    success_rate = (successful_operations / total_operations * 100) if total_operations > 0 else 0
    
    if success_rate >= 80:
        print(f"\n✅ EXCELENTE: {success_rate:.1f}% de operaciones exitosas")
        print("   El run tiene información suficiente para análisis")
    elif success_rate >= 50:
        print(f"\n⚠️  ADECUADO: {success_rate:.1f}% de operaciones exitosas")
        print("   El run tiene información útil, pero hay muchos errores")
    elif success_rate >= 20:
        print(f"\n⚠️  LIMITADO: {success_rate:.1f}% de operaciones exitosas")
        print("   El run tiene información limitada, revisa los errores")
    else:
        print(f"\n❌ CRÍTICO: Solo {success_rate:.1f}% de operaciones exitosas")
        print("   El run tiene muy poca información útil")
    
    # Analizar tipos de errores
    if permission_errors:
        print("\n" + "="*80)
        print(f"🔒 ERRORES DE PERMISOS ({len(permission_errors)} errores)")
        print("="*80)
        print("   Estos errores indican que faltan permisos IAM.\n")
        print("   Top 10 servicios con más errores de permisos:")
        service_counts = Counter([e['service'] for e in permission_errors])
        for i, (service, count) in enumerate(service_counts.most_common(10), 1):
            print(f"   {i:2d}. {service:30s} - {count:3d} operaciones sin permisos")
        
        # Generar lista de permisos faltantes
        print("\n" + "="*80)
        print("🔑 PERMISOS IAM FALTANTES")
        print("="*80)
        
        missing_perms = generate_missing_permissions(permission_errors)
        
        print(f"\n   Total de servicios con permisos faltantes: {len(missing_perms)}")
        print(f"   Total de permisos únicos faltantes: {sum(len(s['permissions']) for s in missing_perms.values())}")
        
        print("\n   📋 Permisos faltantes por servicio:")
        # Ordenar por cantidad de errores
        sorted_services = sorted(missing_perms.items(), key=lambda x: x[1]['count'], reverse=True)
        
        for service, data in sorted_services[:20]:  # Top 20 servicios
            print(f"\n   🔸 {service} ({data['count']} errores):")
            for perm in data['permissions']:
                print(f"      - {perm}")
            if len(data['operations']) <= 5:
                print(f"      Operaciones: {', '.join(data['operations'])}")
            else:
                print(f"      Operaciones: {', '.join(data['operations'][:5])} ... (+{len(data['operations'])-5} más)")
        
        if len(sorted_services) > 20:
            print(f"\n   ... y {len(sorted_services) - 20} servicios más")
        
        # Generar política IAM JSON
        iam_policy = generate_iam_policy_json(missing_perms)
        total_permissions = len(iam_policy['Statement'][0]['Action'])
        
        print("\n" + "="*80)
        print("📄 POLÍTICA IAM SUGERIDA")
        print("="*80)
        print(f"\n   Total de permisos necesarios: {total_permissions}")
        print("\n   💾 ¿Guardar política IAM en archivo? (s/N): ", end="")
        
        try:
            save_choice = input().strip().lower()
            if save_choice == 's':
                policy_file = run_dir / "missing_permissions_policy.json"
                with open(policy_file, 'w', encoding='utf-8') as f:
                    json.dump(iam_policy, f, indent=2, ensure_ascii=False)
                print(f"\n   ✅ Política guardada en: {policy_file}")
                print(f"   📋 Puedes usar este archivo para crear/actualizar tu política IAM en AWS")
                print(f"   💡 Instrucciones:")
                print(f"      1. Ve a AWS Console → IAM → Policies → Create Policy")
                print(f"      2. Selecciona 'JSON' y pega el contenido de {policy_file.name}")
                print(f"      3. Adjunta la política a tu rol/usuario")
        except (KeyboardInterrupt, EOFError):
            print("\n   ⏭️  Saltado")
        
        # Mostrar resumen de política
        print("\n   📋 Resumen de la política (primeros 20 permisos):")
        for i, perm in enumerate(iam_policy['Statement'][0]['Action'][:20], 1):
            print(f"      {i:2d}. {perm}")
        if total_permissions > 20:
            print(f"      ... y {total_permissions - 20} permisos más")
        
        print("\n   💡 RECOMENDACIÓN:")
        print("      - Revisa las políticas IAM en policies/iam-policy-ecad-part*.json")
        print("      - Compara con los permisos faltantes identificados arriba")
        print("      - Agrega los permisos faltantes a tu política IAM")
        print("      - Algunos servicios pueden requerir permisos adicionales específicos")
    
    if throttling_errors:
        print("\n" + "="*80)
        print(f"⏱️  ERRORES DE THROTTLING ({len(throttling_errors)} errores)")
        print("="*80)
        print("   Estos errores son NORMALES - AWS limita la tasa de llamadas API")
        print("   El collector tiene retry automático, pero algunos pueden fallar")
        print("   💡 Si hay muchos, reduce ECAD_MAX_THREADS")
    
    if validation_errors:
        print("\n" + "="*80)
        print(f"❌ ERRORES DE VALIDACIÓN ({len(validation_errors)} errores)")
        print("="*80)
        print("   Algunas operaciones requieren parámetros que no se pudieron inferir")
        print("   Estos errores son esperados y no afectan el inventario principal")
    
    if other_errors:
        print("\n" + "="*80)
        print(f"⚠️  OTROS ERRORES ({len(other_errors)} errores)")
        print("="*80)
        error_types = Counter([e['code'] for e in other_errors])
        print("   Top 10 tipos de errores:")
        for i, (code, count) in enumerate(error_types.most_common(10), 1):
            print(f"   {i:2d}. {code:40s} - {count:4d} ocurrencias")
    
    # Mostrar servicios exitosos
    if services_successful:
        print("\n" + "="*80)
        print(f"✅ SERVICIOS CON DATOS EXITOSOS ({len(services_successful)} servicios)")
        print("="*80)
        print("   Top 15 servicios con más recursos:")
        sorted_services = sorted(services_successful.items(), key=lambda x: x[1]['resources'], reverse=True)
        for i, (service, data) in enumerate(sorted_services[:15], 1):
            print(f"   {i:2d}. {service:30s} - {data['resources']:>8,} recursos, {data['successful_ops']:>3} ops exitosas")
    
    # Top códigos de error
    if error_codes:
        print("\n" + "="*80)
        print("📋 TOP 15 CÓDIGOS DE ERROR MÁS COMUNES")
        print("="*80)
        for i, (error_code, count) in enumerate(error_codes.most_common(15), 1):
            pct = (count / total_errors * 100) if total_errors > 0 else 0
            print(f"   {i:2d}. {error_code:40s} - {count:4d} ocurrencias ({pct:5.1f}%)")
            if error_by_service.get(error_code):
                example = error_by_service[error_code][0]
                print(f"       Ejemplo: {example['service']}.{example['operation']}")
    
    # Recomendaciones finales
    print("\n" + "="*80)
    print("💡 RECOMENDACIONES FINALES")
    print("="*80)
    
    if len(permission_errors) > total_errors * 0.5:
        print("\n   1. 🔴 PRIORIDAD ALTA: Más del 50% de errores son de permisos")
        print("      - Revisa y actualiza las políticas IAM")
        print("      - Ejecuta una nueva recolección después de corregir permisos")
    
    if success_rate < 50:
        print("\n   2. ⚠️  El run tiene menos del 50% de éxito")
        print("      - Considera ejecutar una nueva recolección")
        print("      - Verifica las credenciales AWS (opción 7)")
        print("      - Revisa los permisos IAM")
    
    if total_resources == 0:
        print("\n   3. ⚠️  No se encontraron recursos")
        print("      - Verifica que la cuenta AWS tenga recursos")
        print("      - Revisa que las regiones seleccionadas sean correctas")
    
    if success_rate >= 50 and total_resources > 0:
        print("\n   ✅ El run tiene información suficiente para análisis")
        print("      - Puedes generar reportes (opción 5)")
        print("      - Puedes generar evidence pack (opción 4)")
    
    print("\n" + "="*80)
    
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
            validate_run()
        
        elif choice == '12':
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

