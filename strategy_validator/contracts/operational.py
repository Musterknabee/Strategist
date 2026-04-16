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


RolloutHostKind = Literal["AGENT_HOST", "KEYED_OPERATOR_HOST"]
ReleaseDecision = Literal[
    "KEEP_CURRENT_RELEASE",
    "CANDIDATE_RC2",
    "BLOCK_AND_INVESTIGATE",
    "ROLLBACK_RECOMMENDED",
]
DecisionClassification = Literal[
    "WITHIN_BOUNDS",
    "RUNTIME_FAILURE",
    "DATA_QUALITY_DEGRADATION",
    "ENVIRONMENTAL_NONCONFORMANCE",
    "EVIDENCE_INTEGRITY_FAILURE",
    "POLICY_MISMATCH",
]
SignoffStatus = Literal["APPROVED", "WITHHELD"]
ReleaseStance = Literal[
    "KEEP_CURRENT_BASELINE",
    "KEEP_CURRENT_BASELINE_WITH_GOVERNED_EXCEPTION",
    "SIGNOFF_WITHHELD",
    "ROLLBACK_RECOMMENDED",
]


class KeyedHostFingerprint(BaseModel):
    """Secret-safe fingerprint for the shell/session used to run rollout checks."""
    generated_at_utc: datetime
    host_kind: RolloutHostKind
    host_label: str
    interface_freeze_id: str
    runtime_mode: RuntimeMode
    config_fingerprint: str
    policy_sha256: str
    git_commit: Optional[str] = None
    git_tag: Optional[str] = None
    env_presence: Dict[str, bool] = Field(default_factory=dict)
    env_value_sha256: Dict[str, str] = Field(default_factory=dict)

    model_config = {"extra": "forbid"}


class RolloutScope(BaseModel):
    """Explicit boundary of controlled rollout actions."""
    environment: Literal["staging", "paper", "production_shadow", "unknown"] = "unknown"
    provider: str
    symbols: List[str] = Field(default_factory=list)
    allowed_actions: List[str] = Field(default_factory=list)
    operator_signoff_required: bool = True

    model_config = {"extra": "forbid"}


class ControlledRolloutBundle(BaseModel):
    """Frozen operational rollout bundle for audit and signoff."""
    generated_at_utc: datetime
    runtime_mode: RuntimeMode
    config_fingerprint: str
    policy_sha256: str
    interface_freeze_id: str
    release_commit: Optional[str] = None
    release_tag: Optional[str] = None
    provider_source_policy_summary: str
    keyed_host_fingerprint_path: str
    burnin_artifact_paths: List[str] = Field(default_factory=list)
    scope: RolloutScope
    operator_signoff_name: Optional[str] = None
    operator_signoff_utc: Optional[datetime] = None

    model_config = {"extra": "forbid"}


class DailyOperationsChecklist(BaseModel):
    """Daily machine/human checklist for controlled rollout period."""
    generated_at_utc: datetime
    startup_check_passed: bool
    readiness_status: Literal["READY", "DEGRADED", "BLOCKED"]
    provider_availability_ok: bool
    freshness_anomaly_count: int = 0
    fallback_count: int = 0
    circuit_open_count: int = 0
    auth_rate_limit_count: int = 0
    timeout_count: int = 0
    retry_count: int = 0
    telemetry_sink_healthy: bool
    policy_change_justified: bool = False
    policy_change_reasons: List[str] = Field(default_factory=list)

    model_config = {"extra": "forbid"}


class RuntimeEvidenceReview(BaseModel):
    """Auditable release recommendation from explicit rules."""
    generated_at_utc: datetime
    decision: ReleaseDecision
    primary_classification: DecisionClassification = "WITHIN_BOUNDS"
    secondary_classifications: List[DecisionClassification] = Field(default_factory=list)
    signoff_status: SignoffStatus = "WITHHELD"
    governed_exception_eligible: bool = False
    governed_exception_codes: List[str] = Field(default_factory=list)
    reasons: List[str] = Field(default_factory=list)
    observe_only_flags: List[str] = Field(default_factory=list)
    must_fix_flags: List[str] = Field(default_factory=list)

    model_config = {"extra": "forbid"}


class ControlledRolloutRules(BaseModel):
    """Explicit rollout thresholds for checklist and release recommendations."""
    policy_change_stale_floor: int = 10
    policy_change_stale_fraction_denominator: int = 3
    policy_change_timeout_floor: int = 5
    policy_change_timeout_fraction_denominator: int = 4
    policy_change_circuit_floor: int = 10
    policy_change_circuit_fraction_denominator: int = 3
    policy_change_auth_rate_limit_floor: int = 3
    policy_change_auth_rate_limit_fraction_denominator: int = 5
    decision_auth_rate_limit_block_floor: int = 5
    decision_circuit_block_floor: int = 20

    model_config = {"extra": "forbid"}


class EvidenceResourceDescriptor(BaseModel):
    """Digest-anchored descriptor for a rollout evidence artifact."""
    name: str
    path: str
    digest: Dict[str, str]
    size_bytes: int = Field(ge=0)
    media_type: Optional[str] = None

    model_config = {"extra": "forbid"}


class ClosureSnapshotOperationalSummary(BaseModel):
    """Minimal operational truth captured by the canonical closure snapshot."""
    startup_check_passed: bool
    readiness_status: Literal["READY", "DEGRADED", "BLOCKED"]
    provider_availability_ok: bool
    freshness_anomaly_count: int = 0
    fallback_count: int = 0
    circuit_open_count: int = 0
    auth_rate_limit_count: int = 0
    timeout_count: int = 0
    policy_change_justified: bool = False
    release_decision: ReleaseDecision
    observe_only_flags: List[str] = Field(default_factory=list)
    must_fix_flags: List[str] = Field(default_factory=list)

    model_config = {"extra": "forbid"}


class ClosureSnapshotInvariantSet(BaseModel):
    """Fields that must agree across the canonical evidence chain."""
    interface_freeze_id: str
    policy_sha256: str
    config_fingerprint: str
    runtime_mode: RuntimeMode
    release_commit: Optional[str] = None
    release_tag: Optional[str] = None
    host_kind: RolloutHostKind

    model_config = {"extra": "forbid"}


class ClosureSnapshotManifest(BaseModel):
    """Canonical release-closure snapshot that binds decision-critical evidence by digest."""
    schema_version: Literal["closure_snapshot_manifest/v1"] = "closure_snapshot_manifest/v1"
    generated_at_utc: datetime
    closure_id: str
    closure_dir: str
    integrity_status: Literal["VERIFIED", "INCOMPLETE"]
    subjects: List[EvidenceResourceDescriptor] = Field(default_factory=list)
    missing_artifact_paths: List[str] = Field(default_factory=list)
    invariants: ClosureSnapshotInvariantSet
    scope: RolloutScope
    operational_summary: ClosureSnapshotOperationalSummary

    model_config = {"extra": "forbid"}


class DsseSignature(BaseModel):
    """Single DSSE signature entry."""
    keyid: str
    sig: str

    model_config = {"extra": "forbid"}


class DsseEnvelope(BaseModel):
    """DSSE envelope used to sign a closure snapshot manifest."""
    payloadType: str
    payload: str
    signatures: List[DsseSignature] = Field(default_factory=list)

    model_config = {"extra": "forbid"}


class ClosureSnapshotVerification(BaseModel):
    """Verification result for a closure snapshot manifest and optional DSSE envelope."""
    verified_at_utc: datetime
    manifest_path: str
    status: Literal["VERIFIED", "UNVERIFIED", "INCOMPLETE"]
    verified_subject_count: int = 0
    artifact_digests_verified: bool = False
    signature_verified: bool = False
    digest_mismatches: List[str] = Field(default_factory=list)
    missing_artifact_paths: List[str] = Field(default_factory=list)
    notes: List[str] = Field(default_factory=list)

    model_config = {"extra": "forbid"}


class ClosureReleaseAttestation(BaseModel):
    """Machine-derived release stance generated from a verified closure snapshot."""
    generated_at_utc: datetime
    closure_id: str
    snapshot_path: str
    verification_path: Optional[str] = None
    evidence_integrity_status: Literal["VERIFIED", "UNVERIFIED", "INCOMPLETE"]
    machine_decision: ReleaseDecision
    signoff_status: SignoffStatus
    final_release_stance: ReleaseStance
    primary_classification: DecisionClassification
    secondary_classifications: List[DecisionClassification] = Field(default_factory=list)
    governed_exception_eligible: bool = False
    governed_exception_codes: List[str] = Field(default_factory=list)
    applied_governed_exception_id: Optional[str] = None
    applied_governed_exception_code: Optional[str] = None
    applied_governed_exception_approved_by: Optional[str] = None
    applied_governed_exception_valid_until_utc: Optional[datetime] = None
    reasons: List[str] = Field(default_factory=list)
    required_operator_actions: List[str] = Field(default_factory=list)
    summary_line: str

    model_config = {"extra": "forbid"}


class GovernedExceptionMemo(BaseModel):
    """Signed operator exception memo that preserves a baseline only for scoped environmental nonconformance."""
    schema_version: Literal["governed_exception_memo/v1"] = "governed_exception_memo/v1"
    generated_at_utc: datetime
    exception_id: str
    closure_id: str
    snapshot_path: str
    verification_path: str
    requested_release_stance: Literal["KEEP_CURRENT_BASELINE_WITH_GOVERNED_EXCEPTION"] = "KEEP_CURRENT_BASELINE_WITH_GOVERNED_EXCEPTION"
    machine_decision: ReleaseDecision
    primary_classification: DecisionClassification
    governed_exception_code: str
    base_attestation_sha256: str
    scope: RolloutScope
    requested_by: str
    approved_by: str
    approved_at_utc: datetime
    valid_until_utc: datetime
    rationale: str
    constraints: List[str] = Field(default_factory=list)
    subjects: List[EvidenceResourceDescriptor] = Field(default_factory=list)

    model_config = {"extra": "forbid"}


class GovernedExceptionVerification(BaseModel):
    """Verification result for a governed exception memo and optional DSSE signature."""
    verified_at_utc: datetime
    memo_path: str
    status: Literal["VERIFIED", "UNVERIFIED", "EXPIRED"]
    artifact_digests_verified: bool = False
    signature_verified: bool = False
    base_attestation_match: bool = False
    digest_mismatches: List[str] = Field(default_factory=list)
    notes: List[str] = Field(default_factory=list)

    model_config = {"extra": "forbid"}
