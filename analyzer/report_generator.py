#!/usr/bin/env python3
"""
Report Generator - Generación de reportes ejecutivos desde templates.
"""

import argparse
import json
import logging
import re
import sys
import gzip
from pathlib import Path
from typing import Dict, Any, List, Set, Optional
from datetime import datetime
from jinja2 import Template

from evidence import WELL_ARCH_VERSION, WELL_ARCH_DOC_URL

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
        self._generate_controls_catalog(data)
        self._generate_coverage_report(data)
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
        
        # Versión del Well-Architected Framework usada en la evaluación
        evidence_pack = data.get("evidence_pack", {})
        wa_meta = evidence_pack.get("metadata", {}) if isinstance(evidence_pack, dict) else {}
        well_arch_version = wa_meta.get("well_arch_version") or WELL_ARCH_VERSION

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
            "well_arch_version": well_arch_version,
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
    
    def _improvement_items_from_evidence(self, evidence_pack: Dict) -> List[Dict]:
        """Construir ítems de mejora desde el evidence pack (preguntas no cumplidas o parciales)."""
        items = []
        pillars = evidence_pack.get("pillars", {})
        for pillar_name, pillar_data in pillars.items():
            questions = pillar_data.get("well_architected_questions", [])
            for q in questions:
                comp = q.get("compliance", {})
                status = (comp.get("status") or "").strip()
                if status not in ("not_compliant", "partially_compliant"):
                    continue
                missing = comp.get("missing_services", [])
                detected = comp.get("detected_services", [])
                num_missing = len(missing)
                num_detected = len(detected)
                total = num_detected + num_missing
                if total == 0:
                    continue
                q_id = q.get("id", "")
                question_text = (q.get("question") or "")[:120]
                if len((q.get("question") or "")) > 120:
                    question_text += "..."
                msg = comp.get("message", "")
                rec = f"Revisar evidencias del pilar {pillar_name} y habilitar o documentar los servicios faltantes."
                if missing:
                    rec = f"Habilitar o documentar: {', '.join(missing[:5])}{'...' if len(missing) > 5 else ''}. Revisar evidencias del pilar {pillar_name}."
                effort = "Medio" if (status == "not_compliant" or num_missing >= 3) else "Bajo"
                impact = f"Cumplimiento parcial o no cumplido en {pillar_name}: {msg}"
                items.append({
                    "id": f"EVID-{pillar_name[:3].upper()}-{q_id}",
                    "domain": pillar_name,
                    "title": question_text or f"Cumplimiento {status} ({q_id})",
                    "description": msg,
                    "recommendation": rec,
                    "impact": impact,
                    "effort": effort,
                    "source": "Evidence Pack",
                })
        return items

    def _improvement_items_from_maturity(self, security_maturity: Dict) -> List[Dict]:
        """Construir ítems de mejora desde el modelo de madurez (not_met, partial)."""
        if not security_maturity or not security_maturity.get("results"):
            return []
        items = []
        phases_by_id = {p["id"]: p for p in security_maturity.get("phases", [])}
        for r in security_maturity.get("results", []):
            status = (r.get("status") or "").strip()
            if status not in ("not_met", "partial"):
                continue
            phase_id = r.get("phase", "")
            phase = phases_by_id.get(phase_id, {})
            phase_name = phase.get("name", phase_id)
            name = r.get("name", "")
            category = r.get("category", "")
            detail = (r.get("detail") or "")[:200]
            effort = "Medio" if status == "not_met" else "Bajo"
            rec = f"Implementar o revisar: {name}. Ver modelo en https://maturitymodel.security.aws.dev/es/"
            items.append({
                "id": f"MAT-{phase_id[:4].upper()}-{r.get('id', '') or name[:20].replace(' ', '-')}",
                "domain": "Security",
                "title": name,
                "description": detail or f"Capacidad del modelo de madurez ({phase_name}): {category}.",
                "recommendation": rec,
                "impact": f"Modelo de madurez en seguridad: {phase_name} – {category}.",
                "effort": effort,
                "source": "Modelo de Madurez",
                "category": category,
            })
        return items

    def _extract_missing_services(self, recommendation: str) -> List[str]:
        """Extraer servicios faltantes desde texto de recomendación."""
        if not recommendation:
            return []
        m = re.search(r"Habilitar o documentar:\s*([^\.]+)", recommendation, flags=re.IGNORECASE)
        if not m:
            return []
        raw = m.group(1)
        services = [s.strip() for s in raw.split(",") if s.strip()]
        cleaned = [s for s in services if s != "..."]
        return cleaned

    def _owner_by_domain(self, domain: str) -> str:
        """Sugerir owner técnico por dominio."""
        owners = {
            "Security": "Equipo de Seguridad Cloud",
            "Reliability": "Equipo de Plataforma / SRE",
            "Operational Excellence": "Equipo de Plataforma",
            "Performance Efficiency": "Arquitectura y Performance",
            "Cost Optimization": "FinOps + Plataforma",
            "Sustainability": "Arquitectura Cloud",
        }
        return owners.get(domain, "Equipo de Plataforma")

    def _standard_refs_for_item(self, item: Dict[str, Any]) -> List[Dict[str, str]]:
        """Referencias profesionales sugeridas para ejecutar la remediación."""
        refs = [
            {
                "name": "AWS Well-Architected - Mejorar la carga",
                "url": "https://docs.aws.amazon.com/wellarchitected/latest/userguide/improving-your-workload.html",
            }
        ]
        source = (item.get("source") or "").lower()
        domain = (item.get("domain") or "").lower()
        if "madurez" in source or "security" in domain:
            refs.append(
                {
                    "name": "AWS Security Hub - Workflow de hallazgos",
                    "url": "https://docs.aws.amazon.com/securityhub/latest/userguide/finding-workflow-status.html",
                }
            )
            refs.append(
                {
                    "name": "NIST CSF 2.0",
                    "url": "https://www.nist.gov/publications/nist-cybersecurity-framework-csf-20",
                }
            )
        return refs

    def _build_runbook_for_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Construir runbook de remediación accionable para un ítem del plan."""
        source = item.get("source", "")
        domain = item.get("domain", "General")
        recommendation = item.get("recommendation", "")
        effort = (item.get("effort") or "").strip()
        missing_services = self._extract_missing_services(recommendation)
        target_days = 30 if effort == "Bajo" else 60

        base_steps = [
            "Levantar alcance: cuentas, regiones, workloads y owners afectados.",
            "Crear ticket/cambio con ventana de implementación y responsable técnico.",
        ]
        if source == "Evidence Pack":
            service_hint = ", ".join(missing_services) if missing_services else "servicios faltantes del pilar"
            remediation_steps = base_steps + [
                f"Habilitar o configurar {service_hint} siguiendo baseline corporativo.",
                "Aplicar configuración mínima segura (logs, cifrado, alertas y acceso mínimo necesario).",
                "Actualizar IaC/políticas para evitar regresiones (CloudFormation/Terraform + SCP/guardrails).",
            ]
        elif source == "Modelo de Madurez":
            remediation_steps = base_steps + [
                "Definir control objetivo y alcance organizacional (OU/cuentas/regiones).",
                "Implementar control técnico y guardrails (IAM/SCP/Config/Security Hub según corresponda).",
                "Documentar excepción formal para workloads no compatibles y su fecha de revisión.",
            ]
        else:
            remediation_steps = base_steps + [
                f"Implementar corrección principal: {recommendation or 'aplicar hardening recomendado.'}",
                "Agregar monitoreo y alerta para detectar desviaciones tempranas.",
                "Actualizar runbook operativo y handoff al owner del servicio.",
            ]

        validation_steps = [
            "Validar en consola/CLI que la configuración objetivo está activa en todas las cuentas/regiones en alcance.",
            "Comprobar ausencia de errores en CloudTrail/CloudWatch para el cambio aplicado.",
            f"Re-ejecutar diagnóstico: `make analyze RUN_DIR={self.run_dir}` + `make evidence RUN_DIR={self.run_dir}` + `make reports RUN_DIR={self.run_dir}`.",
            "Confirmar mejora en score/hallazgo (estado mitigado o eliminado).",
        ]
        rollback_steps = [
            "Restaurar configuración previa desde IaC o backup versionado.",
            "Revertir solo el componente que genere impacto y mantener controles compensatorios temporales.",
            "Registrar postmortem corto y ajustar plan antes de nueva ventana.",
        ]

        risk_level = "Medio" if effort == "Bajo" else "Alto"
        if (item.get("severity") or "").lower() == "high":
            risk_level = "Alto"
        elif (item.get("severity") or "").lower() in ("low", "info"):
            risk_level = "Bajo"

        return {
            **item,
            "owner_role": self._owner_by_domain(domain),
            "target_days": target_days,
            "risk_level": risk_level,
            "control_objective": f"Reducir brecha de {domain} y dejar evidencia verificable de remediación.",
            "missing_services": missing_services,
            "remediation_steps": remediation_steps,
            "validation_steps": validation_steps,
            "rollback_steps": rollback_steps,
            "success_criteria": [
                "Control implementado en 100% del alcance definido.",
                "Hallazgo reducido/eliminado en el siguiente ciclo de evaluación.",
                "Owner y fecha de revisión registrados en backlog operativo.",
            ],
            "standard_refs": self._standard_refs_for_item(item),
        }

    def _build_improvement_plan_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Construir dataset estructurado del plan de mejoras (markdown + web)."""
        findings = data.get("findings", {}).get("findings", [])
        evidence_pack = data.get("evidence_pack", {})
        security_maturity = evidence_pack.get("security_maturity")
        if not security_maturity and data.get("index"):
            try:
                from evidence.security_maturity import evaluate as evaluate_maturity
                security_maturity = evaluate_maturity(data["index"], run_dir=self.run_dir)
            except Exception as e:
                logger.debug("No se pudo evaluar modelo de madurez para plan de mejoras: %s", e)

        findings_norm = []
        for f in findings:
            item = dict(f)
            item["source"] = item.get("source") or "Hallazgos"
            findings_norm.append(item)

        items_evidence = self._improvement_items_from_evidence(evidence_pack)
        items_maturity = self._improvement_items_from_maturity(security_maturity or {})

        pronta_f = [f for f in findings_norm if (f.get("effort") or "").strip() == "Bajo"]
        pronta_ev = [i for i in items_evidence if (i.get("effort") or "").strip() == "Bajo"]
        pronta_mat = [i for i in items_maturity if (i.get("effort") or "").strip() == "Bajo"]
        improvement_plan_pronta = pronta_f + pronta_ev + pronta_mat

        mri_f = [f for f in findings_norm if f not in pronta_f]
        mri_ev = [i for i in items_evidence if i not in pronta_ev]
        mri_mat = [i for i in items_maturity if i not in pronta_mat]
        improvement_plan_mri = mri_f + mri_ev + mri_mat

        pronta_enriched = [self._build_runbook_for_item(i) for i in improvement_plan_pronta[:35]]
        mri_enriched = [self._build_runbook_for_item(i) for i in improvement_plan_mri[:40]]

        wa_meta = evidence_pack.get("metadata", {}) if isinstance(evidence_pack, dict) else {}
        well_arch_version = wa_meta.get("well_arch_version") or WELL_ARCH_VERSION
        return {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "well_arch_version": well_arch_version,
            "pronta": pronta_enriched,
            "mri": mri_enriched,
            "summary": {
                "pronta_count": len(pronta_enriched),
                "mri_count": len(mri_enriched),
                "total": len(pronta_enriched) + len(mri_enriched),
            },
        }

    def _generate_improvement_plan(self, data: Dict):
        """Generar Plan de mejoras (Well-Architected Improvement Plan): HRI = pronta solución, MRI por complejidad media/alto. Incluye hallazgos, evidence pack y modelo de madurez."""
        template_file = self.templates_dir / "improvement_plan.md"
        if not template_file.exists():
            logger.warning(f"Template no encontrado: {template_file}")
            return
        
        with open(template_file, 'r', encoding='utf-8') as f:
            template = Template(f.read())
        plan_data = self._build_improvement_plan_data(data)

        context = {
            "date": plan_data["date"],
            "improvement_plan_pronta": plan_data["pronta"],
            "improvement_plan_mri": plan_data["mri"],
            "well_arch_version": plan_data["well_arch_version"],
        }
        
        output = template.render(**context)
        output_file = self.output_dir / "improvement_plan.md"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(output)
        logger.info(f"Plan de mejoras generado: {output_file}")

        # Guardar dataset estructurado para la UI web de remediación
        output_json = self.output_dir / "improvement_plan.json"
        with open(output_json, "w", encoding="utf-8") as f:
            json.dump(plan_data, f, indent=2, ensure_ascii=False)
        logger.info(f"Plan de mejoras (JSON) generado: {output_json}")

    def _normalize_service_name(self, service: str) -> str:
        """Normalizar nombres de servicio para correlación entre index/evidencia/mapeos."""
        raw = (service or "").strip().lower()
        raw = re.sub(r"^aws\s+", "", raw)
        raw = raw.replace("_", " ").replace("-", " ")
        raw = re.sub(r"\s+", " ", raw).strip()
        aliases = {
            "api gateway": "apigateway",
            "apigatewayv2": "apigateway",
            "amazon cloudwatch": "cloudwatch",
            "aws config": "config",
            "security hub": "securityhub",
            "aws security hub": "securityhub",
            "cost explorer": "ce",
            "savings plans": "savingsplans",
            "reserved instances": "reservedinstances",
            "service quotas": "servicequotas",
            "route 53": "route53",
            "elastic load balancing": "elb",
            "elbv2": "elb",
            "systems manager": "ssm",
            "x ray": "xray",
            "cloud trail": "cloudtrail",
            "event bridge": "eventbridge",
            "step functions": "stepfunctions",
            "cloud front": "cloudfront",
            "resource groups tagging api": "tagging",
            "secrets manager": "secretsmanager",
        }
        return aliases.get(raw, raw.replace(" ", ""))

    def _pillar_key(self, pillar: str) -> str:
        """Mapear nombre de pilar a clave de archivos de mapeo."""
        pillar_key_map = {
            "Operational Excellence": "operational_excellence",
            "Security": "security",
            "Reliability": "reliability",
            "Performance Efficiency": "performance_efficiency",
            "Cost Optimization": "cost_optimization",
            "Sustainability": "sustainability",
        }
        return pillar_key_map.get(pillar, "")

    def _well_arch_question_url(self, question_id: str) -> str:
        """Construir URL oficial AWS por pregunta WA (ej. OPS1 -> ops-01)."""
        qid = str(question_id or "").strip().upper()
        m = re.match(r"^([A-Z]+)(\d+)$", qid)
        if not m:
            return WELL_ARCH_DOC_URL
        prefix, num_s = m.group(1), m.group(2)
        try:
            num = int(num_s)
        except Exception:
            return WELL_ARCH_DOC_URL
        slug_map = {
            "OPS": "ops",
            "SEC": "sec",
            "REL": "rel",
            "PERF": "perf",
            "COST": "cost",
            "SUS": "sus",
        }
        slug = slug_map.get(prefix)
        if not slug:
            return WELL_ARCH_DOC_URL
        return f"https://docs.aws.amazon.com/wellarchitected/latest/framework/{slug}-{num:02d}.html"

    def _summarize_related_evidences(self, related: Any) -> List[Dict[str, str]]:
        """Reducir related_evidences a una traza corta y serializable para auditoría."""
        out: List[Dict[str, str]] = []
        for ev in (related or []):
            if not isinstance(ev, dict):
                continue
            out.append({
                "type": str(ev.get("type", "")),
                "status": str(ev.get("status", "")),
                "service": str(ev.get("service", "")),
                "category": str(ev.get("category", "")),
                "finding": str(ev.get("finding", "")),
                "description": str(ev.get("description", "")),
            })
            if len(out) >= 20:
                break
        return out

    def _load_question_service_mapping(self) -> Dict[str, Any]:
        """Cargar mapeo pregunta->servicios para enriquecer cobertura fase 2."""
        mapping_file = Path(__file__).resolve().parent.parent / "evidence" / "question_service_mapping.json"
        if not mapping_file.exists():
            return {}
        try:
            with open(mapping_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.debug("No se pudo cargar question_service_mapping.json: %s", e)
            return {}

    def _load_best_practices_services_mapping(self) -> Dict[str, Any]:
        """Cargar mapeo oficial de best practices -> servicios por pregunta."""
        mapping_file = Path(__file__).resolve().parent.parent / "evidence" / "best_practices_services.json"
        if not mapping_file.exists():
            return {}
        try:
            with open(mapping_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.debug("No se pudo cargar best_practices_services.json: %s", e)
            return {}

    def _phase2_lens_definitions(self) -> List[Dict[str, Any]]:
        """Definiciones de lentes oficiales para evaluación WAFR."""
        all_pillars = [
            "Operational Excellence",
            "Security",
            "Reliability",
            "Performance Efficiency",
            "Cost Optimization",
            "Sustainability",
        ]
        return [
            {
                "id": "wa-core",
                "name": "Well-Architected Core",
                "description": "Preguntas base del AWS Well-Architected Framework.",
                "origin": "aws_official",
                "pillars": all_pillars,
                "services": [],
                "control_type": "question",
            },
            {
                "id": "wa-best-practices",
                "name": "Well-Architected Best Practices",
                "description": "Mejores prácticas oficiales por pregunta WA, mapeadas a servicios observables.",
                "origin": "aws_official",
                "pillars": all_pillars,
                "services": [],
                "control_type": "best_practice",
            },
        ]

    def _phase2_pillar_service_baseline(self) -> Dict[str, List[str]]:
        """Servicios de referencia por pilar para generar controles por servicio."""
        return {
            "Operational Excellence": ["cloudwatch", "cloudtrail", "config", "cloudformation", "ssm", "backup", "eventbridge"],
            "Security": ["iam", "kms", "secretsmanager", "securityhub", "guardduty", "cloudtrail", "config", "wafv2", "acm"],
            "Reliability": ["ec2", "rds", "route53", "elb", "autoscaling", "backup", "s3", "cloudwatch", "sqs", "sns"],
            "Performance Efficiency": ["ec2", "rds", "lambda", "apigateway", "cloudfront", "dynamodb", "eks", "ecs", "cloudwatch"],
            "Cost Optimization": ["ce", "budgets", "computeoptimizer", "savingsplans", "ec2", "rds", "s3", "lambda"],
            "Sustainability": ["computeoptimizer", "cloudwatch", "lambda", "eks", "ecs", "ec2", "s3", "rds"],
        }

    def _collect_phase2_service_signals(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Construir señales de servicios detectados para evaluación de controles fase 2."""
        evidence_pack = data.get("evidence_pack", {})
        pillars = evidence_pack.get("pillars", {}) if isinstance(evidence_pack, dict) else {}
        index_services = data.get("index", {}).get("services", {})

        active_index_services: Set[str] = set()
        for service_name, service_data in index_services.items():
            normalized = self._normalize_service_name(service_name)
            total_ops = int(service_data.get("total_operations", 0) or 0)
            if total_ops > 0:
                active_index_services.add(normalized)
                continue
            for region_data in service_data.get("regions", {}).values():
                for op_info in region_data.get("operations", []):
                    if op_info.get("success"):
                        active_index_services.add(normalized)
                        break
                if normalized in active_index_services:
                    break

        direct_present: Set[str] = set()
        direct_missing: Set[str] = set()
        question_signals: Dict[str, Set[str]] = {}
        question_map = self._load_question_service_mapping()

        for pillar, p_data in pillars.items():
            for ev in p_data.get("evidence", []):
                service_name = self._normalize_service_name(ev.get("service", ""))
                if not service_name:
                    continue
                ev_type = str(ev.get("type", "")).strip().lower()
                status = str(ev.get("status", "")).strip().lower()
                if status == "detected" or ev_type == "service_present":
                    direct_present.add(service_name)
                if status == "not_detected" or ev_type == "service_missing":
                    direct_missing.add(service_name)

            pillar_key = self._pillar_key(pillar)
            p_question_map = question_map.get(pillar_key, {})
            for q in p_data.get("well_architected_questions", []):
                status = (q.get("compliance", {}).get("status") or "").strip()
                if status not in ("compliant", "partially_compliant", "not_compliant"):
                    continue
                qid = q.get("id", "")
                q_map = p_question_map.get(qid, {})
                for svc in q_map.get("services", []):
                    norm = self._normalize_service_name(svc)
                    if not norm:
                        continue
                    question_signals.setdefault(pillar, set()).add(norm)

        direct_signals = sorted(direct_present | direct_missing)
        all_detected = sorted(set(active_index_services) | direct_present | direct_missing)
        return {
            "active_index_services": active_index_services,
            "direct_present": direct_present,
            "direct_missing": direct_missing,
            "direct_signals": set(direct_signals),
            "all_detected": set(all_detected),
            "question_signals": question_signals,
        }

    def _build_controls_catalog(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Construir catálogo de controles WAFR oficiales (preguntas + best practices)."""
        evidence_pack = data.get("evidence_pack", {})
        pillars = evidence_pack.get("pillars", {}) if isinstance(evidence_pack, dict) else {}
        controls: List[Dict[str, Any]] = []
        lenses = self._phase2_lens_definitions()
        signals = self._collect_phase2_service_signals(data)
        question_map = self._load_question_service_mapping()
        best_practices_map = self._load_best_practices_services_mapping()

        pillar_code = {
            "Operational Excellence": "OPS",
            "Security": "SEC",
            "Reliability": "REL",
            "Performance Efficiency": "PERF",
            "Cost Optimization": "COST",
            "Sustainability": "SUS",
        }

        # Controles WA por pregunta (lente core)
        for pillar, p_data in pillars.items():
            pillar_key = self._pillar_key(pillar)
            p_question_map = question_map.get(pillar_key, {})
            for q in p_data.get("well_architected_questions", []):
                qid = q.get("id", "")
                if not qid:
                    continue
                status = (q.get("compliance", {}).get("status") or "").strip()
                related = q.get("related_evidences", [])
                evaluated = status in ("compliant", "partially_compliant", "not_compliant")
                confidence = 0.0
                if evaluated:
                    confidence = 1.0 if related else 0.6

                services = [
                    self._normalize_service_name(s)
                    for s in p_question_map.get(qid, {}).get("services", [])
                    if self._normalize_service_name(s)
                ]
                controls.append({
                    "control_id": f"WA-{pillar_code.get(pillar, 'GEN')}-{qid}",
                    "framework": "AWS Well-Architected",
                    "lens_id": "wa-core",
                    "lens_name": "Well-Architected Core",
                    "pillar": pillar,
                    "control_type": "question",
                    "question_id": qid,
                    "service": "multi",
                    "related_services": sorted(set(services)),
                    "title": q.get("question", ""),
                    "in_scope": True,
                    "evaluated": evaluated,
                    "confidence": confidence,
                    "automation_level": "automated_with_evidence",
                    "evaluation_logic": "compliance_status_from_evidence_pack_question",
                    "source_label": "AWS Well-Architected Framework",
                    "source_url": WELL_ARCH_DOC_URL,
                    "source_url_detail": self._well_arch_question_url(qid),
                    "source_reference": qid,
                    "evidence_trace": self._summarize_related_evidences(related),
                })

        # Controles WAFR por best practice oficial
        for pillar, p_data in pillars.items():
            pillar_key = self._pillar_key(pillar)
            p_best_practices = best_practices_map.get(pillar_key, {})
            p_question_map = question_map.get(pillar_key, {})
            for q in p_data.get("well_architected_questions", []):
                qid = q.get("id", "")
                if not qid:
                    continue
                question_status = str((q.get("compliance", {}) or {}).get("status", "")).strip()
                q_compliance = q.get("compliance", {}) or {}
                q_detected = {
                    self._normalize_service_name(s)
                    for s in q_compliance.get("detected_services", [])
                    if self._normalize_service_name(s)
                }
                q_missing = {
                    self._normalize_service_name(s)
                    for s in q_compliance.get("missing_services", [])
                    if self._normalize_service_name(s)
                }
                global_detected = set(signals.get("all_detected", set()))

                for idx, bp in enumerate(q.get("best_practices", []) or [], start=1):
                    bp_text = str(bp.get("practice", "")).strip()
                    if not bp_text:
                        continue
                    configured_services = bp.get("services", [])
                    if not isinstance(configured_services, list):
                        configured_services = []

                    if not configured_services:
                        configured_services = p_best_practices.get(qid, {}).get(bp_text, []) or []

                    required_services = sorted({
                        self._normalize_service_name(s)
                        for s in configured_services
                        if self._normalize_service_name(s)
                    })
                    related_from_question = {
                        self._normalize_service_name(s)
                        for s in p_question_map.get(qid, {}).get("services", [])
                        if self._normalize_service_name(s)
                    }
                    if not required_services and related_from_question:
                        required_services = sorted(related_from_question)

                    in_scope = bool(required_services)
                    matched: Set[str] = set()
                    evidence_level = "manual"
                    if in_scope:
                        for svc in required_services:
                            if svc in q_detected:
                                matched.add(svc)
                            elif svc in global_detected:
                                matched.add(svc)
                        if matched and len(matched) == len(required_services):
                            evidence_level = "direct" if all(s in q_detected for s in matched) else "direct_plus_inventory"
                        elif matched:
                            evidence_level = "partial"
                        else:
                            evidence_level = "negative"

                    missing = sorted(set(required_services) - matched)
                    if not in_scope:
                        evaluated = False
                        confidence = 0.0
                        status = "not_evaluable"
                    else:
                        evaluated = True
                        if not missing:
                            status = "compliant"
                            confidence = 1.0 if evidence_level == "direct" else 0.9
                        elif matched:
                            status = "partially_compliant"
                            confidence = 0.75
                        else:
                            status = "not_compliant"
                            confidence = 0.65

                    controls.append({
                        "control_id": f"WABP-{pillar_code.get(pillar, 'GEN')}-{qid}-{idx:02d}",
                        "framework": "AWS Well-Architected",
                        "lens_id": "wa-best-practices",
                        "lens_name": "Well-Architected Best Practices",
                        "pillar": pillar,
                        "control_type": "best_practice",
                        "question_id": qid,
                        "title": bp_text,
                        "service": "multi",
                        "related_services": required_services,
                        "in_scope": in_scope,
                        "evaluated": evaluated,
                        "status": status,
                        "confidence": confidence,
                        "evidence_level": evidence_level,
                        "detected_services": sorted(matched),
                        "missing_services": missing,
                        "question_compliance_status": question_status,
                        "question_missing_services": sorted(q_missing),
                        "automation_level": "automated_with_service_signals" if in_scope else "manual_required",
                        "evaluation_logic": "official_best_practice_service_mapping_vs_detected_services",
                        "source_label": "AWS Well-Architected (Best Practices)",
                        "source_url": WELL_ARCH_DOC_URL,
                        "source_url_detail": self._well_arch_question_url(qid),
                        "source_reference": f"{qid} / {bp_text}",
                        "evidence_trace": self._summarize_related_evidences(q.get("related_evidences", [])),
                    })

        return {
            "version": "2.0",
            "generated_at": datetime.utcnow().isoformat(),
            "scope": "AWS Well-Architected WAFR official controls (questions + best practices)",
            "official_only": True,
            "official_sources": [
                {
                    "label": "AWS Well-Architected Framework",
                    "url": WELL_ARCH_DOC_URL,
                },
                {
                    "label": "AWS Well-Architected Tool - Lenses",
                    "url": "https://docs.aws.amazon.com/wellarchitected/latest/userguide/lenses.html",
                },
                {
                    "label": "AWS Well-Architected Tool - Lens Catalog",
                    "url": "https://docs.aws.amazon.com/wellarchitected/latest/userguide/lens-catalog.html",
                },
            ],
            "lenses": lenses,
            "controls_count": len(controls),
            "controls": controls,
        }

    def _generate_controls_catalog(self, data: Dict[str, Any]) -> None:
        """Generar catálogo de controles para auditoría de cobertura."""
        catalog = self._build_controls_catalog(data)
        output_file = self.output_dir / "controls_catalog.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(catalog, f, indent=2, ensure_ascii=False)
        logger.info(f"Catálogo de controles generado: {output_file}")

    def _build_coverage_report(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Construir reporte de cobertura y confianza por pilar/lente (WAFR)."""
        catalog = self._build_controls_catalog(data)
        controls = catalog.get("controls", [])
        in_scope = [c for c in controls if c.get("in_scope")]

        def summarize(group_controls: List[Dict[str, Any]]) -> Dict[str, Any]:
            total = len(group_controls)
            evaluated = sum(1 for c in group_controls if c.get("evaluated"))
            not_evaluable = total - evaluated
            conf_values = [float(c.get("confidence", 0.0)) for c in group_controls if c.get("evaluated")]
            confidence_pct = round((sum(conf_values) / len(conf_values)) * 100, 1) if conf_values else 0.0
            coverage_pct = round((evaluated / total) * 100, 1) if total else 0.0
            not_evaluable_pct = round((not_evaluable / total) * 100, 1) if total else 0.0
            return {
                "total_controls": total,
                "evaluated_controls": evaluated,
                "not_evaluable_controls": not_evaluable,
                "coverage_pct": coverage_pct,
                "confidence_pct": confidence_pct,
                "not_evaluable_pct": not_evaluable_pct,
            }

        pillars_summary: Dict[str, Any] = {}
        for pillar in sorted({c.get("pillar") for c in in_scope if c.get("pillar")}):
            p_controls = [c for c in in_scope if c.get("pillar") == pillar]
            lens_counts: Dict[str, int] = {}
            for c in p_controls:
                lid = c.get("lens_id", "unknown")
                lens_counts[lid] = lens_counts.get(lid, 0) + 1
            summary = summarize(p_controls)
            summary["controls_by_lens"] = lens_counts
            pillars_summary[pillar] = summary

        lenses_summary: Dict[str, Any] = {}
        for lens in catalog.get("lenses", []):
            lid = lens.get("id")
            l_controls = [c for c in in_scope if c.get("lens_id") == lid]
            if not l_controls:
                continue
            summary = summarize(l_controls)
            summary["name"] = lens.get("name", lid)
            summary["description"] = lens.get("description", "")
            summary["origin"] = lens.get("origin", "ecad_custom")
            summary["pillars"] = lens.get("pillars", [])
            lenses_summary[lid] = summary

        services_summary: Dict[str, Any] = {}
        service_controls = [c for c in in_scope if c.get("related_services")]
        unique_services = sorted({
            svc
            for c in service_controls
            for svc in (c.get("related_services") or [])
            if svc
        })
        for service in unique_services:
            s_controls = [c for c in service_controls if service in (c.get("related_services") or [])]
            services_summary[service] = summarize(s_controls)
            services_summary[service]["pillars"] = sorted({c.get("pillar") for c in s_controls if c.get("pillar")})
            services_summary[service]["lenses"] = sorted({c.get("lens_id") for c in s_controls if c.get("lens_id")})

        global_summary = summarize(in_scope)
        global_summary["controls_catalog_total"] = len(controls)
        global_summary["in_scope_controls"] = len(in_scope)
        global_summary["lenses_evaluated"] = len(lenses_summary)
        global_summary["services_evaluated"] = len(services_summary)

        return {
            "version": "2.0",
            "generated_at": datetime.utcnow().isoformat(),
            "framework_scope": "AWS Well-Architected WAFR official controls",
            "global": global_summary,
            "pillars": pillars_summary,
            "lenses": lenses_summary,
            "services": services_summary,
            "notes": [
                "coverage_pct mide controles evaluados / controles en alcance.",
                "confidence_pct refleja la calidad de evidencia por control (directa, parcial, negativa).",
                "Controles sin servicios observables quedan como manual_required y fuera del alcance automatizado.",
            ],
        }

    def _generate_coverage_report(self, data: Dict[str, Any]) -> None:
        """Generar reporte JSON de cobertura y confianza."""
        coverage = self._build_coverage_report(data)
        output_file = self.output_dir / "coverage_report.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(coverage, f, indent=2, ensure_ascii=False)
        logger.info(f"Reporte de cobertura generado: {output_file}")
    
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
        """Calcular scores 1-5 por pilar desde evidence pack con criterio conservador."""
        compliance_to_points = {
            "compliant": 5.0,
            "partially_compliant": 3.0,
            "not_compliant": 1.0,
            "not_applicable": None,  # no cuenta en el promedio de preguntas
        }
        domains = ["Operational Excellence", "Security", "Reliability", "Performance Efficiency", "Cost Optimization", "Sustainability"]
        domain_scores = {}
        pillars = evidence_pack.get("pillars", {})

        def _evidence_penalty(ev: Dict[str, Any]) -> float:
            status = str(ev.get("status", "")).strip().lower()
            ev_type = str(ev.get("type", "")).strip().lower()
            if status in ("negative", "error"):
                return 0.35
            if status == "warning":
                return 0.20
            if status == "not_detected" or ev_type == "service_missing":
                return 0.12
            return 0.0

        def _evidence_bonus(ev: Dict[str, Any]) -> float:
            status = str(ev.get("status", "")).strip().lower()
            if status == "positive":
                return 0.10
            return 0.0

        for domain in domains:
            pillar_data = pillars.get(domain, {})
            questions = pillar_data.get("well_architected_questions", [])
            evidence = pillar_data.get("evidence", [])
            points = []
            for q in questions:
                st = q.get("compliance", {}).get("status", "not_applicable")
                pt = compliance_to_points.get(st)
                if pt is not None:
                    points.append(pt)

            # Base por preguntas: si no hay preguntas evaluables, usar neutral 3.0
            question_score = (sum(points) / len(points)) if points else 3.0

            # Ajuste por evidencia observada: penaliza gaps y hallazgos negativos/warning
            penalty = min(1.8, sum(_evidence_penalty(ev) for ev in evidence))
            bonus = min(0.3, sum(_evidence_bonus(ev) for ev in evidence))

            raw_score = question_score - penalty + bonus
            domain_scores[domain] = max(1, min(5, round(raw_score)))
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
        
        wa_meta = evidence_pack.get("metadata", {}) if isinstance(evidence_pack, dict) else {}
        well_arch_version = wa_meta.get("well_arch_version") or WELL_ARCH_VERSION

        context = {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "domain_scores": domain_scores,
            "average_score": sum(domain_scores.values()) / len(domain_scores) if domain_scores else 0,
            "well_arch_version": well_arch_version,
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

    def _build_evaluation_phases_from_coverage(self, coverage_report: Dict[str, Any]) -> Dict[str, Any]:
        """Construir resumen por fases para UI: baseline WA, cobertura extendida y roadmap WAFR."""
        global_cov = coverage_report.get("global", {})
        lenses = coverage_report.get("lenses", {})
        wa_core = lenses.get("wa-core", {})
        extended_ids = [lid for lid in lenses.keys() if lid != "wa-core"]

        extended_total = sum(int(lenses[lid].get("total_controls", 0) or 0) for lid in extended_ids)
        extended_eval = sum(int(lenses[lid].get("evaluated_controls", 0) or 0) for lid in extended_ids)
        extended_ne = sum(int(lenses[lid].get("not_evaluable_controls", 0) or 0) for lid in extended_ids)
        extended_conf_values = [float(lenses[lid].get("confidence_pct", 0) or 0) for lid in extended_ids if int(lenses[lid].get("evaluated_controls", 0) or 0) > 0]
        extended_conf = round(sum(extended_conf_values) / len(extended_conf_values), 1) if extended_conf_values else 0.0
        extended_cov = round((extended_eval / extended_total) * 100, 1) if extended_total else 0.0
        extended_ne_pct = round((extended_ne / extended_total) * 100, 1) if extended_total else 0.0

        return {
            "phase_1_baseline": {
                "name": "Fase 1 - WA Core",
                "description": "Evaluacion oficial base del Well-Architected Framework (preguntas de los 6 pilares).",
                "status": "implemented",
                "metrics": {
                    "total_controls": wa_core.get("total_controls", 0),
                    "evaluated_controls": wa_core.get("evaluated_controls", 0),
                    "coverage_pct": wa_core.get("coverage_pct", 0),
                    "confidence_pct": wa_core.get("confidence_pct", 0),
                    "not_evaluable_pct": wa_core.get("not_evaluable_pct", 0),
                },
            },
            "phase_2_extended": {
                "name": "Fase 2 - WAFR Official Controls",
                "description": "Controles oficiales WAFR por best practices y evidencia observable.",
                "status": "implemented" if extended_total > 0 else "not_available",
                "metrics": {
                    "total_controls": extended_total,
                    "evaluated_controls": extended_eval,
                    "coverage_pct": extended_cov,
                    "confidence_pct": extended_conf,
                    "not_evaluable_pct": extended_ne_pct,
                    "lenses": [
                        {
                            "id": lid,
                            "name": lenses[lid].get("name", lid),
                            "origin": lenses[lid].get("origin", "ecad_custom"),
                            "controls": lenses[lid].get("total_controls", 0),
                            "coverage_pct": lenses[lid].get("coverage_pct", 0),
                            "confidence_pct": lenses[lid].get("confidence_pct", 0),
                        }
                        for lid in extended_ids
                    ],
                },
            },
            "phase_3_wafr_official": {
                "name": "Fase 3 - WAFR por Workload",
                "description": "Roadmap para incorporar selección de lentes oficiales por tipo de workload.",
                "status": "roadmap",
                "readiness": {
                    "workload_segmentation": "pending",
                    "lens_selection_by_workload": "pending",
                    "manual_non_automatable_answers": "pending",
                    "lens_version_governance": "pending",
                    "review_workflow_with_owners": "pending",
                },
            },
            "global_context": {
                "coverage_pct": global_cov.get("coverage_pct", 0),
                "confidence_pct": global_cov.get("confidence_pct", 0),
                "in_scope_controls": global_cov.get("in_scope_controls", 0),
            },
        }

    def _find_wa_question(self, evidence_pack: Dict[str, Any], pillar_name: str, question_id: str) -> Optional[Dict[str, Any]]:
        """Buscar pregunta WA por pilar e ID."""
        pillars = evidence_pack.get("pillars", {}) if isinstance(evidence_pack, dict) else {}
        questions = ((pillars.get(pillar_name) or {}).get("well_architected_questions") or [])
        for q in questions:
            if str(q.get("id", "")).upper() == str(question_id).upper():
                return q
        return None

    def _caf_status_from_compliance(self, compliance_status: str, organizational: bool = False) -> Dict[str, str]:
        """Normalizar estado de cumplimiento WA a estado de perspectiva CAF."""
        st = str(compliance_status or "").strip().lower()
        if organizational and st in ("", "not_applicable"):
            return {"code": "organizational", "label": "Definición organizacional pendiente"}
        mapping = {
            "compliant": {"code": "aligned", "label": "Alineado"},
            "partially_compliant": {"code": "attention", "label": "Atención requerida"},
            "not_compliant": {"code": "at_risk", "label": "En riesgo"},
            "not_applicable": {"code": "manual", "label": "Validación manual"},
            "evaluated": {"code": "manual", "label": "Validación manual"},
        }
        return mapping.get(st, {"code": "manual", "label": "Validación manual"})

    def _caf_merge_status(self, items: List[Dict[str, Any]]) -> Dict[str, str]:
        """Calcular estado agregado de una perspectiva CAF."""
        priority = {"at_risk": 5, "attention": 4, "organizational": 3, "manual": 2, "aligned": 1}
        selected = {"code": "aligned", "label": "Alineado"}
        selected_score = 0
        for item in items:
            st = item.get("status", "manual")
            score = priority.get(st, 2)
            if score > selected_score:
                selected_score = score
                selected = {
                    "code": st,
                    "label": item.get("status_label", "Validación manual"),
                }
        return selected

    def _build_caf_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Construir vista CAF usando insumos disponibles y señalando lo organizacional."""
        evidence_pack = data.get("evidence_pack", {}) or {}
        index = data.get("index", {}) or {}
        findings = data.get("findings", {}) or {}
        stats = data.get("stats", {}) or {}

        services_total = len((index.get("services") or {}).keys())
        regions_total = len(index.get("regions") or [])
        ops_total = int(stats.get("operations_executed", 0) or 0)
        ops_ok = int(stats.get("operations_successful", 0) or 0)
        ops_failed = int(stats.get("operations_failed", 0) or 0)
        ops_success_pct = round((ops_ok / ops_total) * 100, 1) if ops_total > 0 else 0.0
        findings_total = int(findings.get("total_findings", 0) or 0)

        org_items: List[Dict[str, Any]] = []
        qmap = self._load_question_service_mapping()
        for pillar_key, questions in (qmap or {}).items():
            for qid, q_meta in (questions or {}).items():
                desc = str((q_meta or {}).get("description", "")).lower()
                services = (q_meta or {}).get("services", []) or []
                if services or "organizacional" not in desc:
                    continue
                q = self._find_wa_question(evidence_pack, "Operational Excellence", qid)
                comp = (q or {}).get("compliance", {}) if isinstance(q, dict) else {}
                st = self._caf_status_from_compliance(comp.get("status", ""), organizational=True)
                org_items.append({
                    "id": qid,
                    "title": (q or {}).get("question", f"Pregunta {qid}"),
                    "status": st["code"],
                    "status_label": st["label"],
                    "organizational": True,
                    "source": f"Well-Architected {qid}",
                    "source_url": self._well_arch_question_url(qid),
                    "evidence": comp.get("message", "Pregunta de naturaleza organizacional."),
                    "action": "Definir owner, criterio y evidencia documental en comité de arquitectura/gobierno.",
                })

        def pillar_signal_item(pillar_name: str, title: str, source_id: str, organizational: bool = False) -> Dict[str, Any]:
            p = (evidence_pack.get("pillars", {}) or {}).get(pillar_name, {})
            qs = p.get("well_architected_questions", []) or []
            statuses = [str((q.get("compliance", {}) or {}).get("status", "")).strip() for q in qs]
            if "not_compliant" in statuses:
                st = {"code": "at_risk", "label": "En riesgo"}
            elif "partially_compliant" in statuses:
                st = {"code": "attention", "label": "Atención requerida"}
            elif "compliant" in statuses:
                st = {"code": "aligned", "label": "Alineado"}
            else:
                st = {"code": "manual", "label": "Validación manual"}
            compliant = statuses.count("compliant")
            partial = statuses.count("partially_compliant")
            not_compliant = statuses.count("not_compliant")
            evidence = f"WA: compliant={compliant}, parcial={partial}, no_compliant={not_compliant}."
            return {
                "id": source_id,
                "title": title,
                "status": st["code"],
                "status_label": st["label"],
                "organizational": organizational,
                "source": f"Well-Architected {pillar_name}",
                "source_url": WELL_ARCH_DOC_URL,
                "evidence": evidence,
                "action": "Priorizar plan de mejora de controles con owner y fecha objetivo.",
            }

        sm = evidence_pack.get("security_maturity", {}) or {}
        sm_summary = sm.get("summary", {}) or {}
        sm_met = sum(int((v or {}).get("met", 0) or 0) for v in sm_summary.values())
        sm_not_met = sum(int((v or {}).get("not_met", 0) or 0) for v in sm_summary.values())
        sm_partial = sum(int((v or {}).get("partial", 0) or 0) for v in sm_summary.values())
        if sm_not_met > 0:
            sm_status = {"code": "at_risk", "label": "En riesgo"}
        elif sm_partial > 0:
            sm_status = {"code": "attention", "label": "Atención requerida"}
        else:
            sm_status = {"code": "aligned", "label": "Alineado"}

        perspectives: List[Dict[str, Any]] = []
        perspectives.append({
            "id": "business",
            "name": "Business",
            "description": "Valor de negocio, objetivos y sostenibilidad económica.",
            "items": [
                pillar_signal_item("Cost Optimization", "Disciplina de costo y priorización por valor", "BUS-COST"),
                pillar_signal_item("Sustainability", "Objetivos de sostenibilidad y eficiencia", "BUS-SUS"),
                next((x for x in org_items if x.get("id") == "OPS1"), {
                    "id": "BUS-ORG-01",
                    "title": "Definir prioridades y resultados de negocio",
                    "status": "organizational",
                    "status_label": "Definición organizacional pendiente",
                    "organizational": True,
                    "source": "Well-Architected OPS1",
                    "source_url": self._well_arch_question_url("OPS1"),
                    "evidence": "Requiere definición estratégica y métricas de negocio.",
                    "action": "Aprobar OKRs/KPIs de nube con sponsor de negocio.",
                }),
            ],
        })
        perspectives.append({
            "id": "people",
            "name": "People",
            "description": "Roles, capacidades y cultura operativa del equipo.",
            "items": [
                next((x for x in org_items if x.get("id") == "OPS2"), {
                    "id": "PEO-ORG-01",
                    "title": "Estructura organizacional para resultados cloud",
                    "status": "organizational",
                    "status_label": "Definición organizacional pendiente",
                    "organizational": True,
                    "source": "Well-Architected OPS2",
                    "source_url": self._well_arch_question_url("OPS2"),
                    "evidence": "No se puede inferir completamente desde APIs.",
                    "action": "Definir RACI cloud y capacidades por equipo.",
                }),
                next((x for x in org_items if x.get("id") == "OPS3"), {
                    "id": "PEO-ORG-02",
                    "title": "Cultura y mecanismos de mejora continua",
                    "status": "organizational",
                    "status_label": "Definición organizacional pendiente",
                    "organizational": True,
                    "source": "Well-Architected OPS3",
                    "source_url": self._well_arch_question_url("OPS3"),
                    "evidence": "Requiere evidencia de prácticas organizacionales.",
                    "action": "Acordar rituales operativos, postmortems y capacitación continua.",
                }),
            ],
        })
        perspectives.append({
            "id": "governance",
            "name": "Governance",
            "description": "Gobierno, políticas y seguimiento de decisiones cloud.",
            "items": [
                {
                    "id": "GOV-FIND-01",
                    "title": "Gestión de hallazgos y backlog de remediación",
                    "status": "attention" if findings_total > 0 else "aligned",
                    "status_label": "Atención requerida" if findings_total > 0 else "Alineado",
                    "organizational": False,
                    "source": "findings.json",
                    "source_url": "",
                    "evidence": f"Hallazgos detectados: {findings_total}.",
                    "action": "Asignar dueño y fecha objetivo a cada hallazgo crítico/relevante.",
                },
                {
                    "id": "GOV-TAG-01",
                    "title": "Estandarización de taxonomía de tags",
                    "status": "organizational",
                    "status_label": "Definición organizacional pendiente",
                    "organizational": True,
                    "source": "Tagging report",
                    "source_url": "",
                    "evidence": "Requiere estándar corporativo por dominio/aplicación/entorno/costo.",
                    "action": "Definir política de tags obligatorios y control de cumplimiento.",
                },
            ],
        })
        perspectives.append({
            "id": "platform",
            "name": "Platform",
            "description": "Base técnica de servicios, regiones y confiabilidad de la telemetría.",
            "items": [
                {
                    "id": "PLT-INV-01",
                    "title": "Cobertura de inventario técnico",
                    "status": "aligned" if services_total > 0 else "manual",
                    "status_label": "Alineado" if services_total > 0 else "Validación manual",
                    "organizational": False,
                    "source": "index.json",
                    "source_url": "",
                    "evidence": f"Servicios indexados: {services_total}. Regiones detectadas: {regions_total}.",
                    "action": "Mantener baseline multi-servicio y expandir cobertura regional según alcance.",
                },
                {
                    "id": "PLT-COL-01",
                    "title": "Efectividad de recolección en primera ejecución",
                    "status": "at_risk" if ops_total > 0 and ops_success_pct < 70 else ("attention" if ops_total > 0 and ops_success_pct < 85 else "aligned"),
                    "status_label": "En riesgo" if ops_total > 0 and ops_success_pct < 70 else ("Atención requerida" if ops_total > 0 and ops_success_pct < 85 else "Alineado"),
                    "organizational": False,
                    "source": "collection_stats.json",
                    "source_url": "",
                    "evidence": f"Operaciones: {ops_ok} exitosas, {ops_failed} fallidas, éxito {ops_success_pct}%.",
                    "action": "Optimizar set de operaciones críticas y timeouts para maximizar éxito en primera corrida.",
                },
            ],
        })
        perspectives.append({
            "id": "security",
            "name": "Security",
            "description": "Controles de seguridad y madurez operacional.",
            "items": [
                pillar_signal_item("Security", "Controles Well-Architected de seguridad", "SEC-WA-01"),
                {
                    "id": "SEC-MAT-01",
                    "title": "Modelo de madurez de seguridad AWS",
                    "status": sm_status["code"],
                    "status_label": sm_status["label"],
                    "organizational": False,
                    "source": sm.get("source", "AWS Security Maturity Model"),
                    "source_url": sm.get("source", ""),
                    "evidence": f"Madurez: cumple={sm_met}, parcial={sm_partial}, no_cumple={sm_not_met}.",
                    "action": "Priorizar capacidades no cumplidas por fase de madurez.",
                },
            ],
        })
        perspectives.append({
            "id": "operations",
            "name": "Operations",
            "description": "Operación confiable, observabilidad y respuesta.",
            "items": [
                pillar_signal_item("Operational Excellence", "Disciplina operativa Well-Architected", "OPS-WA-01"),
                pillar_signal_item("Reliability", "Confiabilidad y recuperación", "OPS-REL-01"),
            ],
        })

        organizational_total = 0
        technical_total = 0
        org_backlog: List[Dict[str, Any]] = []
        status_priority = {"at_risk": 5, "attention": 4, "organizational": 3, "manual": 2, "aligned": 1}
        for p in perspectives:
            merged = self._caf_merge_status(p.get("items", []))
            p["status"] = merged["code"]
            p["status_label"] = merged["label"]
            for item in p.get("items", []):
                if item.get("organizational"):
                    organizational_total += 1
                    org_backlog.append({
                        "perspective": p.get("name", ""),
                        "id": item.get("id", ""),
                        "title": item.get("title", ""),
                        "status": item.get("status", "organizational"),
                        "status_label": item.get("status_label", "Definición organizacional pendiente"),
                        "source": item.get("source", ""),
                        "source_url": item.get("source_url", ""),
                        "action": item.get("action", ""),
                        "priority": status_priority.get(item.get("status", "organizational"), 3),
                    })
                else:
                    technical_total += 1
        org_backlog_sorted = sorted(
            org_backlog,
            key=lambda x: (-int(x.get("priority", 0)), str(x.get("perspective", "")), str(x.get("title", ""))),
        )

        return {
            "summary": {
                "perspectives": len(perspectives),
                "organizational_items": organizational_total,
                "technical_items": technical_total,
                "services_discovered": services_total,
                "regions_discovered": regions_total,
                "collection_success_pct": ops_success_pct,
            },
            "perspectives": perspectives,
            "organizational_backlog": org_backlog_sorted[:5],
        }

    def _build_inventory_web_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Construir inventario resumido para visual web (servicios con/sin datos y con errores)."""
        index = data.get("index", {}) or {}
        services = index.get("services", {}) or {}
        arn_lookup = self._build_arn_lookup_from_sources(data)

        rows: List[Dict[str, Any]] = []
        with_data = 0
        with_errors = 0
        without_data = 0

        for service_name in sorted(services.keys()):
            service_data = services.get(service_name, {})
            successful_ops = 0
            failed_ops = 0
            total_resources = 0
            regions_count = 0
            total_ops = 0

            for region_name, region_data in service_data.get("regions", {}).items():
                regions_count += 1
                for op_info in region_data.get("operations", []):
                    total_ops += 1
                    if op_info.get("success"):
                        successful_ops += 1
                        total_resources += int(op_info.get("resource_count", 0) or 0)
                    else:
                        failed_ops += 1

            status = "sin_datos"
            if successful_ops > 0:
                status = "con_datos"
            elif failed_ops > 0:
                status = "errores"

            if status == "con_datos":
                with_data += 1
            elif status == "errores":
                with_errors += 1
            else:
                without_data += 1

            samples_real = self._extract_service_resource_samples(
                service_name=service_name,
                service_data=service_data,
                inventory_only=True,
            )
            samples_catalog = self._extract_service_resource_samples(
                service_name=service_name,
                service_data=service_data,
                inventory_only=False,
            )
            resource_type = self._guess_resource_type(service_name, samples_real.get("operations", []))
            normalized_real = self._normalize_resource_samples(
                service_name=service_name,
                samples=samples_real.get("samples", []),
                arn_lookup=arn_lookup,
                account_id=str((data.get("metadata", {}) or {}).get("account_id", "")).strip(),
            )
            normalized_catalog = self._normalize_resource_samples(
                service_name=service_name,
                samples=samples_catalog.get("samples", []),
                arn_lookup=arn_lookup,
                account_id=str((data.get("metadata", {}) or {}).get("account_id", "")).strip(),
            )
            subcategory_counts_real: Dict[str, int] = {}
            for item in normalized_real:
                sub = item.get("subcategory", "Otros")
                subcategory_counts_real[sub] = subcategory_counts_real.get(sub, 0) + 1
            subcategory_counts_catalog: Dict[str, int] = {}
            for item in normalized_catalog:
                sub = item.get("subcategory", "Otros")
                subcategory_counts_catalog[sub] = subcategory_counts_catalog.get(sub, 0) + 1
            rows.append({
                "service": service_name,
                "regions": regions_count,
                "operations_total": total_ops,
                "operations_ok": successful_ops,
                "operations_error": failed_ops,
                "resources": total_resources,
                "status": status,
                "resource_type": resource_type,
                "resource_samples": normalized_real,
                "resource_samples_preview": normalized_real[:3],
                "resource_samples_real": normalized_real,
                "resource_samples_catalog": normalized_catalog,
                "resource_subcategories": [
                    {"name": name, "count": count}
                    for name, count in sorted(subcategory_counts_real.items(), key=lambda kv: (-kv[1], kv[0]))[:10]
                ],
                "resource_subcategories_real": [
                    {"name": name, "count": count}
                    for name, count in sorted(subcategory_counts_real.items(), key=lambda kv: (-kv[1], kv[0]))[:10]
                ],
                "resource_subcategories_catalog": [
                    {"name": name, "count": count}
                    for name, count in sorted(subcategory_counts_catalog.items(), key=lambda kv: (-kv[1], kv[0]))[:10]
                ],
                "sample_source_ops": samples_real.get("operations", []),
                "sample_source_ops_real": samples_real.get("operations", []),
                "sample_source_ops_catalog": samples_catalog.get("operations", []),
            })

        rows_sorted = sorted(rows, key=lambda r: (0 if r["status"] == "con_datos" else (1 if r["status"] == "errores" else 2), -r["operations_ok"], r["service"]))
        return {
            "summary": {
                "services_total": len(rows),
                "services_with_data": with_data,
                "services_with_errors": with_errors,
                "services_without_data": without_data,
            },
            "rows": rows_sorted,
        }

    def _extract_service_from_arn(self, arn: str) -> str:
        """Extraer servicio desde ARN (arn:partition:service:...)."""
        if not arn or not isinstance(arn, str):
            return ""
        parts = arn.split(":")
        return parts[2].lower() if len(parts) > 2 else ""

    def _arn_candidates_from_arn(self, arn: str) -> Set[str]:
        """Generar claves candidatas para mapear ID -> ARN."""
        candidates: Set[str] = set()
        if not arn or not isinstance(arn, str):
            return candidates
        candidates.add(arn.strip().lower())
        resource_part = arn.split(":", 5)[-1] if ":" in arn else arn
        rp = resource_part.strip().lstrip("/").lower()
        if rp:
            candidates.add(rp)
            if "/" in rp:
                segments = [seg for seg in rp.split("/") if seg]
                if segments:
                    candidates.add(segments[-1])
                if len(segments) >= 2:
                    candidates.add("/".join(segments[-2:]))
            if ":" in rp:
                csegs = [seg for seg in rp.split(":") if seg]
                if csegs:
                    candidates.add(csegs[-1])
                if len(csegs) >= 2:
                    candidates.add(":".join(csegs[-2:]))
        return {c for c in candidates if c}

    def _value_candidates_for_arn_lookup(self, value: str) -> Set[str]:
        """Normalizar posibles IDs/keys para buscar ARN asociado."""
        candidates: Set[str] = set()
        if not value or not isinstance(value, str):
            return candidates
        v = value.strip().lower()
        if not v:
            return candidates
        candidates.add(v)
        v2 = v.lstrip("/")
        candidates.add(v2)
        if "/" in v2:
            segs = [seg for seg in v2.split("/") if seg]
            if segs:
                candidates.add(segs[-1])
            if len(segs) >= 2:
                candidates.add("/".join(segs[-2:]))
        if ":" in v2:
            csegs = [seg for seg in v2.split(":") if seg]
            if csegs:
                candidates.add(csegs[-1])
            if len(csegs) >= 2:
                candidates.add(":".join(csegs[-2:]))
        return {c for c in candidates if c}

    def _build_arn_lookup_from_sources(self, data: Dict[str, Any]) -> Dict[str, Dict[str, str]]:
        """Construir índice service->candidate->ARN usando fuentes reales recolectadas."""
        index = data.get("index", {}) or {}
        services = index.get("services", {}) or {}
        lookup: Dict[str, Dict[str, str]] = {}

        def add_arn(arn_value: str):
            arn = str(arn_value or "").strip()
            if not arn.startswith("arn:"):
                return
            svc = self._extract_service_from_arn(arn)
            if not svc:
                return
            svc_map = lookup.setdefault(svc, {})
            for cand in self._arn_candidates_from_arn(arn):
                if cand not in svc_map:
                    svc_map[cand] = arn

        # Fuente principal: Resource Groups Tagging API (retorna ARNs de recursos reales).
        tag_svc = services.get("resourcegroupstaggingapi", {})
        for region_data in (tag_svc.get("regions", {}) or {}).values():
            for op in region_data.get("operations", []) or []:
                if not op.get("success"):
                    continue
                if str(op.get("operation", "")) != "GetResources":
                    continue
                file_rel = op.get("file")
                if not file_rel:
                    continue
                full_path = self.run_dir / "raw" / file_rel
                if not full_path.exists():
                    continue
                try:
                    with gzip.open(full_path, "rt", encoding="utf-8") as f:
                        payload = json.load(f)
                except Exception:
                    continue
                data_node = payload.get("data", payload)
                for item in (data_node.get("ResourceTagMappingList", []) if isinstance(data_node, dict) else []):
                    if isinstance(item, dict):
                        add_arn(item.get("ResourceARN", ""))

        return lookup

    def _guess_resource_type(self, service_name: str, operations: List[str]) -> str:
        """Inferir tipo de recurso principal por servicio/operaciones."""
        op_text = " ".join((operations or [])).lower()
        op_map = [
            ("listbuckets", "Buckets"),
            ("describeinstances", "Instances"),
            ("describevolumes", "EBS Volumes"),
            ("describevpcs", "VPCs"),
            ("listfunctions", "Functions"),
            ("describedbinstances", "DB Instances"),
            ("describedbclusters", "DB Clusters"),
            ("listtables", "Tables"),
            ("listqueues", "Queues"),
            ("listtopics", "Topics"),
            ("listdistributions", "Distributions"),
            ("listusers", "Users"),
            ("listroles", "Roles"),
            ("describeloadbalancers", "Load Balancers"),
            ("listclusters", "Clusters"),
            ("describecacheclusters", "Cache Clusters"),
        ]
        for key, label in op_map:
            if key in op_text:
                return label

        service_map = {
            "s3": "Buckets",
            "ec2": "Instances",
            "rds": "DB Instances",
            "lambda": "Functions",
            "dynamodb": "Tables",
            "sqs": "Queues",
            "sns": "Topics",
            "cloudfront": "Distributions",
            "iam": "Identities",
            "eks": "Clusters",
            "ecs": "Clusters/Services",
            "elb": "Load Balancers",
            "elbv2": "Load Balancers",
            "elasticache": "Cache Clusters",
        }
        return service_map.get(service_name.lower(), "Resources")

    def _derive_standard_arn(
        self,
        service_name: str,
        value: str,
        region: str,
        account_id: str,
    ) -> str:
        """Derivar ARN estándar en casos determinísticos (sin consultar AWS)."""
        svc = (service_name or "").lower()
        val = str(value or "").strip()
        reg = str(region or "").strip() or "us-east-1"
        acct = str(account_id or "").strip()
        if not val or not acct:
            return ""
        if val.startswith("arn:"):
            return val
        if svc == "ec2":
            mapping = [
                ("vpc-cidr-assoc-", "vpc-cidr-association"),
                ("i-", "instance"),
                ("vol-", "volume"),
                ("snap-", "snapshot"),
                ("subnet-", "subnet"),
                ("vpc-", "vpc"),
                ("sg-", "security-group"),
                ("rtb-", "route-table"),
                ("igw-", "internet-gateway"),
                ("nat-", "natgateway"),
                ("eni-", "network-interface"),
                ("eipalloc-", "elastic-ip"),
                ("eipassoc-", "elastic-ip-association"),
                ("vpce-", "vpc-endpoint"),
                ("lt-", "launch-template"),
                ("acl-", "network-acl"),
            ]
            lv = val.lower()
            for prefix, rtype in mapping:
                if lv.startswith(prefix):
                    return f"arn:aws:ec2:{reg}:{acct}:{rtype}/{val}"
        return ""

    def _normalize_resource_samples(
        self,
        service_name: str,
        samples: List[Any],
        arn_lookup: Optional[Dict[str, Dict[str, str]]] = None,
        account_id: str = "",
    ) -> List[Dict[str, str]]:
        """Normalizar muestras de recursos para render claro en web."""
        normalized: List[Dict[str, str]] = []
        svc_lookup = (arn_lookup or {}).get((service_name or "").lower(), {})
        for raw in samples or []:
            source_key = ""
            source_operation = ""
            source_entity_key = ""
            source_region = ""
            if isinstance(raw, dict):
                value = str(raw.get("value", "")).strip()
                source_key = str(raw.get("key", "")).strip().lower()
                source_operation = str(raw.get("operation", "")).strip()
                source_entity_key = str(raw.get("entity_key", "")).strip()
                source_region = str(raw.get("region", "")).strip()
            else:
                value = str(raw or "").strip()
            if not value:
                continue
            kind = "value"
            resolved_arn = ""
            if value.startswith("arn:"):
                kind = "arn"
                resolved_arn = value
            elif value.startswith("http://") or value.startswith("https://"):
                kind = "url"
            elif re.match(r"^\d{1,3}(?:\.\d{1,3}){3}/\d{1,2}$", value):
                kind = "cidr"
            elif re.match(r"^[a-z]{1,8}-[0-9a-f]+$", value, flags=re.IGNORECASE):
                kind = "id"
            elif "." in value and " " not in value:
                kind = "name"
            if not resolved_arn and svc_lookup:
                for cand in self._value_candidates_for_arn_lookup(value):
                    mapped = svc_lookup.get(cand)
                    if mapped:
                        resolved_arn = mapped
                        break
            if not resolved_arn:
                resolved_arn = self._derive_standard_arn(
                    service_name=service_name,
                    value=value,
                    region=source_region,
                    account_id=account_id,
                )
            subcategory = self._classify_resource_subcategory(
                service_name=service_name,
                source_key=source_key,
                value=value,
                operation=source_operation,
            )
            normalized.append({
                "value": value,
                "kind": kind,
                "resolved_arn": resolved_arn,
                "subcategory": subcategory,
                "key": source_key,
                "operation": source_operation,
                "entity_key": source_entity_key,
                "region": source_region,
            })
        return normalized

    def _classify_resource_subcategory(self, service_name: str, source_key: str, value: str, operation: str) -> str:
        """Clasificar subcategoría del recurso para visualización de inventario."""
        service = (service_name or "").lower()
        key = (source_key or "").lower()
        val = (value or "").lower()
        op = (operation or "").lower()

        rules = [
            ("cidrblockassociationset", "VPC CIDR Associations"),
            ("snapshot", "Snapshots"),
            ("volume", "Volumes"),
            ("instance", "Instances"),
            ("image", "AMIs"),
            ("bucket", "Buckets"),
            ("function", "Functions"),
            ("route", "Route Tables"),
            ("table", "Tables"),
            ("topic", "Topics"),
            ("queue", "Queues"),
            ("cluster", "Clusters"),
            ("service", "Services"),
            ("task", "Tasks"),
            ("database", "Databases"),
            ("dbinstance", "DB Instances"),
            ("dbcluster", "DB Clusters"),
            ("loadbalancer", "Load Balancers"),
            ("targetgroup", "Target Groups"),
            ("listener", "Listeners"),
            ("distribution", "Distributions"),
            ("cache", "Cache"),
            ("securitygroup", "Security Groups"),
            ("subnet", "Subnets"),
            ("vpc", "VPCs"),
            ("networkinterface", "Network Interfaces"),
            ("natgateway", "NAT Gateways"),
            ("internetgateway", "Internet Gateways"),
            ("user", "Users"),
            ("role", "Roles"),
            ("policy", "Policies"),
            ("group", "Groups"),
            ("key", "Keys"),
        ]

        for token, label in rules:
            if token in key:
                return label

        ec2_prefix = {
            "i-": "Instances",
            "vol-": "Volumes",
            "snap-": "Snapshots",
            "ami-": "AMIs",
            "sg-": "Security Groups",
            "subnet-": "Subnets",
            "vpc-": "VPCs",
            "rtb-": "Route Tables",
            "eni-": "Network Interfaces",
            "igw-": "Internet Gateways",
            "nat-": "NAT Gateways",
            "eipalloc-": "Elastic IPs",
            "eipassoc-": "Elastic IPs",
            "acl-": "Network ACLs",
            "lt-": "Launch Templates",
            "vpce-": "VPC Endpoints",
            "pcx-": "VPC Peering",
        }
        if service == "ec2":
            if val.startswith("vpc-cidr-assoc-"):
                return "VPC CIDR Associations"
            for prefix, label in ec2_prefix.items():
                if val.startswith(prefix):
                    return label
            if "describeimages" in op:
                return "AMIs"
            if "describesnapshots" in op:
                return "Snapshots"
            if "describevolumes" in op:
                return "Volumes"
            if "describeinstances" in op:
                return "Instances"

        if val.startswith("arn:"):
            arn_suffix = val.split(":", 5)[-1] if ":" in val else val
            head = arn_suffix.split("/", 1)[0].split(":", 1)[0]
            arn_map = {
                "instance": "Instances",
                "volume": "Volumes",
                "snapshot": "Snapshots",
                "image": "AMIs",
                "db": "DB Instances",
                "cluster": "Clusters",
                "table": "Tables",
                "bucket": "Buckets",
                "function": "Functions",
                "topic": "Topics",
                "queue": "Queues",
                "distribution": "Distributions",
                "user": "Users",
                "role": "Roles",
                "policy": "Policies",
            }
            if head in arn_map:
                return arn_map[head]

        return "Resources"

    def _is_inventory_resource_operation(self, service_name: str, operation: str) -> bool:
        """Determinar si una operación representa recursos reales del inventario."""
        svc = (service_name or "").lower()
        op = (operation or "").strip()
        if not op:
            return False
        op_lower = op.lower()

        svc_allow = {
            "ec2": {
                "DescribeInstances", "DescribeVolumes", "DescribeSnapshots",
                "DescribeVpcs", "DescribeSubnets", "DescribeSecurityGroups",
                "DescribeRouteTables", "DescribeNatGateways", "DescribeInternetGateways",
                "DescribeNetworkInterfaces", "DescribeVpcEndpoints", "DescribeAddresses",
                "DescribeLaunchTemplates",
            },
            "rds": {
                "DescribeDBInstances", "DescribeDBClusters", "DescribeDBSnapshots",
                "DescribeDBClusterSnapshots", "DescribeDBProxies",
                "DescribeDBProxyEndpoints", "DescribeDBSubnetGroups",
                "DescribeDBParameterGroups", "DescribeOptionGroups",
            },
            "s3": {"ListBuckets"},
            "lambda": {"ListFunctions"},
            "dynamodb": {"ListTables"},
            "sns": {"ListTopics"},
            "sqs": {"ListQueues"},
            "eks": {"ListClusters", "ListNodegroups", "ListAddons"},
            "ecs": {"ListClusters", "ListServices", "ListTasks"},
            "iam": {"ListUsers", "ListRoles", "ListPolicies", "ListGroups"},
            # Solo inventario desplegado (evita defaults/catálogo/plataforma)
            "elasticache": {
                "DescribeCacheClusters",
                "DescribeReplicationGroups",
                "DescribeServerlessCaches",
                "DescribeSnapshots",
                "DescribeServerlessCacheSnapshots",
            },
        }
        if svc in svc_allow:
            return op in svc_allow[svc]

        noisy_exact = [
            "DescribeSourceRegions",
            "DescribeCertificates",
            "DescribeDBEngineVersions",
            "DescribeDBMajorEngineVersions",
            "DescribeOrderableDBInstanceOptions",
            "DescribeEvents",
            "DescribePendingMaintenanceActions",
            "ListTags",
        ]
        for pattern in noisy_exact:
            if op == pattern:
                return False

        # Patrones de catálogo/metadata no desplegada (aplican transversalmente)
        noisy_contains = [
            "engineversion",
            "serviceupdate",
            "updateaction",
            "orderable",
            "offering",
            "reserved",
            "catalog",
            "recommendation",
            "events",
            "parametergroup",
            "optiongroup",
            "cachesecuritygroup",
            "default",
            "maintenance",
        ]
        for token in noisy_contains:
            if token in op_lower:
                return False

        noisy_prefix = [
            "Get",
            "DescribeSource",
            "DescribeAccount",
            "DescribeLimits",
        ]
        for pfx in noisy_prefix:
            if op.startswith(pfx):
                return False

        wildcard_patterns = [
            "Get*",
        ]
        for pattern in wildcard_patterns:
            if pattern.endswith("*"):
                if op.startswith(pattern[:-1]):
                    return False

        return op.startswith("List") or op.startswith("Describe")

    def _is_resource_signal_key(self, source_key: str) -> bool:
        """Detectar si una clave del payload representa identidad de recurso."""
        key = str(source_key or "").lower()
        if not key:
            return False
        leaf = key.split(".")[-1]
        # Remover índices residuales tipo field[0]
        leaf = re.sub(r"\[\d+\]", "", leaf)

        exact = {
            "arn", "resourcearn", "id", "name", "identifier", "queueurl",
            "bucket", "bucketname", "tablename", "functionname",
            "topicarn", "distributionid", "dbinstanceidentifier",
            "dbclusteridentifier", "vpcid", "subnetid", "instanceid",
            "volumeid", "snapshotid", "networkinterfaceid", "securitygroupid",
            "routetableid", "internetgatewayid", "natgatewayid",
        }
        if leaf in exact:
            return True
        if leaf.endswith("arn"):
            return True
        if leaf.endswith("id"):
            return True
        if leaf.endswith("name"):
            return True
        if leaf.endswith("identifier"):
            return True
        return False

    def _is_valid_ec2_id_like(self, value: str) -> bool:
        """Validar patrones de IDs de recursos EC2 para evitar ruido (e.g. 'local')."""
        v = str(value or "").strip().lower()
        if not v:
            return False
        if v.startswith("arn:aws:ec2:"):
            return True
        prefixes = (
            "i-", "vol-", "snap-", "ami-", "sg-", "subnet-", "vpc-",
            "rtb-", "igw-", "nat-", "eni-", "eipalloc-", "eipassoc-",
            "acl-", "lt-", "vpce-", "pcx-", "dopt-", "rtbassoc-",
            "vpc-cidr-assoc-", "ela-attach-",
        )
        return any(v.startswith(p) for p in prefixes)

    def _extract_service_resource_samples(
        self,
        service_name: str,
        service_data: Dict[str, Any],
        max_samples: int = 300,
        inventory_only: bool = True,
    ) -> Dict[str, Any]:
        """Extraer muestras de recursos por servicio leyendo archivos crudos de operaciones exitosas."""
        ignore_key_tokens = [
            "responsemetadata",
            "httpheaders",
            "requestid",
            "x-amzn",
            "x-amz",
            "nexttoken",
            "marker",
            "token",
            "pagination",
            "enginename",
            "engineversion",
            "dbparametergroupfamily",
            "description",
            "validfrom",
            "validtill",
            "status",
            "ownerid",
            "accountid",
            "privatednsnameoptionsonlaunch",
            "hostnametype",
            "enablelniatdeviceindex",
            "mappubliciponlaunch",
        ]
        op_candidates: List[Dict[str, Any]] = []
        for region_name, region_data in (service_data.get("regions", {}) or {}).items():
            for op in region_data.get("operations", []):
                if not op.get("success"):
                    continue
                file_rel = op.get("file")
                if not file_rel:
                    continue
                op_name = str(op.get("operation", ""))
                is_inventory_op = self._is_inventory_resource_operation(service_name, op_name)
                if inventory_only and not is_inventory_op:
                    continue
                if (not inventory_only) and is_inventory_op:
                    continue
                rank = 0
                op_lower = op_name.lower()
                if "list" in op_lower:
                    rank += 3
                if "describe" in op_lower:
                    rank += 2
                if "get" in op_lower:
                    rank += 1
                rc = int(op.get("resource_count", 0) or 0)
                rank += 4 if rc > 0 else 0
                op_candidates.append({
                    "operation": op_name,
                    "file": file_rel,
                    "region": region_name,
                    "rank": rank,
                    "resource_count": rc,
                })
        if not op_candidates:
            return {"samples": [], "operations": []}

        op_candidates.sort(key=lambda x: (x["rank"], x["resource_count"]), reverse=True)
        picked = op_candidates[:8]

        samples: List[Dict[str, str]] = []
        seen: Set[str] = set()
        used_ops: List[str] = []

        def _walk(node: Any, current_op: str = "", parent_key: str = ""):
            if len(samples) >= max_samples:
                return
            if isinstance(node, dict):
                for k, v in node.items():
                    if len(samples) >= max_samples:
                        return
                    key = str(k).lower()
                    full_key = f"{parent_key}.{key}" if parent_key else key
                    if isinstance(v, str):
                        v_clean = v.strip()
                        if any(tok in full_key for tok in ignore_key_tokens):
                            continue
                        if v_clean.startswith("Root=1-"):
                            continue
                        if re.match(r"^\d{12}$", v_clean):
                            continue
                        if re.match(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", v_clean, flags=re.IGNORECASE):
                            continue
                        if v_clean and len(v_clean) <= 220 and self._is_resource_signal_key(key):
                            # Guardrail específico EC2: filtra "ids" que no son recurso (e.g. local, cidrs, etc.)
                            if service_name.lower() == "ec2" and key.endswith("id"):
                                if not self._is_valid_ec2_id_like(v_clean):
                                    continue
                            canonical_key = re.sub(r"\[\d+\]", "[]", full_key)
                            unique_key = f"{canonical_key}|{v_clean}"
                            if unique_key not in seen:
                                seen.add(unique_key)
                                samples.append({
                                    "value": v_clean,
                                    "key": full_key,
                                    "operation": current_op,
                                    "entity_key": parent_key,
                                    "region": op.get("region", ""),
                                })
                    else:
                        _walk(v, current_op=current_op, parent_key=full_key)
            elif isinstance(node, list):
                for idx, item in enumerate(node):
                    if len(samples) >= max_samples:
                        return
                    indexed_parent = f"{parent_key}[{idx}]" if parent_key else f"[{idx}]"
                    _walk(item, current_op=current_op, parent_key=indexed_parent)

        for op in picked:
            full_path = self.run_dir / "raw" / op["file"]
            if not full_path.exists():
                continue
            try:
                with gzip.open(full_path, "rt", encoding="utf-8") as f:
                    payload = json.load(f)
                used_ops.append(op["operation"])
                data_node = payload.get("data", payload)
                _walk(data_node, current_op=op["operation"])
                if len(samples) >= max_samples:
                    break
            except Exception:
                continue

        return {"samples": samples, "operations": used_ops}

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
                improvement_plan_json = reports_dir / "improvement_plan.json"
                if improvement_plan_json.exists():
                    with open(improvement_plan_json, "r", encoding="utf-8") as f:
                        extra["improvement_plan_data"] = json.load(f)
                coverage_report_json = reports_dir / "coverage_report.json"
                if coverage_report_json.exists():
                    with open(coverage_report_json, "r", encoding="utf-8") as f:
                        extra["coverage_report"] = json.load(f)
                controls_catalog_json = reports_dir / "controls_catalog.json"
                if controls_catalog_json.exists():
                    with open(controls_catalog_json, "r", encoding="utf-8") as f:
                        extra["controls_catalog"] = json.load(f)
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
            if "improvement_plan_data" not in extra:
                improvement_plan_json = reports_dir / "improvement_plan.json"
                if improvement_plan_json.exists():
                    try:
                        with open(improvement_plan_json, "r", encoding="utf-8") as f:
                            extra["improvement_plan_data"] = json.load(f)
                    except Exception as e:
                        logger.debug("No se pudo cargar improvement_plan.json: %s", e)
            if "coverage_report" not in extra:
                coverage_report_json = reports_dir / "coverage_report.json"
                if coverage_report_json.exists():
                    try:
                        with open(coverage_report_json, "r", encoding="utf-8") as f:
                            extra["coverage_report"] = json.load(f)
                    except Exception as e:
                        logger.debug("No se pudo cargar coverage_report.json: %s", e)
            if "controls_catalog" not in extra:
                controls_catalog_json = reports_dir / "controls_catalog.json"
                if controls_catalog_json.exists():
                    try:
                        with open(controls_catalog_json, "r", encoding="utf-8") as f:
                            extra["controls_catalog"] = json.load(f)
                    except Exception as e:
                        logger.debug("No se pudo cargar controls_catalog.json: %s", e)
            if extra.get("coverage_report"):
                extra["phases_data"] = self._build_evaluation_phases_from_coverage(extra["coverage_report"])
            else:
                extra["phases_data"] = {}
            extra["caf_data"] = self._build_caf_data(data)
            extra["inventory_data"] = self._build_inventory_web_data(data)
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
