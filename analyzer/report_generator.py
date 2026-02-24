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
        self._generate_improvement_plan(data)
        self._generate_technical_annex(data)
        self._generate_scorecard(data)
        self._generate_inventory_report(data)
        self._generate_security_maturity_report(data)
        self._generate_tagging_report(data)
        self._generate_web_unified(data)

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
        
        # Cargar evidence pack (fuente de verdad para scorecard y coherencia)
        evidence_file = self.run_dir / "outputs" / "evidence" / "evidence_pack.json"
        if evidence_file.exists():
            try:
                with open(evidence_file, "r", encoding="utf-8") as f:
                    data["evidence_pack"] = json.load(f)
            except Exception as e:
                logger.warning(f"Error cargando evidence pack: {e}")
                data["evidence_pack"] = {}
        else:
            data["evidence_pack"] = {}
        
        return data
    
    def _generate_executive_summary(self, data: Dict):
        """Generar resumen ejecutivo."""
        template_file = self.templates_dir / "executive_summary.md"
        if not template_file.exists():
            logger.warning(f"Template no encontrado: {template_file}")
            return
        
        with open(template_file, 'r', encoding='utf-8') as f:
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
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(output)
        logger.info(f"Resumen ejecutivo generado: {output_file}")
    
    def _generate_findings_report(self, data: Dict):
        """Generar reporte de hallazgos."""
        template_file = self.templates_dir / "findings_report.md"
        if not template_file.exists():
            logger.warning(f"Template no encontrado: {template_file}")
            return
        
        with open(template_file, 'r', encoding='utf-8') as f:
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
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(output)
        logger.info(f"Reporte de hallazgos generado: {output_file}")
    
    def _generate_improvement_plan(self, data: Dict):
        """Generar Plan de mejoras (Well-Architected Improvement Plan): HRI = pronta solución, MRI por complejidad media/alto."""
        template_file = self.templates_dir / "improvement_plan.md"
        if not template_file.exists():
            logger.warning(f"Template no encontrado: {template_file}")
            return
        
        with open(template_file, 'r', encoding='utf-8') as f:
            template = Template(f.read())
        
        findings = data.get("findings", {}).get("findings", [])
        
        # HRI (High Risk Issues) = pronta solución → severidad high
        improvement_plan_hri = [f for f in findings if (f.get("severity") or "").lower() == "high"]
        # MRI (Medium Risk Issues) → severidad medium, low, info. Subclasificar por complejidad según esfuerzo
        mri = [f for f in findings if (f.get("severity") or "").lower() in ("medium", "low", "info")]
        improvement_plan_mri_media = [f for f in mri if (f.get("effort") or "").strip() == "Bajo"]
        improvement_plan_mri_alto = [f for f in mri if (f.get("effort") or "").strip() in ("Medio", "Alto")]
        
        context = {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "improvement_plan_hri": improvement_plan_hri[:20],
            "improvement_plan_mri_media": improvement_plan_mri_media[:20],
            "improvement_plan_mri_alto": improvement_plan_mri_alto[:20],
        }
        
        output = template.render(**context)
        output_file = self.output_dir / "improvement_plan.md"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(output)
        logger.info(f"Plan de mejoras generado: {output_file}")
    
    def _generate_technical_annex(self, data: Dict):
        """Generar anexo técnico."""
        template_file = self.templates_dir / "technical_annex.md"
        if not template_file.exists():
            logger.warning(f"Template no encontrado: {template_file}")
            return
        
        with open(template_file, 'r', encoding='utf-8') as f:
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
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(output)
        logger.info(f"Anexo técnico generado: {output_file}")
    
    def _scores_from_evidence_pack(self, evidence_pack: Dict) -> Dict[str, int]:
        """Calcular scores 1-5 por pilar desde evidence pack (coherente con evidencias)."""
        compliance_to_points = {
            "compliant": 5,
            "partially_compliant": 4,
            "not_compliant": 2,
            "not_applicable": None,  # no cuenta en el promedio
        }
        domains = ["Operational Excellence", "Security", "Reliability", "Performance Efficiency", "Cost Optimization", "Sustainability"]
        domain_scores = {}
        pillars = evidence_pack.get("pillars", {})
        for domain in domains:
            pillar_data = pillars.get(domain, {})
            questions = pillar_data.get("well_architected_questions", [])
            points = []
            for q in questions:
                st = q.get("compliance", {}).get("status", "not_applicable")
                pt = compliance_to_points.get(st)
                if pt is not None:
                    points.append(pt)
            if points:
                domain_scores[domain] = max(1, min(5, round(sum(points) / len(points))))
            else:
                domain_scores[domain] = 5
        return domain_scores

    def _generate_scorecard(self, data: Dict):
        """Generar scorecard por dominio (prioriza evidence pack para coherencia)."""
        template_file = self.templates_dir / "scorecard.md"
        if not template_file.exists():
            logger.warning(f"Template no encontrado: {template_file}")
            return
        
        with open(template_file, 'r', encoding='utf-8') as f:
            template = Template(f.read())
        
        evidence_pack = data.get("evidence_pack", {})
        domains = ["Security", "Reliability", "Performance Efficiency", "Cost Optimization", "Operational Excellence", "Sustainability"]
        domain_scores = {}
        
        if evidence_pack.get("pillars"):
            domain_scores = self._scores_from_evidence_pack(evidence_pack)
        else:
            findings = data.get("findings", {}).get("findings", [])
            for domain in domains:
                domain_findings = [f for f in findings if f.get("domain") == domain]
                if not domain_findings:
                    score = 5
                else:
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
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(output)
        logger.info(f"Scorecard generado: {output_file}")
    
    def _generate_inventory_report(self, data: Dict):
        """Generar reporte de inventario detallado."""
        template_file = self.templates_dir / "inventory_report.md"
        if not template_file.exists():
            logger.warning(f"Template no encontrado: {template_file}")
            return
        
        with open(template_file, 'r', encoding='utf-8') as f:
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
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(output)
        logger.info(f"Reporte de inventario generado: {output_file}")

    def _generate_security_maturity_report(self, data: Dict) -> None:
        """Generar reporte en Markdown del Modelo de Madurez en Seguridad de AWS (homogéneo con el resto de reportes)."""
        evidence_pack = data.get("evidence_pack", {})
        security_maturity = evidence_pack.get("security_maturity")
        if not security_maturity and data.get("index"):
            try:
                from evidence.security_maturity import evaluate as evaluate_maturity
                security_maturity = evaluate_maturity(data["index"], run_dir=self.run_dir)
            except Exception as e:
                logger.debug("No se pudo evaluar modelo de madurez para reporte: %s", e)
        if not security_maturity or not security_maturity.get("results"):
            return
        lines = [
            "# Modelo de Madurez en Seguridad de AWS",
            "",
            f"Evaluación basada en los datos recolectados por ECAD. Fuente: [Modelo de Madurez en Seguridad de AWS]({security_maturity.get('source', 'https://maturitymodel.security.aws.dev/es/')}) (v2.0).",
            "",
            "Los puntos marcados como **No evaluable** requieren revisión manual (procesos u organización).",
            "",
            "## Resumen por fase",
            "",
        ]
        summary = security_maturity.get("summary", {})
        phases = security_maturity.get("phases", [])
        for phase in phases:
            pid = phase["id"]
            name = phase["name"]
            s = summary.get(pid, {})
            met = s.get("met", 0)
            not_met = s.get("not_met", 0)
            partial = s.get("partial", 0)
            ne = s.get("not_evaluable", 0)
            total = s.get("total", 0)
            lines.append(f"- **{name}**: {met} cumple, {not_met} no cumple, {partial} parcial, {ne} no evaluable ({total} total)")
        lines.extend(["", "---", ""])
        results = security_maturity.get("results", [])
        status_label = {"met": "Cumple", "not_met": "No cumple", "partial": "Parcial", "not_evaluable": "No evaluable"}
        for phase in phases:
            lines.append(f"## {phase['name']}")
            lines.append("")
            lines.append("| Capacidad | Categoría | Estado | Detalle |")
            lines.append("|----------|-----------|--------|--------|")
            for r in results:
                if r["phase"] != phase["id"]:
                    continue
                name_cell = r["name"].replace("|", "\\|")
                cat_cell = (r.get("category") or "").replace("|", "\\|")
                st = status_label.get(r["status"], r["status"])
                detail_cell = (r.get("detail") or "").replace("|", "\\|").replace("\n", " ")
                if len(detail_cell) > 80:
                    detail_cell = detail_cell[:77] + "..."
                lines.append(f"| {name_cell} | {cat_cell} | {st} | {detail_cell} |")
            lines.append("")
        output_file = self.output_dir / "security_maturity.md"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        logger.info(f"Reporte Modelo de Madurez generado: {output_file}")

    def _generate_tagging_report(self, data: Dict) -> None:
        """Generar reporte de tags por servicio (Resource Groups Tagging API)."""
        try:
            from evidence.tagging_evaluator import evaluate as evaluate_tagging
            tagging = evaluate_tagging(data.get("index", {}), run_dir=self.run_dir)
        except Exception as e:
            logger.debug("No se pudo evaluar tagging: %s", e)
            return
        lines = [
            "# Tags por servicio",
            "",
            "Resumen de tags detectados por servicio mediante **Resource Groups Tagging API** (GetResources).",
            "",
        ]
        if tagging.get("error"):
            lines.append(f"**Nota:** {tagging['error']}")
            lines.append("")
            lines.append("Asegúrate de que la política IAM incluya `tag:GetResources`, `tag:GetTagKeys` y `tag:GetTagValues`.")
            lines.append("")
        elif tagging.get("by_service"):
            lines.append(f"- **Total de recursos con tags:** {tagging.get('total_resources', 0)}")
            lines.append(f"- **Claves de tag únicas (todas):** {', '.join(tagging.get('all_tag_keys', [])[:30])}{'...' if len(tagging.get('all_tag_keys', [])) > 30 else ''}")
            lines.append("")
            lines.append("## Por servicio")
            lines.append("")
            lines.append("| Servicio | Recursos | Tags |")
            lines.append("|----------|----------|------|")
            for svc, info in tagging.get("by_service", {}).items():
                keys = info.get("tag_keys", [])
                keys_str = ", ".join(keys[:15]) + ("..." if len(keys) > 15 else "")
                lines.append(f"| {svc} | {info.get('resource_count', 0)} | {keys_str} |")
            lines.append("")
        else:
            lines.append("No se encontraron recursos con tags.")
            lines.append("")
        output_file = self.output_dir / "tagging_report.md"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        logger.info(f"Reporte de tags generado: {output_file}")

    def _security_maturity_to_html(self, security_maturity: Dict) -> str:
        """Generar HTML del modelo de madurez (fallback cuando markdown no está instalado)."""
        import html
        source = security_maturity.get("source", "https://maturitymodel.security.aws.dev/es/")
        lines = [
            f'<p><a href="{html.escape(source)}" target="_blank" rel="noopener">Modelo de Madurez en Seguridad de AWS</a> (v2.0). '
            "Los puntos marcados como <em>No evaluable</em> requieren revisión manual.</p>",
            "<h2>Resumen por fase</h2>",
            "<ul>",
        ]
        for phase in security_maturity.get("phases", []):
            s = security_maturity.get("summary", {}).get(phase["id"], {})
            met, not_met, partial, ne, total = s.get("met", 0), s.get("not_met", 0), s.get("partial", 0), s.get("not_evaluable", 0), s.get("total", 0)
            lines.append(f"<li><strong>{html.escape(phase['name'])}</strong>: {met} cumple, {not_met} no cumple, {partial} parcial, {ne} no evaluable ({total} total)</li>")
        lines.append("</ul>")
        status_label = {"met": "Cumple", "not_met": "No cumple", "partial": "Parcial", "not_evaluable": "No evaluable"}
        for phase in security_maturity.get("phases", []):
            lines.append(f"<h2>{html.escape(phase['name'])}</h2>")
            lines.append("<table><thead><tr><th>Capacidad</th><th>Categoría</th><th>Estado</th><th>Detalle</th></tr></thead><tbody>")
            for r in security_maturity.get("results", []):
                if r["phase"] != phase["id"]:
                    continue
                name = html.escape(r.get("name", ""))
                cat = html.escape(r.get("category", ""))
                st = html.escape(status_label.get(r.get("status", ""), r.get("status", "")))
                detail = html.escape((r.get("detail") or "")[:200])
                lines.append(f"<tr><td>{name}</td><td>{cat}</td><td>{st}</td><td>{detail}</td></tr>")
            lines.append("</tbody></table>")
        return "\n".join(lines)

    def _generate_web_unified(self, data: Dict) -> None:
        """Regenerar reporte web unificado con todos los reportes (Scorecard, Evidence, CAF, Modelo de Madurez, Resumen, Hallazgos, Plan de mejoras)."""
        evidence_pack = data.get("evidence_pack", {})
        if not evidence_pack.get("pillars"):
            logger.debug("Evidence pack sin pilares; no se regenera web unificado.")
            return
        try:
            if not evidence_pack.get("security_maturity") and data.get("index"):
                try:
                    from evidence.security_maturity import evaluate as evaluate_maturity
                    evidence_pack["security_maturity"] = evaluate_maturity(
                        data["index"], run_dir=self.run_dir
                    )
                except Exception as e:
                    logger.debug("No se pudo evaluar modelo de madurez: %s", e)
            reports_dir = Path(self.run_dir).resolve() / "outputs" / "reports"
            extra = {}
            try:
                import markdown
                for key, filename in [
                    ("executive_summary_html", "executive_summary.md"),
                    ("findings_html", "findings_report.md"),
                    ("improvement_plan_html", "improvement_plan.md"),
                    ("security_maturity_html", "security_maturity.md"),
                    ("tagging_html", "tagging_report.md"),
                ]:
                    path = reports_dir / filename
                    if path.exists():
                        with open(path, "r", encoding="utf-8") as f:
                            extra[key] = markdown.markdown(f.read(), extensions=["extra"])
            except ImportError:
                logger.debug("Paquete markdown no instalado; pestañas de reportes mostrarán placeholder. pip install markdown para contenido completo.")
            # Fallback: si no hay security_maturity_html (p. ej. markdown no instalado) pero sí datos, generar HTML desde evidence_pack
            if "security_maturity_html" not in extra and evidence_pack.get("security_maturity", {}).get("results"):
                extra["security_maturity_html"] = self._security_maturity_to_html(evidence_pack["security_maturity"])
            # Fallback simple para tagging_html cuando markdown no está disponible:
            # mostrar el contenido Markdown como texto preformateado para que no quede la pestaña vacía.
            if "tagging_html" not in extra:
                tagging_md = reports_dir / "tagging_report.md"
                if tagging_md.exists():
                    try:
                        import html as _html
                        with open(tagging_md, "r", encoding="utf-8") as f:
                            raw = f.read()
                        extra["tagging_html"] = "<pre>" + _html.escape(raw) + "</pre>"
                    except Exception as e:
                        logger.debug("No se pudo generar fallback HTML para tagging_report.md: %s", e)
            if "improvement_plan_html" not in extra:
                improvement_plan_md = reports_dir / "improvement_plan.md"
                if improvement_plan_md.exists():
                    try:
                        import html as _html
                        with open(improvement_plan_md, "r", encoding="utf-8") as f:
                            raw = f.read()
                        extra["improvement_plan_html"] = "<pre>" + _html.escape(raw) + "</pre>"
                    except Exception as e:
                        logger.debug("No se pudo generar fallback HTML para improvement_plan.md: %s", e)
            from evidence.generator import EvidenceGenerator
            gen = EvidenceGenerator(str(self.run_dir))
            gen._generate_web_report(evidence_pack, extra_reports=extra)
            logger.info("Reporte web unificado actualizado con todos los reportes.")
        except Exception as e:
            logger.warning(f"No se pudo regenerar reporte web unificado: {e}")


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

