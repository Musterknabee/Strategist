from __future__ import annotations

from datetime import datetime
from typing import Optional, List, Literal

from pydantic import BaseModel, Field

from strategy_validator.contracts.oracle_types import (
    AdvisoryRegime,
    EpistemicStatus,
    StrategyAdvisoryAction,
    GlobalAdvisoryAction,
    OracleDriftLevel,
    OracleTransitionClassification,
    OracleEvidenceStatus,
    OracleSupportVerificationStatus,
    OracleMemoryReviewClassification,
    OracleDoctrineDriftClassification,
    OracleDoctrineMemoryClassification,
    OracleQuarterlyReviewClassification,
    OracleSemiannualAuditClassification,
    OracleAnnualReviewClassification,
    OracleConstitutionalDigestClassification,
    OracleDoctrineLineageSealStatus,
    OracleConstitutionalTrustStatus,
    OracleExplanationCategory,
    OracleOperatorReadiness,
    OracleArtifactIntegrityStatus,
    OracleArtifactCoverageStatus,
    OracleSupportChainRemediationStatus,
    OracleReliancePosture,
    OracleEscalationLane,
    OraclePropagationPosture,
    OracleAutomationPosture,
    OracleGovernancePlaneStatus,
    OracleGovernanceDimension,
    OracleGovernancePrimarySeverity,
    OracleGovernancePriorityBand,
    OracleGovernanceReviewTarget,
    OracleGovernanceDispatchPosture,
    OracleGovernanceDispatchTimeliness,
    OracleGovernanceDispatchClaimUrgency,
    OracleGovernanceClaimCode,
    OracleGovernanceClaimWorkerLane,
    OracleGovernanceClaimDisposition,
    OracleGovernanceClaimActionSeverity,
    OracleGovernanceClaimLeaseMode,
    OracleGovernanceClaimLeaseRenewalPosture,
    OracleGovernanceClaimLeaseAction,
    OracleGovernanceClaimLeaseCoverage,
    OracleGovernanceClaimLeaseHealth,
    OracleGovernanceClaimProcessPosture,
    OracleGovernanceClaimOperability,
)
class OracleGovernanceClaimActionItem(BaseModel):
    code: OracleGovernanceClaimCode
    severity: OracleGovernanceClaimActionSeverity
    action_text: str = Field(min_length=1)

OracleGovernanceQueueKey = str
OracleGovernanceCode = Literal["UNTRUSTED_SUPPORT_CHAIN", "TRUST_RESTRICTED_SUPPORT_CHAIN", "REMEDIATION_REQUIRED", "REMEDIATION_RECOMMENDED", "READINESS_HOLD", "READINESS_CAUTION", "RELIANCE_REPAIR_FIRST", "RELIANCE_CAUTION", "ESCALATION_CONSTITUTIONAL_REPAIR", "ESCALATION_HEIGHTENED", "PROPAGATION_LOCAL_ONLY", "PROPAGATION_REVIEW_ONLY", "AUTOMATION_HUMAN_ONLY", "AUTOMATION_REVIEW_REQUIRED"]

OracleDerivedViewClassification = Literal[
    "STABLE_BASELINE",
    "HEIGHTENED_WATCH",
    "DEFENSIVE_POSTURE",
    "RETRAIN_REVIEW",
    "EVIDENCE_GAP",
]


class SemanticSensorSnapshot(BaseModel):
    inflation_hawkishness_score: float = 0.0
    geopolitical_risk_index: float = Field(default=0.0, ge=0.0, le=1.0)
    narrative_contradiction_count: int = Field(default=0, ge=0)
    tribunal_belief_conflict: float = Field(default=0.0, ge=0.0, le=1.0)

    model_config = {"extra": "forbid"}


class MicrostructureSensorSnapshot(BaseModel):
    vpin: float = Field(default=0.0, ge=0.0, le=1.0)
    order_flow_imbalance: float = Field(default=0.0, ge=-1.0, le=1.0)
    spread_variance_zscore: float = 0.0
    liquidity_thinning_score: float = Field(default=0.0, ge=0.0, le=1.0)

    model_config = {"extra": "forbid"}


class MacroRegimeSensorSnapshot(BaseModel):
    yield_curve_slope_bps: float
    high_yield_credit_spread_bps: float = Field(ge=0.0)
    equity_bond_correlation: float = Field(ge=-1.0, le=1.0)
    cross_asset_correlation_stress: float = Field(default=0.0, ge=0.0, le=1.0)
    realized_volatility_zscore: float = 0.0

    model_config = {"extra": "forbid"}


class StrategyHealthSnapshot(BaseModel):
    strategy_id: str
    strategy_type: str
    prior_edge_confidence: float = Field(ge=0.0, le=1.0)
    deflated_sharpe_ratio: float
    cpcv_lower_bound: float
    realized_live_sharpe: float
    recent_win_rate: float = Field(ge=0.0, le=1.0)
    drawdown_fraction: float = Field(ge=0.0, le=1.0)
    expected_regimes: List[AdvisoryRegime] = Field(default_factory=list)

    model_config = {"extra": "forbid"}


class OracleSensorMatrix(BaseModel):
    semantic: SemanticSensorSnapshot
    microstructure: MicrostructureSensorSnapshot
    macro: MacroRegimeSensorSnapshot

    model_config = {"extra": "forbid"}


class OraclePolicyArtifact(BaseModel):
    schema_version: Literal["oracle_policy_artifact/v1"] = "oracle_policy_artifact/v1"
    policy_family: Literal["oracle"] = "oracle"
    policy_version: str = Field(min_length=1)
    generated_at_utc: datetime
    strategic_posture_weights: dict[str, float] = Field(default_factory=dict)
    doctrine_stress_weights: dict[str, float] = Field(default_factory=dict)
    caution_score_weights: dict[str, float] = Field(default_factory=dict)
    opportunity_score_weights: dict[str, float] = Field(default_factory=dict)
    notes: list[str] = Field(default_factory=list)

    model_config = {"extra": "forbid"}


class OracleAdvisoryInput(BaseModel):
    generated_for_utc: datetime
    universe_label: str
    sensors: OracleSensorMatrix
    strategies: List[StrategyHealthSnapshot] = Field(default_factory=list)

    model_config = {"extra": "forbid"}


class RegimeProbability(BaseModel):
    regime: AdvisoryRegime
    probability: float = Field(ge=0.0, le=1.0)
    drivers: List[str] = Field(default_factory=list)

    model_config = {"extra": "forbid"}


class StrategyAdvisory(BaseModel):
    strategy_id: str
    strategy_type: str
    posterior_edge_confidence: float = Field(ge=0.0, le=1.0)
    action: StrategyAdvisoryAction
    reasons: List[str] = Field(default_factory=list)

    model_config = {"extra": "forbid"}


class EpistemicUncertaintyAssessment(BaseModel):
    status: EpistemicStatus
    score: float = Field(ge=0.0, le=1.0)
    advisory_only: bool = True
    triggers: List[str] = Field(default_factory=list)

    model_config = {"extra": "forbid"}




class OracleArtifactFreshnessItem(BaseModel):
    artifact_label: str
    source_path: str | None = None
    generated_at_utc: datetime | None = None
    age_hours: float | None = Field(default=None, ge=0.0)
    freshness_status: Literal["FRESH", "AGING", "STALE", "UNKNOWN"] = "UNKNOWN"

    model_config = {"extra": "forbid"}


class OracleArtifactLineageItem(BaseModel):
    artifact_label: str
    artifact_role: Literal["INPUT", "POLICY", "EVIDENCE", "DERIVED", "STATUS", "INCIDENT"]
    schema_version: str | None = None
    source_path: str | None = None
    integrity_status: Literal["VERIFIED", "INCOMPLETE", "UNVERIFIED", "NOT_APPLICABLE"] = "NOT_APPLICABLE"
    oracle_run_id: str | None = None

    model_config = {"extra": "forbid"}


class OracleGovernanceActionItem(BaseModel):
    dimension: OracleGovernanceDimension
    severity: Literal["BLOCKING", "RESTRICTING"] = "RESTRICTING"
    action_text: str

    model_config = {"extra": "forbid"}


class OracleGovernanceFingerprint(BaseModel):
    governance_plane_vector: str = ""
    governance_plane_sha256: str = ""
    governance_plane_route_vector: str = ""
    governance_plane_route_sha256: str = ""

    model_config = {"extra": "forbid"}


class OracleMorningAttestation(BaseModel):
    generated_at_utc: datetime
    input_timestamp_utc: datetime
    universe_label: str
    oracle_policy_version: str = "oracle-default-v1"
    oracle_policy_sha256: str = ""
    oracle_policy_path: str | None = None
    operator_readiness: OracleOperatorReadiness = "REVIEW_WITH_CAUTION"
    operator_readiness_summary_line: str = ""
    operator_readiness_reasons: List[str] = Field(default_factory=list)
    evidence_freshness_status: Literal["FRESH", "AGING", "STALE", "UNKNOWN"] = "UNKNOWN"
    stale_artifact_count: int = Field(default=0, ge=0)
    freshness_summary_line: str = ""
    artifact_freshness: List[OracleArtifactFreshnessItem] = Field(default_factory=list)
    artifact_lineage_summary_line: str = ""
    artifact_lineage: List[OracleArtifactLineageItem] = Field(default_factory=list)
    evidence_integrity_status: OracleArtifactIntegrityStatus = "UNKNOWN"
    unverified_artifact_count: int = Field(default=0, ge=0)
    integrity_summary_line: str = ""
    evidence_coverage_status: OracleArtifactCoverageStatus = "UNKNOWN"
    missing_expected_artifact_count: int = Field(default=0, ge=0)
    evidence_coverage_summary_line: str = ""
    missing_expected_artifact_labels: List[str] = Field(default_factory=list)
    support_verification_status: OracleSupportVerificationStatus = "ABSENT"
    support_verification_summary_line: str = ""
    support_verification_paths: List[str] = Field(default_factory=list)
    support_chain_trust_status: OracleConstitutionalTrustStatus = "TRUST_RESTRICTED"
    support_chain_trust_summary_line: str = ""
    support_chain_trust_reasons: List[str] = Field(default_factory=list)
    support_chain_remediation_status: OracleSupportChainRemediationStatus = "REMEDIATION_RECOMMENDED"
    support_chain_remediation_summary_line: str = ""
    support_chain_remediation_actions: List[str] = Field(default_factory=list)
    trust_plane_summary_line: str = ""
    operator_reliance_posture: OracleReliancePosture = "CAUTIOUS_ADVISORY_ONLY"
    operator_reliance_summary_line: str = ""
    operator_reliance_reasons: List[str] = Field(default_factory=list)
    operator_escalation_lane: OracleEscalationLane = "HEIGHTENED_OPERATOR_ESCALATION"
    operator_escalation_summary_line: str = ""
    operator_escalation_reasons: List[str] = Field(default_factory=list)
    propagation_posture: OraclePropagationPosture = "REVIEW_ONLY_PROPAGATION"
    propagation_summary_line: str = ""
    propagation_reasons: List[str] = Field(default_factory=list)
    automation_posture: OracleAutomationPosture = "AUTOMATION_REVIEW_REQUIRED"
    automation_summary_line: str = ""
    automation_reasons: List[str] = Field(default_factory=list)
    control_plane_summary_line: str = ""
    governance_plane_status: OracleGovernancePlaneStatus = "GOVERNANCE_RESTRICTED"
    governance_plane_summary_line: str = ""
    governance_plane_reasons: List[str] = Field(default_factory=list)
    governance_plane_codes: List[OracleGovernanceCode] = Field(default_factory=list)
    governance_plane_blocking_dimensions: List[OracleGovernanceDimension] = Field(default_factory=list)
    governance_plane_restricted_dimensions: List[OracleGovernanceDimension] = Field(default_factory=list)
    governance_plane_actions: List[str] = Field(default_factory=list)
    governance_plane_action_items: List[OracleGovernanceActionItem] = Field(default_factory=list)
    governance_plane_primary_dimension: OracleGovernanceDimension | None = None
    governance_plane_primary_severity: OracleGovernancePrimarySeverity = "READY"
    governance_plane_primary_action_text: str = ""
    governance_plane_priority_band: OracleGovernancePriorityBand = "ROUTINE_PRIORITY"
    governance_plane_priority_score: int = Field(default=0, ge=0, le=100)
    governance_plane_priority_summary_line: str = ""
    governance_plane_review_target: OracleGovernanceReviewTarget = "ROUTINE_REVIEW_QUEUE"
    governance_plane_review_sla_hours: int = Field(default=72, ge=1, le=168)
    governance_plane_review_summary_line: str = ""
    governance_plane_review_due_by_utc: datetime | None = None
    governance_plane_review_sort_key: str = ""
    governance_plane_review_envelope_vector: str = ""
    governance_plane_review_envelope_sha256: str = ""
    governance_plane_routing_summary_line: str = ""
    governance_plane_routing_vector: str = ""
    governance_plane_routing_sha256: str = ""
    governance_plane_dispatch_summary_line: str = ""
    governance_plane_dispatch_vector: str = ""
    governance_plane_dispatch_sha256: str = ""
    governance_plane_dispatch_claim_key: str = ""
    governance_plane_dispatch_posture: OracleGovernanceDispatchPosture = "DISPATCH_REVIEW_ONLY"
    governance_plane_dispatch_permitted: bool = False
    governance_plane_dispatch_reasons: List[str] = Field(default_factory=list)
    governance_plane_dispatch_timeliness: OracleGovernanceDispatchTimeliness = "DISPATCH_ACTIVE"
    governance_plane_dispatch_claim_permitted_now: bool = False
    governance_plane_dispatch_timeliness_summary_line: str = ""
    governance_plane_dispatch_claim_urgency: OracleGovernanceDispatchClaimUrgency = "DO_NOT_CLAIM"
    governance_plane_dispatch_claim_score: int = Field(default=0, ge=0, le=100)
    governance_plane_dispatch_claim_summary_line: str = ""
    governance_plane_claim_summary_line: str = ""
    governance_plane_claim_queue_key: OracleGovernanceQueueKey = ""
    governance_plane_claim_review_target: OracleGovernanceReviewTarget = "ROUTINE_REVIEW_QUEUE"
    governance_plane_claim_priority_band: OracleGovernancePriorityBand = "ROUTINE_PRIORITY"
    governance_plane_claim_review_due_by_utc: datetime | None = None
    governance_plane_claim_review_sort_key: str = ""
    governance_plane_claim_route_sha256: str = ""
    governance_plane_claim_review_envelope_sha256: str = ""
    governance_plane_claim_routing_envelope_sha256: str = ""
    governance_plane_claim_dispatch_claim_key: str = ""
    governance_plane_claim_dispatch_sha256: str = ""
    governance_plane_claim_codes: List[OracleGovernanceClaimCode] = Field(default_factory=list)
    governance_plane_claim_primary_code: OracleGovernanceClaimCode | None = None
    governance_plane_claim_action_items: List[OracleGovernanceClaimActionItem] = Field(default_factory=list)
    governance_plane_claim_primary_action_text: str = ""
    governance_plane_claim_worker_lane: OracleGovernanceClaimWorkerLane = "ROUTINE_CLAIM_WORKER"
    governance_plane_claim_worker_summary_line: str = ""
    governance_plane_claim_worker_sort_key: str = ""
    governance_plane_claim_lease_key: str = ""
    governance_plane_claim_lease_mode: OracleGovernanceClaimLeaseMode = "STANDARD_LEASE"
    governance_plane_claim_lease_ttl_seconds: int = 0
    governance_plane_claim_lease_expires_at_utc: Optional[datetime] = None
    governance_plane_claim_lease_active_now: bool = False
    governance_plane_claim_lease_summary_line: str = ""
    governance_plane_claim_lease_coverage: OracleGovernanceClaimLeaseCoverage = "NO_LEASE_COVERAGE"
    governance_plane_claim_lease_coverage_summary_line: str = ""
    governance_plane_claim_lease_health: OracleGovernanceClaimLeaseHealth = "LEASE_BLOCKED"
    governance_plane_claim_lease_health_summary_line: str = ""
    governance_plane_claim_lease_renewal_posture: OracleGovernanceClaimLeaseRenewalPosture = "NO_RENEWAL"
    governance_plane_claim_lease_renewal_permitted_now: bool = False
    governance_plane_claim_lease_renewal_summary_line: str = ""
    governance_plane_claim_lease_action: OracleGovernanceClaimLeaseAction = "NO_LEASE_ACTION"
    governance_plane_claim_lease_action_summary_line: str = ""
    governance_plane_claim_disposition: OracleGovernanceClaimDisposition = "CLAIM_QUEUE_ROUTINE"
    governance_plane_claim_disposition_summary_line: str = ""
    governance_plane_claim_process_posture: OracleGovernanceClaimProcessPosture = "PROCESS_QUEUE_ONLY"
    governance_plane_claim_process_permitted_now: bool = False
    governance_plane_claim_process_summary_line: str = ""
    governance_plane_claim_operability: OracleGovernanceClaimOperability = "CLAIM_INOPERABLE"
    governance_plane_claim_operability_summary_line: str = ""
    governance_plane_claim_vector: str = ""
    governance_plane_claim_sha256: str = ""
    governance_plane_queue_key: OracleGovernanceQueueKey = ""
    governance_plane_route_vector: str = ""
    governance_plane_route_sha256: str = ""
    governance_plane_vector: str = ""
    governance_plane_sha256: str = ""
    execution_authority: Literal["ADVISORY_ONLY"] = "ADVISORY_ONLY"
    dominant_regime: AdvisoryRegime
    regime_probabilities: List[RegimeProbability] = Field(default_factory=list)
    semantic_state_summary: str
    microstructure_summary: str
    strategy_advisories: List[StrategyAdvisory] = Field(default_factory=list)
    epistemic_uncertainty: EpistemicUncertaintyAssessment
    recommended_global_action: GlobalAdvisoryAction
    operator_actions: List[str] = Field(default_factory=list)
    summary_line: str

    model_config = {"extra": "forbid"}

