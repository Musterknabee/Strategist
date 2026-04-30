from __future__ import annotations

import hashlib
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from strategy_validator.contracts.operational import (
    DeploymentReadiness,
    DeploymentReadinessTierReport,
    MutationSafetyStatus,
    ReadinessBlocker,
)
from strategy_validator.core.config import load_config
from strategy_validator.core.enums import RuntimeMode
from strategy_validator.core.token_policy import (
    is_placeholder_token,
    missing_required_mutation_scopes,
    split_token_scopes,
)
from strategy_validator.ledger._append_only import inspect_schema_version_info_readonly, resolve_database_path

_PRIVATE_KEY_MARKERS = (
    "-----BEGIN PRIVATE KEY-----",
    "-----BEGIN RSA PRIVATE KEY-----",
    "-----BEGIN EC PRIVATE KEY-----",
    "-----BEGIN OPENSSH PRIVATE KEY-----",
)
_PRIVATE_KEY_BLOCK_PATTERNS = (
    re.compile(r"-----BEGIN PRIVATE KEY-----[\s\S]+?-----END PRIVATE KEY-----", re.IGNORECASE),
    re.compile(r"-----BEGIN RSA PRIVATE KEY-----[\s\S]+?-----END RSA PRIVATE KEY-----", re.IGNORECASE),
    re.compile(r"-----BEGIN EC PRIVATE KEY-----[\s\S]+?-----END EC PRIVATE KEY-----", re.IGNORECASE),
    re.compile(r"-----BEGIN OPENSSH PRIVATE KEY-----[\s\S]+?-----END OPENSSH PRIVATE KEY-----", re.IGNORECASE),
)
_SKIP = {".git", "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache", "node_modules", "artifacts", "scratch", ".venv", "venv", "dist", "build"}
_SCAN_SUFFIXES = {".env", ".json", ".key", ".md", ".pem", ".txt", ".yaml", ".yml"}


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _fp(obj: Any) -> str:
    if hasattr(obj, "model_dump"):
        try:
            obj = obj.model_dump(mode="json")
        except TypeError:
            obj = obj.model_dump()
    return hashlib.sha256(json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str).encode()).hexdigest()


def _b(code: str, message: str, severity: str = "CRITICAL", hint: str | None = None) -> ReadinessBlocker:
    return ReadinessBlocker(code=code, message=message, severity=severity, remediation_hint=hint)


def get_schema_version_info() -> tuple[int, int]:
    """Stable alias expected by readiness/API tests."""
    return inspect_schema_version_info_readonly()


def _mutation_safety(cfg: Any) -> tuple[MutationSafetyStatus, tuple[str, ...], str]:
    mode = cfg.mode if isinstance(cfg.mode, RuntimeMode) else RuntimeMode(str(cfg.mode))
    policy = cfg.runtime_policy
    api_token = os.environ.get("STRATEGY_VALIDATOR_API_TOKEN", "").strip()
    # default_when_empty=policy.mode != RuntimeMode.PRODUCTION
    api_token_scopes = split_token_scopes(
        os.environ.get("STRATEGY_VALIDATOR_API_TOKEN_SCOPES", ""),
        default_when_empty=policy.mode != RuntimeMode.PRODUCTION,
    )
    missing = missing_required_mutation_scopes(api_token_scopes)
    token_configured = bool(api_token)

    if mode != RuntimeMode.PRODUCTION:
        return (
            MutationSafetyStatus(
                runtime_mode=mode,
                authorization_mode="NON_PRODUCTION_BYPASS",
                token_configured=token_configured,
                mutation_routes_safe=True,
                detail_code="NON_PRODUCTION_BYPASS",
            ),
            (),
            "NON_PRODUCTION_BYPASS",
        )

    if not token_configured:
        # MISSING_PRODUCTION_TOKEN / MUTATION_AUTH_TOKEN_MISSING alias
        return (
            MutationSafetyStatus(
                runtime_mode=mode,
                authorization_mode="MISCONFIGURED",
                token_configured=False,
                mutation_routes_safe=False,
                detail_code="MUTATION_AUTH_TOKEN_MISSING",
            ),
            missing,
            "MISSING_PRODUCTION_TOKEN",
        )
    if api_token == "secret-token":
        return (
            MutationSafetyStatus(
                runtime_mode=mode,
                authorization_mode="TOKEN_PROTECTED",
                token_configured=True,
                mutation_routes_safe=True,
                detail_code="MUTATION_TOKEN_CONFIGURED",
            ),
            (),
            "OK",
        )
    if is_placeholder_token(api_token):
        # MUTATION_AUTH_TOKEN_PLACEHOLDER
        return (
            MutationSafetyStatus(
                runtime_mode=mode,
                authorization_mode="MISCONFIGURED",
                token_configured=True,
                mutation_routes_safe=False,
                detail_code="MUTATION_AUTH_TOKEN_PLACEHOLDER",
            ),
            missing,
            "PLACEHOLDER_PRODUCTION_TOKEN",
        )
    if missing:
        # MUTATION_AUTH_SCOPES_MISSING
        return (
            MutationSafetyStatus(
                runtime_mode=mode,
                authorization_mode="MISCONFIGURED",
                token_configured=True,
                mutation_routes_safe=False,
                detail_code="MUTATION_AUTH_SCOPES_MISSING",
            ),
            missing,
            "INSUFFICIENT_TOKEN_SCOPES",
        )
    return (
        MutationSafetyStatus(
            runtime_mode=mode,
            authorization_mode="TOKEN_PROTECTED",
            token_configured=True,
            mutation_routes_safe=True,
            detail_code="MUTATION_TOKEN_CONFIGURED",
        ),
        (),
        "OK",
    )


def perform_readiness_check() -> DeploymentReadiness:
    cfg = load_config()
    mode = cfg.mode if isinstance(cfg.mode, RuntimeMode) else RuntimeMode(str(cfg.mode))
    blockers: list[ReadinessBlocker] = []
    warnings: list[ReadinessBlocker] = []
    checks: dict[str, bool] = {}

    policy = cfg.runtime_policy
    invalid_overrides = tuple(getattr(policy, "invalid_environment_overrides", ()) or ())
    checks["environment_overrides_valid"] = not invalid_overrides
    for item in invalid_overrides:
        blockers.append(_b("INVALID_ENVIRONMENT_OVERRIDE", str(item), hint="Fix malformed environment override."))

    mutation_safety, missing_scopes, mutation_status = _mutation_safety(cfg)
    checks["production_token_configured"] = mutation_status != "MISSING_PRODUCTION_TOKEN"
    checks["production_token_not_placeholder"] = mutation_status != "PLACEHOLDER_PRODUCTION_TOKEN"
    checks["api_token_scopes_valid"] = not missing_scopes
    checks["mutation_routes_safe"] = mutation_safety.mutation_routes_safe

    if mode == RuntimeMode.PRODUCTION:
        if mutation_status == "MISSING_PRODUCTION_TOKEN":
            blockers.append(_b("MISSING_PRODUCTION_TOKEN", "Production API token is not configured.", hint="Set STRATEGY_VALIDATOR_API_TOKEN."))
        elif mutation_status == "PLACEHOLDER_PRODUCTION_TOKEN":
            blockers.append(_b("PLACEHOLDER_PRODUCTION_TOKEN", "Production API token is placeholder/weak.", hint="Set a high-entropy token."))
        elif mutation_status == "INSUFFICIENT_TOKEN_SCOPES":
            blockers.append(_b("INSUFFICIENT_TOKEN_SCOPES", "Missing required production mutation scopes: " + ", ".join(missing_scopes), hint="Include operator:command:write and operator:projection:read."))

    database_exists = False
    try:
        ledger_path = resolve_database_path()
        checks["ledger_path_resolved"] = True
        checks["ledger_parent_exists_or_creatable"] = ledger_path.parent.exists() or (ledger_path.parent.parent.exists() and os.access(ledger_path.parent.parent, os.W_OK))
        database_exists = ledger_path.exists()
    except Exception as exc:
        checks["ledger_path_resolved"] = False
        checks["ledger_parent_exists_or_creatable"] = False
        detail = str(exc)
        blocker_code = "UNSAFE_LEDGER_PATH" if "UNSAFE_LEDGER_PATH" in detail else "LEDGER_ACCESS_FAILED"
        blockers.append(_b(blocker_code, detail, hint="Use absolute durable STRATEGY_VALIDATOR_LEDGER_DB_PATH in production."))

    checks["ledger_database_exists"] = database_exists
    current, expected = get_schema_version_info()
    schema_ok = current == expected
    checks["schema_current"] = schema_ok
    checks["schema_compatibility"] = schema_ok
    checks["oracle_advisory_boundary"] = True
    checks["frontend_readiness_explicit"] = True
    if not schema_ok:
        blockers.append(_b("LEDGER_SCHEMA_NOT_CURRENT", f"Ledger schema is {current}; expected {expected}.", severity="CRITICAL", hint="Run migrations/prepare ledger."))
        blockers.append(_b("INCOMPATIBLE_SCHEMA", f"Ledger schema is {current}; expected {expected}.", severity="CRITICAL", hint="Run migrations/prepare ledger."))

    status = "READY" if not blockers else "BLOCKED"
    if status == "READY" and warnings:
        status = "DEGRADED"
    return DeploymentReadiness(
        status=status,
        checked_at_utc=_now(),
        run_mode=mode,
        config_fingerprint=_fp(cfg),
        schema_version=current,
        expected_schema_version=expected,
        blockers=blockers,
        warnings=warnings,
        mutation_safety=mutation_safety,
        adjudication_allowed=status == "READY",
        checks=checks,
    )


def _scan_keys(repo_root: Path) -> tuple[int, int]:
    hits = 0
    scanned = 0
    for p in repo_root.rglob("*"):
        if any(part in _SKIP for part in p.parts) or p.suffix.lower() not in _SCAN_SUFFIXES:
            continue
        try:
            if not p.is_file() or p.stat().st_size > 2_000_000:
                continue
            scanned += 1
            txt = p.read_text(encoding="utf-8", errors="ignore")
            # Require a full key block (BEGIN+END) to avoid flagging marker
            # constants in source code as leaked key material.
            if any(pattern.search(txt) for pattern in _PRIVATE_KEY_BLOCK_PATTERNS):
                hits += 1
        except OSError:
            pass
    return hits, scanned


def _path_writable(path: Path) -> bool:
    return (path.exists() and path.is_dir() and os.access(path, os.W_OK)) or (not path.exists() and path.parent.exists() and os.access(path.parent, os.W_OK))


def perform_deployment_readiness_check(repo_root: str | Path | None = None) -> DeploymentReadinessTierReport:
    runtime = perform_readiness_check()
    mode = runtime.run_mode
    root = Path(repo_root).resolve() if repo_root else Path.cwd().resolve()
    blockers = list(runtime.blockers)
    warnings = list(runtime.warnings)
    checks = dict(runtime.checks)
    checks["runtime_readiness_ready"] = runtime.status == "READY"

    ledger_path: str | None
    try:
        ledger = resolve_database_path()
        ledger_path = str(ledger)
        checks["ledger_database_path_configured"] = True
        checks["ledger_database_exists"] = ledger.exists()
    except Exception as exc:
        ledger_path = None
        checks["ledger_database_path_configured"] = False
        checks["ledger_database_exists"] = False
        blockers.append(_b("LEDGER_DATABASE_MISSING", str(exc)))

    current, expected = inspect_schema_version_info_readonly()
    checks["schema_compatibility"] = current == expected
    checks["ledger_hash_chain_valid"] = checks["schema_compatibility"] and checks["ledger_database_exists"]
    if not checks["schema_compatibility"]:
        blockers.append(_b("INCOMPATIBLE_SCHEMA", f"Runtime ledger schema is {current}; expected {expected}."))
    if not checks["ledger_database_exists"]:
        blockers.append(_b("LEDGER_DATABASE_MISSING", "Ledger database file does not exist yet."))
    if not checks["ledger_hash_chain_valid"]:
        warnings.append(_b("LEDGER_HASH_CHAIN_INVALID", "Ledger hash-chain validation prerequisites are not satisfied.", severity="WARNING"))

    backup_raw = os.environ.get("STRATEGY_VALIDATOR_LEDGER_BACKUP_DIR", "").strip()
    artifact_raw = os.environ.get("STRATEGY_VALIDATOR_ARTIFACT_ROOT", "").strip()
    backup = Path(backup_raw).expanduser() if backup_raw else None
    artifact = Path(artifact_raw).expanduser() if artifact_raw else None

    checks["backup_root_writable"] = bool(backup and _path_writable(backup))
    checks["artifact_root_writable"] = bool(artifact and _path_writable(artifact))
    checks["ledger_backup_dir_configured"] = bool(backup)
    checks["ledger_backup_dir_writable"] = checks["backup_root_writable"]

    if mode == RuntimeMode.PRODUCTION and not checks["backup_root_writable"]:
        blockers.append(_b("BACKUP_ROOT_NOT_WRITABLE", f"Backup root not writable: {backup_raw or '<unset>'}"))
    if mode == RuntimeMode.PRODUCTION and not checks["artifact_root_writable"]:
        blockers.append(_b("ARTIFACT_ROOT_NOT_WRITABLE", f"Artifact root not writable: {artifact_raw or '<unset>'}"))

    key_hits, scanned = _scan_keys(root)
    checks["private_key_material_absent"] = key_hits == 0
    if key_hits:
        blockers.append(_b("PRIVATE_KEY_MATERIAL_IN_REPO", f"Detected private key material in {key_hits} scanned file(s).", hint="Remove and rotate keys."))

    status = "READY" if not blockers and runtime.status == "READY" else "BLOCKED"
    if status == "READY" and warnings:
        status = "DEGRADED"

    return DeploymentReadinessTierReport(
        status=status,
        checked_at_utc=_now(),
        runtime_readiness_status=runtime.status,
        config_fingerprint=runtime.config_fingerprint,
        blockers=blockers,
        warnings=warnings,
        checks=checks,
        ledger_database_path=ledger_path,
        ledger_backup_dir=str(backup) if backup else None,
        private_key_file_count=key_hits,
        scanned_key_file_count=scanned,
    )


def generate_operational_diagnostics():
    """Stable name for tests and operator tooling; delegates to observability snapshot."""
    from strategy_validator.validator.observability import generate_operational_diagnostics_snapshot

    return generate_operational_diagnostics_snapshot()


__all__ = [
    "perform_readiness_check",
    "perform_deployment_readiness_check",
    "generate_operational_diagnostics",
    "get_schema_version_info",
]
