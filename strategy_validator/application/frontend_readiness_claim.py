from __future__ import annotations

"""Frontend readiness artifacts are opt-in at runtime (see FRONTEND_READINESS_CLAIM_ENABLE_ENV)."""

import json
import os
from pathlib import Path
from typing import Any

FRONTEND_READINESS_CLAIM_SCHEMA_VERSION = "single_tenant_frontend_readiness/v1"
FRONTEND_READINESS_CLAIM_ENV = "STRATEGY_VALIDATOR_FRONTEND_READINESS_CLAIM_PATH"
FRONTEND_READINESS_CLAIM_ENABLE_ENV = "STRATEGY_VALIDATOR_FRONTEND_READINESS_CLAIM_ENABLE"
FRONTEND_EXPECTED_PACKAGE = "ui/strategist-web"


def frontend_readiness_claim_enable_active() -> bool:
    raw = os.environ.get(FRONTEND_READINESS_CLAIM_ENABLE_ENV, "").strip().lower()
    return raw in ("1", "true", "yes", "on")


def default_frontend_readiness_claim_path(repo_root: Path | None = None) -> Path:
    root = repo_root or Path.cwd()
    return root / "artifacts" / "frontend_readiness" / "single_tenant_frontend_readiness.json"


def frontend_readiness_claim_path(repo_root: Path | None = None) -> Path:
    raw = os.environ.get(FRONTEND_READINESS_CLAIM_ENV, "").strip()
    if raw:
        return Path(raw)
    return default_frontend_readiness_claim_path(repo_root)


def load_frontend_readiness_claim(repo_root: Path | None = None) -> dict[str, Any]:
    path = frontend_readiness_claim_path(repo_root)
    payload: dict[str, Any] = {
        "schema_version": FRONTEND_READINESS_CLAIM_SCHEMA_VERSION,
        "claim_path": str(path),
        "frontend_readiness_claimed": False,
        "frontend_runtime_reachable": None,
        "claim_status": "NOT_CLAIMED",
        "claim_reason": "CLAIM_ARTIFACT_MISSING",
    }
    if not frontend_readiness_claim_enable_active():
        payload["claim_reason"] = (
            "CLAIM_OPT_IN_REQUIRED_ARTIFACT_PRESENT_BUT_IGNORED" if path.is_file() else "CLAIM_OPT_IN_REQUIRED"
        )
        return payload
    if not path.is_file():
        return payload
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        payload["claim_reason"] = "CLAIM_ARTIFACT_UNREADABLE"
        return payload
    if not isinstance(data, dict):
        payload["claim_reason"] = "CLAIM_ARTIFACT_INVALID"
        return payload

    checks = data.get("checks")
    checks_ok = isinstance(checks, dict) and bool(checks) and all(value is True for value in checks.values())
    valid = (
        data.get("schema_version") == FRONTEND_READINESS_CLAIM_SCHEMA_VERSION
        and data.get("deployment_model") == "single_tenant"
        and data.get("frontend_expected_package") == FRONTEND_EXPECTED_PACKAGE
        and data.get("ok") is True
        and data.get("frontend_readiness_claimed") is True
        and checks_ok
    )
    payload.update(data)
    payload["claim_path"] = str(path)
    payload["frontend_readiness_claimed"] = bool(valid)
    payload["frontend_runtime_reachable"] = bool(data.get("frontend_runtime_reachable")) if valid else None
    payload["claim_status"] = "CLAIMED" if valid else "NOT_CLAIMED"
    payload["claim_reason"] = "FORMAL_SINGLE_TENANT_FRONTEND_GATE_PASSED" if valid else "CLAIM_ARTIFACT_FAILED_VALIDATION"
    return payload


__all__ = [
    "FRONTEND_EXPECTED_PACKAGE",
    "FRONTEND_READINESS_CLAIM_ENABLE_ENV",
    "FRONTEND_READINESS_CLAIM_ENV",
    "FRONTEND_READINESS_CLAIM_SCHEMA_VERSION",
    "default_frontend_readiness_claim_path",
    "frontend_readiness_claim_enable_active",
    "frontend_readiness_claim_path",
    "load_frontend_readiness_claim",
]
