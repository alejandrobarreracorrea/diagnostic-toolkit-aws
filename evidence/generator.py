#!/usr/bin/env python3
"""
Evidence Pack Generator - Generación de evidencias para Well-Architected Review.

Genera evidencias objetivas y preguntas sugeridas para cada pilar del
Well-Architected Framework basado en datos recolectados.
"""

import argparse
import json
import gzip
import logging
import sys
from pathlib import Path
from typing import Dict, List, Any
from collections import defaultdict

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class EvidenceGenerator:
    """Generador de evidence pack para Well-Architected."""
    
    # Pilares del Well-Architected Framework
    PILLARS = [
        "Operational Excellence",
        "Security",
        "Reliability",
        "Performance Efficiency",
        "Cost Optimization",
        "Sustainability"
    ]
    
    def __init__(self, run_dir: str):
        self.run_dir = Path(run_dir)
        self.raw_dir = self.run_dir / "raw"
        self.index_dir = self.run_dir / "index"
        self.output_dir = self.run_dir / "outputs" / "evidence"
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def generate(self):
        """Generar evidence pack completo."""
        logger.info("Generando evidence pack para Well-Architected Framework")
        
        # Cargar índice
        index_file = self.index_dir / "index.json"
        if not index_file.exists():
            logger.error(f"Índice no encontrado: {index_file}")
            return
        
        with open(index_file, 'r') as f:
            index = json.load(f)
        
        # Generar evidencias por pilar
        evidence_pack = {
            "metadata": {
                "run_dir": str(self.run_dir),
                "generated_at": None,
                "account_id": self._get_account_id()
            },
            "pillars": {}
        }
        
        for pillar in self.PILLARS:
            logger.info(f"Generando evidencias para: {pillar}")
            evidence_pack["pillars"][pillar] = self._generate_pillar_evidence(
                pillar, index
            )
        
        from datetime import datetime
        evidence_pack["metadata"]["generated_at"] = datetime.utcnow().isoformat()
        
        # Guardar evidence pack
        self._save_evidence_pack(evidence_pack)
        
        logger.info(f"Evidence pack generado en: {self.output_dir}")
    
    def _generate_pillar_evidence(
        self,
        pillar: str,
        index: Dict
    ) -> Dict:
        """Generar evidencias para un pilar específico."""
        if pillar == "Security":
            return self._generate_security_evidence(index)
        elif pillar == "Reliability":
            return self._generate_reliability_evidence(index)
        elif pillar == "Operational Excellence":
            return self._generate_operational_evidence(index)
        elif pillar == "Cost Optimization":
            return self._generate_cost_evidence(index)
        elif pillar == "Performance Efficiency":
            return self._generate_performance_evidence(index)
        elif pillar == "Sustainability":
            return self._generate_sustainability_evidence(index)
        else:
            return {"evidence": [], "questions": []}
    
    def _check_service_enabled(self, service_name: str, operation_name: str, services: Dict) -> bool:
        """
        Verificar si un servicio está realmente habilitado.
        Verifica si la operación específica fue exitosa y no tiene errores que indiquen que el servicio no está habilitado.
        """
        if service_name not in services:
            return False
        
        service_data = services[service_name]
        regions = service_data.get("regions", {})
        
        # Buscar la operación en todas las regiones
        for region_name, region_data in regions.items():
            operations = region_data.get("operations", [])
            for op_info in operations:
                op_name = op_info.get("operation", "")
                # Comparar nombres (pueden estar en PascalCase o snake_case)
                op_name_normalized = op_name.lower().replace("_", "")
                operation_normalized = operation_name.lower().replace("_", "")
                
                if op_name_normalized == operation_normalized:
                    # Verificar primero si hay errores que indiquen que el servicio NO está habilitado
                    error = op_info.get("error", {})
                    if isinstance(error, dict):
                        error_code = error.get("code", "")
                        error_message = error.get("message", "").lower()
                        
                        # Errores que indican que el servicio NO está habilitado
                        if error_code == "InvalidAccessException":
                            if "not subscribed" in error_message or "not enabled" in error_message or "is not subscribed" in error_message:
                                return False
                        elif error_code == "NoSuchConfigurationRecorderException":
                            return False
                        elif error_code == "NoSuchDeliveryChannelException":
                            return False
                    
                    # Si la operación fue exitosa, verificar que haya recursos activos
                    if op_info.get("success", False):
                        # Para algunos servicios, necesitamos verificar que haya recursos activos
                        if service_name == "config":
                            # Verificar que haya configuration recorders activos
                            return self._check_config_enabled(op_info)
                        elif service_name == "cloudtrail":
                            # Verificar que haya trails activos
                            return self._check_cloudtrail_enabled(op_info)
                        elif service_name == "guardduty":
                            # Verificar que haya detectores activos
                            return self._check_guardduty_enabled(op_info)
                        else:
                            # Para otros servicios, si la operación fue exitosa, asumimos que está habilitado
                            return True
        
        return False
    
    def _check_config_enabled(self, op_info: Dict) -> bool:
        """Verificar si Config está realmente habilitado leyendo los datos."""
        file_path = op_info.get("file")
        if not file_path:
            return False
        
        full_path = self.raw_dir / file_path
        if not full_path.exists():
            return False
        
        try:
            with gzip.open(full_path, 'rt', encoding='utf-8') as f:
                data = json.load(f)
            
            response_data = data.get("data", {})
            if isinstance(response_data, dict):
                # Verificar si hay ConfigurationRecorders
                recorders = response_data.get("ConfigurationRecorders", [])
                if isinstance(recorders, list):
                    # Si hay recorders, verificar que al menos uno esté grabando
                    if len(recorders) > 0:
                        for recorder in recorders:
                            # Si tiene recording=True, está habilitado
                            if recorder.get("recording", False):
                                return True
                        # Si hay recorders pero ninguno está grabando, Config no está realmente activo
                        return False
                    else:
                        # Lista vacía = Config no está habilitado
                        return False
        except Exception as e:
            logger.debug(f"Error leyendo archivo Config: {e}")
        
        return False
    
    def _check_cloudtrail_enabled(self, op_info: Dict) -> bool:
        """Verificar si CloudTrail está realmente habilitado leyendo los datos."""
        file_path = op_info.get("file")
        if not file_path:
            return False
        
        full_path = self.raw_dir / file_path
        if not full_path.exists():
            return False
        
        try:
            with gzip.open(full_path, 'rt', encoding='utf-8') as f:
                data = json.load(f)
            
            response_data = data.get("data", {})
            if isinstance(response_data, dict):
                # Verificar si hay Trails
                trails = response_data.get("Trails", []) or response_data.get("trailList", [])
                if isinstance(trails, list):
                    # Si hay trails, verificar que al menos uno esté activo
                    if len(trails) > 0:
                        for trail in trails:
                            # Un trail está activo si IsLogging=True o si es multi-región
                            if trail.get("IsLogging") is True:
                                return True
                            # También considerar multi-región como habilitado
                            if trail.get("IsMultiRegionTrail") is True:
                                return True
                        # Si hay trails pero ninguno está activo, CloudTrail no está realmente activo
                        return False
                    else:
                        # Lista vacía = CloudTrail no está habilitado
                        return False
        except Exception as e:
            logger.debug(f"Error leyendo archivo CloudTrail: {e}")
        
        return False
    
    def _check_guardduty_enabled(self, op_info: Dict) -> bool:
        """Verificar si GuardDuty está realmente habilitado leyendo los datos."""
        file_path = op_info.get("file")
        if not file_path:
            return False
        
        full_path = self.raw_dir / file_path
        if not full_path.exists():
            return False
        
        try:
            with gzip.open(full_path, 'rt', encoding='utf-8') as f:
                data = json.load(f)
            
            response_data = data.get("data", {})
            if isinstance(response_data, dict):
                # Verificar si hay DetectorIds
                detector_ids = response_data.get("DetectorIds", [])
                if isinstance(detector_ids, list):
                    # Si hay detectores, GuardDuty está habilitado
                    if len(detector_ids) > 0:
                        return True
                    else:
                        # Lista vacía = GuardDuty no está habilitado
                        return False
        except Exception as e:
            logger.debug(f"Error leyendo archivo GuardDuty: {e}")
        
        return False
    
    def _generate_security_evidence(self, index: Dict) -> Dict:
        """Generar evidencias de seguridad."""
        evidence = []
        questions = []
        
        services = index.get("services", {})
        
        # Security Hub - Verificar si DescribeHub fue exitoso
        securityhub_enabled = self._check_service_enabled("securityhub", "DescribeHub", services)
        if securityhub_enabled:
            evidence.append({
                "type": "service_present",
                "service": "Security Hub",
                "status": "detected",
                "description": "AWS Security Hub está habilitado"
            })
            questions.append("¿Está Security Hub configurado para todas las regiones activas?")
            questions.append("¿Se están revisando regularmente los findings de Security Hub?")
        else:
            evidence.append({
                "type": "service_missing",
                "service": "Security Hub",
                "status": "not_detected",
                "description": "AWS Security Hub no está habilitado",
                "gap": "Falta de visibilidad centralizada del estado de seguridad"
            })
            questions.append("¿Por qué no se está usando Security Hub?")
            questions.append("¿Qué herramienta alternativa se usa para monitoreo de seguridad?")
        
        # AWS Config - Verificar si DescribeConfigurationRecorders fue exitoso y hay recorders activos
        config_enabled = self._check_service_enabled("config", "DescribeConfigurationRecorders", services)
        if config_enabled:
            evidence.append({
                "type": "service_present",
                "service": "AWS Config",
                "status": "detected",
                "description": "AWS Config está habilitado"
            })
            questions.append("¿Está Config habilitado en todas las regiones?")
            questions.append("¿Se están usando reglas de Config para cumplimiento?")
        else:
            evidence.append({
                "type": "service_missing",
                "service": "AWS Config",
                "status": "not_detected",
                "description": "AWS Config no está habilitado",
                "gap": "Falta de auditoría de cambios de configuración"
            })
            questions.append("¿Cómo se auditan los cambios de configuración sin Config?")
        
        # CloudTrail - Verificar si ListTrails fue exitoso y hay trails activos
        cloudtrail_enabled = self._check_service_enabled("cloudtrail", "ListTrails", services)
        if cloudtrail_enabled:
            evidence.append({
                "type": "service_present",
                "service": "CloudTrail",
                "status": "detected",
                "description": "AWS CloudTrail está habilitado"
            })
            questions.append("¿Está CloudTrail habilitado en todas las regiones?")
            questions.append("¿Los logs de CloudTrail están cifrados y en un bucket separado?")
            questions.append("¿Se están revisando regularmente los logs de CloudTrail?")
        else:
            evidence.append({
                "type": "service_missing",
                "service": "CloudTrail",
                "status": "not_detected",
                "description": "AWS CloudTrail no está habilitado",
                "gap": "CRÍTICO: Falta de auditoría de actividad de API"
            })
            questions.append("¿Por qué no se está usando CloudTrail? (CRÍTICO)")
        
        # IAM - Siempre está accesible, pero verificamos si hay operaciones exitosas
        if "iam" in services:
            iam_has_success = False
            for region_name, region_data in services["iam"].get("regions", {}).items():
                for op_info in region_data.get("operations", []):
                    if op_info.get("success", False):
                        iam_has_success = True
                        break
                if iam_has_success:
                    break
            
            if iam_has_success:
                evidence.append({
                    "type": "service_present",
                    "service": "IAM",
                    "status": "detected",
                    "description": "IAM está accesible"
                })
                questions.append("¿Se está usando MFA para usuarios con privilegios?")
                questions.append("¿Se revisan regularmente las políticas IAM?")
                questions.append("¿Se usan roles en lugar de usuarios para aplicaciones?")
        
        # GuardDuty - Verificar si ListDetectors fue exitoso y hay detectores activos
        guardduty_enabled = self._check_service_enabled("guardduty", "ListDetectors", services)
        if guardduty_enabled:
            evidence.append({
                "type": "service_present",
                "service": "GuardDuty",
                "status": "detected",
                "description": "Amazon GuardDuty está habilitado"
            })
            questions.append("¿Está GuardDuty habilitado en todas las regiones?")
        else:
            evidence.append({
                "type": "service_missing",
                "service": "GuardDuty",
                "status": "not_detected",
                "description": "Amazon GuardDuty no está habilitado",
                "gap": "Falta de detección de amenazas"
            })
        
        # Verificar recursos públicos (requiere análisis más profundo de datos)
        # Por ahora, solo indicamos que se debe revisar
        evidence.append({
            "type": "review_required",
            "category": "public_resources",
            "description": "Revisar manualmente recursos con IPs públicas o acceso público",
            "suggested_review": [
                "EC2 instances con IPs públicas",
                "RDS instances con publicly accessible",
                "S3 buckets con políticas públicas",
                "Load Balancers públicos"
            ]
        })
        questions.append("¿Qué recursos tienen acceso público y por qué?")
        questions.append("¿Se están usando Security Groups y NACLs correctamente?")
        
        return {
            "evidence": evidence,
            "questions": questions,
            "summary": f"{len([e for e in evidence if e.get('status') == 'detected'])} servicios de seguridad detectados"
        }
    
    def _generate_reliability_evidence(self, index: Dict) -> Dict:
        """Generar evidencias de confiabilidad."""
        evidence = []
        questions = []
        
        services = index.get("services", {})
        
        # Auto Scaling - Verificar si está realmente en uso
        autoscaling_in_use = self._check_autoscaling_in_use(services)
        if autoscaling_in_use:
            evidence.append({
                "type": "service_present",
                "service": "Auto Scaling",
                "status": "detected",
                "description": "Auto Scaling Groups están en uso"
            })
            questions.append("¿Las Auto Scaling Groups están configuradas con health checks adecuados?")
            questions.append("¿Las políticas de escalado están optimizadas?")
        else:
            if "ec2" in services:
                evidence.append({
                    "type": "service_missing",
                    "service": "Auto Scaling",
                    "status": "not_detected",
                    "description": "EC2 detectado pero Auto Scaling no",
                    "gap": "Falta de escalado automático y recuperación"
                })
                questions.append("¿Por qué no se está usando Auto Scaling para EC2?")
        
        # RDS - Verificar si está realmente en uso
        rds_in_use = self._check_rds_in_use(services)
        if rds_in_use:
            evidence.append({
                "type": "service_present",
                "service": "RDS",
                "status": "detected",
                "description": "RDS está en uso"
            })
            questions.append("¿Las instancias RDS críticas están configuradas con Multi-AZ?")
            questions.append("¿Se están usando backups automáticos?")
            questions.append("¿Se han probado los procedimientos de failover?")
        else:
            evidence.append({
                "type": "service_missing",
                "service": "RDS",
                "status": "not_detected",
                "description": "RDS no está en uso o no tiene instancias activas",
                "gap": "Falta de bases de datos gestionadas"
            })
        
        # ELB/ALB - Verificar si está realmente en uso
        loadbalancer_in_use = self._check_loadbalancer_in_use(services)
        if loadbalancer_in_use:
            evidence.append({
                "type": "service_present",
                "service": "Load Balancer",
                "status": "detected",
                "description": "Load Balancers están en uso"
            })
            questions.append("¿Los Load Balancers están configurados con health checks?")
            questions.append("¿Se está usando múltiples Availability Zones?")
        else:
            evidence.append({
                "type": "service_missing",
                "service": "Load Balancer",
                "status": "not_detected",
                "description": "Load Balancers no están en uso o no hay balanceadores activos",
                "gap": "Falta de distribución de carga"
            })
        
        # Route 53 - Verificar si está realmente en uso
        route53_in_use = self._check_route53_in_use(services)
        if route53_in_use:
            evidence.append({
                "type": "service_present",
                "service": "Route 53",
                "status": "detected",
                "description": "Route 53 está en uso"
            })
            questions.append("¿Se está usando Route 53 Health Checks?")
            questions.append("¿Hay políticas de failover configuradas?")
        else:
            evidence.append({
                "type": "service_missing",
                "service": "Route 53",
                "status": "not_detected",
                "description": "Route 53 no está en uso o no tiene hosted zones activas",
                "gap": "Falta de gestión de DNS"
            })
        
        return {
            "evidence": evidence,
            "questions": questions,
            "summary": f"{len([e for e in evidence if e.get('status') == 'detected'])} servicios de confiabilidad detectados"
        }
    
    def _check_cloudwatch_in_use(self, services: Dict) -> bool:
        """Verificar si CloudWatch está realmente en uso."""
        if "cloudwatch" not in services and "logs" not in services:
            return False
        
        # Verificar si hay operaciones exitosas que indiquen uso real
        for service_name in ["cloudwatch", "logs"]:
            if service_name not in services:
                continue
            
            service_data = services[service_name]
            regions = service_data.get("regions", {})
            
            for region_name, region_data in regions.items():
                operations = region_data.get("operations", [])
                for op_info in operations:
                    op_name = op_info.get("operation", "").lower()
                    # Operaciones que indican uso real de CloudWatch
                    if op_name in ["describealarms", "listmetrics", "listdashboards"]:
                        if op_info.get("success", False):
                            # Verificar que haya recursos reales
                            if service_name == "cloudwatch":
                                return self._check_cloudwatch_resources(op_info, op_name)
                            else:
                                # Para logs, si la operación fue exitosa, asumimos que está en uso
                                return True
        
        return False
    
    def _check_cloudwatch_resources(self, op_info: Dict, operation_name: str) -> bool:
        """Verificar si CloudWatch tiene recursos reales (alarmas, métricas, dashboards)."""
        file_path = op_info.get("file")
        if not file_path:
            return False
        
        full_path = self.raw_dir / file_path
        if not full_path.exists():
            return False
        
        try:
            with gzip.open(full_path, 'rt', encoding='utf-8') as f:
                data = json.load(f)
            
            response_data = data.get("data", {})
            if isinstance(response_data, dict):
                if "describealarms" in operation_name.lower():
                    # Verificar si hay alarmas
                    alarms = response_data.get("MetricAlarms", []) or response_data.get("CompositeAlarms", [])
                    if isinstance(alarms, list) and len(alarms) > 0:
                        return True
                elif "listmetrics" in operation_name.lower():
                    # Verificar si hay métricas
                    metrics = response_data.get("Metrics", [])
                    if isinstance(metrics, list) and len(metrics) > 0:
                        return True
                elif "listdashboards" in operation_name.lower():
                    # Verificar si hay dashboards
                    dashboards = response_data.get("DashboardEntries", [])
                    if isinstance(dashboards, list) and len(dashboards) > 0:
                        return True
        except Exception as e:
            logger.debug(f"Error leyendo archivo CloudWatch: {e}")
        
        return False
    
    def _check_ssm_in_use(self, services: Dict) -> bool:
        """Verificar si Systems Manager está realmente en uso."""
        if "ssm" not in services:
            return False
        
        service_data = services["ssm"]
        regions = service_data.get("regions", {})
        
        for region_name, region_data in regions.items():
            operations = region_data.get("operations", [])
            for op_info in operations:
                op_name = op_info.get("operation", "").lower()
                # Operaciones que indican uso real de SSM
                if op_name in ["describeinstanceinformation", "listdocuments", "describeparameters"]:
                    if op_info.get("success", False):
                        # Verificar que haya recursos reales
                        return self._check_ssm_resources(op_info, op_name)
        
        return False
    
    def _check_ssm_resources(self, op_info: Dict, operation_name: str) -> bool:
        """Verificar si SSM tiene recursos reales (instancias, documentos, parámetros)."""
        file_path = op_info.get("file")
        if not file_path:
            return False
        
        full_path = self.raw_dir / file_path
        if not full_path.exists():
            return False
        
        try:
            with gzip.open(full_path, 'rt', encoding='utf-8') as f:
                data = json.load(f)
            
            response_data = data.get("data", {})
            if isinstance(response_data, dict):
                if "describeinstanceinformation" in operation_name.lower():
                    # Verificar si hay instancias gestionadas
                    instances = response_data.get("InstanceInformationList", [])
                    if isinstance(instances, list) and len(instances) > 0:
                        return True
                elif "listdocuments" in operation_name.lower():
                    # Verificar si hay documentos
                    documents = response_data.get("DocumentIdentifiers", [])
                    if isinstance(documents, list) and len(documents) > 0:
                        return True
                elif "describeparameters" in operation_name.lower():
                    # Verificar si hay parámetros
                    parameters = response_data.get("Parameters", [])
                    if isinstance(parameters, list) and len(parameters) > 0:
                        return True
        except Exception as e:
            logger.debug(f"Error leyendo archivo SSM: {e}")
        
        return False
    
    def _check_cloudformation_in_use(self, services: Dict) -> bool:
        """Verificar si CloudFormation está realmente en uso."""
        if "cloudformation" not in services:
            return False
        
        service_data = services["cloudformation"]
        regions = service_data.get("regions", {})
        
        # Verificar en todas las regiones
        for region_name, region_data in regions.items():
            operations = region_data.get("operations", [])
            
            # Priorizar ListStacks sobre DescribeStacks (más completo)
            for op_info in operations:
                op_name = op_info.get("operation", "").lower()
                if op_name == "liststacks" and op_info.get("success", False):
                    if self._check_cloudformation_resources(op_info):
                        return True
            
            # Si ListStacks no tiene stacks activos, verificar DescribeStacks
            for op_info in operations:
                op_name = op_info.get("operation", "").lower()
                if op_name == "describestacks" and op_info.get("success", False):
                    if self._check_cloudformation_resources(op_info):
                        return True
        
        return False
    
    def _check_cloudformation_resources(self, op_info: Dict) -> bool:
        """Verificar si CloudFormation tiene stacks activos."""
        file_path = op_info.get("file")
        if not file_path:
            return False
        
        full_path = self.raw_dir / file_path
        if not full_path.exists():
            return False
        
        try:
            with gzip.open(full_path, 'rt', encoding='utf-8') as f:
                data = json.load(f)
            
            response_data = data.get("data", {})
            
            # Si es paginado, response_data tiene estructura: {"pages": N, "data": [page1, page2, ...]}
            if isinstance(response_data, dict) and "pages" in response_data and "data" in response_data:
                pages_list = response_data.get("data", [])
                if isinstance(pages_list, list):
                    # Iterar sobre todas las páginas
                    for page in pages_list:
                        if isinstance(page, dict):
                            # ListStacks devuelve StackSummaries, DescribeStacks devuelve Stacks
                            stacks = page.get("StackSummaries", []) or page.get("Stacks", [])
                            if isinstance(stacks, list):
                                for stack in stacks:
                                    if isinstance(stack, dict):
                                        stack_status = stack.get("StackStatus", "")
                                        # Excluir stacks eliminados y estados de eliminación
                                        if stack_status and stack_status != "DELETE_COMPLETE" and not stack_status.startswith("DELETE_"):
                                            return True
            
            # Si no es paginado, response_data es directamente el dict con la respuesta
            elif isinstance(response_data, dict):
                # ListStacks devuelve StackSummaries, DescribeStacks devuelve Stacks
                stacks = response_data.get("StackSummaries", []) or response_data.get("Stacks", [])
                if isinstance(stacks, list):
                    # Si hay stacks, verificar que al menos uno no esté en estado DELETE_COMPLETE
                    if len(stacks) > 0:
                        for stack in stacks:
                            if isinstance(stack, dict):
                                stack_status = stack.get("StackStatus", "")
                                # Excluir stacks eliminados y estados de eliminación
                                if stack_status and stack_status != "DELETE_COMPLETE" and not stack_status.startswith("DELETE_"):
                                    return True
                        # Si todos los stacks están eliminados o en proceso de eliminación, no está en uso
                        return False
                    else:
                        # Lista vacía = CloudFormation no está en uso
                        return False
            
            # Si la respuesta es una lista directa (caso poco común)
            elif isinstance(response_data, list):
                if len(response_data) > 0:
                    for stack in response_data:
                        if isinstance(stack, dict):
                            stack_status = stack.get("StackStatus", "")
                            if stack_status and stack_status != "DELETE_COMPLETE" and not stack_status.startswith("DELETE_"):
                                return True
                return False
                
        except Exception as e:
            logger.debug(f"Error leyendo archivo CloudFormation: {e}")
        
        return False
    
    def _check_rds_in_use(self, services: Dict) -> bool:
        """Verificar si RDS está realmente en uso."""
        if "rds" not in services:
            return False
        
        service_data = services["rds"]
        regions = service_data.get("regions", {})
        
        # Verificar en todas las regiones
        for region_name, region_data in regions.items():
            operations = region_data.get("operations", [])
            
            # Buscar DescribeDBInstances o DescribeDBClusters
            for op_info in operations:
                op_name = op_info.get("operation", "").lower()
                if op_name in ["describedbinstances", "describedbclusters"] and op_info.get("success", False):
                    if self._check_rds_resources(op_info):
                        return True
        
        return False
    
    def _check_rds_resources(self, op_info: Dict) -> bool:
        """Verificar si RDS tiene instancias o clusters activos."""
        file_path = op_info.get("file")
        if not file_path:
            return False
        
        full_path = self.raw_dir / file_path
        if not full_path.exists():
            return False
        
        try:
            with gzip.open(full_path, 'rt', encoding='utf-8') as f:
                data = json.load(f)
            
            response_data = data.get("data", {})
            
            # Si es paginado
            if isinstance(response_data, dict) and "pages" in response_data and "data" in response_data:
                pages_list = response_data.get("data", [])
                if isinstance(pages_list, list):
                    for page in pages_list:
                        if isinstance(page, dict):
                            # DescribeDBInstances devuelve DBInstances, DescribeDBClusters devuelve DBClusters
                            instances = page.get("DBInstances", []) or page.get("DBClusters", [])
                            if isinstance(instances, list) and len(instances) > 0:
                                # Verificar que al menos una instancia/cluster no esté eliminada
                                for instance in instances:
                                    if isinstance(instance, dict):
                                        status = instance.get("DBInstanceStatus", "") or instance.get("Status", "")
                                        # Excluir estados de eliminación
                                        if status and not status.startswith("delet") and status.lower() != "deleted":
                                            return True
            
            # Si no es paginado
            elif isinstance(response_data, dict):
                instances = response_data.get("DBInstances", []) or response_data.get("DBClusters", [])
                if isinstance(instances, list) and len(instances) > 0:
                    for instance in instances:
                        if isinstance(instance, dict):
                            status = instance.get("DBInstanceStatus", "") or instance.get("Status", "")
                            if status and not status.startswith("delet") and status.lower() != "deleted":
                                return True
                
        except Exception as e:
            logger.debug(f"Error leyendo archivo RDS: {e}")
        
        return False
    
    def _check_autoscaling_in_use(self, services: Dict) -> bool:
        """Verificar si Auto Scaling está realmente en uso."""
        if "autoscaling" not in services:
            return False
        
        service_data = services["autoscaling"]
        regions = service_data.get("regions", {})
        
        # Verificar en todas las regiones
        for region_name, region_data in regions.items():
            operations = region_data.get("operations", [])
            
            # Buscar DescribeAutoScalingGroups
            for op_info in operations:
                op_name = op_info.get("operation", "").lower()
                if op_name == "describeautoscalinggroups" and op_info.get("success", False):
                    if self._check_autoscaling_resources(op_info):
                        return True
        
        return False
    
    def _check_autoscaling_resources(self, op_info: Dict) -> bool:
        """Verificar si Auto Scaling tiene grupos activos."""
        file_path = op_info.get("file")
        if not file_path:
            return False
        
        full_path = self.raw_dir / file_path
        if not full_path.exists():
            return False
        
        try:
            with gzip.open(full_path, 'rt', encoding='utf-8') as f:
                data = json.load(f)
            
            response_data = data.get("data", {})
            
            # Si es paginado
            if isinstance(response_data, dict) and "pages" in response_data and "data" in response_data:
                pages_list = response_data.get("data", [])
                if isinstance(pages_list, list):
                    for page in pages_list:
                        if isinstance(page, dict):
                            groups = page.get("AutoScalingGroups", [])
                            if isinstance(groups, list) and len(groups) > 0:
                                return True
            
            # Si no es paginado
            elif isinstance(response_data, dict):
                groups = response_data.get("AutoScalingGroups", [])
                if isinstance(groups, list) and len(groups) > 0:
                    return True
                
        except Exception as e:
            logger.debug(f"Error leyendo archivo Auto Scaling: {e}")
        
        return False
    
    def _check_loadbalancer_in_use(self, services: Dict) -> bool:
        """Verificar si Load Balancers están realmente en uso."""
        # Verificar ELB (clásico) y ELBv2 (ALB/NLB)
        for service_name in ["elb", "elbv2"]:
            if service_name not in services:
                continue
            
            service_data = services[service_name]
            regions = service_data.get("regions", {})
            
            # Verificar en todas las regiones
            for region_name, region_data in regions.items():
                operations = region_data.get("operations", [])
                
                # ELB clásico usa DescribeLoadBalancers, ELBv2 también
                for op_info in operations:
                    op_name = op_info.get("operation", "").lower()
                    if op_name == "describeloadbalancers" and op_info.get("success", False):
                        if self._check_loadbalancer_resources(op_info):
                            return True
        
        return False
    
    def _check_loadbalancer_resources(self, op_info: Dict) -> bool:
        """Verificar si hay Load Balancers activos."""
        file_path = op_info.get("file")
        if not file_path:
            return False
        
        full_path = self.raw_dir / file_path
        if not full_path.exists():
            return False
        
        try:
            with gzip.open(full_path, 'rt', encoding='utf-8') as f:
                data = json.load(f)
            
            response_data = data.get("data", {})
            
            # Si es paginado
            if isinstance(response_data, dict) and "pages" in response_data and "data" in response_data:
                pages_list = response_data.get("data", [])
                if isinstance(pages_list, list):
                    for page in pages_list:
                        if isinstance(page, dict):
                            # ELB clásico: LoadBalancerDescriptions, ELBv2: LoadBalancers
                            balancers = page.get("LoadBalancerDescriptions", []) or page.get("LoadBalancers", [])
                            if isinstance(balancers, list) and len(balancers) > 0:
                                return True
            
            # Si no es paginado
            elif isinstance(response_data, dict):
                balancers = response_data.get("LoadBalancerDescriptions", []) or response_data.get("LoadBalancers", [])
                if isinstance(balancers, list) and len(balancers) > 0:
                    return True
                
        except Exception as e:
            logger.debug(f"Error leyendo archivo Load Balancer: {e}")
        
        return False
    
    def _check_route53_in_use(self, services: Dict) -> bool:
        """Verificar si Route 53 está realmente en uso."""
        if "route53" not in services:
            return False
        
        service_data = services["route53"]
        regions = service_data.get("regions", {})
        
        # Route 53 es global, pero puede estar en cualquier región
        for region_name, region_data in regions.items():
            operations = region_data.get("operations", [])
            
            # Buscar ListHostedZones
            for op_info in operations:
                op_name = op_info.get("operation", "").lower()
                if op_name == "listhostedzones" and op_info.get("success", False):
                    if self._check_route53_resources(op_info):
                        return True
        
        return False
    
    def _check_route53_resources(self, op_info: Dict) -> bool:
        """Verificar si Route 53 tiene hosted zones activas."""
        file_path = op_info.get("file")
        if not file_path:
            return False
        
        full_path = self.raw_dir / file_path
        if not full_path.exists():
            return False
        
        try:
            with gzip.open(full_path, 'rt', encoding='utf-8') as f:
                data = json.load(f)
            
            response_data = data.get("data", {})
            
            # Si es paginado
            if isinstance(response_data, dict) and "pages" in response_data and "data" in response_data:
                pages_list = response_data.get("data", [])
                if isinstance(pages_list, list):
                    for page in pages_list:
                        if isinstance(page, dict):
                            zones = page.get("HostedZones", [])
                            if isinstance(zones, list) and len(zones) > 0:
                                return True
            
            # Si no es paginado
            elif isinstance(response_data, dict):
                zones = response_data.get("HostedZones", [])
                if isinstance(zones, list) and len(zones) > 0:
                    return True
                
        except Exception as e:
            logger.debug(f"Error leyendo archivo Route 53: {e}")
        
        return False
    
    def _generate_operational_evidence(self, index: Dict) -> Dict:
        """Generar evidencias de excelencia operacional."""
        evidence = []
        questions = []
        
        services = index.get("services", {})
        
        # CloudWatch - Verificar si está realmente en uso
        cloudwatch_in_use = self._check_cloudwatch_in_use(services)
        if cloudwatch_in_use:
            evidence.append({
                "type": "service_present",
                "service": "CloudWatch",
                "status": "detected",
                "description": "CloudWatch está en uso"
            })
            questions.append("¿Se están usando métricas personalizadas?")
            questions.append("¿Hay dashboards configurados?")
            questions.append("¿Se están configurando alarmas para métricas críticas?")
        else:
            evidence.append({
                "type": "service_missing",
                "service": "CloudWatch",
                "status": "not_detected",
                "description": "CloudWatch no está en uso o no tiene recursos configurados",
                "gap": "Falta de monitoreo y observabilidad"
            })
        
        # Systems Manager - Verificar si está realmente en uso
        ssm_in_use = self._check_ssm_in_use(services)
        if ssm_in_use:
            evidence.append({
                "type": "service_present",
                "service": "Systems Manager",
                "status": "detected",
                "description": "Systems Manager está en uso"
            })
            questions.append("¿Se está usando SSM para gestión de instancias?")
            questions.append("¿Se están usando SSM Documents para automatización?")
        else:
            evidence.append({
                "type": "service_missing",
                "service": "Systems Manager",
                "status": "not_detected",
                "description": "Systems Manager no está en uso o no tiene recursos configurados",
                "gap": "Falta de gestión centralizada de instancias"
            })
        
        # CloudFormation - Verificar si está realmente en uso
        cloudformation_in_use = self._check_cloudformation_in_use(services)
        if cloudformation_in_use:
            evidence.append({
                "type": "service_present",
                "service": "CloudFormation",
                "status": "detected",
                "description": "CloudFormation está en uso"
            })
            questions.append("¿Se está usando Infrastructure as Code para todos los recursos?")
            questions.append("¿Se están usando StackSets para múltiples cuentas/regiones?")
        else:
            evidence.append({
                "type": "service_missing",
                "service": "CloudFormation",
                "status": "not_detected",
                "description": "CloudFormation no está en uso o no tiene stacks activos",
                "gap": "Posible falta de Infrastructure as Code"
            })
        
        return {
            "evidence": evidence,
            "questions": questions,
            "summary": f"{len([e for e in evidence if e.get('status') == 'detected'])} servicios operacionales detectados"
        }
    
    def _generate_cost_evidence(self, index: Dict) -> Dict:
        """Generar evidencias de optimización de costos."""
        evidence = []
        questions = []
        
        services = index.get("services", {})
        regions = index.get("regions", [])
        
        # Cost Explorer
        if "ce" in services or "cost-explorer" in services:
            evidence.append({
                "type": "service_present",
                "service": "Cost Explorer",
                "status": "detected",
                "description": "Cost Explorer está accesible"
            })
            questions.append("¿Se están revisando regularmente los costos?")
            questions.append("¿Hay budgets configurados?")
        else:
            evidence.append({
                "type": "service_missing",
                "service": "Cost Explorer",
                "status": "not_detected",
                "description": "Cost Explorer no accesible",
                "gap": "Limitada visibilidad de costos"
            })
        
        # Múltiples regiones
        if len(regions) > 3:
            evidence.append({
                "type": "observation",
                "category": "multi_region",
                "description": f"{len(regions)} regiones activas detectadas",
                "impact": "Posibles costos de transferencia de datos entre regiones"
            })
            questions.append("¿Es necesario tener recursos en todas estas regiones?")
            questions.append("¿Se están optimizando los costos de transferencia de datos?")
        
        # Reserved Instances / Savings Plans
        if "ec2" in services:
            evidence.append({
                "type": "review_required",
                "category": "reserved_instances",
                "description": "Revisar oportunidad de Reserved Instances o Savings Plans",
                "suggested_review": [
                    "Analizar uso de instancias EC2",
                    "Evaluar Reserved Instances vs Savings Plans",
                    "Revisar instancias que podrían usar tipos más económicos"
                ]
            })
            questions.append("¿Se están usando Reserved Instances o Savings Plans?")
            questions.append("¿Se han evaluado instancias que podrían usar tipos más económicos?")
        
        return {
            "evidence": evidence,
            "questions": questions,
            "summary": f"{len(regions)} regiones activas, {len([e for e in evidence if e.get('status') == 'detected'])} servicios de costo detectados"
        }
    
    def _generate_performance_evidence(self, index: Dict) -> Dict:
        """Generar evidencias de eficiencia de rendimiento."""
        evidence = []
        questions = []
        
        services = index.get("services", {})
        
        # CloudFront
        if "cloudfront" in services:
            evidence.append({
                "type": "service_present",
                "service": "CloudFront",
                "status": "detected",
                "description": "CloudFront está en uso"
            })
            questions.append("¿Las distribuciones CloudFront están optimizadas?")
            questions.append("¿Se están usando cache policies adecuadas?")
        
        # Auto Scaling (también relevante para performance) - Verificar si está realmente en uso
        autoscaling_in_use = self._check_autoscaling_in_use(services)
        if autoscaling_in_use:
            evidence.append({
                "type": "service_present",
                "service": "Auto Scaling",
                "status": "detected",
                "description": "Auto Scaling puede ayudar con performance"
            })
            questions.append("¿Las políticas de escalado responden adecuadamente a la carga?")
        
        return {
            "evidence": evidence,
            "questions": questions,
            "summary": f"{len([e for e in evidence if e.get('status') == 'detected'])} servicios de performance detectados"
        }
    
    def _generate_sustainability_evidence(self, index: Dict) -> Dict:
        """Generar evidencias de sostenibilidad."""
        evidence = []
        questions = []
        
        services = index.get("services", {})
        regions = index.get("regions", [])
        
        # Regiones (usar regiones más eficientes energéticamente)
        evidence.append({
            "type": "observation",
            "category": "regions",
            "description": f"{len(regions)} regiones en uso",
            "suggestion": "Considerar usar regiones con energía renovable cuando sea posible"
        })
        questions.append("¿Se han considerado regiones con energía renovable?")
        
        # Auto Scaling (relevante para sostenibilidad - usar solo recursos necesarios) - Verificar si está realmente en uso
        autoscaling_in_use = self._check_autoscaling_in_use(services)
        if autoscaling_in_use:
            evidence.append({
                "type": "service_present",
                "service": "Auto Scaling",
                "status": "detected",
                "description": "Auto Scaling ayuda a usar solo recursos necesarios"
            })
        
        # Lambda (serverless = más eficiente)
        if "lambda" in services:
            evidence.append({
                "type": "service_present",
                "service": "Lambda",
                "status": "detected",
                "description": "Lambda (serverless) es más eficiente energéticamente"
            })
            questions.append("¿Se están usando servicios serverless cuando es posible?")
        
        return {
            "evidence": evidence,
            "questions": questions,
            "summary": f"{len([e for e in evidence if e.get('status') == 'detected'])} servicios relevantes para sostenibilidad"
        }
    
    def _get_account_id(self) -> str:
        """Obtener account ID desde metadata."""
        metadata_file = self.run_dir / "metadata.json"
        if metadata_file.exists():
            try:
                with open(metadata_file, 'r') as f:
                    metadata = json.load(f)
                    return metadata.get("account_id", "N/A")
            except:
                pass
        return "N/A"
    
    def _save_evidence_pack(self, evidence_pack: Dict):
        """Guardar evidence pack en formato Markdown y JSON."""
        # JSON
        json_file = self.output_dir / "evidence_pack.json"
        with open(json_file, 'w') as f:
            json.dump(evidence_pack, f, indent=2, default=str)
        logger.info(f"Evidence pack JSON guardado: {json_file}")
        
        # Markdown
        md_file = self.output_dir / "evidence_pack.md"
        md_content = self._generate_markdown(evidence_pack)
        with open(md_file, 'w') as f:
            f.write(md_content)
        logger.info(f"Evidence pack Markdown guardado: {md_file}")
    
    def _generate_markdown(self, evidence_pack: Dict) -> str:
        """Generar contenido Markdown del evidence pack."""
        lines = []
        lines.append("# Well-Architected Framework - Evidence Pack")
        lines.append("")
        lines.append(f"**Generado:** {evidence_pack['metadata']['generated_at']}")
        lines.append(f"**Account ID:** {evidence_pack['metadata']['account_id']}")
        lines.append("")
        
        for pillar, pillar_data in evidence_pack["pillars"].items():
            lines.append(f"## {pillar}")
            lines.append("")
            lines.append(f"**Resumen:** {pillar_data.get('summary', 'N/A')}")
            lines.append("")
            
            # Evidencias
            lines.append("### Evidencias")
            lines.append("")
            for evidence in pillar_data.get("evidence", []):
                ev_type = evidence.get("type", "unknown")
                status = evidence.get("status", "")
                desc = evidence.get("description", "")
                
                if status == "detected":
                    lines.append(f"- ✅ **{evidence.get('service', 'N/A')}**: {desc}")
                elif status == "not_detected":
                    lines.append(f"- ❌ **{evidence.get('service', 'N/A')}**: {desc}")
                    if "gap" in evidence:
                        lines.append(f"  - *Gap:* {evidence['gap']}")
                else:
                    lines.append(f"- ℹ️ **{evidence.get('category', 'N/A')}**: {desc}")
            
            lines.append("")
            
            # Preguntas
            lines.append("### Preguntas Sugeridas para Workshop")
            lines.append("")
            for i, question in enumerate(pillar_data.get("questions", []), 1):
                lines.append(f"{i}. {question}")
            
            lines.append("")
            lines.append("---")
            lines.append("")
        
        return "\n".join(lines)


def main():
    """Punto de entrada principal."""
    parser = argparse.ArgumentParser(
        description="ECAD Evidence Generator - Generación de evidence pack Well-Architected"
    )
    parser.add_argument(
        "--run-dir",
        required=True,
        help="Directorio del run a analizar"
    )
    
    args = parser.parse_args()
    
    if not Path(args.run_dir).exists():
        logger.error(f"Directorio no existe: {args.run_dir}")
        sys.exit(1)
    
    generator = EvidenceGenerator(args.run_dir)
    
    try:
        generator.generate()
        sys.exit(0)
    except Exception as e:
        logger.error(f"Error generando evidence pack: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()

