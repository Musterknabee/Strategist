from __future__ import annotations
import json
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any

from strategy_validator.core.config import load_config
from strategy_validator.contracts.operational import (
    HealthStatus,
    DeploymentReadiness,
    OperationalHeartbeat,
    DecisionTelemetry,
    RuntimeBlockerSummary,
    OperationalDiagnostics,
)
from strategy_validator.validator.readiness import perform_readiness_check
from strategy_validator.ledger._append_only import resolve_database_path, get_schema_version_info
from strategy_validator.contracts.experiments import AdjudicationDecision

def compute_heartbeat() -> OperationalHeartbeat:
    """Consolidated system heartbeat for machine ingestion."""
    config = load_config()
    readiness = perform_readiness_check()
    cur_v, exp_v = get_schema_version_info()
    
    try:
        storage_summary = f"Path: {resolve_database_path()}"
    except Exception as e:
        storage_summary = f"ERROR: {e}"

    return OperationalHeartbeat(
        runtime_mode=config.mode,
        strict_production_mode=config.runtime_policy.strict_production_mode,
        config_fingerprint=readiness.config_fingerprint,
        readiness_status=readiness.status,
        blocker_count=len(readiness.blockers),
        blocker_reasons=[b.message for b in readiness.blockers],
        schema_version=cur_v,
        expected_schema_version=exp_v,
        storage_status_summary=storage_summary,
        market_data_policy_summary="STRICT" if not config.runtime_policy.allow_provisional_market_data else "PERMISSIVE",
        adjudication_allowed=readiness.adjudication_allowed,
        mutation_safety=readiness.mutation_safety,
        checked_at_utc=datetime.now(timezone.utc)
    )

def compute_health() -> HealthStatus:
    """High-level health checking."""
    heartbeat = compute_heartbeat()
    status = "HEALTHY" if heartbeat.readiness_status == "READY" else "UNHEALTHY"
    
    return HealthStatus(
        status=status,
        checked_at_utc=heartbeat.checked_at_utc,
        summary=f"Status: {heartbeat.readiness_status}. Blockers: {heartbeat.blocker_count}",
        issues=heartbeat.blocker_reasons
    )

def generate_operational_diagnostics_snapshot() -> OperationalDiagnostics:
    """Operational diagnostics snapshot aligned with readiness and heartbeat exports."""
    readiness = perform_readiness_check()
    heartbeat = compute_heartbeat()
    return OperationalDiagnostics(
        runtime_mode=heartbeat.runtime_mode,
        config_fingerprint=heartbeat.config_fingerprint,
        readiness_status=heartbeat.readiness_status,
        storage_target=heartbeat.storage_status_summary,
        market_data_source_policy=heartbeat.market_data_policy_summary,
        production_safe_adjudication_allowed=heartbeat.adjudication_allowed,
        mutation_safety=readiness.mutation_safety,
        last_check_utc=heartbeat.checked_at_utc.isoformat(),
    )


def generate_decision_telemetry(decision: AdjudicationDecision, experiment_id: str) -> DecisionTelemetry:
    """Materialize telemetry from an adjudication decision."""
    readiness = perform_readiness_check()
    
    # Identify gate failures
    failures = [g.gate_name for g in decision.gate_results if not g.passed]
    
    # Check if production policy caused the final state
    policy_impacted = any("STRICT_PRODUCTION_BLOCKER" in n or "PRODUCTION_POLICY_VIOLATION" in n for n in decision.summary_notes)
    
    # Market data source mode summary
    source_modes = {}
    fallback_applied = False
    fallback_reason = None
    liq_fresh = None
    brw_fresh = None
    liq_prov = None
    brw_prov = None
    impact_mode = None
    cap_policy = None
    if decision.execution_report and decision.execution_report.market_data_provenance:
        p = decision.execution_report.market_data_provenance
        source_modes["liquidity"] = p.liquidity_source_mode or "NONE"
        source_modes["borrow"] = p.borrow_source_mode or "NONE"
        fallback_applied = bool(p.fallback_applied)
        fallback_reason = p.fallback_reason
        liq_fresh = p.liquidity_freshness_status
        brw_fresh = p.borrow_freshness_status
        liq_prov = p.liquidity_provider_status
        brw_prov = p.borrow_provider_status
    if decision.execution_report:
        impact_mode = decision.execution_report.impact_model_mode
    try:
        cap_policy = load_config().runtime_policy.capacity_impact_model
    except Exception:
        cap_policy = None

    return DecisionTelemetry(
        experiment_id=experiment_id,
        final_promotion_state=decision.new_state,
        canonical_gate_failures=failures,
        runtime_mode=decision.runtime_mode or readiness.run_mode,
        config_fingerprint=decision.config_fingerprint or readiness.config_fingerprint,
        readiness_status_at_decision_time=readiness.status,
        production_policy_impacted=policy_impacted,
        market_data_source_modes=source_modes,
        evaluation_time_utc=decision.evaluation_time_utc,
        market_data_subject_id=decision.market_data_subject_id,
        market_data_fallback_applied=fallback_applied,
        market_data_fallback_reason=fallback_reason,
        liquidity_freshness_status=liq_fresh,
        borrow_freshness_status=brw_fresh,
        liquidity_provider_status=liq_prov,
        borrow_provider_status=brw_prov,
        impact_model_mode=impact_mode,
        capacity_impact_model_policy=cap_policy,
    )

def export_operational_state(format: str = "json") -> str:
    """Sink-neutral structured export of operational state."""
    heartbeat = compute_heartbeat()
    health = compute_health()
    
    diagnostics = generate_operational_diagnostics_snapshot()

    data = {
        "heartbeat": heartbeat.model_dump(mode="json"),
        "health": health.model_dump(mode="json"),
        "operational_diagnostics": diagnostics.model_dump(mode="json"),
        "mutation_safety": diagnostics.mutation_safety.model_dump(mode="json"),
        "timestamp_utc": datetime.now(timezone.utc).isoformat()
    }
    
    if format == "json":
        return json.dumps(data, indent=2)
    else:
        raise ValueError(f"Unsupported export format: {format}")

def get_runtime_blocker_summaries() -> List[RuntimeBlockerSummary]:
    """Explicit overview of current runtime blockers with remediation hints."""
    readiness = perform_readiness_check()
    summaries = []
    
    for b in readiness.blockers:
        summaries.append(RuntimeBlockerSummary(
            blocker_code=b.code,
            severity="CRITICAL",
            reason=b.message,
            remediation_hint=_get_hint_for_code(b.code)
        ))
    
    return summaries

def _get_hint_for_code(code: str) -> Optional[str]:
    hints = {
        "UNSAFE_LEDGER_PATH": "Set STRATEGY_VALIDATOR_LEDGER_DB_PATH to an absolute path.",
        "DEFAULT_LEDGER_PATH_FORBIDDEN": "Do not rely on default path in production. Set STRATEGY_VALIDATOR_LEDGER_DB_PATH.",
        "INCOMPATIBLE_SCHEMA": "Run 'strategy-validator-migrate' to upgrade the forensic ledger.",
        "MISSING_PRODUCTION_TOKEN": "Set STRATEGY_VALIDATOR_API_TOKEN to a strong production token.",
        "PLACEHOLDER_PRODUCTION_TOKEN": "Replace placeholder STRATEGY_VALIDATOR_API_TOKEN with a strong token.",
        "INSUFFICIENT_TOKEN_SCOPES": "Include operator:command:write and operator:projection:read in STRATEGY_VALIDATOR_API_TOKEN_SCOPES.",
        "INSECURE_SOURCE_POLICY": "Set STRATEGY_VALIDATOR_SOURCE_POLICY to STRICT in production.",
        "LEDGER_ACCESS_FAILED": "Check file permissions or path existence for the ledger DB.",
        "CALIBRATION_ARTIFACT_MISSING": "Set STRATEGY_VALIDATOR_CALIBRATION_ARTIFACT_PATH or switch CAPACITY_IMPACT_MODEL to HEURISTIC.",
        "CALIBRATION_ARTIFACT_INVALID": "Fix CalibrationArtifactV1 JSON or switch STRATEGY_VALIDATOR_CAPACITY_IMPACT_MODEL to HEURISTIC.",
    }
    return hints.get(code)
