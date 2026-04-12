from __future__ import annotations
from datetime import datetime
from typing import List, Literal, Optional, Dict, Any
from pydantic import BaseModel, Field
from strategy_validator.core.enums import RuntimeMode, PromotionState

class ReadinessBlocker(BaseModel):
    """Reason why the system is not production-lawful."""
    code: str
    message: str
    severity: Literal["CRITICAL", "WARNING"] = "CRITICAL"
    remediation_hint: Optional[str] = None

class HealthStatus(BaseModel):
    """Overall system health report."""
    status: Literal["HEALTHY", "UNHEALTHY"]
    checked_at_utc: datetime
    summary: str
    issues: List[str] = []

class DeploymentReadiness(BaseModel):
    """
    Consolidated startup/deployment safety contract.
    Must be READY for production execution.
    """
    status: Literal["READY", "DEGRADED", "BLOCKED"]
    checked_at_utc: datetime
    run_mode: RuntimeMode
    config_fingerprint: str
    schema_version: int
    expected_schema_version: int
    blockers: List[ReadinessBlocker] = []
    warnings: List[ReadinessBlocker] = []
    adjudication_allowed: bool
    checks: Dict[str, bool] = {}

    model_config = {"extra": "forbid"}

class OperationalHeartbeat(BaseModel):
    """
    Machine-readable system heartbeat.
    Consolidates runtime mode, configuration, and readiness.
    """
    runtime_mode: RuntimeMode
    strict_production_mode: bool
    config_fingerprint: str
    readiness_status: Literal["READY", "DEGRADED", "BLOCKED"]
    blocker_count: int
    blocker_reasons: List[str]
    schema_version: int
    expected_schema_version: int
    storage_status_summary: str
    market_data_policy_summary: str
    adjudication_allowed: bool
    checked_at_utc: datetime

class DecisionTelemetry(BaseModel):
    """
    Structured telemetry for a specific adjudication decision.
    Sink-neutral and audit-ready.
    """
    experiment_id: str
    final_promotion_state: PromotionState
    canonical_gate_failures: List[str]
    runtime_mode: RuntimeMode
    config_fingerprint: str
    readiness_status_at_decision_time: Literal["READY", "DEGRADED", "BLOCKED"]
    production_policy_impacted: bool
    market_data_source_modes: Dict[str, str]
    evaluation_time_utc: Optional[datetime] = None
    market_data_subject_id: Optional[str] = None
    market_data_fallback_applied: bool = False
    market_data_fallback_reason: Optional[str] = None
    liquidity_freshness_status: Optional[str] = None
    borrow_freshness_status: Optional[str] = None
    liquidity_provider_status: Optional[str] = None
    borrow_provider_status: Optional[str] = None
    impact_model_mode: Optional[str] = None
    capacity_impact_model_policy: Optional[str] = None

class RuntimeBlockerSummary(BaseModel):
    """Explicit overview of a runtime blocker for operators."""
    blocker_code: str
    severity: Literal["CRITICAL", "WARNING"]
    reason: str
    remediation_hint: Optional[str] = None

class OperationalDiagnostics(BaseModel):
    """
    Typed operational observability report. Legacy naming maintained for internal wiring.
    Captures the heartbeat and safety state of the validator.
    """
    runtime_mode: RuntimeMode
    config_fingerprint: str
    readiness_status: Literal["READY", "DEGRADED", "BLOCKED"]
    storage_target: str
    market_data_source_policy: str
    production_safe_adjudication_allowed: bool
    system_load_summary: Optional[Dict[str, float]] = None
    last_check_utc: str

    model_config = {"extra": "forbid"}
