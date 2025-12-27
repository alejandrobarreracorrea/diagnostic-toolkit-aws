#!/usr/bin/env python3
"""
Generador de Política IAM Completa para ECAD
Basado en documentación oficial de AWS y mejores prácticas
"""

import json
import boto3
from typing import List, Set
from pathlib import Path

# Cambiar al directorio raíz del proyecto
project_root = Path(__file__).parent.parent

def get_all_aws_services() -> List[str]:
    """Obtener lista completa de servicios AWS disponibles."""
    # Lista completa de servicios AWS (actualizada Diciembre 2024)
    # Basada en boto3.get_available_services() y documentación oficial AWS
    # Incluye todos los servicios disponibles en AWS
    services = [
        'accessanalyzer', 'account', 'acm', 'acm-pca', 'aiops', 'amp', 'amplify', 
        'amplifybackend', 'apigateway', 'apigatewaymanagementapi', 'apigatewayv2', 
        'appconfig', 'appconfigdata', 'appfabric', 'appflow', 'appintegrations', 
        'application-autoscaling', 'application-insights', 'application-signals', 
        'applicationcostprofiler', 'appmesh', 'apprunner', 'appstream', 'appsync', 
        'arc-region-switch', 'arc-zonal-shift', 'artifact', 'athena', 'auditmanager', 
        'autoscaling', 'autoscaling-plans', 'b2bi', 'backup', 'backup-gateway', 
        'backupsearch', 'batch', 'bcm-dashboards', 'bcm-data-exports', 
        'bcm-pricing-calculator', 'bcm-recommended-actions', 'bedrock', 
        'bedrock-agent', 'bedrock-agent-runtime', 'bedrock-agentcore-control', 
        'bedrock-data-automation', 'bedrock-runtime', 'billing', 'billingconductor', 
        'braket', 'ce', 'chatbot', 'chime', 'chime-sdk-identity', 
        'chime-sdk-media-pipelines', 'chime-sdk-messaging', 'chime-sdk-voice', 
        'cleanrooms', 'cleanroomsml', 'cloud9', 'cloudcontrol', 'clouddirectory', 
        'cloudformation', 'cloudfront', 'cloudhsm', 'cloudhsmv2', 'cloudsearch', 
        'cloudtrail', 'cloudwatch', 'codeartifact', 'codebuild', 'codecatalyst', 
        'codecommit', 'codeconnections', 'codedeploy', 'codeguru-reviewer', 
        'codeguru-security', 'codeguruprofiler', 'codepipeline', 
        'codestar-connections', 'codestar-notifications', 'cognito-idp', 
        'cognito-sync', 'comprehend', 'comprehendmedical', 'compute-optimizer', 
        'config', 'connect', 'connect-contact-lens', 'connectcampaigns', 
        'connectcases', 'connectparticipant', 'controltower', 'customer-profiles', 
        'databrew', 'dataexchange', 'datapipeline', 'datasync', 'dax', 'detective', 
        'devicefarm', 'devops-guru', 'directconnect', 'directory-service', 'discovery', 
        'dlm', 'dms', 'docdb', 'docdb-elastic', 'drs', 'ds', 'dynamodb', 
        'dynamodbstreams', 'ebs', 'ec2', 'ec2-instance-connect', 'ecr', 'ecr-public', 
        'ecs', 'efs', 'eks', 'elastic-inference', 'elasticache', 'elasticbeanstalk', 
        'elastictranscoder', 'elbv2', 'emr', 'emr-containers', 'emr-serverless', 
        'es', 'events', 'evs', 'finspace', 'finspace-data', 'firehose', 'fis', 
        'fms', 'forecast', 'forecastquery', 'frauddetector', 'freertos', 'fsx', 
        'gamelift', 'gamesparks', 'geo-places', 'geo-routes', 'geo-search', 
        'glacier', 'globalaccelerator', 'glue', 'grafana', 'greengrass', 
        'greengrassv2', 'groundstation', 'guardduty', 'health', 'healthlake', 
        'honeycode', 'iam', 'identitystore', 'importexport', 'inspector', 
        'inspector2', 'internetmonitor', 'iot', 'iot-data', 'iot-jobs-data', 
        'iot1click-devices', 'iot1click-projects', 'iotanalytics', 'iotdeviceadvisor', 
        'iotevents', 'iotevents-data', 'iotfleethub', 'iotfleetwise', 'iotsecuretunneling', 
        'iotsitewise', 'iotthingsgraph', 'iottwinmaker', 'iotwireless', 'ivs', 
        'ivs-realtime', 'ivschat', 'kafka', 'kafkaconnect', 'kendra', 'kendra-ranking', 
        'keyspaces', 'keyspacesstreams', 'kinesis', 'kinesis-video-archived-media', 
        'kinesis-video-media', 'kinesis-video-signaling', 'kinesis-video-webrtc-storage', 
        'kinesisanalytics', 'kinesisanalyticsv2', 'kinesisvideo', 'kms', 'lakeformation', 
        'lambda', 'lex-models', 'lex-runtime', 'lexv2-models', 'lexv2-runtime', 
        'license-manager', 'license-manager-linux-subscriptions', 
        'license-manager-user-subscriptions', 'lightsail', 'location', 'logs', 
        'lookoutequipment', 'lookoutmetrics', 'lookoutvision', 'm2', 'machinelearning', 
        'macie', 'macie2', 'managedblockchain', 'managedblockchain-query', 'marketplace-catalog', 
        'marketplace-entitlement', 'marketplacecommerceanalytics', 'mediaconnect', 
        'mediaconvert', 'medialive', 'mediapackage', 'mediapackage-vod', 
        'mediapackagev2', 'mediastore', 'mediastore-data', 'mediatailor', 'memorydb', 
        'meteringmarketplace', 'mgh', 'mgn', 'migration-hub-refactor-spaces', 
        'migrationhub-config', 'migrationhuborchestrator', 'migrationhubstrategy', 
        'mobile', 'mq', 'mturk', 'mwaa', 'neptune', 'neptune-graph', 'neptunedata', 
        'network-firewall', 'networkflowmonitor', 'networkmanager', 'nimble', 
        'nova-act', 'oam', 'omics', 'opensearch', 'opensearchserverless', 
        'opsworks', 'opsworkscm', 'organizations', 'osis', 'outposts', 'panorama', 
        'payment-cryptography', 'payment-cryptography-data', 'pcs', 'personalize', 
        'personalize-events', 'personalize-runtime', 'pi', 'pinpoint', 
        'pinpoint-email', 'pinpoint-sms-voice', 'pinpoint-sms-voice-v2', 'pipes', 
        'polly', 'pricing', 'privatenetworks', 'proton', 'qbusiness', 'qldb', 
        'qldb-session', 'quicksight', 'ram', 'rbin', 'rds', 'rds-data', 'redshift', 
        'redshift-data', 'redshift-serverless', 'rekognition', 'resiliencehub', 
        'resource-explorer-2', 'resource-groups', 'resourcegroupstaggingapi', 
        'robomaker', 'rolesanywhere', 'route53', 'route53-recovery-cluster', 
        'route53-recovery-control-config', 'route53-recovery-readiness', 
        'route53domains', 'route53resolver', 'rum', 's3', 's3control', 's3outposts', 
        'sagemaker', 'sagemaker-a2i-runtime', 'sagemaker-edge', 'sagemaker-featurestore-runtime', 
        'sagemaker-geospatial', 'sagemaker-metrics', 'sagemaker-runtime', 'savingsplans', 
        'scheduler', 'schemas', 'sdb', 'secretsmanager', 'securityhub', 'serverlessrepo', 
        'service-quotas', 'servicecatalog', 'servicecatalog-appregistry', 'servicediscovery', 
        'ses', 'sesv2', 'shield', 'signer', 'simspaceweaver', 'sms', 'sms-voice', 
        'snow-device-management', 'snowball', 'sns', 'sqs', 'ssm', 'ssm-contacts', 
        'ssm-incidents', 'ssm-sap', 'sso', 'sso-admin', 'sso-oidc', 'stepfunctions', 
        'storagegateway', 'sts', 'support', 'support-app', 'swf', 'synthetics', 
        'textract', 'timestream-query', 'timestream-write', 'tnb', 'transcribe', 
        'transfer', 'translate', 'trustedadvisor', 'verifiedpermissions', 'voice-id', 
        'vpc-lattice', 'waf', 'waf-regional', 'wafv2', 'wellarchitected', 'wickr', 
        'workdocs', 'worklink', 'workmail', 'workmailmessageflow', 'workspaces', 
        'workspaces-thin-client', 'workspaces-web', 'xray', 'rtbfabric'
    ]
    return sorted(services)

def generate_readonly_actions_for_service(service_name: str) -> List[str]:
    """
    Generar acciones ReadOnly para un servicio específico.
    Basado en convenciones estándar de AWS:
    - List*: Listar recursos
    - Describe*: Describir recursos
    - Get*: Obtener recursos específicos
    """
    actions = []
    
    # Acciones estándar ReadOnly
    actions.extend([
        f"{service_name}:List*",
        f"{service_name}:Describe*",
        f"{service_name}:Get*"
    ])
    
    # Servicios con convenciones especiales
    special_cases = {
        's3': [
            's3:ListAllMyBuckets',
            's3:GetBucketLocation',
            's3:GetBucketVersioning',
            's3:ListBucket',
            's3:GetBucketAcl',
            's3:GetBucketPolicy',
            's3:GetBucketPublicAccessBlock',
            's3:GetEncryptionConfiguration',
            's3:GetLifecycleConfiguration',
            's3:GetReplicationConfiguration',
            's3:GetBucketTagging',
            's3:GetBucketWebsite',
            's3:GetObjectVersion',
            's3:GetObject',
            's3:GetObjectAcl',
            's3:GetObjectTagging',
        ],
        'apigateway': [
            'apigateway:GET',  # API Gateway usa verbos HTTP
        ],
        'apigatewayv2': [
            'apigatewayv2:Get*',
            'apigatewayv2:List*',
        ],
        'iam': [
            'iam:Get*',
            'iam:List*',
            'iam:Generate*',  # Para GenerateServiceLastAccessedDetails
        ],
        'sts': [
            'sts:GetCallerIdentity',
            'sts:GetSessionToken',
        ],
        'cloudtrail': [
            'cloudtrail:Describe*',
            'cloudtrail:Get*',
            'cloudtrail:List*',
            'cloudtrail:LookupEvents',
        ],
        'logs': [
            'logs:Describe*',
            'logs:Get*',
            'logs:List*',
            'logs:FilterLogEvents',
            'logs:TestMetricFilter',
        ],
        'support': [
            'support:Describe*',
        ],
        'ce': [  # Cost Explorer
            'ce:Describe*',
            'ce:Get*',
            'ce:List*',
        ],
        'organizations': [
            'organizations:Describe*',
            'organizations:List*',
        ],
        'securityhub': [
            'securityhub:Describe*',
            'securityhub:Get*',
            'securityhub:List*',
            'securityhub:BatchGet*',
        ],
        'guardduty': [
            'guardduty:Describe*',
            'guardduty:Get*',
            'guardduty:List*',
        ],
        'config': [
            'config:Describe*',
            'config:Get*',
            'config:List*',
            'config:SelectResourceConfig',
        ],
        'backup': [
            'backup:Describe*',
            'backup:Get*',
            'backup:List*',
        ],
        'shield': [
            'shield:Describe*',
            'shield:Get*',
            'shield:List*',
        ],
        'wafv2': [
            'wafv2:Get*',
            'wafv2:List*',
        ],
        'waf': [
            'waf:Get*',
            'waf:List*',
        ],
        'waf-regional': [
            'waf-regional:Get*',
            'waf-regional:List*',
        ],
    }
    
    if service_name in special_cases:
        return special_cases[service_name]
    
    return actions

def generate_complete_iam_policy() -> dict:
    """
    Generar política IAM completa con todos los servicios AWS.
    Basado en documentación oficial y mejores prácticas.
    """
    services = get_all_aws_services()
    
    print(f"Generando política para {len(services)} servicios AWS...")
    
    # Agrupar acciones por servicio para mejor organización
    all_actions = set()
    
    for service in services:
        actions = generate_readonly_actions_for_service(service)
        all_actions.update(actions)
    
    # Crear política estructurada
    policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "ECADReadOnlyAccessAllServices",
                "Effect": "Allow",
                "Action": sorted(list(all_actions)),
                "Resource": "*"
            },
            {
                "Sid": "ECADCostExplorerReadOnly",
                "Effect": "Allow",
                "Action": [
                    "ce:Describe*",
                    "ce:Get*",
                    "ce:List*"
                ],
                "Resource": "*"
            },
            {
                "Sid": "ECADSTSAccess",
                "Effect": "Allow",
                "Action": [
                    "sts:GetCallerIdentity",
                    "sts:GetSessionToken"
                ],
                "Resource": "*"
            }
        ]
    }
    
    return policy

def main():
    """Generar y guardar política IAM completa."""
    print("="*80)
    print("Generador de Política IAM Completa para ECAD")
    print("Basado en documentación oficial de AWS")
    print("="*80)
    print()
    
    policy = generate_complete_iam_policy()
    
    # Guardar política
    output_file = project_root / "policies" / "iam-policy-ecad-complete.json"
    output_file.parent.mkdir(exist_ok=True)
    
    with open(output_file, 'w') as f:
        json.dump(policy, f, indent=2)
    
    total_actions = sum(len(stmt.get("Action", [])) for stmt in policy["Statement"])
    print(f"✅ Política generada: {output_file}")
    print(f"   Total de acciones: {total_actions}")
    print(f"   Servicios cubiertos: {len(get_all_aws_services())}")
    print()
    print("📋 Notas:")
    print("   - Esta política otorga permisos ReadOnly (List*, Describe*, Get*)")
    print("   - No incluye permisos de escritura, eliminación o modificación")
    print("   - Sigue el principio de privilegio mínimo para operaciones de diagnóstico")
    print("   - Basada en documentación oficial de AWS IAM")
    print()
    print("🔒 Seguridad:")
    print("   - Resource: '*' (necesario para operaciones de listado)")
    print("   - Solo acciones ReadOnly permitidas")
    print("   - No permite modificar, crear o eliminar recursos")
    print()
    print("📖 Referencias:")
    print("   - AWS IAM Best Practices: https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html")
    print("   - AWS Managed Policies: https://docs.aws.amazon.com/IAM/latest/UserGuide/access_policies_managed-vs-inline.html")
    print("   - ReadOnlyAccess Policy: Similar a AWS managed policy ReadOnlyAccess")

if __name__ == "__main__":
    main()


