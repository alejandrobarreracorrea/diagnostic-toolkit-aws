#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para diagnosticar por qué EC2 falla aunque las políticas estén adjuntas.
"""

import json
import sys
import subprocess
from pathlib import Path

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

def test_ec2_permissions():
    """Probar permisos de EC2 directamente con AWS CLI."""
    print("="*80)
    print("🔍 DIAGNÓSTICO DE PERMISOS EC2")
    print("="*80)
    
    print("\n1. Verificando identidad de AWS...")
    try:
        result = subprocess.run(
            ['aws', 'sts', 'get-caller-identity'],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            identity = json.loads(result.stdout)
            print(f"   ✅ Usuario/Rol: {identity.get('Arn', 'N/A')}")
            print(f"   ✅ Account ID: {identity.get('Account', 'N/A')}")
        else:
            print(f"   ❌ Error: {result.stderr}")
            return
    except FileNotFoundError:
        print("   ❌ AWS CLI no encontrado")
        return
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return
    
    print("\n2. Probando operaciones básicas de EC2...")
    
    test_operations = [
        ('describe-regions', 'ec2:DescribeRegions'),
        ('describe-instances', 'ec2:DescribeInstances'),
        ('describe-vpcs', 'ec2:DescribeVpcs'),
        ('describe-security-groups', 'ec2:DescribeSecurityGroups'),
        ('describe-account-attributes', 'ec2:DescribeAccountAttributes'),
    ]
    
    results = []
    for op_name, required_perm in test_operations:
        try:
            result = subprocess.run(
                ['aws', 'ec2', op_name, '--region', 'us-east-1', '--max-items', '1'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                results.append({
                    'operation': op_name,
                    'permission': required_perm,
                    'status': '✅ EXITOSO',
                    'error': None
                })
            else:
                error_output = result.stderr
                # Extraer código de error
                error_code = 'Unknown'
                if 'UnauthorizedOperation' in error_output:
                    error_code = 'UnauthorizedOperation'
                elif 'AccessDenied' in error_output:
                    error_code = 'AccessDenied'
                elif 'Forbidden' in error_output:
                    error_code = 'Forbidden'
                
                results.append({
                    'operation': op_name,
                    'permission': required_perm,
                    'status': '❌ FALLO',
                    'error': error_code,
                    'details': error_output[:200]
                })
        except Exception as e:
            results.append({
                'operation': op_name,
                'permission': required_perm,
                'status': '❌ ERROR',
                'error': str(e)
            })
    
    print("\n   Resultados:")
    print(f"   {'Operación':<35} {'Permiso Requerido':<35} {'Estado':<15}")
    print("   " + "-"*85)
    for r in results:
        print(f"   {r['operation']:<35} {r['permission']:<35} {r['status']:<15}")
        if r.get('error'):
            print(f"      Error: {r['error']}")
            if r.get('details'):
                print(f"      Detalles: {r['details'][:150]}...")
    
    successful = sum(1 for r in results if '✅' in r['status'])
    failed = len(results) - successful
    
    print(f"\n   Resumen: {successful} exitosas, {failed} fallidas")
    
    if failed > 0:
        print("\n3. Verificando políticas adjuntas...")
        try:
            # Intentar obtener el rol/usuario actual
            identity_result = subprocess.run(
                ['aws', 'sts', 'get-caller-identity'],
                capture_output=True,
                text=True,
                timeout=10
            )
            if identity_result.returncode == 0:
                identity = json.loads(identity_result.stdout)
                arn = identity.get('Arn', '')
                
                if ':user/' in arn:
                    user_name = arn.split(':user/')[-1]
                    print(f"   Usuario: {user_name}")
                    
                    # Listar políticas adjuntas al usuario
                    result = subprocess.run(
                        ['aws', 'iam', 'list-attached-user-policies', '--user-name', user_name],
                        capture_output=True,
                        text=True,
                        timeout=10
                    )
                    if result.returncode == 0:
                        policies = json.loads(result.stdout)
                        print(f"   Políticas adjuntas: {len(policies.get('AttachedPolicies', []))}")
                        for policy in policies.get('AttachedPolicies', []):
                            print(f"      - {policy.get('PolicyName', 'N/A')}")
                
                elif ':role/' in arn:
                    role_name = arn.split(':role/')[-1].split('/')[0]
                    print(f"   Rol: {role_name}")
                    
                    # Listar políticas adjuntas al rol
                    result = subprocess.run(
                        ['aws', 'iam', 'list-attached-role-policies', '--role-name', role_name],
                        capture_output=True,
                        text=True,
                        timeout=10
                    )
                    if result.returncode == 0:
                        policies = json.loads(result.stdout)
                        print(f"   Políticas adjuntas: {len(policies.get('AttachedPolicies', []))}")
                        for policy in policies.get('AttachedPolicies', []):
                            print(f"      - {policy.get('PolicyName', 'N/A')}")
                        
                        # Verificar políticas inline
                        inline_result = subprocess.run(
                            ['aws', 'iam', 'list-role-policies', '--role-name', role_name],
                            capture_output=True,
                            text=True,
                            timeout=10
                        )
                        if inline_result.returncode == 0:
                            inline_policies = json.loads(inline_result.stdout)
                            if inline_policies.get('PolicyNames'):
                                print(f"   Políticas inline: {len(inline_policies.get('PolicyNames', []))}")
                                for policy_name in inline_policies.get('PolicyNames', []):
                                    print(f"      - {policy_name}")
        except Exception as e:
            print(f"   ⚠️  No se pudo verificar políticas: {e}")
    
    print("\n" + "="*80)
    print("💡 DIAGNÓSTICO")
    print("="*80)
    
    if failed == len(results):
        print("\n   ❌ CRÍTICO: Todas las operaciones de EC2 fallan")
        print("\n   Posibles causas:")
        print("   1. 🔴 EXPLICIT DENY en otra política")
        print("      - Revisa todas las políticas adjuntas al rol/usuario")
        print("      - Busca políticas con 'Effect': 'Deny' que puedan bloquear EC2")
        print("      - Los Deny tienen prioridad sobre los Allow")
        print()
        print("   2. 🔴 SERVICE CONTROL POLICY (SCP) a nivel de organización")
        print("      - Si estás en una organización AWS, verifica los SCPs")
        print("      - Los SCPs pueden bloquear servicios completos")
        print("      - Ejecuta: aws organizations list-policies-for-target")
        print()
        print("   3. 🔴 PERMISOS ADICIONALES REQUERIDOS")
        print("      - EC2 puede requerir permisos específicos además de Describe*/Get*/List*")
        print("      - Algunas operaciones pueden requerir permisos de otros servicios")
        print("      - Verifica la documentación de EC2 para permisos específicos")
        print()
        print("   4. 🔴 REGIÓN O SERVICIO NO HABILITADO")
        print("      - Verifica que EC2 esté habilitado en la cuenta")
        print("      - Algunas cuentas pueden tener restricciones por región")
        print()
        print("   📋 ACCIÓN RECOMENDADA:")
        print("      1. Ejecuta: aws iam simulate-principal-policy para verificar permisos")
        print("      2. Revisa todas las políticas adjuntas buscando 'Deny'")
        print("      3. Verifica SCPs si estás en una organización")
        print("      4. Prueba con una operación simple: aws ec2 describe-regions")
    
    elif failed > 0:
        print(f"\n   ⚠️  {failed} operaciones fallan de {len(results)}")
        print("   Algunas operaciones funcionan, otras no")
        print("   Esto puede indicar permisos específicos faltantes")
    
    else:
        print("\n   ✅ Todas las operaciones funcionan correctamente")
        print("   El problema puede estar en el collector, no en los permisos")
    
    print("\n" + "="*80)

if __name__ == "__main__":
    test_ec2_permissions()

