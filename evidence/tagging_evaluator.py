#!/usr/bin/env python3
"""
Evaluador de tags por servicio.

Extrae tags de Resource Groups Tagging API (GetResources) o de datos raw
por servicio, y devuelve un resumen de tags por servicio para reportes.
"""

import gzip
import json
import logging
import re
from pathlib import Path
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)


def _service_from_arn(arn: str) -> str:
    """Extraer nombre de servicio desde ARN. Ej: arn:aws:ec2:us-east-1:123:instance/i-1 -> ec2."""
    if not arn or not isinstance(arn, str):
        return "unknown"
    parts = arn.split(":")
    if len(parts) >= 4 and parts[2] == "aws":
        svc = parts[3]
        if svc == "s3" and len(parts) > 5:
            return "s3"
        if svc in ("ec2", "rds", "lambda", "dynamodb", "s3", "ecs", "eks", "backup", "kms"):
            return svc
        return svc
    return "unknown"


def _read_get_resources_raw(run_dir: Path) -> List[Dict]:
    """Leer GetResources desde raw (todas las regiones) y devolver lista de ResourceTagMapping."""
    raw_dir = run_dir / "raw" / "resourcegroupstaggingapi"
    if not raw_dir.exists():
        return []
    mappings = []
    for region_dir in raw_dir.iterdir():
        if not region_dir.is_dir():
            continue
        gz_file = region_dir / "GetResources.json.gz"
        if not gz_file.exists():
            continue
        try:
            with gzip.open(gz_file, "rt", encoding="utf-8") as f:
                d = json.load(f)
        except Exception as e:
            logger.debug("Error leyendo GetResources %s: %s", gz_file, e)
            continue
        if d.get("error"):
            continue
        data = d.get("data") or {}
        if isinstance(data, dict) and "data" in data:
            pages = data.get("data", [])
            for page in pages:
                if isinstance(page, dict) and "ResourceTagMappingList" in page:
                    mappings.extend(page.get("ResourceTagMappingList", []))
        elif isinstance(data, dict) and "ResourceTagMappingList" in data:
            mappings.extend(data.get("ResourceTagMappingList", []))
    return mappings


def evaluate(index: Dict, run_dir: Optional[Path] = None) -> Dict[str, Any]:
    """
    Evaluar tags por servicio desde Resource Groups Tagging API (GetResources).

    Returns:
        Dict con:
        - by_service: { servicio: { tag_keys: [...], resource_count: N } }
        - all_tag_keys: lista única de todas las claves
        - total_resources: total de recursos con tags
        - source: "resourcegroupstaggingapi" | "none"
        - error: mensaje si no se pudo evaluar
    """
    result = {
        "by_service": {},
        "all_tag_keys": [],
        "total_resources": 0,
        "source": "none",
        "error": None,
    }
    run_path = Path(run_dir) if run_dir else None
    if not run_path:
        result["error"] = "No se proporcionó run_dir para leer datos raw."
        return result

    mappings = _read_get_resources_raw(run_path)
    if not mappings:
        result["error"] = (
            "No hay datos de GetResources (Resource Groups Tagging API). "
            "Verifica permisos tag:GetResources en la política IAM."
        )
        return result

    result["source"] = "resourcegroupstaggingapi"
    result["total_resources"] = len(mappings)
    all_keys = set()

    for m in mappings:
        arn = m.get("ResourceARN", "")
        tags = m.get("Tags", []) or []
        service = _service_from_arn(arn)
        if service not in result["by_service"]:
            result["by_service"][service] = {"tag_keys": [], "resource_count": 0}
        result["by_service"][service]["resource_count"] += 1
        for t in tags:
            key = t.get("Key") or t.get("key")
            if key and key not in result["by_service"][service]["tag_keys"]:
                result["by_service"][service]["tag_keys"].append(key)
            if key:
                all_keys.add(key)

    for svc_data in result["by_service"].values():
        svc_data["tag_keys"] = sorted(svc_data["tag_keys"])
    result["all_tag_keys"] = sorted(all_keys)
    result["by_service"] = dict(sorted(result["by_service"].items()))

    return result
