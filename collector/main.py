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


class Collector:
    """Coordinador principal de recolección de datos AWS."""
    
    def __init__(
        self,
        output_dir: str,
        role_arn: Optional[str] = None,
        external_id: Optional[str] = None,
        regions: Optional[List[str]] = None,
        max_threads: int = 20,
        max_pages: int = 100,
        max_followups: int = 5,
        service_allowlist: Optional[List[str]] = None,
        service_denylist: Optional[List[str]] = None,
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
        self.service_denylist = set(service_denylist) if service_denylist else set()
        
        # Estadísticas
        self.stats = {
            "services_discovered": 0,
            "operations_executed": 0,
            "operations_successful": 0,
            "operations_failed": 0,
            "operations_skipped": 0,
            "errors": []
        }
        
        # Inicializar sesión AWS
        self.session = self._create_session()
        
        # Componentes
        self.discovery = ServiceDiscovery(self.session)
        # Configurar timeouts para evitar operaciones que se cuelguen
        connect_timeout = int(os.getenv("ECAD_CONNECT_TIMEOUT", "10"))
        read_timeout = int(os.getenv("ECAD_READ_TIMEOUT", "30"))
        operation_timeout = int(os.getenv("ECAD_OPERATION_TIMEOUT", "120"))
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
        
        # Recolectar por servicio y región
        tasks = []
        for service_name in services_to_collect:
            for region in self.regions:
                tasks.append((service_name, region))
        
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
        try:
            # Descubrir operaciones del servicio
            operations = self.discovery.discover_operations(service_name, region)
            
            if not operations:
                logger.debug(f"No se encontraron operaciones para {service_name} en {region}")
                return
            
            # Contar operaciones safe_to_call
            safe_ops = [op for op, info in operations.items() if info.get("safe_to_call", False)]
            logger.debug(
                f"{service_name}/{region}: {len(operations)} operaciones, "
                f"{len(safe_ops)} safe_to_call"
            )
            
            # Ejecutar operaciones
            executed_count = 0
            for op_name, op_info in operations.items():
                result = self.executor.execute_operation(
                    service_name, region, op_name, op_info
                )
                
                if result:
                    self._save_result(service_name, region, op_name, result)
                    self.stats["operations_executed"] += 1
                    executed_count += 1
                    if result.get("success"):
                        self.stats["operations_successful"] += 1
                    else:
                        self.stats["operations_failed"] += 1
                else:
                    self.stats["operations_skipped"] += 1
            
            if executed_count > 0:
                logger.debug(f"{service_name}/{region}: {executed_count} operaciones ejecutadas")
        
        except Exception as e:
            logger.error(f"Error recolectando {service_name}/{region}: {e}")
            raise
    
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
        default=int(os.getenv("ECAD_MAX_THREADS", "20")),
        help="Número máximo de threads paralelos"
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        default=int(os.getenv("ECAD_MAX_PAGES", "100")),
        help="Número máximo de páginas por operación paginada"
    )
    parser.add_argument(
        "--max-followups",
        type=int,
        default=int(os.getenv("ECAD_MAX_FOLLOWUPS", "5")),
        help="Número máximo de followups por operación List"
    )
    parser.add_argument(
        "--service-allowlist",
        help="Servicios permitidos separados por coma"
    )
    parser.add_argument(
        "--service-denylist",
        help="Servicios excluidos separados por coma"
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

