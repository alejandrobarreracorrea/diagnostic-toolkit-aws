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
            # NOTA: No filtramos por hasattr aquí porque algunas operaciones pueden
            # estar disponibles pero no ser detectadas correctamente por hasattr
            # El executor las verificará antes de ejecutar
            for operation_name in service_model.operation_names:
                try:
                    operation_model = service_model.operation_model(operation_name)
                    op_info = self._analyze_operation(operation_model)
                    if op_info:
                        operations[operation_name] = op_info
                except Exception as e:
                    logger.debug(f"Error analizando {operation_name}: {e}")
                    continue
        
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

