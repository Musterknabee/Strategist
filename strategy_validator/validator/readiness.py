"""
Typed runtime readiness/self-check report.

Answers:
  - Is the runtime production-lawful?
  - What exact blockers exist?
  - Are market-data source policies acceptable?
  - Is ledger/storage config acceptable?
  - Is config/version/fingerprint integrity present?

The report is explicit and machine-usable (Pydantic model), not just log strings.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import List, Literal, Optional, Dict

from pydantic import BaseModel

from strategy_validator.core.config import load_config, AppConfig
from strategy_validator.core.enums import RuntimeMode
from strategy_validator.contracts.operational import (
    DeploymentReadiness,
    OperationalDiagnostics,
    ReadinessBlocker,
)
from strategy_validator.ledger._append_only import (
    resolve_database_path,
    _DEFAULT_DB_DIR,
    _DEFAULT_DB_NAME,
    get_schema_version_info,
    get_storage_posture,
)
from strategy_validator.validator.calibration_governance import calibration_governance_violations
from strategy_validator.validator.calibration_loader import load_calibration_artifact_from_path

def perform_readiness_check() -> DeploymentReadiness:
    """
    Perform a production-level readiness self-check.
    Returns a typed DeploymentReadiness contract.
    """
    config = load_config()
    policy = config.runtime_policy
    blockers: List[ReadinessBlocker] = []
    checks: Dict[str, bool] = {}
    storage_posture = get_storage_posture()

    # 1. Config Fingerprint
    config_dict = config.tribunal_thresholds.model_dump(mode="json")
    # Add policy fields to fingerprint
    config_dict["policy"] = policy.model_dump(mode="json")
    canonical = json.dumps(config_dict, sort_keys=True)
    fingerprint = hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:12]

    # 2. Ledger Path Safety
    try:
        db_path = resolve_database_path()
        is_default = (
            db_path.name == _DEFAULT_DB_NAME
            and db_path.parent.name == _DEFAULT_DB_DIR
        )
        checks["ledger_connectivity"] = True
    except Exception as e:
        blockers.append(ReadinessBlocker(code="LEDGER_ACCESS_FAILED", message=str(e)))
        db_path = None
        is_default = False
        checks["ledger_connectivity"] = False

    if db_path and policy.require_absolute_ledger_path:
        if not db_path.is_absolute():
            blockers.append(ReadinessBlocker(
                code="UNSAFE_LEDGER_PATH", 
                message=f"Production requires an absolute path. Got: {db_path}"
            ))
        if is_default:
            blockers.append(ReadinessBlocker(
                code="DEFAULT_LEDGER_PATH_FORBIDDEN", 
                message="Production cannot use default local path."
            ))

    # 3. Schema Integrity
    cur_v, exp_v = get_schema_version_info()
    checks["schema_compatibility"] = cur_v >= exp_v
    if cur_v < exp_v:
        blockers.append(ReadinessBlocker(
            code="INCOMPATIBLE_SCHEMA",
            message=f"Ledger schema version {cur_v} is behind required version {exp_v}."
        ))

    # 4. Calibration artifact (production fail-closed when CALIBRATED)
    if policy.mode == RuntimeMode.PRODUCTION and policy.capacity_impact_model == "CALIBRATED":
        cal_path = policy.calibration_artifact_path
        if not cal_path:
            blockers.append(ReadinessBlocker(
                code="CALIBRATION_ARTIFACT_MISSING",
                message="Production mode with capacity_impact_model=CALIBRATED requires calibration_artifact_path.",
                remediation_hint="Set STRATEGY_VALIDATOR_CALIBRATION_ARTIFACT_PATH to a CalibrationArtifactV1 JSON file.",
            ))
        else:
            art = load_calibration_artifact_from_path(cal_path)
            if art is None:
                blockers.append(ReadinessBlocker(
                    code="CALIBRATION_ARTIFACT_INVALID",
                    message=f"Calibration artifact at {cal_path} is missing or failed schema validation.",
                    remediation_hint="Fix the artifact file or switch STRATEGY_VALIDATOR_CAPACITY_IMPACT_MODEL to HEURISTIC.",
                ))
            else:
                gov = calibration_governance_violations(art, policy)
                if gov:
                    blockers.append(ReadinessBlocker(
                        code="CALIBRATION_GOVERNANCE_REJECTED",
                        message="; ".join(gov),
                        remediation_hint="Tighten the artifact (scores, curve spread, training_run_id) or relax governance env gates.",
                    ))

    # 5. Market Data Policy
    checks["source_policy_safe"] = True
    if policy.mode == RuntimeMode.PRODUCTION:
        if policy.allow_provisional_market_data:
            blockers.append(ReadinessBlocker(
                code="INSECURE_SOURCE_POLICY",
                message="Production mode must not allow PROVISIONAL market data."
            ))
            checks["source_policy_safe"] = False
        if policy.strict_production_mode and policy.allow_provisional_market_data:
            blockers.append(ReadinessBlocker(
                code="STRICT_MODE_INSECURE_SOURCE",
                message="Strict production mode requires allow_provisional_market_data=False."
            ))
            checks["source_policy_safe"] = False

    # 6. Explicit Context Requirements
    checks["explicit_context_ok"] = True
    if policy.require_explicit_evaluation_time or policy.require_explicit_market_data_subject_id:
        # The readiness check cannot verify that callers provide these values;
        # enforcement happens at adjudication time.  We only verify the policy is set.
        pass

    # Decision logic
    status = "READY"
    if blockers:
        status = "BLOCKED"
    elif not all(checks.values()):
        # If any check fails but no specific blocker was added, it's DEGRADED
        status = "DEGRADED"

    return DeploymentReadiness(
        status=status,
        checked_at_utc=datetime.now(timezone.utc),
        run_mode=policy.mode,
        config_fingerprint=fingerprint,
        schema_version=cur_v,
        expected_schema_version=exp_v,
        storage_backend=storage_posture["storage_backend"],
        storage_upgrade_status=storage_posture["storage_upgrade_status"],
        storage_upgrade_summary=storage_posture["storage_upgrade_summary"],
        blockers=blockers,
        warnings=[], # Implement warning logic if needed in future
        adjudication_allowed=status == "READY",
        checks=checks
    )

def generate_operational_diagnostics() -> OperationalDiagnostics:
    """Generate a typed operational visibility report."""
    config = load_config()
    readiness = perform_readiness_check()
    policy = config.runtime_policy

    # Determine market-data policy label
    if policy.strict_production_mode:
        md_policy_label = "STRICT_PRODUCTION"
    elif not policy.allow_provisional_market_data:
        md_policy_label = "NO_PROVISIONAL"
    elif not policy.allow_snapshot_market_data:
        md_policy_label = "LIVE_ONLY"
    else:
        md_policy_label = "PERMISSIVE"

    return OperationalDiagnostics(
        runtime_mode=config.mode,
        config_fingerprint=readiness.config_fingerprint,
        readiness_status=readiness.status,
        storage_backend=readiness.storage_backend,
        storage_upgrade_status=readiness.storage_upgrade_status,
        storage_upgrade_summary=readiness.storage_upgrade_summary,
        storage_target=str(resolve_database_path()),
        market_data_source_policy=md_policy_label,
        production_safe_adjudication_allowed=readiness.status == "READY",
        last_check_utc=datetime.now(timezone.utc).isoformat()
    )
