"""
Data Indexer - Indexación de datos recolectados para búsqueda rápida.
"""

import json
import gzip
import logging
from pathlib import Path
from typing import Dict, List, Any
from collections import defaultdict

logger = logging.getLogger(__name__)


class DataIndexer:
    """Indexador de datos recolectados."""
    
    def __init__(self, raw_dir: Path, index_dir: Path):
        self.raw_dir = raw_dir
        self.index_dir = index_dir
    
    def index_all(self) -> Dict:
        """Indexar todos los datos recolectados."""
        index = {
            "services": {},
            "regions": set(),
            "operations": defaultdict(list),
            "total_files": 0,
            "total_operations": 0
        }
        
        if not self.raw_dir.exists():
            logger.warning(f"Directorio raw no existe: {self.raw_dir}")
            return index
        
        # Iterar sobre estructura: raw/{service}/{region}/{operation}.json.gz
        for service_dir in self.raw_dir.iterdir():
            if not service_dir.is_dir():
                continue
            
            service_name = service_dir.name
            service_data = {
                "name": service_name,
                "regions": {},
                "operations": set(),
                "total_operations": 0
            }
            
            for region_dir in service_dir.iterdir():
                if not region_dir.is_dir():
                    continue
                
                region_name = region_dir.name
                index["regions"].add(region_name)
                
                region_data = {
                    "operations": [],
                    "count": 0
                }
                
                # Procesar archivos de operaciones
                for op_file in region_dir.glob("*.json.gz"):
                    op_name = op_file.stem.replace(".json", "")
                    
                    try:
                        # Leer y parsear archivo
                        with gzip.open(op_file, 'rt', encoding='utf-8') as f:
                            data = json.load(f)
                        
                        # Extraer información
                        metadata = data.get("metadata", {})
                        success = metadata.get("success", False)
                        
                        # Verificar si el error es de tipo "no disponible" (no es un error real)
                        error = data.get("error", {})
                        error_code = error.get("code", "") if isinstance(error, dict) else ""
                        # También verificar si el metadata tiene el flag not_available
                        metadata_not_available = metadata.get("not_available", False)
                        # Códigos de error que indican "no disponible" (no son errores reales)
                        # También incluir RequestExpired como "no disponible" ya que indica credenciales expiradas
                        not_available_codes = ["OperationNotFound", "EndpointNotAvailable", "RequestExpired"]
                        is_not_available = (
                            metadata_not_available or 
                            error_code in not_available_codes
                        )
                        
                        operation_info = {
                            "operation": op_name,
                            "success": success,
                            "paginated": metadata.get("paginated", False),
                            "file": str(op_file.relative_to(self.raw_dir)),
                            "error": error,
                            "not_available": is_not_available  # Marcar si no está disponible
                        }
                        
                        # Solo contar recursos si la operación fue exitosa y hay datos
                        resource_count = 0
                        if success:
                            # Intentar contar recursos tanto de datos paginados como no paginados
                            data_content = data.get("data", {})
                            if not data_content:
                                # Si no hay "data", intentar con el nivel superior
                                data_content = data
                            
                            resource_count = self._count_resources(
                                data_content,
                                service_name=service_name,
                                operation_name=op_name
                            )
                            if resource_count > 0:
                                operation_info["resource_count"] = resource_count
                        # NO asumir 1 recurso si no hay datos - esto causa conteos incorrectos
                        
                        region_data["operations"].append(operation_info)
                        service_data["operations"].add(op_name)
                        index["operations"][f"{service_name}:{region_name}"].append(op_name)
                        index["total_operations"] += 1
                        index["total_files"] += 1
                        
                        # Contar operaciones exitosas/fallidas por región
                        # Ignorar operaciones "no disponibles" (OperationNotFound) como errores
                        if success:
                            if "successful" not in region_data:
                                region_data["successful"] = 0
                            region_data["successful"] += 1
                        elif not is_not_available:  # Solo contar como fallida si no es "no disponible"
                            if "failed" not in region_data:
                                region_data["failed"] = 0
                            region_data["failed"] += 1
                        # Si es "not_available", no se cuenta ni como exitosa ni como fallida
                        
                    except Exception as e:
                        logger.warning(f"Error indexando {op_file}: {e}")
                        continue
                
                region_data["count"] = len(region_data["operations"])
                service_data["regions"][region_name] = region_data
            
            service_data["total_operations"] = sum(
                r["count"] for r in service_data["regions"].values()
            )
            
            # Contar operaciones exitosas y fallidas totales
            service_data["successful_operations"] = sum(
                r.get("successful", 0) for r in service_data["regions"].values()
            )
            service_data["failed_operations"] = sum(
                r.get("failed", 0) for r in service_data["regions"].values()
            )
            
            # Convertir set de operaciones a lista para JSON
            service_data["operations"] = sorted(list(service_data["operations"]))
            
            index["services"][service_name] = service_data
        
        # Convertir sets a listas para JSON
        index["regions"] = sorted(list(index["regions"]))
        
        # Guardar índice
        index_file = self.index_dir / "index.json"
        with open(index_file, 'w') as f:
            json.dump(index, f, indent=2, default=str)
        
        logger.info(f"Índice guardado: {index_file}")
        logger.info(f"Servicios: {len(index['services'])}, Regiones: {len(index['regions'])}, Operaciones: {index['total_operations']}")
        
        return index
    
    def _is_aws_managed_iam_resource(self, item: Dict) -> bool:
        """Verificar si un recurso de IAM es gestionado por AWS."""
        if not isinstance(item, dict):
            return False
        
        # Verificar ARN - recursos de AWS tienen ARN con cuenta "aws"
        arn = item.get('Arn') or item.get('arn') or item.get('ARN', '')
        if isinstance(arn, str):
            # ARNs de AWS gestionados: arn:aws:iam::aws:policy/... o arn:aws:iam::aws:role/...
            if ':iam::aws:' in arn:
                return True
            # ARNs de servicio: arn:aws:iam::ACCOUNT:role/aws-service-role/...
            if '/aws-service-role/' in arn or '/service-role/' in arn:
                return True
        
        # Verificar Path - roles/políticas de servicio tienen paths específicos
        path = item.get('Path') or item.get('path', '')
        if isinstance(path, str):
            if path.startswith('/aws-service-role/') or path.startswith('/service-role/'):
                return True
        
        # Verificar nombre - algunos recursos de AWS tienen nombres específicos
        # Nota: Políticas gestionadas por AWS suelen tener nombres como "AWSLambdaBasicExecutionRole"
        # Pero esto es difícil de detectar sin una lista completa, mejor confiar en ARN y Path
        
        return False
    
    def _count_resources(self, data: Any, service_name: str = None, operation_name: str = None) -> int:
        """Contar recursos en datos de operación, excluyendo recursos gestionados por AWS para IAM."""
        if isinstance(data, dict):
            # Buscar campos comunes que contienen listas de recursos
            # Nota: Los nombres de campos varían por servicio
            common_list_keys = [
                'Items', 'items', 'Results', 'results', 'Resources', 'resources',
                'Instances', 'instances', 'Certificates', 'certificates',
                'CertificateSummaryList', 'certificateSummaryList',  # ACM
                'RestApis', 'restApis',  # API Gateway v1
                'Buckets', 'buckets', 'BucketsList', 'Users', 'users',
                'Roles', 'roles', 'Policies', 'policies', 'Groups', 'groups',
                'Vpcs', 'vpcs', 'Subnets', 'subnets', 'SecurityGroups', 'securityGroups',
                'RouteTables', 'routeTables',  # EC2 Route Tables
                'LaunchTemplates', 'launchTemplates',  # EC2 Launch Templates
                'NetworkAcls', 'networkAcls',  # EC2 Network ACLs
                'NetworkInsightsPaths', 'networkInsightsPaths',  # EC2 Network Insights Paths
                'TransitGatewayRouteTables', 'transitGatewayRouteTables',  # EC2 Transit Gateway Route Tables
                'Fleets', 'fleets',  # EC2 Fleets
                'InternetGateways', 'internetGateways',  # EC2 Internet Gateways
                'NatGateways', 'natGateways',  # EC2 NAT Gateways
                'TransitGateways', 'transitGateways',  # EC2 Transit Gateways
                'TransitGatewayAttachments', 'transitGatewayAttachments',  # EC2 Transit Gateway Attachments
                'CustomerGateways', 'customerGateways',  # EC2 Customer Gateways
                'DhcpOptions', 'dhcpOptions',  # EC2 DHCP Options
                'FlowLogs', 'flowLogs',  # EC2 Flow Logs
                'VpnConnections', 'vpnConnections',  # EC2 VPN Connections
                'LoadBalancers', 'loadBalancers', 'TargetGroups', 'targetGroups',
                'Listeners', 'listeners',  # ELBv2 Listeners
                'NetworkInterfaces', 'networkInterfaces',  # EC2 Network Interfaces
                'Volumes', 'volumes',  # EC2 Volumes
                'MetricAlarms', 'metricAlarms', 'CompositeAlarms', 'compositeAlarms',  # CloudWatch Alarms (pueden estar en MetricAlarms o CompositeAlarms)
                'Alarms', 'alarms',  # CloudWatch Alarms (formato alternativo)
                'DeploymentConfigs', 'deploymentConfigs',  # CodeDeploy
                'DBClusterSnapshots', 'dbClusterSnapshots',  # RDS DB Cluster Snapshots
                'DBSnapshots', 'dbSnapshots',  # RDS DB Snapshots
                'Addresses', 'addresses',  # EC2 Elastic IPs
                'Keys', 'keys',  # KMS Keys
                'Aliases', 'aliases',  # KMS Aliases
                'Rules', 'rules',  # Events Rules
                'QueueUrls', 'queueUrls', 'Queues', 'queues',  # SQS Queues
                'Addons', 'addons',  # EKS Addons
                'Functions', 'functions', 'Layers', 'layers', 'EventSourceMappings', 'eventSourceMappings',
                'DBInstances', 'dbInstances', 'DBClusters', 'dbClusters',
                'Clusters', 'clusters', 'Services', 'services', 'Tasks', 'tasks',
                'Repositories', 'repositories', 'Images', 'images',
                'DBClusterMembers', 'DBClusterMembersList',  # DocumentDB - solo clusters, no miembros individuales
                'StackSummaries', 'stackSummaries', 'Stacks', 'stacks',  # CloudFormation
                'BackupPlansList', 'BackupPlans', 'backupPlansList', 'backupPlans',  # Backup Plans
                'BackupVaultList', 'BackupVaults', 'backupVaultList', 'backupVaults',  # Backup Vaults
                'AutoScalingGroups', 'AutoScalingGroupNames', 'autoScalingGroups', 'autoScalingGroupNames'  # Auto Scaling Groups
            ]
            
            # PRIMERO: Si es paginado, contar todas las páginas (esto es lo más común)
            # IMPORTANTE: Deduplicar recursos usando IDs/ARNs únicos
            # Para IAM: excluir recursos gestionados por AWS
            # Para CloudFormation: excluir stacks en estado DELETE_COMPLETE
            is_iam = service_name == 'iam'
            is_cloudformation = service_name == 'cloudformation'
            is_ec2_describe_instances = (service_name == 'ec2' and 
                                        operation_name and 
                                        'describeinstances' in operation_name.lower())
            is_ec2_describe_network_interfaces = (service_name == 'ec2' and 
                                                  operation_name and 
                                                  'describenetworkinterfaces' in operation_name.lower())
            # Detectar DescribeFleets - normalizar nombre para comparación
            is_ec2_describe_fleets = False
            if service_name == 'ec2' and operation_name:
                normalized = operation_name.lower().replace('_', '').replace('-', '').replace(' ', '')
                is_ec2_describe_fleets = (
                    normalized == 'describefleets' or
                    'describefleets' in normalized or
                    (normalized.startswith('describe') and 'fleet' in normalized)
                )
            is_rds_dbcluster_snapshots = (service_name == 'rds' and 
                                         operation_name and 
                                         'describedbclustersnapshots' in operation_name.lower())
            is_rds_dbsnapshots = (service_name == 'rds' and 
                                 operation_name and 
                                 'describedbsnapshots' in operation_name.lower())
            is_rds_dbclusters = (service_name == 'rds' and 
                                operation_name and 
                                'describedbclusters' in operation_name.lower())
            is_docdb_dbclusters = (service_name == 'docdb' and 
                                  operation_name and 
                                  'describedbclusters' in operation_name.lower())
            is_docdb_dbinstances = (service_name == 'docdb' and 
                                    operation_name and 
                                    'describedbinstances' in operation_name.lower())
            is_neptune_dbclusters = (service_name == 'neptune' and 
                                    operation_name and 
                                    'describedbclusters' in operation_name.lower())
            is_neptune_dbinstances = (service_name == 'neptune' and 
                                     operation_name and 
                                     'describedbinstances' in operation_name.lower())
            is_cloudformation_list_stacks = (service_name == 'cloudformation' and 
                                            operation_name and 
                                            'liststacks' in operation_name.lower())
            is_codedeploy_deployment_configs = (service_name == 'codedeploy' and 
                                                operation_name and 
                                                'listdeploymentconfigs' in operation_name.lower())
            is_sqs_list_queues = (service_name == 'sqs' and 
                                 operation_name and 
                                 'listqueues' in operation_name.lower())
            
            if "pages" in data and "data" in data:
                seen_ids = set()
                pages_list = data["data"]
                if isinstance(pages_list, list):
                    for page in pages_list:
                        if isinstance(page, dict):
                            # CASO ESPECIAL: EC2 DescribeInstances - las instancias están en Reservations
                            if is_ec2_describe_instances and "Reservations" in page:
                                reservations = page.get("Reservations", [])
                                if isinstance(reservations, list):
                                    for reservation in reservations:
                                        if isinstance(reservation, dict) and "Instances" in reservation:
                                            instances = reservation.get("Instances", [])
                                            if isinstance(instances, list):
                                                for instance in instances:
                                                    if isinstance(instance, dict):
                                                        instance_id = instance.get("InstanceId")
                                                        if instance_id and instance_id not in seen_ids:
                                                            seen_ids.add(instance_id)
                                continue  # Ya procesamos esta página, continuar con la siguiente
                            
                            # CASO ESPECIAL: EC2 DescribeNetworkInterfaces - contar network interfaces directamente
                            if is_ec2_describe_network_interfaces and "NetworkInterfaces" in page:
                                network_interfaces = page.get("NetworkInterfaces", [])
                                if isinstance(network_interfaces, list):
                                    for ni in network_interfaces:
                                        if isinstance(ni, dict):
                                            ni_id = ni.get("NetworkInterfaceId")
                                            if ni_id and ni_id not in seen_ids:
                                                seen_ids.add(ni_id)
                                continue  # Ya procesamos esta página, continuar con la siguiente
                            
                            # CASO ESPECIAL: EC2 DescribeFleets - contar fleets directamente
                            if is_ec2_describe_fleets:
                                fleets_found = False
                                # Buscar en diferentes variaciones del campo
                                fleets = None
                                for fleet_key in ["Fleets", "fleets", "FleetList", "fleetList"]:
                                    if fleet_key in page:
                                        fleets = page.get(fleet_key, [])
                                        break
                                
                                # Si no encontramos en el nivel superior, buscar recursivamente
                                if not fleets:
                                    # Buscar recursivamente en el diccionario
                                    def find_fleets(data, depth=0):
                                        if depth > 3:  # Limitar profundidad
                                            return None
                                        if isinstance(data, dict):
                                            for key, value in data.items():
                                                if key.lower() in ['fleets', 'fleetlist'] and isinstance(value, list):
                                                    return value
                                                if isinstance(value, (dict, list)):
                                                    result = find_fleets(value, depth + 1)
                                                    if result:
                                                        return result
                                        elif isinstance(data, list):
                                            for item in data:
                                                result = find_fleets(item, depth + 1)
                                                if result:
                                                    return result
                                        return None
                                    
                                    fleets = find_fleets(page)
                                
                                if fleets and isinstance(fleets, list):
                                    fleets_found = True
                                    for fleet in fleets:
                                        if isinstance(fleet, dict):
                                            # Buscar FleetId en diferentes variaciones
                                            fleet_id = (fleet.get("FleetId") or 
                                                       fleet.get("fleetId") or 
                                                       fleet.get("FleetID") or
                                                       fleet.get("Id") or
                                                       fleet.get("id"))
                                            if fleet_id and fleet_id not in seen_ids:
                                                seen_ids.add(fleet_id)
                                
                                # Si encontramos fleets, continuar (ya procesamos)
                                # Si no encontramos, dejar que el procesamiento genérico lo intente
                                if fleets_found and fleets and isinstance(fleets, list) and len(fleets) > 0:
                                    continue  # Ya procesamos esta página, continuar con la siguiente
                            
                            # CASO ESPECIAL: RDS DescribeDBClusterSnapshots - contar snapshots directamente
                            if is_rds_dbcluster_snapshots and "DBClusterSnapshots" in page:
                                snapshots = page.get("DBClusterSnapshots", [])
                                if isinstance(snapshots, list):
                                    for snapshot in snapshots:
                                        if isinstance(snapshot, dict):
                                            snapshot_id = snapshot.get("DBClusterSnapshotIdentifier")
                                            if snapshot_id and snapshot_id not in seen_ids:
                                                seen_ids.add(snapshot_id)
                                continue  # Ya procesamos esta página, continuar con la siguiente
                            
                            # CASO ESPECIAL: RDS DescribeDBSnapshots - contar snapshots directamente
                            if is_rds_dbsnapshots and "DBSnapshots" in page:
                                snapshots = page.get("DBSnapshots", [])
                                if isinstance(snapshots, list):
                                    for snapshot in snapshots:
                                        if isinstance(snapshot, dict):
                                            snapshot_id = snapshot.get("DBSnapshotIdentifier")
                                            if snapshot_id and snapshot_id not in seen_ids:
                                                seen_ids.add(snapshot_id)
                                continue  # Ya procesamos esta página, continuar con la siguiente
                            
                            # CASO ESPECIAL: RDS DescribeDBClusters - contar clusters directamente (excluir snapshots)
                            if is_rds_dbclusters and "DBClusters" in page:
                                clusters = page.get("DBClusters", [])
                                if isinstance(clusters, list):
                                    for cluster in clusters:
                                        if isinstance(cluster, dict):
                                            cluster_id = cluster.get("DBClusterIdentifier")
                                            if cluster_id and cluster_id not in seen_ids:
                                                seen_ids.add(cluster_id)
                                continue  # Ya procesamos esta página, continuar con la siguiente
                            
                            # CASO ESPECIAL: DocumentDB DescribeDBClusters - contar solo clusters de DocumentDB, NO Aurora
                            if is_docdb_dbclusters and "DBClusters" in page:
                                clusters = page.get("DBClusters", [])
                                if isinstance(clusters, list):
                                    for cluster in clusters:
                                        if isinstance(cluster, dict):
                                            # Solo contar clusters de DocumentDB, excluir Aurora (aurora, aurora-mysql, aurora-postgresql)
                                            engine = cluster.get("Engine", "").lower()
                                            if engine and "docdb" in engine:
                                                cluster_id = cluster.get("DBClusterIdentifier")
                                                if cluster_id and cluster_id not in seen_ids:
                                                    seen_ids.add(cluster_id)
                                continue  # Ya procesamos esta página, continuar con la siguiente
                            
                            # CASO ESPECIAL: DocumentDB DescribeDBInstances - contar solo instancias de DocumentDB válidas (excluir Aurora y eliminadas)
                            if is_docdb_dbinstances and "DBInstances" in page:
                                instances = page.get("DBInstances", [])
                                if isinstance(instances, list):
                                    for instance in instances:
                                        if isinstance(instance, dict):
                                            # Solo contar instancias de DocumentDB, excluir Aurora
                                            engine = instance.get("Engine", "").lower()
                                            if engine and "docdb" in engine:
                                                # Solo contar instancias que no están en estado "deleted" o similares
                                                instance_status = instance.get("DBInstanceStatus", "").lower()
                                                if instance_status and not any(x in instance_status for x in ["deleted", "deleting", "failed"]):
                                                    instance_id = instance.get("DBInstanceIdentifier")
                                                    if instance_id and instance_id not in seen_ids:
                                                        seen_ids.add(instance_id)
                                continue  # Ya procesamos esta página, continuar con la siguiente
                            
                            # CASO ESPECIAL: Neptune DescribeDBClusters - contar solo clusters de Neptune, NO Aurora
                            if is_neptune_dbclusters and "DBClusters" in page:
                                clusters = page.get("DBClusters", [])
                                if isinstance(clusters, list):
                                    for cluster in clusters:
                                        if isinstance(cluster, dict):
                                            # Solo contar clusters de Neptune, excluir Aurora (aurora, aurora-mysql, aurora-postgresql)
                                            engine = cluster.get("Engine", "").lower()
                                            if engine and "neptune" in engine:
                                                cluster_id = cluster.get("DBClusterIdentifier")
                                                if cluster_id and cluster_id not in seen_ids:
                                                    seen_ids.add(cluster_id)
                                continue  # Ya procesamos esta página, continuar con la siguiente
                            
                            # CASO ESPECIAL: Neptune DescribeDBInstances - contar solo instancias de Neptune válidas (excluir Aurora y eliminadas)
                            if is_neptune_dbinstances and "DBInstances" in page:
                                instances = page.get("DBInstances", [])
                                if isinstance(instances, list):
                                    for instance in instances:
                                        if isinstance(instance, dict):
                                            # Solo contar instancias de Neptune, excluir Aurora
                                            engine = instance.get("Engine", "").lower()
                                            if engine and "neptune" in engine:
                                                # Solo contar instancias que no están en estado "deleted" o similares
                                                instance_status = instance.get("DBInstanceStatus", "").lower()
                                                if instance_status and not any(x in instance_status for x in ["deleted", "deleting", "failed"]):
                                                    instance_id = instance.get("DBInstanceIdentifier")
                                                    if instance_id and instance_id not in seen_ids:
                                                        seen_ids.add(instance_id)
                                continue  # Ya procesamos esta página, continuar con la siguiente
                            
                            # CASO ESPECIAL: CloudFormation ListStacks - contar stacks (excluir DELETE_COMPLETE)
                            if is_cloudformation_list_stacks and "StackSummaries" in page:
                                stacks = page.get("StackSummaries", [])
                                if isinstance(stacks, list):
                                    for stack in stacks:
                                        if isinstance(stack, dict):
                                            stack_status = stack.get("StackStatus", "")
                                            # Excluir stacks en estado DELETE_COMPLETE
                                            if stack_status != "DELETE_COMPLETE" and not stack_status.startswith("DELETE_"):
                                                stack_name = stack.get("StackName") or stack.get("StackId")
                                                if stack_name and stack_name not in seen_ids:
                                                    seen_ids.add(stack_name)
                                continue  # Ya procesamos esta página, continuar con la siguiente
                            
                            # CASO ESPECIAL: CodeDeploy ListDeploymentConfigs - los configs son strings
                            if is_codedeploy_deployment_configs and "deploymentConfigsList" in page:
                                configs = page.get("deploymentConfigsList", [])
                                if isinstance(configs, list):
                                    for config in configs:
                                        # Los configs pueden ser strings o dicts
                                        if isinstance(config, str):
                                            if config not in seen_ids:
                                                seen_ids.add(config)
                                        elif isinstance(config, dict):
                                            config_name = config.get("deploymentConfigName") or config.get("DeploymentConfigName")
                                            if config_name and config_name not in seen_ids:
                                                seen_ids.add(config_name)
                                continue  # Ya procesamos esta página, continuar con la siguiente
                            
                            # CASO ESPECIAL: SQS ListQueues - los queues están en QueueUrls (lista de strings)
                            if is_sqs_list_queues and "QueueUrls" in page:
                                queue_urls = page.get("QueueUrls", [])
                                if isinstance(queue_urls, list):
                                    for queue_url in queue_urls:
                                        if isinstance(queue_url, str) and queue_url not in seen_ids:
                                            seen_ids.add(queue_url)
                                continue  # Ya procesamos esta página, continuar con la siguiente
                            
                            # Buscar listas de recursos en cada página
                            # IMPORTANTE: Procesar todas las claves encontradas, no solo la primera
                            # EXCLUIR: DBClusterMembers para DocumentDB/Neptune - son miembros del cluster, no recursos separados
                            for key in common_list_keys:
                                # Excluir DBClusterMembers cuando se procesa DescribeDBClusters (DocumentDB/Neptune)
                                if key in ['DBClusterMembers', 'DBClusterMembersList', 'dbClusterMembers', 'dbClusterMembersList']:
                                    if is_docdb_dbclusters or is_neptune_dbclusters:
                                        continue  # No contar miembros del cluster como recursos separados
                                
                                if key in page and isinstance(page[key], list):
                                    items_list = page[key]
                                    for item in items_list:
                                        # Para IAM: excluir recursos gestionados por AWS
                                        if is_iam and isinstance(item, dict):
                                            if self._is_aws_managed_iam_resource(item):
                                                continue  # Saltar recursos de AWS
                                        
                                        # Para CloudFormation: excluir stacks en estado DELETE_COMPLETE
                                        if is_cloudformation and isinstance(item, dict):
                                            stack_status = item.get('StackStatus', '')
                                            if stack_status == 'DELETE_COMPLETE' or stack_status.startswith('DELETE_'):
                                                continue  # Saltar stacks eliminados
                                        
                                        # Intentar obtener ID único para deduplicar
                                        item_id = None
                                        
                                        # Si el item es un string (como DeploymentConfigs), usarlo directamente
                                        if isinstance(item, str):
                                            item_id = item
                                        elif isinstance(item, dict):
                                            # Buscar campos comunes de ID
                                            # IMPORTANTE: Buscar primero los IDs específicos antes de los genéricos
                                            for id_key in ['RouteTableId', 'SubnetId', 'LaunchTemplateId', 'LaunchTemplateName',  # EC2 específicos primero
                                                          'NetworkAclId', 'NetworkInsightsPathId', 'TransitGatewayRouteTableId', 'FleetId',
                                                          'InternetGatewayId', 'NatGatewayId', 'TransitGatewayId', 'TransitGatewayAttachmentId',
                                                          'CustomerGatewayId', 'DhcpOptionsId', 'FlowLogId', 'VpnConnectionId',
                                                          'InstanceId', 'NetworkInterfaceId', 'VolumeId',  # EC2 recursos
                                                          'GroupId', 'SecurityGroupId',  # EC2 Security Groups
                                                          'DBInstanceIdentifier', 'DBClusterIdentifier', 'DBClusterSnapshotIdentifier', 'DBSnapshotIdentifier',  # RDS
                                                          'DBSubnetGroupName', 'OptionGroupName',  # RDS DB Subnet Groups y Option Groups
                                                          'Id', 'id', 'Arn', 'arn', 'ARN', 'CertificateArn',  # Genéricos después 
                                                          'RestApiId', 'BucketName', 'UserId', 'RoleName', 
                                                          'InstanceId', 'NetworkInterfaceId', 'VolumeId',  # EC2 recursos
                                                          'GroupId', 'SecurityGroupId',  # EC2 Security Groups
                                                          'VpcId', 'FunctionName', 'TableName',
                                                          'ClusterName', 'ServiceName', 'TaskDefinitionArn',
                                                          'UserName', 'GroupName', 'PolicyName',
                                                          'StackName', 'StackId',  # CloudFormation
                                                          'TargetGroupArn', 'ListenerArn', 'LoadBalancerArn',  # ELBv2
                                                          'DBInstanceIdentifier', 'DBClusterIdentifier', 'DBClusterSnapshotIdentifier', 'DBSnapshotIdentifier',  # RDS
                                                          'AllocationId', 'PublicIp',  # EC2 Elastic IPs
                                                          'RouteTableId',  # EC2 Route Tables
                                                          'SubnetId',  # EC2 Subnets
                                                          'LaunchTemplateId', 'LaunchTemplateName',  # EC2 Launch Templates
                                                          'NetworkAclId',  # EC2 Network ACLs
                                                          'NetworkInsightsPathId',  # EC2 Network Insights Paths
                                                          'TransitGatewayRouteTableId',  # EC2 Transit Gateway Route Tables
                                                          'FleetId',  # EC2 Fleets
                                                          'VpcId',  # EC2 VPCs
                                                          'InternetGatewayId',  # EC2 Internet Gateways
                                                          'NatGatewayId',  # EC2 NAT Gateways
                                                          'TransitGatewayId',  # EC2 Transit Gateways
                                                          'TransitGatewayAttachmentId',  # EC2 Transit Gateway Attachments
                                                          'CustomerGatewayId',  # EC2 Customer Gateways
                                                          'DhcpOptionsId',  # EC2 DHCP Options
                                                          'FlowLogId',  # EC2 Flow Logs
                                                          'VpnConnectionId',  # EC2 VPN Connections
                                                          'DBSubnetGroupName',  # RDS DB Subnet Groups
                                                          'OptionGroupName',  # RDS Option Groups
                                                          'BackupPlanId', 'BackupPlanArn',  # Backup Plans
                                                          'BackupVaultName', 'BackupVaultArn',  # Backup Vaults
                                                          'Id', 'DeploymentStrategyId',  # AppConfig Deployment Strategies
                                                          'KeyspaceName',  # Cassandra Keyspaces
                                                          'ARN', 'SecretId', 'Name',  # Secrets Manager Secrets
                                                          'AutoScalingGroupName',  # Auto Scaling Groups
                                                          'Name',  # Config Configuration Recorders
                                                          'Name', 'CapacityProviderArn',  # ECS Capacity Providers
                                                          'TopicArn',  # SNS Topics
                                                          'CertificateArn',  # ACM Certificates
                                                          'Name', 'WorkGroup',  # Athena Work Groups
                                                          'TrailARN', 'Name',  # CloudTrail Trails
                                                          'Name', 'Arn',  # Events Event Buses
                                                          'DetectorId',  # GuardDuty Detectors
                                                          'Arn',  # IAM OIDC/SAML Providers
                                                          'Arn',  # Resource Explorer 2 Indexes
                                                          'Id', 'HostedZoneId',  # Route53 Hosted Zones
                                                          'Id', 'ResolverRuleId',  # Route53 Resolver Rules
                                                          'ResolverRuleId',  # Route53 Resolver Rule Associations
                                                          'KeyId', 'KeyArn',  # KMS
                                                          'AliasName', 'AliasArn',  # KMS Aliases
                                                          'RuleName', 'Name',  # Events Rules
                                                          'QueueUrl', 'QueueName',  # SQS
                                                          'AddonName',  # EKS Addons
                                                          'AlarmName',  # CloudWatch
                                                          'deploymentConfigName', 'DeploymentConfigName',  # CodeDeploy
                                                          'repositoryName', 'RepositoryName']:  # ECR
                                                if id_key in item:
                                                    item_id = str(item[id_key])
                                                    break
                                        
                                        # Si encontramos un ID, usarlo para deduplicar
                                        if item_id:
                                            if item_id not in seen_ids:
                                                seen_ids.add(item_id)
                                        else:
                                            # Si no hay ID, usar el item completo como string (menos eficiente pero funciona)
                                            item_str = str(item)
                                            if item_str not in seen_ids:
                                                seen_ids.add(item_str)
                
                if len(seen_ids) > 0:
                    return len(seen_ids)
            
            # SEGUNDO: Caso especial EC2 DescribeInstances sin paginación (datos directos)
            if is_ec2_describe_instances and "Reservations" in data:
                reservations = data.get("Reservations", [])
                if isinstance(reservations, list):
                    seen_ids = set()
                    for reservation in reservations:
                        if isinstance(reservation, dict) and "Instances" in reservation:
                            instances = reservation.get("Instances", [])
                            if isinstance(instances, list):
                                for instance in instances:
                                    if isinstance(instance, dict):
                                        instance_id = instance.get("InstanceId")
                                        if instance_id and instance_id not in seen_ids:
                                            seen_ids.add(instance_id)
                    if len(seen_ids) > 0:
                        return len(seen_ids)
            
            # SEGUNDO (b): Caso especial EC2 DescribeNetworkInterfaces sin paginación (datos directos)
            if is_ec2_describe_network_interfaces and "NetworkInterfaces" in data:
                network_interfaces = data.get("NetworkInterfaces", [])
                if isinstance(network_interfaces, list):
                    seen_ids = set()
                    for ni in network_interfaces:
                        if isinstance(ni, dict):
                            ni_id = ni.get("NetworkInterfaceId")
                            if ni_id and ni_id not in seen_ids:
                                seen_ids.add(ni_id)
                    if len(seen_ids) > 0:
                        return len(seen_ids)
            
            # SEGUNDO (c): Caso especial RDS/DocumentDB/Neptune DescribeDBClusters sin paginación (datos directos)
            if (is_rds_dbclusters or is_docdb_dbclusters or is_neptune_dbclusters) and "DBClusters" in data:
                clusters = data.get("DBClusters", [])
                if isinstance(clusters, list):
                    seen_ids = set()
                    for cluster in clusters:
                        if isinstance(cluster, dict):
                            # Para DocumentDB: solo contar clusters de DocumentDB, excluir Aurora
                            if is_docdb_dbclusters:
                                engine = cluster.get("Engine", "").lower()
                                if not engine or "docdb" not in engine:
                                    continue  # Saltar clusters que no son de DocumentDB
                            
                            # Para Neptune: solo contar clusters de Neptune, excluir Aurora
                            if is_neptune_dbclusters:
                                engine = cluster.get("Engine", "").lower()
                                if not engine or "neptune" not in engine:
                                    continue  # Saltar clusters que no son de Neptune
                            
                            cluster_id = cluster.get("DBClusterIdentifier")
                            if cluster_id and cluster_id not in seen_ids:
                                seen_ids.add(cluster_id)
                    if len(seen_ids) > 0:
                        return len(seen_ids)
            
            # SEGUNDO (c2): Caso especial DocumentDB DescribeDBInstances sin paginación (datos directos)
            if is_docdb_dbinstances and "DBInstances" in data:
                instances = data.get("DBInstances", [])
                if isinstance(instances, list):
                    seen_ids = set()
                    for instance in instances:
                        if isinstance(instance, dict):
                            # Solo contar instancias de DocumentDB, excluir Aurora
                            engine = instance.get("Engine", "").lower()
                            if engine and "docdb" in engine:
                                # Solo contar instancias que no están en estado "deleted" o similares
                                instance_status = instance.get("DBInstanceStatus", "").lower()
                                if instance_status and not any(x in instance_status for x in ["deleted", "deleting", "failed"]):
                                    instance_id = instance.get("DBInstanceIdentifier")
                                    if instance_id and instance_id not in seen_ids:
                                        seen_ids.add(instance_id)
                    if len(seen_ids) > 0:
                        return len(seen_ids)
            
            # SEGUNDO (c3): Caso especial Neptune DescribeDBInstances sin paginación (datos directos)
            if is_neptune_dbinstances and "DBInstances" in data:
                instances = data.get("DBInstances", [])
                if isinstance(instances, list):
                    seen_ids = set()
                    for instance in instances:
                        if isinstance(instance, dict):
                            # Solo contar instancias de Neptune, excluir Aurora
                            engine = instance.get("Engine", "").lower()
                            if engine and "neptune" in engine:
                                # Solo contar instancias que no están en estado "deleted" o similares
                                instance_status = instance.get("DBInstanceStatus", "").lower()
                                if instance_status and not any(x in instance_status for x in ["deleted", "deleting", "failed"]):
                                    instance_id = instance.get("DBInstanceIdentifier")
                                    if instance_id and instance_id not in seen_ids:
                                        seen_ids.add(instance_id)
                    if len(seen_ids) > 0:
                        return len(seen_ids)
            
            # SEGUNDO (d): Caso especial EC2 DescribeFleets sin paginación (datos directos)
            if is_ec2_describe_fleets:
                # Buscar en diferentes variaciones del campo
                fleets = None
                for fleet_key in ["Fleets", "fleets", "FleetList", "fleetList"]:
                    if fleet_key in data:
                        fleets = data.get(fleet_key, [])
                        break
                
                # Si no encontramos en el nivel superior, buscar recursivamente
                if not fleets:
                    # Buscar recursivamente en el diccionario
                    def find_fleets(data, depth=0):
                        if depth > 3:  # Limitar profundidad
                            return None
                        if isinstance(data, dict):
                            for key, value in data.items():
                                if key.lower() in ['fleets', 'fleetlist'] and isinstance(value, list):
                                    return value
                                if isinstance(value, (dict, list)):
                                    result = find_fleets(value, depth + 1)
                                    if result:
                                        return result
                        elif isinstance(data, list):
                            for item in data:
                                result = find_fleets(item, depth + 1)
                                if result:
                                    return result
                        return None
                    
                    fleets = find_fleets(data)
                
                if fleets and isinstance(fleets, list):
                    seen_ids = set()
                    for fleet in fleets:
                        if isinstance(fleet, dict):
                            # Buscar FleetId en diferentes variaciones
                            fleet_id = (fleet.get("FleetId") or 
                                       fleet.get("fleetId") or 
                                       fleet.get("FleetID") or
                                       fleet.get("Id") or
                                       fleet.get("id"))
                            if fleet_id and fleet_id not in seen_ids:
                                seen_ids.add(fleet_id)
                    if len(seen_ids) > 0:
                        return len(seen_ids)
            
            # TERCERO: Buscar listas directas en el nivel superior
            for key in common_list_keys:
                # Excluir DBClusterMembers cuando se procesa DescribeDBClusters (DocumentDB/Neptune)
                if key in ['DBClusterMembers', 'DBClusterMembersList', 'dbClusterMembers', 'dbClusterMembersList']:
                    if is_docdb_dbclusters or is_neptune_dbclusters:
                        continue  # No contar miembros del cluster como recursos separados
                
                if key in data and isinstance(data[key], list):
                    # Para IAM: excluir recursos gestionados por AWS
                    if is_iam:
                        filtered_list = [
                            item for item in data[key]
                            if not (isinstance(item, dict) and self._is_aws_managed_iam_resource(item))
                        ]
                        count = len(filtered_list)
                    # Para CloudFormation: excluir stacks en estado DELETE_COMPLETE
                    elif is_cloudformation:
                        filtered_list = [
                            item for item in data[key]
                            if not (isinstance(item, dict) and (
                                item.get('StackStatus', '') == 'DELETE_COMPLETE' or 
                                item.get('StackStatus', '').startswith('DELETE_')
                            ))
                        ]
                        count = len(filtered_list)
                    else:
                        count = len(data[key])
                    if count > 0:
                        return count
            
            # Si el dict tiene una estructura de respuesta directa (sin lista explícita)
            # pero tiene campos que sugieren un solo recurso, contar 1
            # Solo si tiene campos típicos de un recurso individual
            if any(key in data for key in ['CertificateArn', 'RestApiId', 'BucketName', 'UserId', 'RoleName', 'InstanceId', 'VpcId']):
                return 1
        
        elif isinstance(data, list):
            return len(data)
        
        # NO asumir 1 recurso si no se puede determinar - retornar 0
        # Esto evita conteos incorrectos cuando no hay datos reales
        return 0

