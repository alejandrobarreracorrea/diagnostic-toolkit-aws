"""
Operation Executor - Ejecución de operaciones AWS con manejo de errores,
retry, y seguimiento de operaciones que requieren parámetros.
"""

import logging
import time
import re
import signal
from typing import Dict, List, Optional, Any
import boto3
from botocore.exceptions import (
    ClientError, 
    EndpointConnectionError,
    ConnectTimeoutError,
    ReadTimeoutError,
    ConnectionError as BotoConnectionError
)
from botocore.client import BaseClient
from botocore.config import Config

logger = logging.getLogger(__name__)


def _pascal_to_snake(name: str) -> str:
    """Convertir PascalCase a snake_case."""
    # Insertar underscore antes de mayúsculas (excepto la primera)
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    # Insertar underscore antes de mayúsculas seguidas de minúsculas
    s2 = re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1)
    return s2.lower()


class OperationExecutor:
    """Ejecutor de operaciones AWS con manejo inteligente de parámetros."""
    
    def __init__(
        self,
        session: boto3.Session,
        max_pages: int = 100,
        max_followups: int = 5,
        connect_timeout: int = 10,
        read_timeout: int = 30,
        operation_timeout: int = 120
    ):
        self.session = session
        self.max_pages = max_pages
        self.max_followups = max_followups
        self.connect_timeout = connect_timeout
        self.read_timeout = read_timeout
        self.operation_timeout = operation_timeout
        self._client_cache: Dict[str, BaseClient] = {}
        self._list_results_cache: Dict[str, List[Dict]] = {}
    
    def execute_operation(
        self,
        service_name: str,
        region: str,
        operation_name: str,
        operation_info: Dict
    ) -> Optional[Dict]:
        """Ejecutar una operación AWS."""
        
        # Si es safe-to-call, ejecutar directamente
        if operation_info.get("safe_to_call", False):
            return self._execute_safe_operation(
                service_name, region, operation_name, operation_info
            )
        
        # Si tiene parámetros requeridos, intentar inferirlos
        required_params = operation_info.get("required_params", [])
        
        # Intentar con 1 parámetro requerido
        if len(required_params) == 1:
            result = self._execute_with_inferred_params(
                service_name, region, operation_name, operation_info, required_params
            )
            if result:
                return result
        
        # Para operaciones con múltiples parámetros requeridos,
        # intentar ejecutar sin parámetros (algunas APIs los aceptan como opcionales)
        if len(required_params) > 1:
            logger.debug(
                f"Intentando {service_name}.{operation_name} sin parámetros "
                f"(tiene {len(required_params)} requeridos, pero algunos APIs los aceptan opcionales)"
            )
            # Intentar ejecutar sin parámetros - algunas APIs los marcan como required
            # pero en realidad son opcionales
            try:
                client = self._get_client(service_name, region)
                if hasattr(client, operation_name):
                    operation = getattr(client, operation_name)
                    # Intentar ejecutar sin parámetros
                    result = self._execute_with_retry(operation)
                    return {
                        "success": True,
                        "data": result,
                        "paginated": operation_info.get("paginated", False),
                        "note": "Executed without required params (API accepted)"
                    }
            except Exception as e:
                # Si falla, es porque realmente requiere parámetros
                logger.debug(
                    f"Saltando {service_name}.{operation_name}: "
                    f"realmente requiere {len(required_params)} parámetros"
                )
        
        return None
    
    def _execute_safe_operation(
        self,
        service_name: str,
        region: str,
        operation_name: str,
        operation_info: Dict
    ) -> Dict:
        """Ejecutar operación sin parámetros requeridos."""
        client = self._get_client(service_name, region)
        
        try:
            # Convertir nombre de operación de PascalCase a snake_case
            # Ejemplo: DescribeRegions -> describe_regions
            # Intentar primero con el nombre original (por si ya está en snake_case)
            method_name = operation_name
            operation = getattr(client, method_name, None)
            
            # Si no existe, convertir a snake_case
            if operation is None:
                method_name = _pascal_to_snake(operation_name)
                operation = getattr(client, method_name, None)
            
            if operation is None:
                # Operación no existe en el cliente - esto es normal, no es un error
                # No guardamos estas operaciones para evitar ruido
                logger.debug(f"Operación {operation_name} ({method_name}) no existe en cliente {service_name} (normal, no disponible)")
                return None  # Retornar None para que no se guarde
            
            # Verificar que es callable
            if not callable(operation):
                logger.debug(f"Operación {operation_name} no es callable en {service_name}")
                return {
                    "success": False,
                    "error": {
                        "code": "OperationNotCallable",
                        "message": f"Operation {operation_name} is not callable"
                    }
                }
            
            # Ejecutar con retry (usar method_name para paginación)
            result = self._execute_with_retry(operation)
            
            # Si es paginada, obtener todas las páginas
            if operation_info.get("paginated", False):
                result = self._paginate_operation(
                    client, method_name, result, operation_info
                )
            
            # Cachear resultados de List* para uso posterior
            if operation_name.lower().startswith('list'):
                cache_key = f"{service_name}:{region}:{operation_name}"
                # Extraer items individuales de resultados paginados
                items = self._extract_items_from_result(result)
                self._list_results_cache[cache_key] = items
            
            return {
                "success": True,
                "data": result,
                "paginated": operation_info.get("paginated", False)
            }
        
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', 'Unknown')
            
            # Errores esperados que no son críticos
            if error_code in ['AccessDenied', 'UnauthorizedOperation']:
                logger.debug(f"Acceso denegado: {service_name}.{operation_name}")
                return {
                    "success": False,
                    "error": {
                        "code": error_code,
                        "message": str(e)
                    }
                }
            
            # Throttling - retry ya manejado arriba
            if error_code in ['Throttling', 'TooManyRequestsException']:
                logger.warning(f"Throttling en {service_name}.{operation_name}")
                return {
                    "success": False,
                    "error": {
                        "code": error_code,
                        "message": "Rate limit exceeded"
                    }
                }
            
            # Otros errores
            logger.debug(f"Error en {service_name}.{operation_name}: {error_code}")
            return {
                "success": False,
                "error": {
                    "code": error_code,
                    "message": str(e)
                }
            }
        
        except AttributeError as e:
            # Operación no existe en el cliente
            logger.debug(f"Operación {operation_name} no disponible en {service_name}: {e}")
            return {
                "success": False,
                "error": {
                    "code": "OperationNotFound",
                    "message": f"Operation {operation_name} not available"
                }
            }
        except (EndpointConnectionError, ConnectTimeoutError, ReadTimeoutError, BotoConnectionError) as e:
            # Errores de conexión - servicios no disponibles o endpoints no accesibles
            # Estos son esperados para algunos servicios/regiones
            error_str = str(e).lower()
            if "could not connect" in error_str or "connect timeout" in error_str:
                logger.debug(
                    f"Endpoint no disponible: {service_name}.{operation_name} "
                    f"(servicio puede no estar habilitado o región no soportada)"
                )
            else:
                logger.debug(f"Error de conexión en {service_name}.{operation_name}: {e}")
            return {
                "success": False,
                "error": {
                    "code": "EndpointNotAvailable",
                    "message": str(e)
                },
                "not_available": True  # Marcar como no disponible, no como error real
            }
        except Exception as e:
            # Categorizar otros errores esperados
            error_str = str(e).lower()
            
            # Errores esperados que no deberían ser warnings
            expected_errors = [
                "unable to locate authorization token",  # CodeCatalyst
                "has no attribute",
                "operation not found",
                "not implemented",
                "service not available"
            ]
            
            is_expected = any(expected in error_str for expected in expected_errors)
            
            if is_expected:
                logger.debug(f"Error esperado en {service_name}.{operation_name}: {e}")
            else:
                # Solo loggear como warning si es realmente inesperado
                logger.warning(f"Error inesperado en {service_name}.{operation_name}: {e}")
            
            return {
                "success": False,
                "error": {
                    "code": "UnexpectedError",
                    "message": str(e)
                },
                "not_available": is_expected  # Marcar como no disponible si es esperado
            }
    
    def _execute_with_inferred_params(
        self,
        service_name: str,
        region: str,
        operation_name: str,
        operation_info: Dict,
        required_params: List[Dict]
    ) -> Optional[Dict]:
        """Ejecutar operación con parámetros inferidos desde List operations."""
        if len(required_params) != 1:
            return None
        
        param_name = required_params[0]["name"]
        
        # Buscar en cache de List operations
        cache_key = f"{service_name}:{region}:list*"
        
        # Buscar cualquier List operation del mismo servicio
        matching_keys = [
            k for k in self._list_results_cache.keys()
            if k.startswith(f"{service_name}:{region}:list")
        ]
        
        if not matching_keys:
            logger.debug(f"No hay datos de List para inferir {param_name} en {operation_name}")
            return None
        
        # Intentar extraer IDs desde resultados de List
        inferred_values = []
        for cache_key in matching_keys[:self.max_followups]:  # Limitar followups
            list_results = self._list_results_cache[cache_key]
            for item in list_results:
                # Heurísticas comunes para extraer IDs
                id_value = self._extract_id_from_item(item, param_name, service_name)
                if id_value:
                    inferred_values.append(id_value)
        
        if not inferred_values:
            return None
        
        # Ejecutar operación con cada valor inferido (limitado)
        client = self._get_client(service_name, region)
        results = []
        
        # Convertir nombre de operación a snake_case
        method_name = _pascal_to_snake(operation_name)
        
        for value in inferred_values[:self.max_followups]:
            try:
                # Verificar que la operación existe (intentar ambos formatos)
                operation = getattr(client, method_name, None)
                if operation is None:
                    operation = getattr(client, operation_name, None)
                
                if operation is None:
                    logger.debug(f"Operación {operation_name} ({method_name}) no disponible en cliente {service_name}")
                    break
                result = self._execute_with_retry(
                    operation,
                    **{param_name: value}
                )
                results.append(result)
            except AttributeError:
                logger.debug(f"Operación {operation_name} no disponible en {service_name}")
                break
            except Exception as e:
                logger.debug(f"Error con parámetro inferido {param_name}={value}: {e}")
                continue
        
        if results:
            return {
                "success": True,
                "data": results,
                "paginated": False,
                "inferred_params": {param_name: inferred_values[:self.max_followups]}
            }
        
        return None
    
    def _extract_items_from_result(self, result: Dict) -> List[Dict]:
        """Extraer items individuales de un resultado (puede ser paginado o no)."""
        items = []
        data = result.get("data", {})
        
        # Si es paginado, extraer items de cada página
        if isinstance(data, dict) and "data" in data and "pages" in data:
            pages = data.get("data", [])
            for page in pages:
                if isinstance(page, dict):
                    # Buscar listas comunes de items
                    for key in ["HostedZones", "HostedZoneSummaries", "Items", "Results", "Values"]:
                        if key in page and isinstance(page[key], list):
                            items.extend(page[key])
                    # Si no hay lista, el page mismo puede ser un item
                    if not any(key in page for key in ["HostedZones", "HostedZoneSummaries", "Items", "Results", "Values"]):
                        items.append(page)
        # Si no es paginado pero tiene estructura de lista
        elif isinstance(data, dict):
            # Buscar listas comunes de items
            for key in ["HostedZones", "HostedZoneSummaries", "Items", "Results", "Values"]:
                if key in data and isinstance(data[key], list):
                    items.extend(data[key])
            # Si no hay lista, el data mismo puede ser un item
            if not items and data:
                items.append(data)
        # Si data es una lista directamente
        elif isinstance(data, list):
            items = data
        
        return items
    
    def _extract_id_from_item(self, item: Any, param_name: str, service_name: str = "") -> Optional[str]:
        """Extraer ID desde un item de resultado de List operation."""
        if not isinstance(item, dict):
            return None
        
        # Buscar directamente
        if param_name in item:
            value = item[param_name]
            if isinstance(value, (str, int)):
                value_str = str(value)
                # Lógica específica para Route 53: el HostedZoneId puede venir con formato /hostedzone/Z1234567890
                if service_name == "route53" and param_name.lower() in ["hostedzoneid", "hostedzone"]:
                    if "/hostedzone/" in value_str:
                        # Extraer solo el ID después de /hostedzone/
                        value_str = value_str.split("/hostedzone/")[-1]
                    return value_str
                return value_str
        
        # Heurísticas comunes
        id_variants = [
            param_name,
            f"{param_name}Id",
            f"{param_name}_id",
            "Id",
            "ID",
            "id",
            "Arn",
            "ARN",
            "arn"
        ]
        
        for variant in id_variants:
            if variant in item:
                value = item[variant]
                if isinstance(value, (str, int)):
                    value_str = str(value)
                    # Lógica específica para Route 53
                    if service_name == "route53" and "hostedzone" in variant.lower():
                        if "/hostedzone/" in value_str:
                            value_str = value_str.split("/hostedzone/")[-1]
                        return value_str
                    return value_str
        
        return None
    
    def _execute_with_retry(self, operation, **kwargs) -> Any:
        """Ejecutar operación con retry y backoff exponencial, con timeout general."""
        max_retries = 2  # Reducir retries para evitar esperas largas
        base_delay = 1
        
        # Timeout general para evitar que operaciones se cuelguen
        start_time = time.time()
        
        for attempt in range(max_retries):
            try:
                # Verificar timeout antes de ejecutar
                elapsed = time.time() - start_time
                if elapsed > self.operation_timeout:
                    raise TimeoutError(f"Operación excedió timeout de {self.operation_timeout}s")
                
                result = operation(**kwargs)
                
                # Verificar timeout después de ejecutar
                elapsed = time.time() - start_time
                if elapsed > self.operation_timeout:
                    logger.warning(f"Operación completó pero excedió timeout de {self.operation_timeout}s")
                
                return result
            except ClientError as e:
                error_code = e.response.get('Error', {}).get('Code', '')
                
                # Throttling - retry con backoff
                if error_code in ['Throttling', 'TooManyRequestsException', 'RequestLimitExceeded']:
                    if attempt < max_retries - 1:
                        delay = base_delay * (2 ** attempt)
                        logger.debug(f"Throttling, retry en {delay}s (intento {attempt + 1}/{max_retries})")
                        time.sleep(delay)
                        continue
                
                # Otros errores - no retry
                raise
            
            except (EndpointConnectionError, ConnectTimeoutError, ReadTimeoutError, BotoConnectionError, TimeoutError) as e:
                # Error de conexión o timeout - no hacer retry para evitar esperas largas
                error_str = str(e).lower()
                if "timeout" in error_str:
                    logger.debug(f"Timeout en operación: {e}")
                    # No hacer retry en timeouts - probablemente el servicio está lento o no disponible
                    raise
                # Si es "could not connect", probablemente el servicio no está disponible
                # No hacer retry para evitar esperas largas
                raise
            except Exception as e:
                # Otros errores - verificar timeout
                elapsed = time.time() - start_time
                if elapsed > self.operation_timeout:
                    logger.warning(f"Operación falló después de {elapsed:.1f}s (timeout: {self.operation_timeout}s)")
                    raise TimeoutError(f"Operación excedió timeout de {self.operation_timeout}s")
                raise
        
        raise Exception("Max retries exceeded")
    
    def _paginate_operation(
        self,
        client: BaseClient,
        operation_name: str,
        first_result: Any,
        operation_info: Dict
    ) -> Dict:
        """Obtener todas las páginas de una operación paginada."""
        all_data = []
        
        if isinstance(first_result, dict):
            all_data.append(first_result)
        else:
            all_data.append({"result": first_result})
        
        # Intentar paginación usando paginator si está disponible
        try:
            paginator = client.get_paginator(operation_name)
            page_iterator = paginator.paginate()
            
            page_count = 0
            for page in page_iterator:
                if page_count >= self.max_pages:
                    logger.warning(f"Límite de páginas alcanzado para {operation_name}")
                    break
                all_data.append(page)
                page_count += 1
            
        except Exception as e:
            # Si no hay paginator, intentar paginación manual
            logger.debug(f"No hay paginator para {operation_name}, usando resultado inicial")
        
        return {
            "pages": len(all_data),
            "data": all_data
        }
    
    def _get_client(self, service_name: str, region: str) -> BaseClient:
        """Obtener cliente AWS desde cache o crear nuevo con timeouts configurados."""
        cache_key = f"{service_name}:{region}"
        if cache_key not in self._client_cache:
            # Configurar timeouts para evitar operaciones que se cuelguen
            config = Config(
                connect_timeout=self.connect_timeout,
                read_timeout=self.read_timeout,
                retries={'max_attempts': 2}  # Reducir retries para evitar esperas largas
            )
            self._client_cache[cache_key] = self.session.client(
                service_name,
                region_name=region,
                config=config
            )
        return self._client_cache[cache_key]

