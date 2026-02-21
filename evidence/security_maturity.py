#!/usr/bin/env python3
"""
Evaluador del Modelo de Madurez en Seguridad de AWS.

Evalúa cada capacidad del modelo (https://maturitymodel.security.aws.dev/es/)
contra los datos recolectados (índice y evidence pack) y devuelve estado:
met, not_met, partial, not_evaluable.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

# Estados posibles por capacidad
STATUS_MET = "met"
STATUS_NOT_MET = "not_met"
STATUS_PARTIAL = "partial"
STATUS_NOT_EVALUABLE = "not_evaluable"


def _load_model() -> Dict:
    """Cargar modelo desde JSON."""
    path = Path(__file__).parent / "security_maturity_model.json"
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _check_service_enabled(
    services: Dict, service_name: str, operation_name: str
) -> bool:
    """
    Verificar si un servicio está habilitado según el índice.
    Busca la operación en todas las regiones y comprueba success y ausencia de errores bloqueantes.
    """
    if not services or service_name not in services:
        return False
    regions = services.get(service_name, {}).get("regions", {})
    op_norm = operation_name.lower().replace("_", "")
    for _region, region_data in regions.items():
        for op_info in region_data.get("operations", []):
            name = (op_info.get("operation") or "").lower().replace("_", "")
            if name == op_norm:
                err = op_info.get("error") or {}
                if isinstance(err, dict):
                    code = err.get("code", "")
                    msg = (err.get("message") or "").lower()
                    if code == "InvalidAccessException" and (
                        "not subscribed" in msg or "not enabled" in msg
                    ):
                        return False
                    if code in (
                        "NoSuchConfigurationRecorderException",
                        "NoSuchDeliveryChannelException",
                    ):
                        return False
                if op_info.get("success") is True:
                    return True
    return False


def _check_has_resources(
    services: Dict, service_name: str, operation_name: str, min_count: int = 1
) -> bool:
    """Verificar que una operación exista y tenga resource_count >= min_count (si está presente)."""
    if not services or service_name not in services:
        return False
    regions = services.get(service_name, {}).get("regions", {})
    op_norm = operation_name.lower().replace("_", "")
    total = 0
    for _region, region_data in regions.items():
        for op_info in region_data.get("operations", []):
            name = (op_info.get("operation") or "").lower().replace("_", "")
            if name == op_norm and op_info.get("success") is True:
                total += op_info.get("resource_count", 0) or 0
    return total >= min_count


def _check_operation_success(services: Dict, service_name: str, operation_name: str) -> bool:
    """Verificar que la operación exista y haya sido exitosa en al menos una región."""
    return _check_service_enabled(services, service_name, operation_name)


def evaluate(
    index: Dict,
    run_dir: Optional[Path] = None,
    evidence_pack: Optional[Dict] = None,
) -> Dict[str, Any]:
    """
    Evaluar todas las capacidades del modelo de madurez contra el índice (y opcionalmente evidence).

    Returns:
        Dict con:
        - source: URL del modelo
        - phases: lista de fases con order/name
        - results: lista de { phase, category, id, name, status, detail }
        - summary: { phase_id: { met, not_met, partial, not_evaluable, total } }
    """
    model = _load_model()
    services = index.get("services") or {}
    run_path = Path(run_dir) if run_dir else None

    results = []
    phase_order = {p["id"]: p["order"] for p in model["phases"]}

    for item in model["items"]:
        phase = item["phase"]
        category = item["category"]
        item_id = item["id"]
        name = item["name"]
        check = item.get("check") or "manual"

        status = STATUS_NOT_EVALUABLE
        detail = "Requiere revisión manual (proceso u organización)."

        if check == "manual":
            pass
        elif check == "security_hub":
            if _check_service_enabled(services, "securityhub", "DescribeHub"):
                status = STATUS_MET
                detail = "Security Hub está habilitado."
            else:
                status = STATUS_NOT_MET
                detail = "Security Hub no detectado o no habilitado."
        elif check == "config":
            if _check_service_enabled(services, "config", "DescribeConfigurationRecorders"):
                status = STATUS_MET
                detail = "AWS Config está habilitado."
            else:
                status = STATUS_NOT_MET
                detail = "AWS Config no detectado o sin configuration recorders."
        elif check == "cloudtrail":
            if _check_service_enabled(services, "cloudtrail", "ListTrails"):
                status = STATUS_MET
                detail = "CloudTrail está habilitado."
            else:
                status = STATUS_NOT_MET
                detail = "CloudTrail no detectado o sin trails."
        elif check == "guardduty":
            if _check_service_enabled(services, "guardduty", "ListDetectors"):
                status = STATUS_MET
                detail = "GuardDuty está habilitado."
            else:
                status = STATUS_NOT_MET
                detail = "GuardDuty no detectado o sin detectores."
        elif check == "billing_alarm":
            if _check_has_resources(services, "cloudwatch", "DescribeAlarms", 1) or _check_operation_success(
                services, "budgets", "DescribeBudgets"
            ):
                status = STATUS_MET
                detail = "Alarmas de billing o Budgets detectados."
            else:
                status = STATUS_NOT_MET
                detail = "No se detectaron alarmas de CloudWatch ni Budgets."
        elif check == "security_groups":
            if _check_has_resources(services, "ec2", "DescribeSecurityGroups", 1):
                status = STATUS_MET
                detail = "Security Groups en uso (revisar reglas restrictivas manualmente)."
            else:
                status = STATUS_NOT_MET
                detail = "No se detectaron security groups o EC2."
        elif check == "block_public_access":
            if _check_operation_success(services, "s3", "GetBucketPublicAccessBlock") or _check_operation_success(
                services, "ec2", "DescribeVpcs"
            ):
                status = STATUS_PARTIAL
                detail = "S3 o VPC detectados; verificar BPA y acceso público manualmente."
            else:
                status = STATUS_NOT_MET
                detail = "No se pudo verificar bloqueo de acceso público (revisar S3 BPA y EC2)."
        elif check == "macie":
            if _check_service_enabled(services, "macie2", "GetFindingsPublicationConfiguration") or _check_operation_success(
                services, "macie2", "ListS3Buckets"
            ):
                status = STATUS_MET
                detail = "Amazon Macie en uso."
            else:
                status = STATUS_NOT_MET
                detail = "Macie no detectado."
        elif check == "waf":
            if _check_operation_success(services, "wafv2", "ListWebACLs") or _check_operation_success(
                services, "waf", "ListWebACLs"
            ):
                status = STATUS_MET
                detail = "AWS WAF en uso."
            else:
                status = STATUS_NOT_MET
                detail = "WAF no detectado."
        elif check == "security_hub_findings":
            if _check_service_enabled(services, "securityhub", "DescribeHub"):
                status = STATUS_PARTIAL
                detail = "Security Hub habilitado; verificar que se actúe ante hallazgos críticos."
            else:
                status = STATUS_NOT_MET
                detail = "Security Hub no habilitado."
        elif check == "resilience_hub":
            if _check_service_enabled(services, "resiliencehub", "ListAppAssessments") or _check_operation_success(
                services, "resiliencehub", "DescribeAppVersionResourcesResolutionStatus"
            ):
                status = STATUS_MET
                detail = "Resilience Hub en uso."
            else:
                status = STATUS_NOT_MET
                detail = "Resilience Hub no detectado."
        elif check == "organizations":
            if _check_operation_success(services, "organizations", "DescribeOrganization") or _check_operation_success(
                services, "organizations", "ListRoots"
            ):
                status = STATUS_MET
                detail = "AWS Organizations en uso (revisar SCPs manualmente)."
            else:
                status = STATUS_NOT_MET
                detail = "Organizations no detectado."
        elif check == "iam_roles":
            if _check_has_resources(services, "iam", "ListRoles", 1):
                status = STATUS_PARTIAL
                detail = "Roles IAM detectados; verificar uso de credenciales temporales vs claves largas."
            else:
                status = STATUS_NOT_MET
                detail = "No se detectaron roles IAM."
        elif check == "imdsv2":
            if _check_has_resources(services, "ec2", "DescribeInstances", 1):
                status = STATUS_PARTIAL
                detail = "Instancias EC2 detectadas; verificar IMDSv2 en cada instancia."
            else:
                status = STATUS_NOT_EVALUABLE
                detail = "No hay instancias EC2 en el inventario."
        elif check == "inspector":
            if _check_service_enabled(services, "inspector2", "ListFindings") or _check_operation_success(
                services, "inspector", "ListFindings"
            ):
                status = STATUS_MET
                detail = "Amazon Inspector en uso."
            else:
                status = STATUS_NOT_MET
                detail = "Inspector no detectado."
        elif check == "ssm":
            if _check_has_resources(services, "ssm", "DescribeInstanceInformation", 1) or _check_operation_success(
                services, "ssm", "DescribeInstanceInformation"
            ):
                status = STATUS_MET
                detail = "Systems Manager con instancias gestionadas."
            else:
                status = STATUS_NOT_MET
                detail = "Systems Manager sin instancias gestionadas o no en uso."
        elif check == "vpcs":
            if _check_has_resources(services, "ec2", "DescribeVpcs", 1):
                status = STATUS_MET
                detail = "VPCs en uso (revisar segmentación pública/privada)."
            else:
                status = STATUS_NOT_MET
                detail = "No se detectaron VPCs."
        elif check == "kms":
            if _check_operation_success(services, "kms", "ListKeys") or _check_has_resources(
                services, "kms", "ListKeys", 1
            ):
                status = STATUS_MET
                detail = "KMS en uso (revisar cifrado en reposo por servicio)."
            else:
                status = STATUS_NOT_MET
                detail = "KMS no detectado."
        elif check == "backup":
            if _check_operation_success(services, "backup", "ListBackupPlans") or _check_has_resources(
                services, "backup", "ListBackupPlans", 1
            ):
                status = STATUS_MET
                detail = "AWS Backup en uso."
            else:
                status = STATUS_PARTIAL
                detail = "AWS Backup no detectado; pueden existir backups nativos por servicio."
        elif check == "secrets_manager":
            if _check_operation_success(services, "secretsmanager", "ListSecrets"):
                status = STATUS_MET
                detail = "Secrets Manager en uso."
            else:
                status = STATUS_NOT_MET
                detail = "Secrets Manager no detectado."
        elif check == "multi_az":
            if _check_has_resources(services, "ec2", "DescribeVpcs", 1) or _check_has_resources(
                services, "rds", "DescribeDBInstances", 1
            ):
                status = STATUS_PARTIAL
                detail = "Recursos detectados; verificar multi-AZ por carga de trabajo."
            else:
                status = STATUS_NOT_EVALUABLE
                detail = "No hay suficientes datos para evaluar multi-AZ."
        elif check == "cloudformation":
            if _check_has_resources(services, "cloudformation", "DescribeStacks", 1) or _check_operation_success(
                services, "cloudformation", "ListStacks"
            ):
                status = STATUS_MET
                detail = "CloudFormation en uso (IaC)."
            else:
                status = STATUS_NOT_MET
                detail = "CloudFormation no detectado."
        elif check == "tags":
            if _check_has_resources(services, "ec2", "DescribeTags", 1) or _check_operation_success(
                services, "resourcegroupstaggingapi", "GetResources"
            ):
                status = STATUS_PARTIAL
                detail = "Uso de tags detectado; revisar estrategia de etiquetado."
            else:
                status = STATUS_NOT_MET
                detail = "No se pudo verificar uso de tags."
        elif check == "cognito":
            if _check_operation_success(services, "cognito-idp", "ListUserPools") or _check_operation_success(
                services, "cognito-identity", "ListIdentityPools"
            ):
                status = STATUS_MET
                detail = "Amazon Cognito en uso (CIAM)."
            else:
                status = STATUS_NOT_MET
                detail = "Cognito no detectado."
        elif check == "image_builder":
            if _check_operation_success(services, "imagebuilder", "ListImagePipelineImages") or _check_operation_success(
                services, "imagebuilder", "ListImagePipelines"
            ):
                status = STATUS_MET
                detail = "EC2 Image Builder en uso."
            else:
                status = STATUS_NOT_MET
                detail = "Image Builder no detectado."
        elif check == "nacls":
            if _check_has_resources(services, "ec2", "DescribeNetworkAcls", 1):
                status = STATUS_PARTIAL
                detail = "NACLs en uso; revisar control de tráfico saliente."
            else:
                status = STATUS_NOT_MET
                detail = "NACLs no detectados."
        elif check == "acm":
            if _check_operation_success(services, "acm", "ListCertificates") or _check_has_resources(
                services, "acm", "ListCertificates", 1
            ):
                status = STATUS_MET
                detail = "ACM en uso (certificados para cifrado en tránsito)."
            else:
                status = STATUS_NOT_MET
                detail = "ACM no detectado."
        elif check == "eventbridge":
            if _check_has_resources(services, "events", "ListRules", 1) or _check_operation_success(
                services, "events", "ListRules"
            ):
                status = STATUS_MET
                detail = "EventBridge/CloudWatch Events en uso (automatización)."
            else:
                status = STATUS_NOT_MET
                detail = "EventBridge no detectado."
        elif check == "detective":
            if _check_service_enabled(services, "detective", "ListGraphs") or _check_operation_success(
                services, "detective", "ListGraphs"
            ):
                status = STATUS_MET
                detail = "Amazon Detective en uso."
            else:
                status = STATUS_NOT_MET
                detail = "Detective no detectado."
        elif check == "shield":
            if _check_operation_success(services, "shield", "DescribeSubscription") or _check_operation_success(
                services, "shield", "GetSubscriptionState"
            ):
                status = STATUS_MET
                detail = "AWS Shield en uso."
            else:
                status = STATUS_NOT_MET
                detail = "Shield no detectado (Shield Standard está siempre activo)."
        elif check == "flow_logs":
            if _check_operation_success(services, "ec2", "DescribeFlowLogs") or _check_has_resources(
                services, "ec2", "DescribeFlowLogs", 1
            ):
                status = STATUS_MET
                detail = "VPC Flow Logs en uso."
            else:
                status = STATUS_NOT_MET
                detail = "VPC Flow Logs no detectados."
        elif check == "lambda":
            if _check_has_resources(services, "lambda", "ListFunctions", 1):
                status = STATUS_PARTIAL
                detail = "Lambda en uso (servicios abstractos)."
            else:
                status = STATUS_NOT_MET
                detail = "Lambda no detectado."
        elif check == "access_analyzer":
            if _check_operation_success(services, "accessanalyzer", "ListAnalyzers") or _check_operation_success(
                services, "accessanalyzer", "ListFindings"
            ):
                status = STATUS_MET
                detail = "IAM Access Analyzer en uso."
            else:
                status = STATUS_NOT_MET
                detail = "Access Analyzer no detectado."
        elif check == "security_contacts":
            if _check_operation_success(services, "account", "GetAlternateContact") or _check_operation_success(
                services, "account", "ListRegions"
            ):
                status = STATUS_PARTIAL
                detail = "API de cuenta disponible; verificar contactos de seguridad en la consola."
            else:
                status = STATUS_NOT_EVALUABLE
                detail = "No se pudo verificar contactos de seguridad (revisión manual)."
        elif check == "choose_regions":
            if services:
                status = STATUS_PARTIAL
                detail = "Regiones en uso detectadas; revisar restricción de regiones en Organizations/SCP."
            else:
                status = STATUS_NOT_EVALUABLE
                detail = "Revisión manual de política de regiones."
        elif check == "mfa":
            if _check_operation_success(services, "iam", "GetAccountSummary"):
                status = STATUS_PARTIAL
                detail = "IAM en uso; verificar MFA para usuarios raíz y privilegiados en la consola."
            else:
                status = STATUS_NOT_EVALUABLE
                detail = "No se pudo evaluar MFA (revisión manual en IAM)."
        elif check == "root_protection":
            if _check_operation_success(services, "iam", "GetAccountSummary"):
                status = STATUS_PARTIAL
                detail = "Verificar MFA en cuenta root y no usar root para operaciones diarias."
            else:
                status = STATUS_NOT_EVALUABLE
                detail = "Revisión manual de protección de cuenta root."
        elif check == "identity_federation":
            if _check_operation_success(services, "iam", "ListSAMLProviders") or _check_has_resources(
                services, "iam", "ListOpenIDConnectProviders", 1
            ):
                status = STATUS_MET
                detail = "Proveedores de identidad federada detectados."
            else:
                status = STATUS_NOT_MET
                detail = "Federación de identidades no detectada (IAM IdP o roles para IdP)."

        results.append({
            "phase": phase,
            "category": category,
            "id": item_id,
            "name": name,
            "status": status,
            "detail": detail,
        })

    # Resumen por fase
    summary = {}
    for pid in phase_order:
        summary[pid] = {"met": 0, "not_met": 0, "partial": 0, "not_evaluable": 0, "total": 0}
    for r in results:
        s = summary[r["phase"]]
        s["total"] += 1
        s[r["status"]] = s.get(r["status"], 0) + 1

    return {
        "source": model.get("source", "https://maturitymodel.security.aws.dev/es/"),
        "phases": model["phases"],
        "results": results,
        "summary": summary,
    }
