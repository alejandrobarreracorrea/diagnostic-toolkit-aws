#!/usr/bin/env python3
"""
Report Generator - Generación de reportes ejecutivos desde templates.
"""

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any
from datetime import datetime
from jinja2 import Template

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ReportGenerator:
    """Generador de reportes ejecutivos."""
    
    def __init__(self, run_dir: str, templates_dir: Path):
        self.run_dir = Path(run_dir)
        self.templates_dir = templates_dir
        self.output_dir = self.run_dir / "outputs" / "reports"
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_all(self):
        """Generar todos los reportes."""
        # Cargar datos
        data = self._load_data()
        
        # Si no hay índice, intentar generarlo primero
        if not data.get("index", {}).get("services"):
            logger.warning("No se encontró índice. Ejecutando analyzer primero...")
            try:
                from analyzer.main import Analyzer
                analyzer = Analyzer(str(self.run_dir))
                analyzer.analyze()
                # Recargar datos después de generar índice
                data = self._load_data()
            except Exception as e:
                logger.error(f"Error ejecutando analyzer: {e}")
        
        # Generar reportes
        self._generate_executive_summary(data)
        self._generate_findings_report(data)
        self._generate_roadmap(data)
        self._generate_technical_annex(data)
        self._generate_scorecard(data)
        self._generate_inventory_report(data)
        
        logger.info(f"Reportes generados en: {self.output_dir}")
    
    def _load_data(self) -> Dict:
        """Cargar todos los datos necesarios para reportes."""
        data = {}
        
        # Cargar índice
        index_file = self.run_dir / "index" / "index.json"
        if index_file.exists():
            try:
                with open(index_file, 'r') as f:
                    data["index"] = json.load(f)
            except Exception as e:
                logger.warning(f"Error cargando índice: {e}")
                data["index"] = {}
        else:
            logger.warning(f"Índice no encontrado: {index_file}")
            data["index"] = {}
        
        # Cargar inventario
        inventory_file = self.run_dir / "outputs" / "inventory" / "inventory.json"
        if inventory_file.exists():
            try:
                with open(inventory_file, 'r') as f:
                    data["inventory"] = json.load(f)
            except Exception as e:
                logger.warning(f"Error cargando inventario: {e}")
                data["inventory"] = {}
        else:
            logger.warning(f"Inventario no encontrado: {inventory_file}")
            data["inventory"] = {}
        
        # Cargar hallazgos
        findings_file = self.run_dir / "outputs" / "findings.json"
        if findings_file.exists():
            try:
                with open(findings_file, 'r') as f:
                    data["findings"] = json.load(f)
            except Exception as e:
                logger.warning(f"Error cargando hallazgos: {e}")
                data["findings"] = {}
        else:
            data["findings"] = {}
        
        # Cargar metadatos
        metadata_file = self.run_dir / "metadata.json"
        if metadata_file.exists():
            try:
                with open(metadata_file, 'r') as f:
                    data["metadata"] = json.load(f)
            except Exception as e:
                logger.warning(f"Error cargando metadatos: {e}")
                data["metadata"] = {}
        else:
            data["metadata"] = {}
        
        # Cargar estadísticas
        stats_file = self.run_dir / "collection_stats.json"
        if stats_file.exists():
            try:
                with open(stats_file, 'r') as f:
                    data["stats"] = json.load(f)
            except Exception as e:
                logger.warning(f"Error cargando estadísticas: {e}")
                data["stats"] = {}
        else:
            data["stats"] = {}
        
        return data
    
    def _generate_executive_summary(self, data: Dict):
        """Generar resumen ejecutivo."""
        template_file = self.templates_dir / "executive_summary.md"
        if not template_file.exists():
            logger.warning(f"Template no encontrado: {template_file}")
            return
        
        with open(template_file, 'r') as f:
            template = Template(f.read())
        
        # Obtener servicios desde índice si no hay inventario
        index = data.get("index", {})
        inventory = data.get("inventory", {})
        
        # Si no hay inventario, usar información del índice
        if not inventory.get("services"):
            # Generar top servicios desde índice
            services = index.get("services", {})
            service_counts = []
            for service_name, service_data in services.items():
                total_ops = service_data.get("total_operations", 0)
                if total_ops > 0:
                    service_counts.append({"service": service_name, "count": total_ops})
            service_counts.sort(key=lambda x: x["count"], reverse=True)
            top_services = service_counts[:5]
        else:
            top_services = inventory.get("top_services", [])[:5]
        
        # Regiones desde índice
        regions_from_index = index.get("regions", [])
        if not inventory.get("regions") and regions_from_index:
            top_regions = [{"region": r, "count": 0} for r in regions_from_index[:5]]
        else:
            top_regions = inventory.get("top_regions", [])[:5]
        
        context = {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "account_id": data.get("metadata", {}).get("account_id", "N/A"),
            "account_alias": data.get("metadata", {}).get("account_alias", "N/A"),
            "services_count": len(index.get("services", {})),
            "regions_count": len(regions_from_index) if regions_from_index else len(inventory.get("regions", [])),
            "total_resources": inventory.get("total_resources", 0) if inventory else 0,
            "findings_count": data.get("findings", {}).get("total_findings", 0),
            "top_services": top_services,
            "top_regions": top_regions,
        }
        
        output = template.render(**context)
        output_file = self.output_dir / "executive_summary.md"
        with open(output_file, 'w') as f:
            f.write(output)
        logger.info(f"Resumen ejecutivo generado: {output_file}")
    
    def _generate_findings_report(self, data: Dict):
        """Generar reporte de hallazgos."""
        template_file = self.templates_dir / "findings_report.md"
        if not template_file.exists():
            logger.warning(f"Template no encontrado: {template_file}")
            return
        
        with open(template_file, 'r') as f:
            template = Template(f.read())
        
        findings = data.get("findings", {}).get("findings", [])
        
        # Agrupar por dominio y severidad
        findings_by_domain = {}
        for finding in findings:
            domain = finding.get("domain", "Other")
            if domain not in findings_by_domain:
                findings_by_domain[domain] = []
            findings_by_domain[domain].append(finding)
        
        context = {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "total_findings": len(findings),
            "findings_by_severity": data.get("findings", {}).get("findings_by_severity", {}),
            "findings_by_domain": findings_by_domain,
            "all_findings": findings
        }
        
        output = template.render(**context)
        output_file = self.output_dir / "findings_report.md"
        with open(output_file, 'w') as f:
            f.write(output)
        logger.info(f"Reporte de hallazgos generado: {output_file}")
    
    def _generate_roadmap(self, data: Dict):
        """Generar roadmap 30/60/90."""
        template_file = self.templates_dir / "roadmap.md"
        if not template_file.exists():
            logger.warning(f"Template no encontrado: {template_file}")
            return
        
        with open(template_file, 'r') as f:
            template = Template(f.read())
        
        findings = data.get("findings", {}).get("findings", [])
        
        # Clasificar hallazgos por esfuerzo y severidad para roadmap
        roadmap_30 = [f for f in findings if f.get("effort") == "Bajo" and f.get("severity") in ["high", "medium"]]
        roadmap_60 = [f for f in findings if f.get("effort") == "Medio"]
        roadmap_90 = [f for f in findings if f.get("effort") == "Alto"]
        
        context = {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "roadmap_30": roadmap_30[:10],
            "roadmap_60": roadmap_60[:10],
            "roadmap_90": roadmap_90[:10]
        }
        
        output = template.render(**context)
        output_file = self.output_dir / "roadmap_30_60_90.md"
        with open(output_file, 'w') as f:
            f.write(output)
        logger.info(f"Roadmap generado: {output_file}")
    
    def _generate_technical_annex(self, data: Dict):
        """Generar anexo técnico."""
        template_file = self.templates_dir / "technical_annex.md"
        if not template_file.exists():
            logger.warning(f"Template no encontrado: {template_file}")
            return
        
        with open(template_file, 'r') as f:
            template = Template(f.read())
        
        index = data.get("index", {})
        inventory = data.get("inventory", {})
        
        # Si no hay inventario, generar información básica desde índice
        if not inventory:
            # Crear inventario básico desde índice
            services_info = {}
            for service_name, service_data in index.get("services", {}).items():
                services_info[service_name] = {
                    "name": service_name,
                    "regions": list(service_data.get("regions", {}).keys()),
                    "operations": list(service_data.get("operations", [])),
                    "total_operations": service_data.get("total_operations", 0),
                    "resource_count": 0  # No podemos contar sin datos exitosos
                }
            
            inventory = {
                "services": services_info,
                "regions": {},
                "total_resources": 0,
                "top_services": [],
                "top_regions": []
            }
        
        context = {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "services": index.get("services", {}),
            "regions": index.get("regions", []),
            "inventory": inventory,
            "stats": data.get("stats", {})
        }
        
        output = template.render(**context)
        output_file = self.output_dir / "technical_annex.md"
        with open(output_file, 'w') as f:
            f.write(output)
        logger.info(f"Anexo técnico generado: {output_file}")
    
    def _generate_scorecard(self, data: Dict):
        """Generar scorecard por dominio."""
        template_file = self.templates_dir / "scorecard.md"
        if not template_file.exists():
            logger.warning(f"Template no encontrado: {template_file}")
            return
        
        with open(template_file, 'r') as f:
            template = Template(f.read())
        
        findings = data.get("findings", {}).get("findings", [])
        
        # Calcular scores por dominio
        domains = ["Security", "Reliability", "Performance Efficiency", "Cost Optimization", "Operational Excellence", "Sustainability"]
        domain_scores = {}
        
        for domain in domains:
            domain_findings = [f for f in findings if f.get("domain") == domain]
            if not domain_findings:
                score = 5  # Sin hallazgos = score perfecto
            else:
                # Calcular score basado en severidad (5 = perfecto, 1 = crítico)
                severity_weights = {"high": -2, "medium": -1, "low": -0.5, "info": 0}
                base_score = 5
                for finding in domain_findings:
                    base_score += severity_weights.get(finding.get("severity", "info"), 0)
                score = max(1, min(5, int(base_score)))
            domain_scores[domain] = score
        
        context = {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "domain_scores": domain_scores,
            "average_score": sum(domain_scores.values()) / len(domain_scores) if domain_scores else 0
        }
        
        output = template.render(**context)
        output_file = self.output_dir / "scorecard.md"
        with open(output_file, 'w') as f:
            f.write(output)
        logger.info(f"Scorecard generado: {output_file}")
    
    def _generate_inventory_report(self, data: Dict):
        """Generar reporte de inventario detallado."""
        template_file = self.templates_dir / "inventory_report.md"
        if not template_file.exists():
            logger.warning(f"Template no encontrado: {template_file}")
            return
        
        with open(template_file, 'r') as f:
            template = Template(f.read())
        
        index = data.get("index", {})
        inventory = data.get("inventory", {})
        stats = data.get("stats", {})
        
        # Preparar datos de servicios
        services_data = {}
        total_operations = 0
        total_resources = 0
        
        for service_name, service_data in index.get("services", {}).items():
            successful_ops = 0
            failed_ops = 0
            resource_count = 0
            
            for region_name, region_data in service_data.get("regions", {}).items():
                for op_info in region_data.get("operations", []):
                    if op_info.get("success"):
                        successful_ops += 1
                        resource_count += op_info.get("resource_count", 0)
                    else:
                        failed_ops += 1
            
            # Preparar datos de regiones para el template
            regions_dict = service_data.get("regions", {})
            if isinstance(regions_dict, dict):
                regions_list = list(regions_dict.keys())
                regions_data_for_template = regions_dict  # Mantener dict para el template
            else:
                regions_list = regions_dict if isinstance(regions_dict, list) else []
                regions_data_for_template = {}
            
            # Preparar operaciones
            operations_set = service_data.get("operations", set())
            if isinstance(operations_set, str):
                # Si es string (serializado), parsearlo
                import ast
                try:
                    operations_list = list(ast.literal_eval(operations_set))
                except:
                    operations_list = []
            elif isinstance(operations_set, set):
                operations_list = list(operations_set)
            else:
                operations_list = list(operations_set) if operations_set else []
            
            services_data[service_name] = {
                "regions": regions_list,  # Lista para mostrar
                "regions_data": regions_data_for_template,  # Dict para el template
                "operations": operations_list,
                "total_operations": service_data.get("total_operations", 0),
                "successful_operations": successful_ops,
                "failed_operations": failed_ops,
                "resource_count": resource_count
            }
            total_operations += service_data.get("total_operations", 0)
            total_resources += resource_count
        
        # Ordenar servicios por nombre para la tabla
        services_sorted = dict(sorted(services_data.items()))
        
        # Top servicios por operaciones
        top_services_by_ops = sorted(
            [
                {"service": name, "count": data.get("total_operations", 0)}
                for name, data in services_data.items()
            ],
            key=lambda x: x["count"],
            reverse=True
        )[:20]
        
        # Calcular estadísticas para el resumen
        services_with_success = sum(1 for s in services_data.values() if s.get("successful_operations", 0) > 0)
        services_with_errors = sum(1 for s in services_data.values() if s.get("failed_operations", 0) > 0)
        services_without_data = sum(1 for s in services_data.values() if s.get("total_operations", 0) == 0)
        
        context = {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "account_id": data.get("metadata", {}).get("account_id", "N/A"),
            "services": services_sorted,  # Servicios ordenados alfabéticamente
            "services_count": len(services_data),
            "regions": index.get("regions", []),
            "regions_count": len(index.get("regions", [])),
            "total_operations": total_operations,
            "total_resources": total_resources if inventory else 0,
            "top_services_by_operations": top_services_by_ops,
            "stats": stats,
            "stats_summary": {
                "services_with_success": services_with_success,
                "services_with_errors": services_with_errors,
                "services_without_data": services_without_data
            }
        }
        
        output = template.render(**context)
        output_file = self.output_dir / "inventory_report.md"
        with open(output_file, 'w') as f:
            f.write(output)
        logger.info(f"Reporte de inventario generado: {output_file}")


def main():
    """Punto de entrada principal."""
    parser = argparse.ArgumentParser(
        description="ECAD Report Generator - Generación de reportes ejecutivos"
    )
    parser.add_argument(
        "--run-dir",
        required=True,
        help="Directorio del run a analizar"
    )
    parser.add_argument(
        "--templates-dir",
        default="./templates",
        help="Directorio de templates (default: ./templates)"
    )
    
    args = parser.parse_args()
    
    if not Path(args.run_dir).exists():
        logger.error(f"Directorio no existe: {args.run_dir}")
        sys.exit(1)
    
    generator = ReportGenerator(args.run_dir, Path(args.templates_dir))
    
    try:
        generator.generate_all()
        sys.exit(0)
    except Exception as e:
        logger.error(f"Error generando reportes: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()

