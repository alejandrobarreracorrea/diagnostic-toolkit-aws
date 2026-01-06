#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para verificar permisos directamente con AWS CLI.
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

def run_aws_command(cmd, description):
    """Ejecutar comando AWS CLI."""
    print(f"\n{'='*80}")
    print(f"🔍 {description}")
    print(f"{'='*80}")
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
            shell=True if sys.platform == 'win32' else False
        )
        
        if result.returncode == 0:
            if result.stdout.strip():
                try:
                    data = json.loads(result.stdout)
                    print(json.dumps(data, indent=2, ensure_ascii=False))
                    return data
                except json.JSONDecodeError:
                    print(result.stdout)
                    return result.stdout
            else:
                print("   ✅ Comando ejecutado exitosamente (sin salida)")
                return True
        else:
            print(f"   ❌ Error ejecutando comando")
            print(f"   Código: {result.returncode}")
            if result.stderr:
                print(f"   Error: {result.stderr[:500]}")
            return None
    except subprocess.TimeoutExpired:
        print(f"   ⏱️  Timeout ejecutando comando")
        return None
    except FileNotFoundError:
        print(f"   ❌ AWS CLI no encontrado. Instala AWS CLI primero.")
        return None
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return None

def main():
    print("="*80)
    print("🔍 VERIFICACIÓN DE PERMISOS AWS CON CLI")
    print("="*80)
    
    # 1. Verificar identidad
    identity = run_aws_command(
        ['aws', 'sts', 'get-caller-identity'],
        "1. IDENTIDAD DE AWS"
    )
    
    if not identity:
        print("\n❌ No se pudo obtener la identidad. Verifica las credenciales AWS.")
        return
    
    arn = identity.get('Arn', '')
    account_id = identity.get('Account', '')
    user_id = identity.get('UserId', '')
    
    print(f"\n   ✅ Usuario/Rol ARN: {arn}")
    print(f"   ✅ Account ID: {account_id}")
    print(f"   ✅ User ID: {user_id}")
    
    # Determinar si es usuario o rol
    is_role = ':role/' in arn
    is_user = ':user/' in arn
    
    entity_name = None
    if is_role:
        entity_name = arn.split(':role/')[-1].split('/')[0]
        entity_type = "Rol"
    elif is_user:
        entity_name = arn.split(':user/')[-1]
        entity_type = "Usuario"
    else:
        print("\n⚠️  No se pudo determinar el tipo de entidad")
        return
    
    print(f"\n   📋 Tipo: {entity_type}")
    print(f"   📋 Nombre: {entity_name}")
    
    # 2. Listar políticas adjuntas
    if is_role:
        print(f"\n{'='*80}")
        print(f"2. POLÍTICAS ADJUNTAS AL ROL")
        print(f"{'='*80}")
        
        # Políticas administradas adjuntas
        attached_policies = run_aws_command(
            ['aws', 'iam', 'list-attached-role-policies', '--role-name', entity_name],
            f"Políticas administradas adjuntas a {entity_name}"
        )
        
        if attached_policies:
            policies = attached_policies.get('AttachedPolicies', [])
            print(f"\n   📋 Total de políticas administradas: {len(policies)}")
            for policy in policies:
                policy_arn = policy.get('PolicyArn', '')
                policy_name = policy.get('PolicyName', '')
                print(f"      - {policy_name}")
                if 'ECAD' in policy_name or 'ecad' in policy_name.lower():
                    print(f"        ✅ Política ECAD encontrada: {policy_name}")
        
        # Políticas inline
        inline_policies = run_aws_command(
            ['aws', 'iam', 'list-role-policies', '--role-name', entity_name],
            f"Políticas inline del rol {entity_name}"
        )
        
        if inline_policies:
            policy_names = inline_policies.get('PolicyNames', [])
            if policy_names:
                print(f"\n   📋 Total de políticas inline: {len(policy_names)}")
                for policy_name in policy_names:
                    print(f"      - {policy_name}")
                    
                    # Obtener contenido de política inline
                    policy_doc = run_aws_command(
                        ['aws', 'iam', 'get-role-policy', '--role-name', entity_name, '--policy-name', policy_name],
                        f"Contenido de política inline: {policy_name}"
                    )
        
        # Obtener información del rol (incluyendo Permissions Boundary)
        role_info = run_aws_command(
            ['aws', 'iam', 'get-role', '--role-name', entity_name],
            f"Información completa del rol {entity_name}"
        )
        
        if role_info:
            role_data = role_info.get('Role', {})
            permissions_boundary = role_data.get('PermissionsBoundary', {})
            if permissions_boundary:
                print(f"\n   ⚠️  PERMISSIONS BOUNDARY DETECTADO:")
                print(f"      ARN: {permissions_boundary.get('PermissionsBoundaryArn', 'N/A')}")
                print(f"      Tipo: {permissions_boundary.get('PermissionsBoundaryType', 'N/A')}")
                print(f"      ⚠️  Esto puede estar limitando los permisos!")
            
            # Verificar si hay políticas con Deny
            print(f"\n   🔍 Verificando políticas con 'Deny'...")
            # Esto requiere obtener el contenido de cada política
    
    elif is_user:
        print(f"\n{'='*80}")
        print(f"2. POLÍTICAS ADJUNTAS AL USUARIO")
        print(f"{'='*80}")
        
        attached_policies = run_aws_command(
            ['aws', 'iam', 'list-attached-user-policies', '--user-name', entity_name],
            f"Políticas administradas adjuntas a {entity_name}"
        )
        
        if attached_policies:
            policies = attached_policies.get('AttachedPolicies', [])
            print(f"\n   📋 Total de políticas administradas: {len(policies)}")
            for policy in policies:
                policy_arn = policy.get('PolicyArn', '')
                policy_name = policy.get('PolicyName', '')
                print(f"      - {policy_name}")
                if 'ECAD' in policy_name or 'ecad' in policy_name.lower():
                    print(f"        ✅ Política ECAD encontrada: {policy_name}")
    
    # 3. Probar operaciones de EC2 directamente
    print(f"\n{'='*80}")
    print(f"3. PROBANDO OPERACIONES DE EC2")
    print(f"{'='*80}")
    
    ec2_operations = [
        ('describe-regions', 'ec2:DescribeRegions'),
        ('describe-instances', 'ec2:DescribeInstances'),
        ('describe-vpcs', 'ec2:DescribeVpcs'),
        ('describe-account-attributes', 'ec2:DescribeAccountAttributes'),
    ]
    
    print(f"\n   Probando {len(ec2_operations)} operaciones de EC2:")
    print()
    
    results = []
    for op_name, required_perm in ec2_operations:
        print(f"   🔸 {op_name} (requiere {required_perm})...")
        # Construir comando según la operación
        if op_name == 'describe-regions':
            cmd = ['aws', 'ec2', op_name, '--region', 'us-east-1', '--output', 'json']
        elif op_name == 'describe-account-attributes':
            cmd = ['aws', 'ec2', op_name, '--region', 'us-east-1', '--output', 'json']
        else:
            cmd = ['aws', 'ec2', op_name, '--region', 'us-east-1', '--output', 'json']
        
        result = run_aws_command(cmd, f"   Ejecutando {op_name}")
        
        if result is not None and result is not True:
            if isinstance(result, dict) and 'Regions' in result or 'Instances' in result or 'Vpcs' in result or 'AccountAttributes' in result:
                results.append({'operation': op_name, 'status': '✅ EXITOSO', 'permission': required_perm})
                print(f"      ✅ {op_name}: EXITOSO")
            else:
                results.append({'operation': op_name, 'status': '❌ FALLO', 'permission': required_perm})
                print(f"      ❌ {op_name}: FALLO")
        elif result is True:
            results.append({'operation': op_name, 'status': '✅ EXITOSO', 'permission': required_perm})
            print(f"      ✅ {op_name}: EXITOSO")
        else:
            results.append({'operation': op_name, 'status': '❌ FALLO', 'permission': required_perm})
            print(f"      ❌ {op_name}: FALLO")
    
    # 4. Simular permisos con IAM Policy Simulator (si está disponible)
    if is_role:
        print(f"\n{'='*80}")
        print(f"4. SIMULACIÓN DE PERMISOS (IAM Policy Simulator)")
        print(f"{'='*80}")
        
        test_actions = [
            'ec2:DescribeRegions',
            'ec2:DescribeInstances',
            'ec2:DescribeVpcs',
            'ec2:DescribeAccountAttributes',
        ]
        
        for action in test_actions:
            print(f"\n   🔸 Simulando: {action}")
            result = run_aws_command(
                ['aws', 'iam', 'simulate-principal-policy', 
                 '--policy-source-arn', arn,
                 '--action-names', action,
                 '--resource-arns', '*'],
                f"   Simulación de {action}"
            )
            
            if result:
                evaluation_results = result.get('EvaluationResults', [])
                if evaluation_results:
                    eval_result = evaluation_results[0]
                    decision = eval_result.get('EvalDecision', 'Unknown')
                    decision_details = eval_result.get('EvalDecisionDetails', {})
                    
                    print(f"      Decisión: {decision}")
                    if decision_details:
                        for key, value in decision_details.items():
                            print(f"      {key}: {value}")
    
    # 5. Verificar SCPs (si está en una organización)
    print(f"\n{'='*80}")
    print(f"5. VERIFICANDO SERVICE CONTROL POLICIES (SCPs)")
    print(f"{'='*80}")
    
    try:
        org_info = run_aws_command(
            ['aws', 'organizations', 'describe-account', '--account-id', account_id],
            "Información de la organización"
        )
        
        if org_info:
            print(f"\n   ⚠️  La cuenta está en una organización AWS")
            print(f"   Verificando SCPs aplicadas...")
            
            scps = run_aws_command(
                ['aws', 'organizations', 'list-policies-for-target', 
                 '--target-id', account_id, 
                 '--filter', 'SERVICE_CONTROL_POLICY'],
                "SCPs aplicadas a la cuenta"
            )
            
            if scps:
                policy_refs = scps.get('Policies', [])
                if policy_refs:
                    print(f"\n   ⚠️  SCPs encontradas: {len(policy_refs)}")
                    for policy_ref in policy_refs:
                        policy_id = policy_ref.get('Id', '')
                        policy_name = policy_ref.get('Name', '')
                        print(f"      - {policy_name} (ID: {policy_id})")
                        
                        # Obtener contenido del SCP
                        scp_content = run_aws_command(
                            ['aws', 'organizations', 'describe-policy', '--policy-id', policy_id],
                            f"Contenido del SCP: {policy_name}"
                        )
                        
                        if scp_content:
                            policy_doc = scp_content.get('Policy', {}).get('Content', '')
                            if policy_doc:
                                try:
                                    policy_json = json.loads(policy_doc)
                                    statements = policy_json.get('Statement', [])
                                    for stmt in statements:
                                        effect = stmt.get('Effect', '')
                                        actions = stmt.get('Action', [])
                                        if effect == 'Deny' and ('ec2:*' in str(actions) or 'ec2:Describe*' in str(actions)):
                                            print(f"         ⚠️  DENY encontrado para EC2!")
                                except:
                                    pass
                else:
                    print(f"\n   ✅ No hay SCPs aplicadas")
        else:
            print(f"\n   ✅ La cuenta no está en una organización o no tienes permisos para verificar")
    except:
        print(f"\n   ℹ️  No se pudo verificar SCPs (puede que no estés en una organización)")
    
    # Resumen final
    print(f"\n{'='*80}")
    print(f"📊 RESUMEN")
    print(f"{'='*80}")
    
    successful_ops = sum(1 for r in results if '✅' in r['status'])
    failed_ops = len(results) - successful_ops
    
    print(f"\n   Operaciones de EC2 probadas: {len(results)}")
    print(f"   ✅ Exitosas: {successful_ops}")
    print(f"   ❌ Fallidas: {failed_ops}")
    
    if failed_ops > 0:
        print(f"\n   ⚠️  PROBLEMAS DETECTADOS:")
        print(f"      1. Verifica que las políticas ECAD estén adjuntas")
        print(f"      2. Revisa si hay Permissions Boundary que limite los permisos")
        print(f"      3. Verifica si hay SCPs bloqueando EC2")
        print(f"      4. Revisa si hay políticas con 'Effect': 'Deny' para EC2")
        print(f"      5. Verifica que no haya condiciones restrictivas en las políticas")
    
    print(f"\n{'='*80}")

if __name__ == "__main__":
    main()

