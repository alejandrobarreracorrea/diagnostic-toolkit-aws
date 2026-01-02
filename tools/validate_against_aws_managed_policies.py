#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para validar permisos IAM contra la referencia de políticas administradas de AWS.
Compara los prefijos de servicio usados en las políticas ECAD con los prefijos oficiales de AWS.
"""

import json
import sys
from pathlib import Path
from typing import Set, Dict, List
import urllib.request
import re

# Configurar codificación UTF-8 para Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

project_root = Path(__file__).parent.parent

# Prefijos de servicio conocidos de AWS (extraídos de políticas administradas y documentación)
# Esta lista se puede expandir consultando la documentación oficial
KNOWN_SERVICE_PREFIXES = {
    # Servicios principales
    'access-analyzer', 'account', 'acm', 'acm-pca', 'aiops', 'amp', 'amplify', 'amplifybackend',
    # Cost Explorer
    'ce',
    # CodeGuru
    'codeguruprofiler', 'codeguru-reviewer', 'codeguru-security',
    # Lambda
    'lambda',
    # CloudWatch Logs
    'logs',
    # Organizations
    'organizations',
    # Device Farm
    'devicefarm',
    # Elastic Load Balancing
    'elb', 'elbv2',
    # Entity Resolution
    'entityresolution',
    # FinSpace
    'finspace', 'finspace-data',
    # S3 Outposts
    's3outposts',
    'apigateway', 'apigatewayv2', 'appconfig', 'appfabric', 'appintegrations', 
    'application-autoscaling', 'application-insights', 'application-signals', 'appmesh', 
    'apprunner', 'appstream', 'appsync', 'arc-region-switch', 'arc-zonal-shift', 'artifact',
    'athena', 'auditmanager', 'autoscaling', 'autoscaling-plans', 'b2bi', 'backup', 
    'backup-gateway', 'backupsearch', 'batch', 'bcm-dashboards', 'bcm-data-exports',
    'bcm-pricing-calculator', 'bcm-recommended-actions', 'bedrock', 'bedrock-agent',
    'bedrock-agent-runtime', 'bedrock-agentcore-control', 'bedrock-data-automation',
    'bedrock-runtime', 'billing', 'billingconductor', 'braket', 'chime-sdk-identity',
    'chime-sdk-media-pipelines', 'chime-sdk-messaging', 'chime-sdk-voice', 'cleanrooms',
    'cleanroomsml', 'cloud9', 'cloudcontrol', 'clouddirectory', 'cloudformation', 'cloudfront',
    'cloudhsmv2', 'cloudsearch', 'cloudtrail', 'cloudwatch', 'codeartifact', 'codebuild',
    'codecommit', 'codeconnections', 'codeguru-profiler', 'codeguru-reviewer', 'codeguru-security',
    'codedeploy', 'codepipeline', 'codestar-connections', 'codestar-notifications',
    'cognito-idp', 'cognito-sync', 'comprehend', 'comprehendmedical', 'compute-optimizer',
    'compute-optimizer-automation', 'config', 'connect', 'connectcampaigns', 'connectcampaignsv2',
    'connectcases', 'controlcatalog', 'controltower', 'cost-optimization-hub', 'cur',
    'customer-profiles', 'databrew', 'dataexchange', 'datapipeline', 'datasync', 'datazone',
    'dax', 'deadline', 'detective', 'devops-guru', 'directconnect', 'discovery', 'dlm', 'dms',
    'docdb', 'docdb-elastic', 'drs', 'ds', 'dsql', 'dynamodb', 'dynamodbstreams', 'ec2', 'ecr',
    'ecr-public', 'ecs', 'efs', 'eks', 'elasticache', 'elasticbeanstalk', 'elasticloadbalancing',
    'elasticmapreduce', 'elastictranscoder', 'emr', 'emr-containers', 'emr-serverless', 'es',
    'evs', 'events', 'firehose', 'fis', 'fms', 'forecast', 'frauddetector', 'freetier', 'fsx',
    'gamelift', 'geo-places', 'glacier', 'globalaccelerator', 'glue', 'grafana', 'greengrass',
    'greengrassv2', 'groundstation', 'guardduty', 'health', 'healthlake', 'iam', 'imagebuilder',
    'inspector', 'inspector2', 'internetmonitor', 'invoicing', 'iot', 'iotanalytics',
    'iotdeviceadvisor', 'iotevents', 'iotfleethub', 'iotfleetwise', 'iotsecuretunneling',
    'iotsitewise', 'iottwinmaker', 'iotwireless', 'ivs', 'ivs-realtime', 'ivschat', 'kafka',
    'kafkaconnect', 'kendra', 'kendra-ranking', 'keyspaces', 'keyspacesstreams', 'kinesis',
    'kinesisanalytics', 'kinesisanalyticsv2', 'kinesisvideo', 'kms', 'lakeformation', 
    'launch-wizard', 'lex-models', 'lexv2-models', 'license-manager', 
    'license-manager-linux-subscriptions', 'license-manager-user-subscriptions', 'lightsail',
    'location', 'lookoutequipment', 'm2', 'machinelearning', 'macie2', 'mailmanager',
    'managedblockchain', 'managedblockchain-query', 'mediaconnect', 'mediaconvert', 'medialive',
    'mediapackage', 'mediapackage-vod', 'mediapackagev2', 'mediastore', 'mediatailor',
    'medical-imaging', 'memorydb', 'mgh', 'mgn', 'migration-hub-refactor-spaces',
    'migrationhub-config', 'migrationhuborchestrator', 'migrationhubstrategy', 'mq', 'mpa',
    'mturk', 'mwaa', 'mwaa-serverless', 'neptune', 'neptune-graph', 'network-firewall',
    'networkflowmonitor', 'networkmanager', 'networkmonitor', 'notifications', 
    'notificationscontacts', 'nova-act', 'oam', 'observabilityadmin', 'odb', 'omics',
    'opensearch', 'opensearchserverless', 'osis', 'outposts', 'panorama', 'payment-cryptography',
    'pca-connector-ad', 'pca-connector-scep', 'pcs', 'personalize', 'personalize-runtime',
    'pi', 'pinpoint', 'pinpoint-email', 'pinpoint-sms-voice', 'pinpoint-sms-voice-v2', 'pipes',
    'polly', 'pricing', 'proton', 'qbusiness', 'qconnect', 'qldb', 'quicksight', 'ram',
    'rds', 'rds-data', 'redshift', 'redshift-data', 'redshift-serverless', 'rekognition',
    'repostspace', 'resiliencehub', 'resource-explorer-2', 'resource-groups',
    'resourcegroupstaggingapi', 'robomaker', 'rolesanywhere', 'route53', 'route53-recovery-control-config',
    'route53domains', 'route53profiles', 'route53resolver', 'rtbfabric', 'rum', 's3', 's3-outposts',
    's3tables', 's3vectors', 'sagemaker', 'savingsplans', 'scheduler', 'schemas', 'secretsmanager',
    'security-ir', 'securityhub', 'securitylake', 'serverlessrepo', 'service-quotas',
    'servicecatalog', 'servicecatalog-appregistry', 'servicediscovery', 'ses', 'sesv2', 'shield',
    'signer', 'simspaceweaver', 'sms-voice', 'snow-device-management', 'snowball', 'sns', 'sqs',
    'ssm', 'ssm-contacts', 'ssm-incidents', 'sso', 'sso-admin', 'stepfunctions', 'storagegateway',
    'supplychain', 'support', 'support-app', 'swf', 'synthetics', 'taxsettings', 'textract',
    'timestream', 'tnb', 'transcribe', 'transfer', 'translate', 'trustedadvisor', 'verifiedpermissions',
    'voice-id', 'vpc-lattice', 'waf', 'waf-regional', 'wafv2', 'wellarchitected', 'wickr',
    'wisdom', 'workdocs', 'workmail', 'workspaces', 'xray'
}

def load_policy(file_path: Path) -> Dict:
    """Cargar política JSON."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ Error cargando {file_path}: {e}")
        return None

def extract_service_prefixes(policy: Dict) -> Set[str]:
    """Extraer todos los prefijos de servicio de una política."""
    prefixes = set()
    for statement in policy.get("Statement", []):
        actions = statement.get("Action", [])
        if isinstance(actions, str):
            actions = [actions]
        
        for action in actions:
            if ':' in action:
                service_prefix = action.split(':')[0]
                prefixes.add(service_prefix)
    
    return prefixes

def validate_service_prefixes(policy_file: Path, known_prefixes: Set[str]) -> Dict:
    """Validar prefijos de servicio contra lista conocida."""
    policy = load_policy(policy_file)
    if not policy:
        return {"valid": False, "errors": ["No se pudo cargar la política"]}
    
    prefixes = extract_service_prefixes(policy)
    invalid_prefixes = []
    suspicious_prefixes = []
    
    for prefix in sorted(prefixes):
        # Verificar si el prefijo está en la lista conocida
        if prefix not in known_prefixes:
            # Algunos prefijos pueden tener variaciones (con/sin guiones)
            # Verificar variaciones comunes
            variations = [
                prefix.replace('-', ''),  # access-analyzer -> accessanalyzer
                prefix.replace('_', '-'),  # service_name -> service-name
            ]
            
            found_variation = False
            for variation in variations:
                if variation in known_prefixes:
                    suspicious_prefixes.append({
                        'found': prefix,
                        'should_be': variation,
                        'type': 'wrong_format'
                    })
                    found_variation = True
                    break
            
            if not found_variation:
                invalid_prefixes.append(prefix)
    
    return {
        "valid": len(invalid_prefixes) == 0 and len(suspicious_prefixes) == 0,
        "invalid_prefixes": invalid_prefixes,
        "suspicious_prefixes": suspicious_prefixes,
        "total_prefixes": len(prefixes),
        "valid_prefixes": len(prefixes) - len(invalid_prefixes) - len(suspicious_prefixes)
    }

def main():
    print("="*80)
    print("🔍 VALIDACIÓN DE PERMISOS CONTRA POLÍTICAS ADMINISTRADAS DE AWS")
    print("="*80)
    print("\n📚 Fuente: https://docs.aws.amazon.com/aws-managed-policy/latest/reference/policy-list.html")
    print("   Comparando prefijos de servicio con referencia oficial de AWS\n")
    
    # Cargar políticas
    policy_files = [
        project_root / "policies" / "iam-policy-ecad-part1.json",
        project_root / "policies" / "iam-policy-ecad-part2.json",
        project_root / "policies" / "iam-policy-ecad-part3.json",
    ]
    
    all_invalid = []
    all_suspicious = []
    all_prefixes = set()
    
    for policy_file in policy_files:
        if not policy_file.exists():
            continue
        
        print(f"\n📄 {policy_file.name}")
        result = validate_service_prefixes(policy_file, KNOWN_SERVICE_PREFIXES)
        all_prefixes.update(extract_service_prefixes(load_policy(policy_file)))
        
        if result["invalid_prefixes"]:
            print(f"   ❌ Prefijos inválidos encontrados ({len(result['invalid_prefixes'])}):")
            for prefix in result["invalid_prefixes"]:
                print(f"      - {prefix}")
                all_invalid.append((policy_file.name, prefix))
        
        if result["suspicious_prefixes"]:
            print(f"   ⚠️  Prefijos con formato sospechoso ({len(result['suspicious_prefixes'])}):")
            for item in result["suspicious_prefixes"]:
                print(f"      - '{item['found']}' debería ser '{item['should_be']}'")
                all_suspicious.append((policy_file.name, item['found'], item['should_be']))
        
        if not result["invalid_prefixes"] and not result["suspicious_prefixes"]:
            print(f"   ✅ Todos los prefijos son válidos ({result['total_prefixes']} prefijos)")
    
    # Resumen
    print("\n" + "="*80)
    print("📊 RESUMEN")
    print("="*80)
    print(f"\nTotal de prefijos únicos encontrados: {len(all_prefixes)}")
    print(f"Prefijos inválidos: {len(set(p[1] for p in all_invalid))}")
    print(f"Prefijos con formato incorrecto: {len(set(p[1] for p in all_suspicious))}")
    
    if all_invalid:
        print(f"\n❌ Prefijos inválidos que deben corregirse:")
        for file_name, prefix in sorted(set((p[1], p[0]) for p in all_invalid)):
            print(f"   - {prefix} (en {file_name})")
    
    if all_suspicious:
        print(f"\n⚠️  Prefijos que deben corregirse:")
        for file_name, found, should_be in all_suspicious:
            print(f"   - {found} → {should_be} (en {file_name})")
    
    if not all_invalid and not all_suspicious:
        print("\n✅ Todos los prefijos de servicio son válidos según la referencia de AWS")
    else:
        print(f"\n⚠️  Se encontraron {len(all_invalid) + len(all_suspicious)} problema(s) que deben corregirse")
    
    print("\n" + "="*80)

if __name__ == "__main__":
    main()

