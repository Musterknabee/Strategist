from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from strategy_validator.application.frontend_readiness_claim import (
    frontend_readiness_claim_enable_active,
    load_frontend_readiness_claim,
)
from strategy_validator.application.paper_research_replay import latest_replay_verification_summary
from strategy_validator.application.release_publication import publish_release_readiness_bundle
from strategy_validator.providers.health import build_provider_research_spine_addon
from strategy_validator.application.strategic_horizon_readiness import get_strategic_horizon_readiness_payload
from strategy_validator.validator.services.integrity_gate_service import get_current_readiness
from strategy_validator.validator.readiness import perform_deployment_readiness_check, perform_readiness_check


def _canonical_from_runtime_status(status: str) -> str:
    normalized = (status or "UNKNOWN").upper()
    if normalized == "READY":
        return "OK"
    if normalized == "DEGRADED":
        return "DEGRADED"
    if normalized == "BLOCKED":
        return "BLOCKED"
    return "UNKNOWN"


def _provider_readiness_status(spine: dict[str, Any]) -> str:
    summary = spine.get("summary") if isinstance(spine, dict) else {}
    if not isinstance(summary, dict):
        return "UNKNOWN"
    issue_n = int(summary.get("non_ok_checked_count") or 0)
    pending_n = int(summary.get("pending_or_stub_count") or 0)
    if issue_n > 0:
        return "DEGRADED"
    if pending_n > 0:
        return "OPTIONAL_NOT_CONFIGURED"
    if bool(summary.get("sample_manifest_present")):
        return "OK"
    return "PENDING"


def _replay_readiness_status(repo_root: Path | None = None) -> str:
    replay = latest_replay_verification_summary(repo_root=repo_root)
    status = str(replay.get("status") or "UNKNOWN").upper()
    mismatch = int(replay.get("digest_mismatch_count") or 0)
    missing = int(replay.get("missing_artifact_count") or 0)
    if mismatch > 0 or status == "DEGRADED":
        return "DEGRADED"
    if status == "OK" and missing == 0:
        return "OK"
    return "PENDING"


def _frontend_readiness_status(repo_root: Path | None = None) -> tuple[str, bool]:
    claim = load_frontend_readiness_claim(repo_root)
    claimed = bool(claim.get("frontend_readiness_claimed"))
    if claimed:
        return "OK", True
    if frontend_readiness_claim_enable_active():
        return "NOT_CONFIGURED", False
    return "OPTIONAL_NOT_CONFIGURED", False


def get_runtime_readiness_report():
    """Return the full runtime readiness report through the application seam."""
    return perform_readiness_check()


def get_readiness_health_payload() -> dict[str, Any]:
    """Return a transport-neutral readiness summary for API/CLI surfaces."""
    readiness = get_current_readiness()
    warnings = getattr(readiness, 'warnings', [])
    mutation_safety = getattr(readiness, 'mutation_safety', None)
    root = Path.cwd()
    provider_spine = build_provider_research_spine_addon(
        env=os.environ,
        repo_root=root,
    )
    runtime_canonical = _canonical_from_runtime_status(readiness.status)
    provider_status = _provider_readiness_status(provider_spine)
    replay_status = _replay_readiness_status(root)
    frontend_status, frontend_claimed = _frontend_readiness_status(root)

    return {
        'schema_version': 'runtime_readiness_payload/v2',
        'ok': readiness.status == 'READY',
        'surface': 'readiness',
        'readiness_tier': 'runtime',
        'runtime_readiness_status': readiness.status,
        'canonical_status': runtime_canonical,
        'provider_readiness_status': provider_status,
        'replay_readiness_status': replay_status,
        'frontend_readiness_status': frontend_status,
        'frontend_readiness_claimed': frontend_claimed,
        'deployment_readiness_status': None,
        'status': readiness.status,
        'adjudication_allowed': readiness.adjudication_allowed,
        'blocker_codes': [blocker.code for blocker in readiness.blockers],
        'warning_codes': [warning.code for warning in warnings],
        'mutation_safety': (
            mutation_safety.model_dump(mode='json')
            if hasattr(mutation_safety, 'model_dump')
            else mutation_safety.dict()
            if mutation_safety is not None and hasattr(mutation_safety, 'dict')
            else None
        ),
        'provider_research_spine': provider_spine,
        'readiness_scope_disclaimer': 'Diagnostic readiness posture only; not deployment approval, operator signoff, or profitability evidence.',
    }



def get_deployment_readiness_payload(*, repo_root: str | Path | None = None) -> dict[str, Any]:
    """Return transport-neutral deployment readiness preflight details.

    Runtime readiness answers whether adjudication may run. Deployment readiness
    includes release/operator hygiene such as ledger hash-chain integrity, backup
    target configuration, and private-key material checks.
    """
    report = perform_deployment_readiness_check(repo_root=repo_root)
    return {
        'schema_version': 'deployment_readiness_payload/v2',
        'ok': report.status == 'READY',
        'surface': 'deployment_readiness',
        'readiness_tier': 'deployment',
        'status': report.status,
        'canonical_status': _canonical_from_runtime_status(report.status),
        'deployment_readiness_status': report.status,
        'runtime_readiness_status': report.runtime_readiness_status,
        'config_fingerprint': report.config_fingerprint,
        'blocker_codes': [blocker.code for blocker in report.blockers],
        'warning_codes': [warning.code for warning in report.warnings],
        'checks': dict(report.checks),
        'ledger_database_path': report.ledger_database_path,
        'ledger_backup_dir': report.ledger_backup_dir,
        'private_key_file_count': report.private_key_file_count,
        'scanned_key_file_count': report.scanned_key_file_count,
    }



def summarize_deployment_readiness_payload(*, repo_root: str | Path | None = None) -> dict[str, Any]:
    """Return a compact operator-facing deployment readiness summary."""
    payload = get_deployment_readiness_payload(repo_root=repo_root)
    failed_checks = [name for name, ok in payload["checks"].items() if ok is False]
    blocker_codes = list(payload["blocker_codes"])
    warning_codes = list(payload["warning_codes"])
    if blocker_codes:
        recommended_action = "BLOCK_DEPLOYMENT"
    elif warning_codes or failed_checks:
        recommended_action = "DEPLOY_WITH_GOVERNED_EXCEPTION_OR_FIX_WARNINGS"
    else:
        recommended_action = "DEPLOYMENT_PREFLIGHT_READY"
    return {
        "schema_version": "deployment_readiness_summary/v1",
        "ok": payload["ok"],
        "readiness_tier": "deployment",
        "status": payload["status"],
        "canonical_status": payload.get("canonical_status", "UNKNOWN"),
        "deployment_readiness_status": payload["status"],
        "recommended_action": recommended_action,
        "runtime_readiness_status": payload["runtime_readiness_status"],
        "config_fingerprint": payload["config_fingerprint"],
        "blocker_codes": blocker_codes,
        "warning_codes": warning_codes,
        "failed_checks": failed_checks,
        "ledger_database_path": payload["ledger_database_path"],
        "ledger_backup_dir": payload["ledger_backup_dir"],
    }


def publish_release_bundle_from_paths(
    *,
    policy_path: str | Path,
    keyed_host_fingerprint_path: str | Path,
    publication_path: str | Path,
    scope: str = 'FULL',
    burnin_artifact_paths: list[str | Path] | None = None,
) -> dict[str, object]:
    return publish_release_readiness_bundle(
        policy_path=Path(policy_path),
        keyed_host_fingerprint_path=Path(keyed_host_fingerprint_path),
        burnin_artifact_paths=[Path(item) for item in (burnin_artifact_paths or [])],
        scope=scope,
        publication_path=Path(publication_path),
    )
