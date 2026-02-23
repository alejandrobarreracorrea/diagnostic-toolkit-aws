#!/usr/bin/env python3
"""
Generar nombre del directorio de run incluyendo cuenta AWS.

Cuando RUN_DIR no se especifica, se usa este módulo para crear un nombre
run-YYYYMMDD-HHMMSS-ACCOUNTID (o run-YYYYMMDD-HHMMSS si no hay credenciales).
"""

import os
import re
from datetime import datetime
from pathlib import Path


def _safe_account_suffix(account_id: str, account_alias: str = None) -> str:
    """Sufijo seguro para nombre de directorio: solo dígitos o alias sanitizado."""
    if account_id and re.match(r"^\d{12}$", account_id):
        return account_id
    if account_alias:
        # Permitir letras, números, guiones y guión bajo
        safe = re.sub(r"[^a-zA-Z0-9_-]", "-", account_alias).strip("-")
        if safe:
            return safe[:32]  # límite razonable de longitud
    return account_id or "unknown"


def get_run_dir(runs_base: str = "runs") -> str:
    """
    Obtener ruta del directorio para este run: runs/run-YYYYMMDD-HHMMSS-ACCOUNTID.
    Usa credenciales AWS para obtener account_id (y opcionalmente alias).
    Si no hay credenciales, devuelve runs/run-YYYYMMDD-HHMMSS.
    """
    timestamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    base = Path(runs_base)
    try:
        import boto3
        session = boto3.Session(
            profile_name=os.getenv("AWS_PROFILE"),
            region_name=os.getenv("AWS_REGION", "us-east-1"),
        )
        sts = session.client("sts")
        identity = sts.get_caller_identity()
        account_id = identity.get("Account")
        account_alias = None
        try:
            iam = session.client("iam")
            aliases = iam.list_account_aliases()
            if aliases.get("AccountAliases"):
                account_alias = aliases["AccountAliases"][0]
        except Exception:
            pass
        suffix = _safe_account_suffix(account_id or "", account_alias)
        name = f"run-{timestamp}-{suffix}"
    except Exception:
        name = f"run-{timestamp}"
    return str(base / name)


if __name__ == "__main__":
    print(get_run_dir())
