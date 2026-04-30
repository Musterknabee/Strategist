from __future__ import annotations

from pathlib import Path
from typing import Any

from strategy_validator.application.release_publication import publish_release_readiness_bundle
from strategy_validator.application.strategic_horizon_readiness import get_strategic_horizon_readiness_payload
from strategy_validator.validator.services.integrity_gate_service import get_current_readiness
from strategy_validator.validator.readiness import perform_deployment_readiness_check, perform_readiness_check


def get_runtime_readiness_report():
    """Return the full runtime readiness report through the application seam."""
    return perform_readiness_check()


def get_readiness_health_payload() -> dict[str, Any]:
    """Return a transport-neutral readiness summary for API/CLI surfaces."""
    readiness = get_current_readiness()
    warnings = getattr(readiness, 'warnings', [])
    mutation_safety = getattr(readiness, 'mutation_safety', None)
    return {
        'schema_version': 'runtime_readiness_payload/v2',
        'ok': readiness.status == 'READY',
        'surface': 'readiness',
        'readiness_tier': 'runtime',
        'runtime_readiness_status': readiness.status,
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
