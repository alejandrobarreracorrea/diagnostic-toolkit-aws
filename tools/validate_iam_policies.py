#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para validar políticas IAM de ECAD y filtrar solo errores de operaciones de lectura.
Excluye operaciones de escritura (Create, Delete, Update, etc.) que no deberían ejecutarse.
"""

import json
import sys
import os
from pathlib import Path
from collections import Counter, defaultdict

# Configurar codificación UTF-8 para Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Agregar el directorio raíz al path para importar desde collector
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from collector.discovery import ServiceDiscovery
import boto3

def is_read_operation(operation_name: str) -> bool:
    """Determinar si una operación es de solo lectura (misma lógica que discovery.py)."""
    name_lower = operation_name.lower()
    
    # Operaciones de lectura permitidas
    read_prefixes = [
        'list',      # ListBuckets, ListUsers, etc.
        'describe',  # DescribeInstances, DescribeDBInstances, etc.
        'get',       # GetUser, GetBucket, etc.
        'batchget',  # BatchGetItem, BatchGetImage, etc.
        'batchdescribe',  # BatchDescribe*
        'scan',      # DynamoDB Scan
        'query',     # DynamoDB Query, Athena Query
        'select',    # S3 Select
        'head',      # S3 HeadObject, HeadBucket
        'search',    # SearchDomains, SearchResources, etc.
        'lookup',    # LookupEvents, LookupAttributeKey, etc.
        'check',     # CheckDomainAvailability, etc. (solo lectura)
        'validate',  # ValidateTemplate, ValidateConfiguration, etc. (solo lectura)
        'estimate',  # EstimateCost, etc. (solo lectura)
        'view',      # ViewBilling, etc. (solo lectura)
        'fetch',     # FetchAttributes, etc. (solo lectura)
    ]
    
    # Operaciones de lectura específicas (por nombre exacto o patrón)
    read_operations = [
        'assumeroletrust',  # AssumeRoleTrust (lectura de política)
        'getcalleridentity',  # GetCallerIdentity (lectura)
        'getaccountauthorizationdetails',  # GetAccountAuthorizationDetails (lectura)
    ]
    
    # Verificar operaciones específicas primero
    if name_lower in read_operations:
        return True
    
    # Verificar si empieza con algún prefijo de lectura
    for prefix in read_prefixes:
        if name_lower.startswith(prefix):
            return True
    
    # Operaciones de escritura que DEBEN ser excluidas
    write_prefixes = [
        'create',    # CreateBucket, CreateUser, etc.
        'delete',    # DeleteBucket, DeleteUser, etc.
        'update',    # UpdateUser, UpdateBucket, etc.
        'put',       # PutObject, PutItem, etc.
        'modify',    # ModifyInstance, ModifyDBInstance, etc.
        'add',       # AddTags, AddPermission, etc.
        'remove',    # RemoveTags, RemovePermission, etc.
        'attach',    # AttachRolePolicy, AttachVolume, etc.
        'detach',    # DetachRolePolicy, DetachVolume, etc.
        'associate', # AssociateRouteTable, etc.
        'disassociate', # DisassociateRouteTable, etc.
        'enable',    # EnableLogging, EnableMetrics, etc.
        'disable',   # DisableLogging, DisableMetrics, etc.
        'start',     # StartInstance, StartJob, etc.
        'stop',      # StopInstance, StopJob, etc.
        'terminate', # TerminateInstance, etc.
        'reboot',    # RebootInstance, etc.
        'restore',   # RestoreDBInstance, etc.
        'copy',      # CopyObject, CopySnapshot, etc.
        'move',      # MoveObject, etc.
        'import',    # ImportImage, ImportSnapshot, etc.
        'export',    # ExportImage, ExportSnapshot, etc.
        'invoke',    # InvokeFunction, InvokeEndpoint, etc.
        'send',      # SendMessage, SendCommand, etc.
        'publish',   # PublishMessage, PublishTopic, etc.
        'subscribe', # Subscribe, etc.
        'unsubscribe', # Unsubscribe, etc.
        'authorize', # AuthorizeSecurityGroupIngress, etc.
        'revoke',    # RevokeSecurityGroupIngress, etc.
        'grant',     # GrantPermission, etc.
        'deny',      # DenyPermission, etc.
        'set',       # SetBucketPolicy, SetUserPolicy, etc.
        'reset',     # ResetPassword, etc.
        'change',    # ChangePassword, ChangeResourceRecordSets, etc.
        'register',  # RegisterInstance, RegisterTarget, RegisterPublisher, etc.
        'deregister', # DeregisterInstance, DeregisterTarget, DeregisterType, etc.
        'activate',  # ActivateLicense, etc.
        'deactivate', # DeactivateLicense, DeactivateType, etc.
        'cancel',    # CancelJob, CancelExportTask, etc.
        'abort',     # AbortMultipartUpload, etc.
        'complete',  # CompleteMultipartUpload, etc.
        'initiate',  # InitiateMultipartUpload, etc.
        'upload',    # UploadPart, etc.
        'download',  # DownloadDBLogFile, DownloadDefaultKeyPair, etc.
        'restart',   # RestartAppServer, etc.
        'resume',    # ResumeProcesses, etc.
        'suspend',   # SuspendProcesses, etc.
        'scale',     # ScaleOut, ScaleIn, etc.
        'tag',       # TagResource, etc.
        'untag',     # UntagResource, etc.
        'accept',    # AcceptTransitGatewayMulticastDomainAssociations, etc.
        'allocate',  # AllocateAddress, AllocateHosts, etc.
        'release',   # ReleaseAddress, etc.
        'replace',   # ReplaceImageCriteriaInAllowedImagesSettings, etc.
        'request',   # RequestSpotInstances, etc.
        'reject',    # RejectTransitGatewayMulticastDomainAssociations, etc.
        'clear',     # ClearDefaultAuthorizer, etc.
        'batchstart', # BatchStartRecommendations, etc.
        'batchupdate', # BatchUpdateFindingsV2, BatchUpdateAutomatedDiscoveryAccounts, etc.
        'batchdelete', # BatchDelete, etc.
        'batchstop', # BatchStop, etc.
        'claim',     # ClaimDevice, etc.
        'publish',   # PublishType, PublishMessage, PublishTopic, etc.
        'peer',      # PeerVpc, etc.
        'unpeer',    # UnpeerVpc, etc.
        'accept',    # AcceptTransitGatewayMulticastDomainAssociations, etc.
        'allocate',  # AllocateAddress, AllocateHosts, etc.
        'release',   # ReleaseAddress, etc.
        'replace',   # ReplaceImageCriteriaInAllowedImagesSettings, etc.
        'request',   # RequestSpotInstances, etc.
        'reject',    # RejectTransitGatewayMulticastDomainAssociations, etc.
        'clear',     # ClearDefaultAuthorizer, etc.
        'batchstart', # BatchStartRecommendations, etc.
        'batchupdate', # BatchUpdateFindingsV2, BatchUpdateAutomatedDiscoveryAccounts, etc.
        'batchdelete', # BatchDelete, etc.
        'batchstop', # BatchStop, etc.
        'claim',     # ClaimDevice, etc.
        'deactivate', # DeactivateType, etc.
        'deregister', # DeregisterType, etc.
        'publish',   # PublishType, etc.
        'register',  # RegisterPublisher, etc.
    ]
    
    # Si empieza con algún prefijo de escritura, excluir
    for prefix in write_prefixes:
        if name_lower.startswith(prefix):
            return False
    
    # Si no es claramente de lectura ni de escritura, ser conservador y excluir
    # Solo permitir si es explícitamente una operación de lectura conocida
    return False

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
    elif op_lower.startswith('search'):
        return f"{service_name}:List*"
    elif op_lower.startswith('lookup'):
        return f"{service_name}:Get*"
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

def load_json_file(file_path):
    """Cargar archivo JSON."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error cargando {file_path}: {e}")
        return None

def find_latest_run():
    """Encontrar el run más reciente."""
    runs_dir = project_root / "runs"
    if not runs_dir.exists():
        return None
    runs = sorted([d for d in runs_dir.iterdir() if d.is_dir()], reverse=True)
    return runs[0] if runs else None

def check_permission_covered(permission: str, policy_permissions: set) -> bool:
    """Verificar si un permiso está cubierto por las políticas (incluyendo wildcards)."""
    # Verificar coincidencia exacta
    if permission in policy_permissions:
        return True
    
    # Verificar wildcards
    if ':' in permission:
        service_name, action_pattern = permission.split(':', 1)
        
        # Buscar wildcards que cubran este permiso
        for policy_perm in policy_permissions:
            if ':' in policy_perm:
                policy_service, policy_action = policy_perm.split(':', 1)
                
                # Si el servicio coincide
                if policy_service == service_name:
                    # Si la política tiene wildcard al final
                    if policy_action.endswith('*'):
                        base_action = policy_action[:-1]
                        if action_pattern.startswith(base_action):
                            return True
                    # Si la política es exacta
                    elif policy_action == action_pattern:
                        return True
    
    return False

def main():
    print("="*80)
    print("🔍 VALIDACIÓN DE POLÍTICAS IAM ECAD - SOLO OPERACIONES DE LECTURA")
    print("="*80)
    
    # Cargar políticas
    policy1_file = project_root / "policies" / "iam-policy-ecad-part1.json"
    policy2_file = project_root / "policies" / "iam-policy-ecad-part2.json"
    policy3_file = project_root / "policies" / "iam-policy-ecad-part3.json"
    
    policy1 = load_json_file(policy1_file) if policy1_file.exists() else None
    policy2 = load_json_file(policy2_file) if policy2_file.exists() else None
    policy3 = load_json_file(policy3_file) if policy3_file.exists() else None
    
    if not policy1 and not policy2:
        print("\n❌ No se encontraron políticas IAM")
        return
    
    # Recopilar todos los permisos de las políticas
    all_policy_permissions = set()
    if policy1:
        for stmt in policy1.get("Statement", []):
            actions = stmt.get("Action", [])
            if isinstance(actions, str):
                all_policy_permissions.add(actions)
            else:
                all_policy_permissions.update(actions)
    
    if policy2:
        for stmt in policy2.get("Statement", []):
            actions = stmt.get("Action", [])
            if isinstance(actions, str):
                all_policy_permissions.add(actions)
            else:
                all_policy_permissions.update(actions)
    
    if policy3:
        for stmt in policy3.get("Statement", []):
            actions = stmt.get("Action", [])
            if isinstance(actions, str):
                all_policy_permissions.add(actions)
            else:
                all_policy_permissions.update(actions)
    
    policy_count = sum([1 for p in [policy1, policy2, policy3] if p])
    print(f"\n✅ Políticas cargadas ({policy_count} archivos): {len(all_policy_permissions)} permisos únicos")
    
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
    
    idx = load_json_file(index_file)
    if not idx:
        return
    
    # Analizar errores - SOLO operaciones de lectura
    permission_errors = []
    permission_codes = ['AccessDenied', 'UnauthorizedOperation', 'Forbidden', 'AccessDeniedException']
    
    total_ops = 0
    successful_ops = 0
    failed_ops = 0
    write_operations_errors = 0  # Contador de errores de operaciones de escritura
    
    for service_name, service_data in idx.get("services", {}).items():
        for region_name, region_data in service_data.get("regions", {}).items():
            for op_info in region_data.get("operations", []):
                total_ops += 1
                op_name = op_info.get("operation", "")
                
                if op_info.get("success", True):
                    successful_ops += 1
                else:
                    failed_ops += 1
                    if not op_info.get("not_available", False):
                        error = op_info.get("error", {})
                        if isinstance(error, dict):
                            error_code = error.get("code", "")
                            
                            # FILTRAR: Solo considerar errores de operaciones de LECTURA
                            if is_read_operation(op_name):
                                if error_code in permission_codes:
                                    permission_errors.append({
                                        "service": service_name,
                                        "operation": op_name,
                                        "code": error_code
                                    })
                            else:
                                # Esta es una operación de escritura - no debería ejecutarse
                                write_operations_errors += 1
    
    print(f"\n📊 ESTADÍSTICAS DEL RUN:")
    print(f"   Total de operaciones: {total_ops:,}")
    print(f"   Operaciones exitosas: {successful_ops:,} ({successful_ops/total_ops*100:.1f}%)")
    print(f"   Operaciones fallidas: {failed_ops:,} ({failed_ops/total_ops*100:.1f}%)")
    print(f"   ⚠️  Errores de operaciones de ESCRITURA (no deberían ejecutarse): {write_operations_errors:,}")
    print(f"   🔍 Errores de permisos en operaciones de LECTURA: {len(permission_errors):,}")
    
    if write_operations_errors > 0:
        print(f"\n   ⚠️  IMPORTANTE: Se encontraron {write_operations_errors} errores de operaciones de escritura.")
        print(f"      Estas operaciones NO deberían ejecutarse en un diagnóstico de solo lectura.")
        print(f"      El filtro de operaciones de escritura debería prevenir esto en futuras recolecciones.")
    
    if not permission_errors:
        print("\n✅ No se encontraron errores de permisos en operaciones de lectura")
        print("   Las políticas IAM están correctamente configuradas para operaciones de lectura")
        return
    
    # Analizar permisos faltantes - SOLO para operaciones de lectura
    print("\n" + "="*80)
    print("🔍 ANÁLISIS DE PERMISOS FALTANTES (SOLO OPERACIONES DE LECTURA)")
    print("="*80)
    
    missing_perms_by_service = defaultdict(set)
    covered_perms_by_service = defaultdict(set)
    
    for error in permission_errors:
        service = error['service']
        operation = error['operation']
        perm = operation_to_iam_permission(service, operation)
        
        # Verificar si está en las políticas
        is_covered = check_permission_covered(perm, all_policy_permissions)
        
        if is_covered:
            covered_perms_by_service[service].add(perm)
        else:
            missing_perms_by_service[service].add(perm)
    
    # Mostrar resultados
    print(f"\n📋 RESUMEN:")
    print(f"   Servicios con permisos de LECTURA NO cubiertos: {len(missing_perms_by_service)}")
    print(f"   Servicios con permisos de LECTURA cubiertos pero que fallan: {len(covered_perms_by_service)}")
    
    if missing_perms_by_service:
        print("\n" + "="*80)
        print("❌ SERVICIOS CON PERMISOS DE LECTURA FALTANTES EN LAS POLÍTICAS")
        print("="*80)
        print("\n   Estos son permisos de operaciones de LECTURA que deberían estar en las políticas:")
        
        # Ordenar por cantidad de permisos faltantes
        sorted_services = sorted(missing_perms_by_service.items(), 
                               key=lambda x: len(x[1]), reverse=True)
        
        total_missing = 0
        for service, perms in sorted_services:
            total_missing += len(perms)
            print(f"\n   🔸 {service} ({len(perms)} permisos faltantes):")
            for perm in sorted(perms):
                print(f"      - {perm}")
        
        print(f"\n   📊 Total de permisos de lectura faltantes: {total_missing}")
        
        # Generar política sugerida
        print("\n" + "="*80)
        print("📄 PERMISOS DE LECTURA SUGERIDOS PARA AGREGAR")
        print("="*80)
        
        all_missing_perms = set()
        for perms in missing_perms_by_service.values():
            all_missing_perms.update(perms)
        
        print(f"\n   Total de permisos únicos de lectura faltantes: {len(all_missing_perms)}")
        print("\n   Permisos sugeridos (ordenados por servicio):")
        
        # Agrupar por servicio
        perms_by_service = defaultdict(list)
        for perm in sorted(all_missing_perms):
            if ':' in perm:
                service = perm.split(':')[0]
                perms_by_service[service].append(perm)
        
        for service in sorted(perms_by_service.keys()):
            print(f"\n   {service}:")
            for perm in sorted(perms_by_service[service]):
                print(f"      - {perm}")
    
    if covered_perms_by_service:
        print("\n" + "="*80)
        print("⚠️  SERVICIOS CON PERMISOS CUBIERTOS PERO QUE FALLAN")
        print("="*80)
        print("\n   Estos permisos de LECTURA ESTÁN en las políticas pero aún fallan.")
        print("   Posibles causas:")
        print("   - El rol/usuario no tiene las políticas adjuntas")
        print("   - Hay un 'explicit deny' en otra política")
        print("   - El servicio requiere permisos adicionales específicos")
        
        sorted_covered = sorted(covered_perms_by_service.items(),
                              key=lambda x: len(x[1]), reverse=True)
        
        for service, perms in sorted_covered[:10]:  # Top 10
            print(f"\n   🔸 {service} ({len(perms)} permisos):")
            for perm in sorted(list(perms))[:5]:  # Primeros 5
                print(f"      - {perm}")
            if len(perms) > 5:
                print(f"      ... y {len(perms) - 5} más")
    
    # Recomendaciones finales
    print("\n" + "="*80)
    print("💡 RECOMENDACIONES")
    print("="*80)
    
    if missing_perms_by_service:
        print(f"\n   1. 🔴 PRIORIDAD ALTA: Agregar {len(missing_perms_by_service)} servicios a las políticas")
        print(f"      - Revisa la lista de servicios con permisos de lectura faltantes arriba")
        print(f"      - Agrega los permisos necesarios a iam-policy-ecad-part1.json o part2.json")
        print(f"      - Actualiza el template de CloudFormation")
    
    if write_operations_errors > 0:
        print(f"\n   2. ⚠️  Se detectaron {write_operations_errors} errores de operaciones de escritura")
        print(f"      - Estas operaciones NO deberían ejecutarse en un diagnóstico")
        print(f"      - El filtro de operaciones de escritura debería prevenir esto en futuras recolecciones")
        print(f"      - Considera ejecutar una nueva recolección después de actualizar el código")
    
    if covered_perms_by_service:
        print(f"\n   3. ⚠️  Verificar que el rol/usuario tenga las políticas adjuntas")
        print(f"      - Los permisos están en las políticas pero aún fallan")
        print(f"      - Puede haber un 'explicit deny' en otra política")
        print(f"      - Verifica las políticas adjuntas al usuario/rol en AWS Console")
    
    print("\n" + "="*80)

if __name__ == "__main__":
    main()

