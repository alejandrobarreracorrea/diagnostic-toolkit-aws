"""
Service Discovery - Descubrimiento de servicios y operaciones AWS.

Usa el modelo de botocore para descubrir automáticamente todas las
operaciones disponibles y determinar qué parámetros son requeridos.
"""

import logging
from typing import Dict, List, Optional, Set
import boto3
from botocore.client import BaseClient
from botocore.exceptions import ClientError, EndpointConnectionError
from botocore.model import OperationModel, ServiceModel

logger = logging.getLogger(__name__)


class ServiceDiscovery:
    """Descubrimiento de servicios y operaciones AWS."""
    
    def __init__(self, session: boto3.Session):
        self.session = session
        self._service_cache: Dict[str, ServiceModel] = {}
    
    def discover_services(self) -> List[str]:
        """Descubrir todos los servicios AWS disponibles."""
        try:
            services = self.session.get_available_services()
            logger.info(f"Servicios disponibles: {len(services)}")
            return sorted(services)
        except Exception as e:
            logger.error(f"Error descubriendo servicios: {e}")
            return []
    
    def discover_operations(
        self,
        service_name: str,
        region: str
    ) -> Dict[str, Dict]:
        """Descubrir operaciones de un servicio en una región."""
        operations = {}
        total_operations = 0
        filtered_operations = 0
        
        try:
            # Obtener modelo del servicio
            service_model = self._get_service_model(service_name)
            if not service_model:
                return operations
            
            # Crear cliente para verificar disponibilidad en región
            try:
                client = self.session.client(service_name, region_name=region)
            except Exception as e:
                logger.debug(f"Servicio {service_name} no disponible en {region}: {e}")
                return operations
            
            # Iterar sobre todas las operaciones
            # FILTRAR: Solo incluir operaciones de lectura (List, Describe, Get, etc.)
            # Excluir operaciones de escritura (Create, Delete, Update, Put, etc.)
            for operation_name in service_model.operation_names:
                total_operations += 1
                
                # Filtrar solo operaciones de lectura
                if not self._is_read_operation(operation_name):
                    filtered_operations += 1
                    logger.debug(f"Excluyendo operación de escritura: {service_name}.{operation_name}")
                    continue
                
                try:
                    operation_model = service_model.operation_model(operation_name)
                    op_info = self._analyze_operation(operation_model)
                    if op_info:
                        operations[operation_name] = op_info
                except Exception as e:
                    logger.debug(f"Error analizando {operation_name}: {e}")
                    continue
            
            # Log informativo sobre el filtrado
            if filtered_operations > 0:
                logger.info(
                    f"{service_name}/{region}: {len(operations)} operaciones de lectura "
                    f"(se filtraron {filtered_operations} operaciones de escritura de {total_operations} totales)"
                )
        
        except Exception as e:
            logger.warning(f"Error descubriendo operaciones de {service_name}: {e}")
        
        return operations
    
    def _get_service_model(self, service_name: str) -> Optional[ServiceModel]:
        """Obtener modelo del servicio desde cache o botocore."""
        if service_name in self._service_cache:
            return self._service_cache[service_name]
        
        try:
            loader = self.session._loader
            service_model = loader.load_service_model(service_name, 'service-2')
            model = ServiceModel(service_model, service_name=service_name)
            self._service_cache[service_name] = model
            return model
        except Exception as e:
            logger.debug(f"No se pudo cargar modelo para {service_name}: {e}")
            return None
    
    def _analyze_operation(self, operation_model: OperationModel) -> Optional[Dict]:
        """Analizar una operación para determinar parámetros requeridos."""
        try:
            input_shape = operation_model.input_shape
            
            required_params = []
            optional_params = []
            
            if input_shape:
                members = input_shape.members if hasattr(input_shape, 'members') else {}
                # Obtener required_members de forma más robusta
                if hasattr(input_shape, 'required_members'):
                    required_members = input_shape.required_members
                elif hasattr(input_shape, '_required_members'):
                    required_members = input_shape._required_members
                else:
                    required_members = []
                
                for param_name, param_shape in members.items():
                    if param_name in required_members:
                        required_params.append({
                            "name": param_name,
                            "type": str(param_shape.type_name) if hasattr(param_shape, 'type_name') else "unknown"
                        })
                    else:
                        optional_params.append({
                            "name": param_name,
                            "type": str(param_shape.type_name) if hasattr(param_shape, 'type_name') else "unknown"
                        })
            
            # Determinar si es "safe-to-call" (sin parámetros requeridos)
            # Si no hay input_shape, es safe_to_call
            safe_to_call = len(required_params) == 0
            
            # Clasificar tipo de operación
            op_type = self._classify_operation(operation_model.name)
            
            return {
                "name": operation_model.name,
                "safe_to_call": safe_to_call,
                "required_params": required_params,
                "optional_params": optional_params,
                "operation_type": op_type,
                "paginated": self._is_paginated(operation_model)
            }
        
        except Exception as e:
            logger.debug(f"Error analizando operación {operation_model.name}: {e}")
            return None
    
    def _classify_operation(self, operation_name: str) -> str:
        """Clasificar tipo de operación basado en el nombre."""
        name_lower = operation_name.lower()
        
        if name_lower.startswith('list') or name_lower.startswith('describe'):
            return "list"
        elif name_lower.startswith('get'):
            return "get"
        elif name_lower.startswith('describe'):
            return "describe"
        else:
            return "other"
    
    def _is_read_operation(self, operation_name: str) -> bool:
        """Determinar si una operación es de solo lectura (safe para ejecutar)."""
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
            'register',  # RegisterInstance, RegisterTarget, etc.
            'deregister', # DeregisterInstance, DeregisterTarget, etc.
            'activate',  # ActivateLicense, etc.
            'deactivate', # DeactivateLicense, etc.
            'cancel',    # CancelJob, CancelExportTask, etc.
            'abort',     # AbortMultipartUpload, etc.
            'complete',  # CompleteMultipartUpload, etc.
            'initiate',  # InitiateMultipartUpload, etc.
            'upload',    # UploadPart, etc.
            'download',  # DownloadDBLogFile, etc.
            'restart',   # RestartAppServer, etc.
            'resume',    # ResumeProcesses, etc.
            'suspend',   # SuspendProcesses, etc.
            'scale',     # ScaleOut, ScaleIn, etc.
            'tag',       # TagResource, etc.
            'untag',     # UntagResource, etc.
        ]
        
        # Si empieza con algún prefijo de escritura, excluir
        for prefix in write_prefixes:
            if name_lower.startswith(prefix):
                return False
        
        # Si no es claramente de lectura ni de escritura, ser conservador y excluir
        # Solo permitir si es explícitamente una operación de lectura conocida
        return False
    
    def _is_paginated(self, operation_model: OperationModel) -> bool:
        """Determinar si una operación es paginada."""
        try:
            output_shape = operation_model.output_shape
            if not output_shape:
                return False
            
            # Buscar indicadores de paginación comunes
            members = output_shape.members if hasattr(output_shape, 'members') else {}
            
            # Común: NextToken, Marker, NextPageToken
            pagination_indicators = ['NextToken', 'Marker', 'NextPageToken', 'nextToken']
            for indicator in pagination_indicators:
                if indicator in members:
                    return True
            
            # También verificar si hay un campo que sugiere múltiples resultados
            for key in members.keys():
                if key.lower() in ['items', 'results', 'list', 'values']:
                    return True
            
            return False
        except:
            return False

