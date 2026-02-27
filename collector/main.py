#!/usr/bin/env python3
"""
ECAD Collector - Recolección de datos desde AWS

Descubre y ejecuta operaciones de todos los servicios AWS disponibles,
guardando los resultados en formato JSON comprimido.
"""

import argparse
import json
import gzip
import os
import sys
import time
import threading
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging

import boto3
from botocore.exceptions import ClientError, EndpointConnectionError
from botocore.model import OperationModel
from tqdm import tqdm

from collector.discovery import ServiceDiscovery
from collector.executor import OperationExecutor
from collector.metadata import MetadataCollector

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Defaults orientados a maximizar cobertura en la primera ejecución.
DEFAULT_MAX_THREADS = 12
DEFAULT_MAX_PAGES = 50
DEFAULT_MAX_FOLLOWUPS = 10
DEFAULT_MAX_SERVICE_SECONDS = 240
DEFAULT_MAX_OPS_PER_SERVICE = 80
DEFAULT_CONNECT_TIMEOUT = 15
DEFAULT_READ_TIMEOUT = 45
DEFAULT_OPERATION_TIMEOUT = 120

# Servicios globales de AWS: no tienen endpoint por región — se consultan solo en us-east-1
# para evitar duplicados y errores de endpoint en regiones que no los soportan.
_GLOBAL_SERVICES = frozenset({
    "iam",           # Users, Roles, Policies — global
    "route53",       # Hosted Zones, Records — global
    "route53domains",
    "cloudfront",    # Distributions, OAC — global
    "waf",           # WAFv1 global (distinto de wafv2 regional)
    "shield",        # Shield Advanced — global (us-east-1)
    "s3",            # Buckets son globales; ListBuckets devuelve todo
    "sts",           # GetCallerIdentity — global
    "account",       # Contactos de cuenta — global
    "organizations", # Organización, SCPs — global
    "ce",            # Cost Explorer — solo us-east-1
    "budgets",       # Budgets — solo us-east-1
    "support",       # Support API — solo us-east-1
    "health",        # Health API — solo us-east-1
    "trustedadvisor",
    "artifact",
    "marketplace",
})

# Servicios irrelevantes para el diagnóstico Well-Architected o que siempre fallan
# con errores de endpoint / permisos que no aportan datos útiles.
_DEFAULT_SOFT_DENYLIST = frozenset({
    "s3control",        # S3 control-plane require account-id en endpoint
    "s3outposts",
    "iotevents-data",   # Requiere endpoint privado
    "iot-data",
    "greengrass",
    "robomaker",
    "braket",
    "workmail",
    "chime",
    "connect",          # Contact Center — endpoint complejo
    "pinpoint-sms-voice",
    "pinpoint-sms-voice-v2",
    "marketplace-catalog",
    "marketplace-entitlement",
    "codestar-notifications",
    "codestar-connections",
    "datazone",
    "omics",
    "privatenetworks",
    "simspaceweaver",
    "ivschat",
    "ivs",
    "cleanrooms",
    "verifiedpermissions",
    "taxsettings",
    "entityresolution",
    "resourceexplorer2",  # Requiere activación previa
    "b2bi",
    "repostspace",
    "managedblockchain",
    "managedblockchain-query",
    "tnb",               # Telco Network Builder
    "freetier",
    "workspacesthinclient",
})


class Collector:
    """Coordinador principal de recolección de datos AWS."""
    
    def __init__(
        self,
        output_dir: str,
        role_arn: Optional[str] = None,
        external_id: Optional[str] = None,
        regions: Optional[List[str]] = None,
        max_threads: int = 15,
        max_pages: int = 20,
        max_followups: int = 5,
        service_allowlist: Optional[List[str]] = None,
        service_denylist: Optional[List[str]] = None,
        max_service_seconds: int = 90,
        max_ops_per_service: int = DEFAULT_MAX_OPS_PER_SERVICE,
        include_nonsafe_ops: bool = False,
    ):
        self.output_dir = Path(output_dir)
        self.raw_dir = self.output_dir / "raw"
        self.raw_dir.mkdir(parents=True, exist_ok=True)
        
        self.role_arn = role_arn or os.getenv("AWS_ROLE_ARN")
        self.external_id = external_id or os.getenv("AWS_EXTERNAL_ID")
        self.regions = regions or self._get_regions()
        self.max_threads = max_threads
        self.max_pages = max_pages
        self.max_followups = max_followups
        self.service_allowlist = set(service_allowlist) if service_allowlist else None
        # Denylist = explícito del usuario + soft denylist incorporado
        user_denylist = set(service_denylist) if service_denylist else set()
        self.service_denylist = user_denylist | _DEFAULT_SOFT_DENYLIST
        # Tiempo máximo por tarea (servicio+región). Si un servicio tiene 200+ ops y algunas son lentas,
        # se corta para no bloquear el pool de threads.
        self.max_service_seconds = max_service_seconds
        # Presupuesto de operaciones por servicio para evitar colas largas de bajo valor.
        self.max_ops_per_service = max_ops_per_service
        # Si es false, se priorizan operaciones safe-to-call para maximizar éxitos.
        self.include_nonsafe_ops = include_nonsafe_ops
        
        # Estadísticas — protegidas con lock para uso seguro en múltiples threads
        self._stats_lock = threading.Lock()
        self.stats = {
            "services_discovered": 0,
            "operations_executed": 0,
            "operations_successful": 0,
            "operations_failed": 0,
            "operations_skipped": 0,
            "errors": []
        }
        # Cache para saltarse rápido servicios cuyo endpoint no está disponible en una región
        self._unavailable_endpoints: Set[str] = set()  # "{service}:{region}"
        self._unavailable_lock = threading.Lock()
        
        # Inicializar sesión AWS
        self.session = self._create_session()
        
        # Componentes
        self.discovery = ServiceDiscovery(self.session)
        # Configurar timeouts para evitar operaciones que se cuelguen
        connect_timeout = int(os.getenv("ECAD_CONNECT_TIMEOUT", str(DEFAULT_CONNECT_TIMEOUT)))
        read_timeout = int(os.getenv("ECAD_READ_TIMEOUT", str(DEFAULT_READ_TIMEOUT)))
        operation_timeout = int(os.getenv("ECAD_OPERATION_TIMEOUT", str(DEFAULT_OPERATION_TIMEOUT)))
        self.executor = OperationExecutor(
            self.session,
            max_pages=max_pages,
            max_followups=max_followups,
            connect_timeout=connect_timeout,
            read_timeout=read_timeout,
            operation_timeout=operation_timeout
        )
        self.metadata_collector = MetadataCollector(self.session)
    
    def _get_regions(self) -> List[str]:
        """Obtener lista de regiones desde variable de entorno o usar default."""
        env_regions = os.getenv("AWS_REGIONS")
        if env_regions:
            if env_regions.lower() == "all":
                # Obtener todas las regiones disponibles
                try:
                    ec2 = self.session.client('ec2', region_name='us-east-1')
                    regions_response = ec2.describe_regions()
                    all_regions = [r['RegionName'] for r in regions_response.get('Regions', [])]
                    logger.info(f"Usando todas las regiones disponibles: {len(all_regions)} regiones")
                    return all_regions
                except Exception as e:
                    logger.warning(f"Error obteniendo todas las regiones: {e}, usando default")
                    default_region = os.getenv("AWS_REGION", "us-east-1")
                    return [default_region]
            else:
                return [r.strip() for r in env_regions.split(",")]
        
        default_region = os.getenv("AWS_REGION", "us-east-1")
        return [default_region]
    
    def _create_session(self) -> boto3.Session:
        """Crear sesión AWS con AssumeRole si es necesario."""
        # Respetar AWS_PROFILE si está configurado (útil para SSO)
        profile_name = os.getenv("AWS_PROFILE")
        
        if self.role_arn:
            logger.info(f"Usando AssumeRole: {self.role_arn}")
            # Crear sesión inicial (puede usar perfil SSO)
            if profile_name:
                initial_session = boto3.Session(profile_name=profile_name)
            else:
                initial_session = boto3.Session()
            
            sts = initial_session.client('sts')
            assume_role_kwargs = {
                "RoleArn": self.role_arn,
                "RoleSessionName": os.getenv("AWS_ROLE_SESSION_NAME", "ECAD-Session")
            }
            if self.external_id:
                assume_role_kwargs["ExternalId"] = self.external_id
            
            response = sts.assume_role(**assume_role_kwargs)
            credentials = response['Credentials']
            
            return boto3.Session(
                aws_access_key_id=credentials['AccessKeyId'],
                aws_secret_access_key=credentials['SecretAccessKey'],
                aws_session_token=credentials['SessionToken']
            )
        
        # Sin AssumeRole: usar perfil SSO si está configurado
        if profile_name:
            logger.info(f"Usando perfil AWS: {profile_name}")
            return boto3.Session(profile_name=profile_name)
        
        return boto3.Session()
    
    def _should_collect_service(self, service_name: str) -> bool:
        """Determinar si un servicio debe ser recolectado."""
        if service_name in self.service_denylist:
            return False
        if self.service_allowlist and service_name not in self.service_allowlist:
            return False
        return True

    def _effective_region_for_service(self, service_name: str) -> str:
        """Devuelve la región efectiva para el servicio.

        Los servicios globales siempre se consultan en us-east-1, independientemente
        de qué regiones se estén recolectando, para evitar errores de endpoint y
        resultados duplicados.
        """
        if service_name in _GLOBAL_SERVICES:
            return "us-east-1"
        return None  # None → usar la región del task normalmente
    
    def collect(self):
        """Ejecutar recolección completa."""
        logger.info("Iniciando recolección de datos AWS")
        logger.info(f"Regiones: {', '.join(self.regions)}")
        logger.info(f"Threads: {self.max_threads}")
        
        start_time = time.time()
        
        # Descubrir servicios
        services = self.discovery.discover_services()
        logger.info(f"Servicios descubiertos: {len(services)}")
        
        # Filtrar servicios
        services_to_collect = [
            s for s in services
            if self._should_collect_service(s)
        ]
        logger.info(f"Servicios a recolectar: {len(services_to_collect)}")
        self.stats["services_discovered"] = len(services_to_collect)
        
        # Recolectar metadatos de cuenta
        try:
            account_metadata = self.metadata_collector.collect()
            metadata_file = self.output_dir / "metadata.json"
            with open(metadata_file, 'w') as f:
                json.dump(account_metadata, f, indent=2, default=str)
            logger.info(f"Metadatos guardados en {metadata_file}")
        except Exception as e:
            logger.warning(f"Error recolectando metadatos: {e}")
        
        # Recolectar por servicio y región.
        # Los servicios globales se asignan solo a us-east-1 (una tarea, no N por región).
        seen_global: Set[str] = set()
        tasks = []
        for service_name in services_to_collect:
            fixed_region = self._effective_region_for_service(service_name)
            if fixed_region is not None:
                # Servicio global: solo una tarea
                if service_name not in seen_global:
                    tasks.append((service_name, fixed_region))
                    seen_global.add(service_name)
            else:
                for region in self.regions:
                    tasks.append((service_name, region))

        logger.info(f"Tareas de recolección: {len(tasks)} "
                    f"({len(seen_global)} servicios globales → us-east-1 únicamente)")

        # Ejecutar en paralelo
        with ThreadPoolExecutor(max_workers=self.max_threads) as executor:
            futures = {
                executor.submit(self._collect_service_region, service, region): (service, region)
                for service, region in tasks
            }
            
            with tqdm(total=len(futures), desc="Recolectando") as pbar:
                for future in as_completed(futures):
                    service, region = futures[future]
                    try:
                        future.result()
                    except Exception as e:
                        logger.error(f"Error en {service}/{region}: {e}")
                        with self._stats_lock:
                            self.stats["errors"].append({
                                "service": service,
                                "region": region,
                                "error": str(e)
                            })
                    finally:
                        pbar.update(1)
        
        # Guardar estadísticas finales
        elapsed = time.time() - start_time
        self.stats["elapsed_seconds"] = elapsed
        self.stats["timestamp"] = datetime.utcnow().isoformat()
        
        stats_file = self.output_dir / "collection_stats.json"
        with open(stats_file, 'w') as f:
            json.dump(self.stats, f, indent=2, default=str)
        
        logger.info(f"Recolección completada en {elapsed:.2f} segundos")
        logger.info(f"Operaciones exitosas: {self.stats['operations_successful']}")
        logger.info(f"Operaciones fallidas: {self.stats['operations_failed']}")
        logger.info(f"Estadísticas guardadas en {stats_file}")
    
    def _collect_service_region(self, service_name: str, region: str):
        """Recolectar datos de un servicio en una región específica."""
        endpoint_key = f"{service_name}:{region}"

        # Early-exit: si ya sabemos que el endpoint no está disponible en esta región, saltar
        with self._unavailable_lock:
            if endpoint_key in self._unavailable_endpoints:
                with self._stats_lock:
                    self.stats["operations_skipped"] += 1
                return

        try:
            # Descubrir operaciones del servicio
            operations = self.discovery.discover_operations(service_name, region)
            
            if not operations:
                logger.debug(f"No se encontraron operaciones para {service_name} en {region}")
                return

            # Reordenar para ejecutar primero operaciones críticas de inventario.
            # Esto evita que queden fuera por timeout en servicios muy grandes (ej. ec2).
            ordered_operations = self._prioritize_operations(service_name, operations)
            filtered_operations = self._filter_and_budget_operations(service_name, ordered_operations)
            dropped = len(ordered_operations) - len(filtered_operations)
            if dropped > 0:
                with self._stats_lock:
                    self.stats["operations_skipped"] += dropped
            ordered_operations = filtered_operations
            
            safe_ops = [op for op, info in operations.items() if info.get("safe_to_call", False)]
            logger.debug(
                f"{service_name}/{region}: {len(operations)} operaciones, "
                f"{len(safe_ops)} safe_to_call"
            )
            
            # Ejecutar operaciones — si la primera devuelve EndpointNotAvailable, saltar el resto
            executed_count = 0
            first_op = True
            service_start = time.time()
            for idx, (op_name, op_info) in enumerate(ordered_operations):
                # Timeout por tarea de servicio: si llevamos demasiado tiempo, dejamos de ejecutar
                # más operaciones para este servicio y liberamos el thread.
                elapsed_service = time.time() - service_start
                if elapsed_service > self.max_service_seconds:
                    remaining = len(ordered_operations) - idx
                    logger.warning(
                        f"{service_name}/{region}: timeout de tarea ({elapsed_service:.0f}s), "
                        f"se omiten {remaining} operaciones restantes"
                    )
                    with self._stats_lock:
                        self.stats["operations_skipped"] += remaining
                    break

                result = self.executor.execute_operation(
                    service_name, region, op_name, op_info
                )
                
                if result:
                    # Si el primer intento ya indica que el endpoint no existe, marcar y salir
                    if first_op and result.get("not_available"):
                        with self._unavailable_lock:
                            self._unavailable_endpoints.add(endpoint_key)
                        with self._stats_lock:
                            self.stats["operations_skipped"] += len(ordered_operations) - 1
                        return

                    self._save_result(service_name, region, op_name, result)
                    with self._stats_lock:
                        self.stats["operations_executed"] += 1
                    executed_count += 1
                    if result.get("success"):
                        with self._stats_lock:
                            self.stats["operations_successful"] += 1
                    else:
                        with self._stats_lock:
                            self.stats["operations_failed"] += 1
                else:
                    with self._stats_lock:
                        self.stats["operations_skipped"] += 1

                first_op = False
            
            if executed_count > 0:
                logger.debug(f"{service_name}/{region}: {executed_count} operaciones ejecutadas")
        
        except Exception as e:
            logger.error(f"Error recolectando {service_name}/{region}: {e}")
            raise

    def _prioritize_operations(self, service_name: str, operations: Dict[str, Dict]) -> List[tuple]:
        """Ordenar operaciones para ejecutar primero inventario real y señales de alto valor."""
        service_key = (service_name or "").lower()
        priority_map = {
            "ec2": [
                "DescribeInstances",
                "DescribeVolumes",
                "DescribeSnapshots",
                "DescribeVpcs",
                "DescribeSubnets",
                "DescribeSecurityGroups",
                "DescribeNetworkInterfaces",
                "DescribeRouteTables",
                "DescribeInternetGateways",
                "DescribeNatGateways",
                "DescribeAddresses",
                "DescribeLaunchTemplates",
            ],
            "rds": [
                "DescribeDBInstances",
                "DescribeDBClusters",
                "DescribeDBSnapshots",
                "DescribeDBClusterSnapshots",
                "DescribeDBSubnetGroups",
                "DescribeDBParameterGroups",
                "DescribeOptionGroups",
            ],
            "s3": ["ListBuckets"],
            "lambda": ["ListFunctions"],
            "dynamodb": ["ListTables"],
            "iam": ["ListUsers", "ListRoles", "ListPolicies", "ListGroups"],
            "ecs": ["ListClusters", "ListServices", "ListTasks"],
            "eks": ["ListClusters", "ListNodegroups"],
        }
        preferred = priority_map.get(service_key, [])
        if not preferred:
            return list(operations.items())

        preferred_set = set(preferred)
        priority_items: List[tuple] = []
        remainder_items: List[tuple] = []

        for name in preferred:
            if name in operations:
                priority_items.append((name, operations[name]))

        for name, info in operations.items():
            if name not in preferred_set:
                remainder_items.append((name, info))

        return priority_items + remainder_items

    def _operation_budget_for_service(self, service_name: str) -> int:
        """Presupuesto máximo de operaciones por servicio."""
        heavy_budgets = {
            "ec2": 70,
            "sagemaker": 70,
            "quicksight": 70,
            "glue": 70,
            "iot": 70,
            "cloudfront": 70,
            "cloudformation": 70,
        }
        return heavy_budgets.get((service_name or "").lower(), self.max_ops_per_service)

    def _filter_and_budget_operations(self, service_name: str, ordered_operations: List[tuple]) -> List[tuple]:
        """Filtrar operaciones no-safe (salvo críticas) y aplicar presupuesto por servicio."""
        priority_names = set(name for name, _ in ordered_operations[:24])
        filtered: List[tuple] = []
        for name, info in ordered_operations:
            safe = bool(info.get("safe_to_call", False))
            if safe or self.include_nonsafe_ops or name in priority_names:
                filtered.append((name, info))

        budget = self._operation_budget_for_service(service_name)
        if budget > 0 and len(filtered) > budget:
            logger.info(
                f"{service_name}: presupuesto de operaciones {budget} aplicado "
                f"(total candidatas: {len(filtered)})"
            )
            return filtered[:budget]
        return filtered
    
    def _save_result(
        self,
        service_name: str,
        region: str,
        operation: str,
        result: Dict
    ):
        """Guardar resultado de operación en archivo comprimido."""
        # Estructura: raw/{service}/{region}/{operation}.json.gz
        service_dir = self.raw_dir / service_name / region
        service_dir.mkdir(parents=True, exist_ok=True)
        
        filename = f"{operation}.json.gz"
        filepath = service_dir / filename
        
        # Preparar metadata
        metadata = {
            "service": service_name,
            "region": region,
            "operation": operation,
            "timestamp": datetime.utcnow().isoformat(),
            "paginated": result.get("paginated", False),
            "success": result.get("success", False),
        }
        
        # Incluir flag not_available si está presente
        if result.get("not_available") is not None:
            metadata["not_available"] = result.get("not_available")
        
        output = {
            "metadata": metadata,
            "data": result.get("data"),
            "error": result.get("error")
        }
        
        # Guardar comprimido
        with gzip.open(filepath, 'wt', encoding='utf-8') as f:
            json.dump(output, f, indent=2, default=str)


def main():
    """Punto de entrada principal."""
    parser = argparse.ArgumentParser(
        description="ECAD Collector - Recolección de datos AWS"
    )
    parser.add_argument(
        "--output-dir",
        required=True,
        help="Directorio de salida para datos recolectados"
    )
    parser.add_argument(
        "--role-arn",
        help="ARN del rol IAM para AssumeRole"
    )
    parser.add_argument(
        "--external-id",
        help="External ID para AssumeRole"
    )
    parser.add_argument(
        "--regions",
        help="Regiones separadas por coma (default: AWS_REGION o us-east-1)"
    )
    parser.add_argument(
        "--max-threads",
        type=int,
        default=int(os.getenv("ECAD_MAX_THREADS", str(DEFAULT_MAX_THREADS))),
        help=f"Número máximo de threads paralelos (default: {DEFAULT_MAX_THREADS})"
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        default=int(os.getenv("ECAD_MAX_PAGES", str(DEFAULT_MAX_PAGES))),
        help=f"Número máximo de páginas por operación paginada (default: {DEFAULT_MAX_PAGES})"
    )
    parser.add_argument(
        "--max-followups",
        type=int,
        default=int(os.getenv("ECAD_MAX_FOLLOWUPS", str(DEFAULT_MAX_FOLLOWUPS))),
        help=f"Número máximo de followups por operación List (default: {DEFAULT_MAX_FOLLOWUPS})"
    )
    parser.add_argument(
        "--service-allowlist",
        help="Servicios permitidos separados por coma"
    )
    parser.add_argument(
        "--service-denylist",
        help="Servicios excluidos separados por coma"
    )
    parser.add_argument(
        "--max-service-seconds",
        type=int,
        default=int(os.getenv("ECAD_MAX_SERVICE_SECONDS", str(DEFAULT_MAX_SERVICE_SECONDS))),
        help=f"Timeout en segundos por tarea de servicio/región (default: {DEFAULT_MAX_SERVICE_SECONDS})"
    )
    parser.add_argument(
        "--max-ops-per-service",
        type=int,
        default=int(os.getenv("ECAD_MAX_OPS_PER_SERVICE", str(DEFAULT_MAX_OPS_PER_SERVICE))),
        help=f"Máximo de operaciones por servicio tras priorización (default: {DEFAULT_MAX_OPS_PER_SERVICE})"
    )
    parser.add_argument(
        "--include-nonsafe-ops",
        action="store_true",
        default=os.getenv("ECAD_INCLUDE_NONSAFE_OPS", "0").lower() in ("1", "true", "yes"),
        help="Incluir operaciones que requieren parámetros (puede aumentar errores/timeouts)"
    )

    args = parser.parse_args()
    
    # Parsear listas
    regions = None
    if args.regions:
        regions = [r.strip() for r in args.regions.split(",")]
    
    service_allowlist = None
    if args.service_allowlist:
        service_allowlist = [s.strip() for s in args.service_allowlist.split(",")]
    
    service_denylist = None
    if args.service_denylist:
        service_denylist = [s.strip() for s in args.service_denylist.split(",")]
    elif os.getenv("ECAD_SERVICE_DENYLIST"):
        service_denylist = [s.strip() for s in os.getenv("ECAD_SERVICE_DENYLIST").split(",")]
    
    # Crear collector y ejecutar
    collector = Collector(
        output_dir=args.output_dir,
        role_arn=args.role_arn,
        external_id=args.external_id,
        regions=regions,
        max_threads=args.max_threads,
        max_pages=args.max_pages,
        max_followups=args.max_followups,
        service_allowlist=service_allowlist,
        service_denylist=service_denylist,
        max_service_seconds=args.max_service_seconds,
        max_ops_per_service=args.max_ops_per_service,
        include_nonsafe_ops=args.include_nonsafe_ops,
    )
    
    try:
        collector.collect()
        sys.exit(0)
    except KeyboardInterrupt:
        logger.info("Recolección interrumpida por usuario")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error fatal: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
