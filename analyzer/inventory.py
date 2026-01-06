"""
Inventory Generator - Generación de inventarios y tablas ejecutivas.
"""

import json
import csv
import logging
from pathlib import Path
from typing import Dict, List, Any
from collections import defaultdict, Counter

logger = logging.getLogger(__name__)


class InventoryGenerator:
    """Generador de inventarios de recursos."""
    
    def __init__(self, index_dir: Path, output_dir: Path):
        self.index_dir = index_dir
        self.output_dir = output_dir
    
    def generate(self) -> Dict:
        """Generar inventarios completos."""
        # Cargar índice
        index_file = self.index_dir / "index.json"
        if not index_file.exists():
            logger.error(f"Índice no encontrado: {index_file}")
            return {}
        
        with open(index_file, 'r') as f:
            index = json.load(f)
        
        inventory = {
            "services": {},
            "regions": {},
            "total_resources": 0,
            "top_services": [],
            "top_regions": []
        }
        
        # Inventario por servicio
        service_counts = Counter()
        region_counts = Counter()
        
        # Servicios a excluir completamente del inventario
        excluded_services = {
            'support',  # AWS Support - servicio de soporte, no tiene recursos gestionables
            'pricing',  # Servicio de consulta de precios
            'ce',  # Cost Explorer
            'cur',  # Cost and Usage Report
            'health',  # AWS Health
            'budgets',  # AWS Budgets
            'servicequotas',  # Service Quotas
            'account',  # AWS Account
            'sts',  # Security Token Service
        }
        
        for service_name, service_data in index.get("services", {}).items():
            # Saltar servicios excluidos
            if service_name in excluded_services:
                continue
            service_inventory = {
                "name": service_name,
                "regions": list(service_data.get("regions", {}).keys()),
                "operations": list(service_data.get("operations", [])),
                "total_operations": service_data.get("total_operations", 0),
                "resource_count": 0
            }
            
            # Contar recursos por región
            # Solo contar recursos de operaciones "List" o "Describe" principales
            # Ignorar operaciones auxiliares como GetSdkTypes, GetAccountConfiguration, etc.
            primary_operations = {
                'acm': ['ListCertificates'],
                'apigateway': ['GetRestApis', 'GetApis'],  # APIs principales
                'apigatewayv2': ['GetApis'],
                's3': ['ListBuckets'],
                'ec2': ['DescribeInstances', 'DescribeNetworkInterfaces', 'DescribeVolumes', 'DescribeSecurityGroups', 'DescribeAddresses',
                        'DescribeRouteTables', 'DescribeSubnets', 'DescribeLaunchTemplates', 'DescribeNetworkAcls',
                        'DescribeNetworkInsightsPaths', 'DescribeTransitGatewayRouteTables', 'DescribeFleets',
                        'DescribeVpcs', 'DescribeInternetGateways', 'DescribeNatGateways', 'DescribeTransitGateways',
                        'DescribeTransitGatewayAttachments', 'DescribeCustomerGateways', 'DescribeDhcpOptions',
                        'DescribeFlowLogs', 'DescribeVpnConnections'],  # Varios recursos EC2
                'iam': ['ListUsers', 'ListRoles', 'ListGroups'],
                'autoscaling': ['DescribeAutoScalingGroups'],
                'rds': ['DescribeDBInstances', 'DescribeDBClusters', 'DescribeDBClusterSnapshots', 'DescribeDBSnapshots'],
                'kms': ['ListKeys', 'ListAliases'],
                'events': ['ListRules'],
                'eks': ['ListClusters', 'ListAddons'],
                'docdb': ['DescribeDBClusters'],  # Solo clusters (las instancias son parte de los clusters)
                'neptune': ['DescribeDBClusters'],  # Solo clusters (las instancias son parte de los clusters, no contar snapshots)
                'memorydb': ['DescribeClusters'],  # Solo clusters, no parámetros ni otros recursos
                'timestream': ['ListDatabases'],  # Solo databases, no tablas individuales
                'qldb': ['ListLedgers'],  # Solo ledgers
                'opensearch': ['ListDomainNames'],  # Solo dominios
                'redshift': ['DescribeClusters'],  # Solo clusters, no snapshots ni parámetros
                'elasticache': ['DescribeCacheClusters', 'DescribeReplicationGroups'],  # Clusters y replication groups
                'lambda': ['ListFunctions'],
                'cloudformation': ['ListStacks'],
                'ecs': ['ListClusters', 'ListServices'],
                'dynamodb': ['ListTables'],
                'sns': ['ListTopics'],
                'sqs': ['ListQueues'],
                'kinesis': ['ListStreams'],
                'elbv2': ['DescribeLoadBalancers', 'DescribeTargetGroups', 'DescribeListeners'],
                'route53': ['ListHostedZones'],
                'cloudfront': ['ListDistributions'],
                'wafv2': ['ListWebACLs'],
                'shield': ['ListProtections'],
                'guardduty': ['ListDetectors'],
                'securityhub': ['GetFindings'],
                'config': ['ListDiscoveredResources', 'GetDiscoveredResourceCounts', 'SelectResourceConfig'],
                'cloudtrail': ['ListTrails'],
                'backup': ['ListBackupVaults', 'ListBackupPlans'],
                # Servicios de seguridad y compliance
                'inspector': ['ListFindings'],  # Solo findings, no assessments individuales
                'inspector2': ['ListFindings'],  # Solo findings
                'macie': ['ListS3Buckets'],  # Solo buckets de Macie
                'macie2': ['ListBuckets'],  # Solo buckets
                'securityhub': ['GetFindings'],  # Ya está, pero asegurémonos que solo cuenta findings
                # Servicios de networking adicionales
                'directconnect': ['DescribeConnections'],  # Solo connections principales
                'networkmanager': ['ListNetworks'],  # Solo networks
                'globalaccelerator': ['ListAccelerators'],  # Solo accelerators
                # Servicios de contenedores adicionales
                'apprunner': ['ListServices'],  # Solo services
                'lightsail': ['GetInstances', 'GetDatabases'],  # Instances y databases
                # Servicios de desarrollo adicionales
                'cloud9': ['ListEnvironments'],  # Solo environments
                'xray': ['GetGroups'],  # Solo groups
                # Servicios de media
                'mediastore': ['ListContainers'],  # Solo containers
                'mediastore-data': [],  # Servicio de datos, no recursos gestionables
                'mediaconvert': ['ListJobs'],  # Solo jobs activos
                'mediapackage': ['ListChannels'],  # Solo channels
                'mediapackage-vod': ['ListPackagingGroups'],  # Solo packaging groups
                'mediatailor': ['ListPlaybackConfigurations'],  # Solo configurations
                'glacier': ['ListVaults'],
                'efs': ['DescribeFileSystems'],
                'fsx': ['DescribeFileSystems'],
                'workspaces': ['DescribeWorkspaces'],
                'directory-service': ['DescribeDirectories'],
                'secretsmanager': ['ListSecrets'],
                'ssm': ['DescribeInstances'],
                'codecommit': ['ListRepositories'],
                'codebuild': ['ListProjects'],
                'codepipeline': ['ListPipelines'],
                'codedeploy': ['ListApplications'],
                'amplify': ['ListApps'],
                'amplifybackend': ['ListBackends'],  # Solo backends, no otros recursos auxiliares
                'appsync': ['ListGraphqlApis'],
                'cognito-idp': ['ListUserPools'],
                'systems-manager': ['DescribeInstances'],
                'organizations': ['ListAccounts'],
                'servicecatalog': ['ListPortfolios'],
                'cloudwatch': ['ListDashboards'],
                'logs': ['DescribeLogGroups'],
                'events': ['ListRules'],
                'stepfunctions': ['ListStateMachines'],
                'batch': ['DescribeJobQueues'],
                'glue': ['GetDatabases', 'ListJobs'],
                'athena': ['ListDatabases', 'ListWorkGroups'],
                'quicksight': ['ListDashboards'],
                'sagemaker': ['ListNotebookInstances'],
                # Servicios de base de datos adicionales
                'rds-data': [],  # Servicio de datos, no tiene recursos gestionables directamente
                'aurora': ['DescribeDBClusters', 'DescribeDBInstances'],  # Similar a RDS
                # Servicios de almacenamiento adicionales
                'storagegateway': ['ListGateways'],  # Solo gateways principales
                'datasync': ['ListAgents', 'ListLocations'],  # Agents y locations
                # Servicios de análisis adicionales
                'kinesisanalytics': ['ListApplications'],  # Solo aplicaciones
                'kinesis-video': ['ListStreams'],  # Solo streams
                'kinesis-video-archived-media': [],  # Servicio de media, no recursos gestionables
                'kinesis-video-media': [],  # Servicio de media, no recursos gestionables
                'kinesis-video-signaling': [],  # Servicio de señalización, no recursos gestionables
                'comprehend': ['ListEntitiesDetectionJobs'],
                'rekognition': ['ListCollections'],
                'transcribe': ['ListTranscriptionJobs'],
                'polly': ['ListLexicons'],
                'translate': ['ListTextTranslationJobs'],
                'lex': ['GetBots'],
                'connect': ['ListInstances'],
                'chime': ['ListAccounts'],
                'workmail': ['ListOrganizations'],
                'ses': ['ListIdentities'],
                'pinpoint': ['GetApps'],
                'mobile': ['ListProjects'],
                'devicefarm': ['ListProjects'],
                'iot': ['ListThings'],
                'iot-core': ['ListThings'],
                'greengrass': ['ListGroups'],
                'iotanalytics': ['ListDatastores'],
                'iotevents': ['ListDetectorModels'],
                'iot-sitewise': ['ListPortals'],
                'iot-twinmaker': ['ListWorkspaces'],
                'iotwireless': ['ListServiceProfiles'],
                'freertos': ['ListFreeRTOSVersions'],
                'iot1click': ['ListPlacements'],
                'iot1click-devices': ['ListDevices'],
                'iot1click-projects': ['ListProjects'],
                'iot-device-tester': ['ListSuiteDefinitions'],
                'iot-events': ['ListDetectorModels'],
                'iot-jobs-data': ['ListJobs'],
                'iot-secure-tunneling': ['ListTunnels'],
                'iot-things-graph': ['SearchThings'],
                'iotanalytics': ['ListDatastores'],
                'iotevents': ['ListDetectorModels'],
                'iot-sitewise': ['ListPortals'],
                'iot-twinmaker': ['ListWorkspaces'],
                'iotwireless': ['ListServiceProfiles'],
                'freertos': ['ListFreeRTOSVersions'],
                'iot1click': ['ListPlacements'],
                'iot1click-devices': ['ListDevices'],
                'iot1click-projects': ['ListProjects'],
                'iot-device-tester': ['ListSuiteDefinitions'],
                'iot-events': ['ListDetectorModels'],
                'iot-jobs-data': ['ListJobs'],
                'iot-secure-tunneling': ['ListTunnels'],
                'iot-things-graph': ['SearchThings'],
                # Servicios de consulta/información que NO tienen recursos gestionables
                'pricing': [],  # Servicio de consulta de precios, no tiene recursos
                'ce': [],  # Cost Explorer - servicio de consulta, no tiene recursos
                'cur': [],  # Cost and Usage Report - servicio de reportes, no tiene recursos
                'support': [],  # AWS Support - servicio de soporte, no tiene recursos gestionables
                'health': [],  # AWS Health - servicio de información de salud, no tiene recursos
                'budgets': [],  # AWS Budgets - servicio de presupuestos, no tiene recursos gestionables directamente
                'servicequotas': [],  # Service Quotas - servicio de consulta de cuotas, no tiene recursos
                'account': [],  # AWS Account - servicio de información de cuenta, no tiene recursos
                'sts': [],  # Security Token Service - servicio de tokens, no tiene recursos gestionables
                'iam': ['ListUsers', 'ListRoles', 'ListGroups'],  # Ya está, pero asegurémonos
                # Servicios de datos adicionales
                'dataexchange': ['ListDataSets'],  # Solo datasets
                'datapipeline': ['ListPipelines'],  # Solo pipelines
                'databrew': ['ListDatasets'],  # Solo datasets
                'forecast': ['ListDatasets'],  # Solo datasets
                'frauddetector': ['GetDetectors'],  # Solo detectors
                # Servicios de machine learning adicionales
                'personalize': ['ListDatasets'],  # Solo datasets
                'lookoutvision': ['ListProjects'],  # Solo projects
                'lookoutmetrics': ['ListAnomalyDetectors'],  # Solo detectors
                'lookoutequipment': ['ListDatasets'],  # Solo datasets
                # Servicios de blockchain
                'managedblockchain': ['ListNetworks'],  # Solo networks
                # Servicios de quantum
                'braket': ['ListDevices'],  # Solo devices
            }
            
            for region_name, region_data in service_data.get("regions", {}).items():
                region_count = 0
                # Si hay operaciones principales definidas para este servicio, solo contar esas
                if service_name in primary_operations:
                    allowed_ops = primary_operations[service_name]
                    for op in region_data.get("operations", []):
                        if op.get("success", False):
                            op_name = op.get("operation", "")
                            # Convertir snake_case a PascalCase para comparar
                            # Ejemplo: list_users -> ListUsers
                            op_pascal = ''.join(word.capitalize() for word in op_name.split('_'))
                            # Comparar tanto el nombre original como el convertido
                            if op_name in allowed_ops or op_pascal in allowed_ops:
                                region_count += op.get("resource_count", 0) or 0
                else:
                    # Si no hay operaciones principales definidas, usar heurística:
                    # Solo contar operaciones que empiezan con "List" o "Describe" o "Get" (para algunos servicios)
                    for op in region_data.get("operations", []):
                        if op.get("success", False):
                            op_name = op.get("operation", "").lower()
                            # Contar solo operaciones principales, no auxiliares
                            if (op_name.startswith("list") or 
                                op_name.startswith("describe") or
                                (op_name.startswith("get") and any(x in op_name for x in ["apis", "tables", "instances", "clusters", "functions", "buckets", "users", "roles"]))):
                                region_count += op.get("resource_count", 0) or 0
                
                service_inventory["resource_count"] += region_count
                region_counts[region_name] += region_count
            
            service_counts[service_name] = service_inventory["resource_count"]
            inventory["services"][service_name] = service_inventory
            inventory["total_resources"] += service_inventory["resource_count"]
        
        # Top servicios y regiones
        inventory["top_services"] = [
            {"service": name, "count": count}
            for name, count in service_counts.most_common(20)
        ]
        inventory["top_regions"] = [
            {"region": name, "count": count}
            for name, count in region_counts.most_common(10)
        ]
        
        # Inventario por región
        for region_name in index.get("regions", []):
            region_inventory = {
                "name": region_name,
                "services": [],
                "total_resources": 0
            }
            
            for service_name, service_data in index.get("services", {}).items():
                if region_name in service_data.get("regions", {}):
                    region_data = service_data["regions"][region_name]
                    region_count = sum(
                        op.get("resource_count", 0) or 0
                        for op in region_data.get("operations", [])
                        if op.get("success", False)
                    )
                    if region_count > 0:
                        region_inventory["services"].append({
                            "service": service_name,
                            "count": region_count
                        })
                        region_inventory["total_resources"] += region_count
            
            inventory["regions"][region_name] = region_inventory
        
        # Guardar inventarios
        self._save_inventory_json(inventory)
        self._save_inventory_csv(inventory)
        
        return inventory
    
    def _save_inventory_json(self, inventory: Dict):
        """Guardar inventario en JSON."""
        inventory_file = self.output_dir / "inventory.json"
        with open(inventory_file, 'w') as f:
            json.dump(inventory, f, indent=2, default=str)
        logger.info(f"Inventario JSON guardado: {inventory_file}")
    
    def _save_inventory_csv(self, inventory: Dict):
        """Guardar inventarios en CSV para análisis ejecutivo."""
        # CSV: Top servicios
        top_services_file = self.output_dir / "top_services.csv"
        with open(top_services_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["Service", "Resource Count"])
            for item in inventory.get("top_services", []):
                writer.writerow([item["service"], item["count"]])
        logger.info(f"Top servicios CSV guardado: {top_services_file}")
        
        # CSV: Top regiones
        top_regions_file = self.output_dir / "top_regions.csv"
        with open(top_regions_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["Region", "Resource Count"])
            for item in inventory.get("top_regions", []):
                writer.writerow([item["region"], item["count"]])
        logger.info(f"Top regiones CSV guardado: {top_regions_file}")
        
        # CSV: Inventario por servicio y región
        service_region_file = self.output_dir / "service_region_matrix.csv"
        with open(service_region_file, 'w', newline='') as f:
            writer = csv.writer(f)
            
            # Headers
            regions = sorted(inventory.get("regions", {}).keys())
            writer.writerow(["Service"] + regions)
            
            # Data
            for service_name, service_data in inventory.get("services", {}).items():
                row = [service_name]
                for region in regions:
                    count = 0
                    if region in service_data.get("regions", []):
                        # Buscar count en region_data
                        for region_inv in inventory.get("regions", {}).get(region, {}).get("services", []):
                            if region_inv["service"] == service_name:
                                count = region_inv["count"]
                                break
                    row.append(count)
                writer.writerow(row)
        logger.info(f"Matriz servicio-región CSV guardada: {service_region_file}")

