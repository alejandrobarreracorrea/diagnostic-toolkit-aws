"""
Findings Generator - Generación de hallazgos arquitectónicos.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Any
from collections import defaultdict

logger = logging.getLogger(__name__)


class FindingsGenerator:
    """Generador de hallazgos arquitectónicos."""
    
    def __init__(self, index_dir: Path, output_dir: Path):
        self.index_dir = index_dir
        self.output_dir = output_dir
    
    def generate(self) -> Dict:
        """Generar hallazgos arquitectónicos."""
        # Cargar índice
        index_file = self.index_dir / "index.json"
        if not index_file.exists():
            logger.error(f"Índice no encontrado: {index_file}")
            return {"findings": []}
        
        with open(index_file, 'r') as f:
            index = json.load(f)
        
        findings = []
        
        # Generar hallazgos por dominio
        findings.extend(self._find_security_issues(index))
        findings.extend(self._find_reliability_issues(index))
        findings.extend(self._find_cost_issues(index))
        findings.extend(self._find_operational_issues(index))
        
        # Clasificar por severidad
        findings_by_severity = defaultdict(list)
        for finding in findings:
            findings_by_severity[finding["severity"]].append(finding)
        
        result = {
            "findings": findings,
            "findings_by_severity": {
                severity: len(findings_list)
                for severity, findings_list in findings_by_severity.items()
            },
            "total_findings": len(findings)
        }
        
        # Guardar hallazgos
        findings_file = self.output_dir / "findings.json"
        with open(findings_file, 'w') as f:
            json.dump(result, f, indent=2, default=str)
        logger.info(f"Hallazgos guardados: {findings_file} ({len(findings)} hallazgos)")
        
        return result
    
    def _find_security_issues(self, index: Dict) -> List[Dict]:
        """Encontrar problemas de seguridad."""
        findings = []
        
        # Verificar presencia de servicios de seguridad
        services = index.get("services", {})
        
        # Security Hub
        if "securityhub" not in services:
            findings.append({
                "id": "SEC-001",
                "domain": "Security",
                "severity": "medium",
                "title": "Security Hub no detectado",
                "description": "AWS Security Hub no está habilitado o no se pudo acceder. Security Hub proporciona una vista centralizada del estado de seguridad.",
                "recommendation": "Habilitar AWS Security Hub para obtener visibilidad centralizada del estado de seguridad.",
                "impact": "Baja visibilidad del estado de seguridad de la cuenta",
                "effort": "Bajo"
            })
        
        # Config
        if "config" not in services:
            findings.append({
                "id": "SEC-002",
                "domain": "Security",
                "severity": "medium",
                "title": "AWS Config no detectado",
                "description": "AWS Config no está habilitado o no se pudo acceder. Config permite auditoría y cumplimiento continuo.",
                "recommendation": "Habilitar AWS Config para auditoría y cumplimiento continuo.",
                "impact": "Falta de visibilidad de cambios de configuración",
                "effort": "Medio"
            })
        
        # CloudTrail
        if "cloudtrail" not in services:
            findings.append({
                "id": "SEC-003",
                "domain": "Security",
                "severity": "high",
                "title": "CloudTrail no detectado",
                "description": "AWS CloudTrail no está habilitado o no se pudo acceder. CloudTrail es esencial para auditoría y cumplimiento.",
                "recommendation": "Habilitar CloudTrail en todas las regiones para registro de actividad de API.",
                "impact": "Falta de auditoría de actividad de API",
                "effort": "Bajo"
            })
        
        return findings
    
    def _find_reliability_issues(self, index: Dict) -> List[Dict]:
        """Encontrar problemas de confiabilidad."""
        findings = []
        
        services = index.get("services", {})
        
        # RDS - verificar si hay instancias (requiere análisis más profundo)
        # Por ahora, solo verificamos si el servicio está presente
        if "rds" in services:
            findings.append({
                "id": "REL-001",
                "domain": "Reliability",
                "severity": "info",
                "title": "RDS detectado - Verificar configuración Multi-AZ",
                "description": "Se detectó uso de RDS. Se recomienda verificar que las instancias críticas estén configuradas con Multi-AZ para alta disponibilidad.",
                "recommendation": "Revisar configuración de instancias RDS y habilitar Multi-AZ para bases de datos críticas.",
                "impact": "Posible falta de alta disponibilidad en bases de datos",
                "effort": "Medio"
            })
        
        # Auto Scaling Groups
        if "autoscaling" in services:
            findings.append({
                "id": "REL-002",
                "domain": "Reliability",
                "severity": "info",
                "title": "Auto Scaling detectado",
                "description": "Se detectó uso de Auto Scaling Groups. Verificar configuración de health checks y políticas de escalado.",
                "recommendation": "Revisar configuración de Auto Scaling Groups para asegurar escalado adecuado.",
                "impact": "Potencial mejora en confiabilidad y disponibilidad",
                "effort": "Bajo"
            })
        else:
            # Si hay EC2 pero no Auto Scaling
            if "ec2" in services:
                findings.append({
                    "id": "REL-003",
                    "domain": "Reliability",
                    "severity": "medium",
                    "title": "EC2 sin Auto Scaling detectado",
                    "description": "Se detectó uso de EC2 pero no se detectó Auto Scaling Groups. Esto puede indicar falta de escalado automático.",
                    "recommendation": "Considerar implementar Auto Scaling Groups para instancias EC2 que requieren alta disponibilidad.",
                    "impact": "Falta de escalado automático y recuperación automática",
                    "effort": "Medio"
                })
        
        return findings
    
    def _find_cost_issues(self, index: Dict) -> List[Dict]:
        """Encontrar problemas de costo."""
        findings = []
        
        services = index.get("services", {})
        
        # Cost Explorer - verificar acceso
        if "ce" not in services and "cost-explorer" not in services:
            findings.append({
                "id": "COST-001",
                "domain": "Cost Optimization",
                "severity": "low",
                "title": "Cost Explorer no detectado o sin acceso",
                "description": "No se pudo acceder a Cost Explorer. Esto puede limitar la visibilidad de costos.",
                "recommendation": "Habilitar acceso a Cost Explorer para análisis de costos detallado.",
                "impact": "Limitada visibilidad de costos",
                "effort": "Bajo"
            })
        
        # Múltiples regiones activas
        regions = index.get("regions", [])
        if len(regions) > 5:
            findings.append({
                "id": "COST-002",
                "domain": "Cost Optimization",
                "severity": "info",
                "title": "Múltiples regiones activas detectadas",
                "description": f"Se detectaron {len(regions)} regiones activas. Esto puede aumentar costos de transferencia de datos.",
                "recommendation": "Revisar uso de regiones y considerar consolidación si es posible.",
                "impact": "Posibles costos de transferencia de datos entre regiones",
                "effort": "Alto"
            })
        
        return findings
    
    def _find_operational_issues(self, index: Dict) -> List[Dict]:
        """Encontrar problemas operacionales."""
        findings = []
        
        services = index.get("services", {})
        
        # CloudWatch
        if "cloudwatch" not in services and "logs" not in services:
            findings.append({
                "id": "OPS-001",
                "domain": "Operational Excellence",
                "severity": "medium",
                "title": "CloudWatch/Logs no detectado",
                "description": "No se detectó uso de CloudWatch o CloudWatch Logs. Esto limita el monitoreo y observabilidad.",
                "recommendation": "Habilitar CloudWatch y CloudWatch Logs para monitoreo y observabilidad.",
                "impact": "Falta de monitoreo y observabilidad",
                "effort": "Medio"
            })
        
        # Systems Manager
        if "ssm" not in services:
            findings.append({
                "id": "OPS-002",
                "domain": "Operational Excellence",
                "severity": "low",
                "title": "Systems Manager no detectado",
                "description": "AWS Systems Manager no está habilitado o no se pudo acceder. SSM proporciona gestión centralizada de instancias.",
                "recommendation": "Considerar habilitar Systems Manager para gestión centralizada de instancias EC2.",
                "impact": "Falta de gestión centralizada de instancias",
                "effort": "Medio"
            })
        
        return findings


