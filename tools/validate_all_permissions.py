#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para validar TODOS los permisos en las políticas IAM de ECAD
contra la documentación oficial de AWS usando AWS IAM Access Analyzer.
"""

import json
import sys
import subprocess
from pathlib import Path
from typing import List, Dict, Set

# Configurar codificación UTF-8 para Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

project_root = Path(__file__).parent.parent

def load_policy(file_path: Path) -> Dict:
    """Cargar política JSON."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ Error cargando {file_path}: {e}")
        return None

def extract_all_permissions(policy: Dict) -> Set[str]:
    """Extraer todos los permisos de una política."""
    permissions = set()
    for statement in policy.get("Statement", []):
        actions = statement.get("Action", [])
        if isinstance(actions, str):
            permissions.add(actions)
        elif isinstance(actions, list):
            permissions.update(actions)
    return permissions

def validate_policy_syntax(policy_file: Path) -> Dict:
    """Validar sintaxis JSON de la política."""
    print(f"\n🔍 Validando sintaxis JSON de {policy_file.name}...")
    
    try:
        with open(policy_file, 'r', encoding='utf-8') as f:
            policy = json.load(f)
        
        # Validar estructura básica
        if "Version" not in policy:
            return {"valid": False, "error": "Falta campo 'Version'"}
        if "Statement" not in policy:
            return {"valid": False, "error": "Falta campo 'Statement'"}
        
        # Validar cada statement
        for i, stmt in enumerate(policy.get("Statement", [])):
            if "Effect" not in stmt:
                return {"valid": False, "error": f"Statement {i}: Falta campo 'Effect'"}
            if "Action" not in stmt and "NotAction" not in stmt:
                return {"valid": False, "error": f"Statement {i}: Falta campo 'Action' o 'NotAction'"}
        
        return {"valid": True, "message": "Sintaxis JSON válida"}
    except json.JSONDecodeError as e:
        return {"valid": False, "error": f"Error JSON: {str(e)}"}
    except Exception as e:
        return {"valid": None, "error": str(e)}

def validate_policy_with_access_analyzer(policy_file: Path) -> Dict:
    """Validar política usando AWS Access Analyzer."""
    print(f"\n🔍 Validando {policy_file.name} con AWS Access Analyzer...")
    
    try:
        # Leer el contenido de la política
        with open(policy_file, 'r', encoding='utf-8') as f:
            policy_content = f.read()
        
        # Intentar validar con Access Analyzer usando AWS CLI
        result = subprocess.run(
            ['aws', 'accessanalyzer', 'validate-policy',
             '--policy-type', 'IDENTITY_POLICY',
             '--policy-document', policy_content],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            output = json.loads(result.stdout) if result.stdout else {}
            findings = output.get('findings', [])
            
            # Filtrar solo errores críticos (no warnings)
            critical_findings = [
                f for f in findings 
                if f.get('findingType') in ['ERROR', 'SECURITY_WARNING']
            ]
            
            return {
                "valid": len(critical_findings) == 0, 
                "findings": findings,
                "critical_findings": critical_findings,
                "output": output
            }
        else:
            # Si Access Analyzer falla, intentar con boto3
            return validate_with_boto3_access_analyzer(policy_file)
    except FileNotFoundError:
        return {"valid": None, "error": "AWS CLI no encontrado"}
    except subprocess.TimeoutExpired:
        return {"valid": None, "error": "Timeout validando política"}
    except json.JSONDecodeError:
        return {"valid": None, "error": "Error parseando respuesta JSON"}
    except Exception as e:
        return {"valid": None, "error": str(e)}

def validate_with_boto3_access_analyzer(policy_file: Path) -> Dict:
    """Validar política usando boto3 Access Analyzer."""
    try:
        import boto3
        accessanalyzer = boto3.client('accessanalyzer')
        
        with open(policy_file, 'r', encoding='utf-8') as f:
            policy_doc = f.read()
        
        # Intentar validar con Access Analyzer
        response = accessanalyzer.validate_policy(
            policyType='IDENTITY_POLICY',
            policyDocument=policy_doc
        )
        
        findings = response.get('findings', [])
        critical_findings = [
            f for f in findings 
            if f.get('findingType') in ['ERROR', 'SECURITY_WARNING']
        ]
        
        return {
            "valid": len(critical_findings) == 0,
            "findings": findings,
            "critical_findings": critical_findings
        }
    except accessanalyzer.exceptions.ValidationException as e:
        return {"valid": False, "error": f"Error de validación: {str(e)}"}
    except Exception as e:
        return {"valid": None, "error": f"No se pudo validar: {str(e)}"}

def validate_by_creating_policy(policy_file: Path) -> Dict:
    """Validar intentando crear una política temporal en AWS."""
    try:
        import boto3
        iam = boto3.client('iam')
        
        # Leer la política
        with open(policy_file, 'r', encoding='utf-8') as f:
            policy_doc = f.read()
        
        policy_name = f"ECAD-VALIDATION-TEMP-{policy_file.stem}"
        
        # Intentar crear la política
        try:
            response = iam.create_policy(
                PolicyName=policy_name,
                PolicyDocument=policy_doc
            )
            
            # Si se creó exitosamente, eliminarla
            policy_arn = response['Policy']['Arn']
            iam.delete_policy(PolicyArn=policy_arn)
            
            return {"valid": True, "message": "Política validada exitosamente"}
        except iam.exceptions.MalformedPolicyDocumentException as e:
            return {"valid": False, "error": f"Política malformada: {str(e)}"}
        except iam.exceptions.InvalidInputException as e:
            return {"valid": False, "error": f"Entrada inválida: {str(e)}"}
        except Exception as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            error_msg = e.response.get('Error', {}).get('Message', str(e))
            return {"valid": False, "error": f"{error_code}: {error_msg}"}
    except ImportError:
        # Si boto3 no está disponible, usar AWS CLI
        try:
            policy_name = f"ECAD-VALIDATION-TEMP-{policy_file.stem}"
            result = subprocess.run(
                ['aws', 'iam', 'create-policy',
                 '--policy-name', policy_name,
                 '--policy-document', f'file://{policy_file.absolute()}'],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                output = json.loads(result.stdout) if result.stdout else {}
                policy_arn = output.get('Policy', {}).get('Arn', '')
                
                if policy_arn:
                    subprocess.run(
                        ['aws', 'iam', 'delete-policy', '--policy-arn', policy_arn],
                        capture_output=True,
                        timeout=10
                    )
                
                return {"valid": True, "message": "Política validada exitosamente"}
            else:
                error_msg = result.stderr
                return {"valid": False, "error": error_msg}
        except Exception as e:
            return {"valid": None, "error": str(e)}
    except Exception as e:
        return {"valid": None, "error": str(e)}

def check_aws_cli_available() -> bool:
    """Verificar si AWS CLI está disponible."""
    try:
        result = subprocess.run(
            ['aws', '--version'],
            capture_output=True,
            timeout=5
        )
        return result.returncode == 0
    except:
        return False

def check_aws_credentials() -> bool:
    """Verificar si hay credenciales AWS configuradas."""
    try:
        import boto3
        session = boto3.Session()
        credentials = session.get_credentials()
        if credentials is None:
            return False
        # Intentar obtener el caller identity
        sts = boto3.client('sts')
        sts.get_caller_identity()
        return True
    except Exception:
        # Si boto3 falla, intentar con AWS CLI
        try:
            result = subprocess.run(
                ['aws', 'sts', 'get-caller-identity'],
                capture_output=True,
                timeout=10
            )
            return result.returncode == 0
        except:
            return False

def main():
    print("="*80)
    print("🔍 VALIDACIÓN COMPLETA DE PERMISOS IAM - ECAD")
    print("="*80)
    
    # Verificar AWS CLI
    if not check_aws_cli_available():
        print("\n❌ AWS CLI no está instalado o no está en el PATH")
        print("   Instala AWS CLI: https://aws.amazon.com/cli/")
        return
    
    # Verificar credenciales
    if not check_aws_credentials():
        print("\n⚠️  No hay credenciales AWS configuradas")
        print("   Configura credenciales con: aws configure")
        print("   O usando variables de entorno: AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY")
        print("\n   Continuando con validación de sintaxis solamente...")
        use_access_analyzer = False
    else:
        print("\n✅ Credenciales AWS encontradas")
        use_access_analyzer = True
    
    # Cargar políticas
    policy_files = [
        project_root / "policies" / "iam-policy-ecad-part1.json",
        project_root / "policies" / "iam-policy-ecad-part2.json",
        project_root / "policies" / "iam-policy-ecad-part3.json",
    ]
    
    all_permissions = set()
    results = {}
    
    for policy_file in policy_files:
        if not policy_file.exists():
            continue
        
        policy = load_policy(policy_file)
        if not policy:
            continue
        
        permissions = extract_all_permissions(policy)
        all_permissions.update(permissions)
        
        print(f"\n📄 {policy_file.name}")
        print(f"   Permisos encontrados: {len(permissions)}")
        
        # Validar sintaxis JSON
        validation_result = validate_policy_syntax(policy_file)
        results[policy_file.name] = {
            "permissions": permissions,
            "validation": validation_result
        }
        
        if validation_result.get("valid") is True:
            print("   ✅ Sintaxis JSON válida")
        elif validation_result.get("valid") is False:
            print(f"   ❌ Error de sintaxis: {validation_result.get('error', 'Unknown error')}")
        else:
            print(f"   ⚠️  No se pudo validar: {validation_result.get('error', 'Unknown error')}")
        
        # Validar con Access Analyzer si hay credenciales
        if use_access_analyzer:
            analyzer_result = validate_policy_with_access_analyzer(policy_file)
            results[policy_file.name]["analyzer"] = analyzer_result
            
            if analyzer_result.get("valid") is True:
                print("   ✅ Política validada exitosamente (sin errores)")
            elif analyzer_result.get("valid") is False:
                error_msg = analyzer_result.get("error", "Error desconocido")
                print(f"   ❌ Error validando política: {error_msg}")
                # Si hay findings, mostrarlos
                findings = analyzer_result.get("findings", [])
                critical = analyzer_result.get("critical_findings", [])
                if findings:
                    print(f"   ⚠️  Access Analyzer encontró {len(findings)} problema(s):")
                    for finding in findings[:5]:  # Mostrar primeros 5
                        issue_type = finding.get('findingType', 'Unknown')
                        issue_code = finding.get('issueCode', 'Unknown')
                        location = finding.get('locations', [{}])[0].get('path', 'N/A')
                        print(f"      - {issue_type}: {issue_code} (en {location})")
                    if len(findings) > 5:
                        print(f"      ... y {len(findings) - 5} más")
                if critical:
                    print(f"   ⚠️  {len(critical)} error(es) crítico(s) encontrado(s)")
            else:
                error_msg = analyzer_result.get("error", "No se pudo validar")
                print(f"   ⚠️  No se pudo validar: {error_msg}")
    
    # Resumen
    print("\n" + "="*80)
    print("📊 RESUMEN")
    print("="*80)
    print(f"\nTotal de permisos únicos: {len(all_permissions)}")
    
    # Agrupar por servicio
    services = {}
    for perm in all_permissions:
        if ':' in perm:
            service = perm.split(':')[0]
            if service not in services:
                services[service] = []
            services[service].append(perm)
    
    print(f"Servicios únicos: {len(services)}")
    
    # Mostrar servicios con más permisos
    print("\n🔝 Top 10 servicios por número de permisos:")
    sorted_services = sorted(services.items(), key=lambda x: len(x[1]), reverse=True)
    for i, (service, perms) in enumerate(sorted_services[:10], 1):
        print(f"   {i}. {service}: {len(perms)} permisos")
    
    # Guardar resultados
    results_file = project_root / "policies" / "validation_results.json"
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump({
            "total_permissions": len(all_permissions),
            "total_services": len(services),
            "results": {k: {
                "permission_count": len(v["permissions"]),
                "validation_status": v["validation"].get("valid"),
                "analyzer_status": v.get("analyzer", {}).get("valid")
            } for k, v in results.items()}
        }, f, indent=2)
    
    print(f"\n💾 Resultados guardados en: {results_file}")
    print("\n✅ Validación completada")

if __name__ == "__main__":
    main()

