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
                        not_available_codes = ["OperationNotFound", "EndpointNotAvailable"]
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
                        if success and data.get("data"):
                            resource_count = self._count_resources(
                                data.get("data", {}),
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
                'LoadBalancers', 'loadBalancers', 'TargetGroups', 'targetGroups',
                'Functions', 'functions', 'Layers', 'layers', 'EventSourceMappings', 'eventSourceMappings',
                'DBInstances', 'dbInstances', 'DBClusters', 'dbClusters',
                'Clusters', 'clusters', 'Services', 'services', 'Tasks', 'tasks',
                'Repositories', 'repositories', 'Images', 'images',
                'DBClusterMembers', 'DBClusterMembersList',  # DocumentDB - solo clusters, no miembros individuales
                'StackSummaries', 'stackSummaries', 'Stacks', 'stacks'  # CloudFormation
            ]
            
            # PRIMERO: Si es paginado, contar todas las páginas (esto es lo más común)
            # IMPORTANTE: Deduplicar recursos usando IDs/ARNs únicos
            # Para IAM: excluir recursos gestionados por AWS
            # Para CloudFormation: excluir stacks en estado DELETE_COMPLETE
            is_iam = service_name == 'iam'
            is_cloudformation = service_name == 'cloudformation'
            
            if "pages" in data and "data" in data:
                seen_ids = set()
                pages_list = data["data"]
                if isinstance(pages_list, list):
                    for page in pages_list:
                        if isinstance(page, dict):
                            # Buscar listas de recursos en cada página
                            for key in common_list_keys:
                                if key in page and isinstance(page[key], list):
                                    for item in page[key]:
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
                                        if isinstance(item, dict):
                                            # Buscar campos comunes de ID
                                            for id_key in ['Id', 'id', 'Arn', 'arn', 'ARN', 'CertificateArn', 
                                                          'RestApiId', 'BucketName', 'UserId', 'RoleName', 
                                                          'InstanceId', 'VpcId', 'FunctionName', 'TableName',
                                                          'ClusterName', 'ServiceName', 'TaskDefinitionArn',
                                                          'UserName', 'GroupName', 'PolicyName',
                                                          'StackName', 'StackId']:  # CloudFormation
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
            
            # SEGUNDO: Buscar listas directas en el nivel superior
            for key in common_list_keys:
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

