from __future__ import annotations

from datetime import datetime
from typing import Optional, List, Literal

from pydantic import BaseModel, Field

from strategy_validator.contracts.operational import EvidenceResourceDescriptor

from strategy_validator.contracts.oracle_core import (
    StrategyHealthSnapshot,
    OracleAdvisoryInput,
    OracleArtifactFreshnessItem,
    OracleArtifactLineageItem,
    OracleGovernanceActionItem,
    RegimeProbability,
)
from strategy_validator.contracts.oracle_types import (
    EpistemicStatus,
    OracleOperatorReadiness,
    OracleArtifactIntegrityStatus,
    OracleArtifactCoverageStatus,
    OracleSupportVerificationStatus,
    OracleEvidenceStatus,
    OracleConstitutionalTrustStatus,
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
    OracleGovernanceClaimLeaseMode,
    OracleGovernanceClaimLeaseRenewalPosture,
    OracleGovernanceClaimLeaseAction,
    OracleGovernanceClaimLeaseCoverage,
    OracleGovernanceClaimLeaseHealth,
    OracleGovernanceClaimProcessPosture,
    OracleGovernanceClaimOperability,
    AdvisoryRegime,
    StrategyAdvisoryAction,
)

from strategy_validator.contracts.oracle_core import OracleGovernanceCode, OracleGovernanceQueueKey, OracleGovernanceClaimActionItem


OracleStrategicPosture = Literal[
    "OPPORTUNITY_BIASED",
    "BALANCED_OBSERVATION",
    "CAUTION_BIASED",
    "DEFENSIVE_RESEARCH",
    "RESEARCH_FREEZE",
]

OracleStrategicTransitionClassification = Literal[
    "STABLE_REGIME",
    "DRIFTING",
    "TRANSITIONING",
    "HIGH_UNCERTAINTY",
    "STRUCTURAL_BREAK_CANDIDATE",
]

OracleStrategicQueueKind = Literal["OPPORTUNITY", "CAUTION", "RESEARCH_REVIEW"]
OracleThesisCurrentState = Literal["SUPPORTIVE", "CAUTIONARY", "AT_RISK", "BROKEN", "NEUTRAL"]
OracleThesisEvolutionState = Literal["EMERGING", "STRENGTHENING", "WEAKENING", "REVERSING", "STABLE"]
OracleScenarioKind = Literal["UPSIDE", "DOWNSIDE", "RESEARCH_REVIEW"]
OracleStrategyCohortBucket = Literal["LEAD", "WATCH", "PRESSURED", "RESEARCH_ONLY"]
OracleResearchPriorityKind = Literal["REGIME_INVESTIGATION", "STRATEGY_VALIDATION", "DOCTRINE_REVIEW", "THESIS_REVIEW", "SCENARIO_PROBE"]

StrategyRegimeFit = Literal["ALIGNED", "MISMATCH", "NEUTRAL"]


class OracleSensorRawMacroInput(BaseModel):
    yield_curve_slope_bps: float
    high_yield_credit_spread_bps: float = Field(ge=0.0)
    equity_bond_correlation_20d: float = Field(ge=-1.0, le=1.0)
    cross_asset_correlation_20d: float = Field(ge=-1.0, le=1.0)
    realized_volatility_20d: float = Field(ge=0.0)
    realized_volatility_252d: float = Field(gt=0.0)

    model_config = {"extra": "forbid"}


class OracleSensorRawSemanticInput(BaseModel):
    hawkish_document_ratio: float = Field(ge=0.0, le=1.0)
    dovish_document_ratio: float = Field(ge=0.0, le=1.0)
    geopolitical_headline_share: float = Field(ge=0.0, le=1.0)
    contradiction_count: int = Field(default=0, ge=0)
    belief_conflict_score: float = Field(default=0.0, ge=0.0, le=1.0)

    model_config = {"extra": "forbid"}


class OracleSensorRawMicrostructureInput(BaseModel):
    buy_volume: float = Field(ge=0.0)
    sell_volume: float = Field(ge=0.0)
    median_spread_bps: float = Field(ge=0.0)
    baseline_spread_bps: float = Field(gt=0.0)
    top_book_depth_usd: float = Field(ge=0.0)
    baseline_top_book_depth_usd: float = Field(gt=0.0)
    toxic_flow_ratio: float = Field(default=0.0, ge=0.0, le=1.0)

    model_config = {"extra": "forbid"}


class OracleSensorIngestionInput(BaseModel):
    schema_version: Literal["oracle_sensor_ingestion_input/v1"] = "oracle_sensor_ingestion_input/v1"
    generated_for_utc: datetime
    universe_label: str
    macro_raw: OracleSensorRawMacroInput
    semantic_raw: OracleSensorRawSemanticInput
    microstructure_raw: OracleSensorRawMicrostructureInput
    strategies: List[StrategyHealthSnapshot] = Field(default_factory=list)

    model_config = {"extra": "forbid"}


class OracleSensorIngestionReport(BaseModel):
    schema_version: Literal["oracle_sensor_ingestion_report/v1"] = "oracle_sensor_ingestion_report/v1"
    generated_at_utc: datetime
    universe_label: str
    advisory_input: OracleAdvisoryInput
    quality_score: float = Field(ge=0.0, le=1.0)
    normalization_notes: List[str] = Field(default_factory=list)
    summary_line: str

    model_config = {"extra": "forbid"}


class OracleStrategicFusionReport(BaseModel):
    schema_version: Literal["oracle_strategic_fusion_report/v1"] = "oracle_strategic_fusion_report/v1"
    generated_at_utc: datetime
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
    oracle_run_id: str
    input_timestamp_utc: datetime
    dominant_regime: AdvisoryRegime
    preferred_strategic_backing_source: str | None = None
    preferred_strategic_backing_classification: Literal["SEALED_STRATEGIC_STACK_BACKED", "DOCTRINE_ONLY_LADDER_BACKED", "NO_STRATEGIC_STACK_HISTORY"] | None = None
    exact_feedback_confirmation_count: int = Field(default=0, ge=0)
    exact_feedback_relief_count: int = Field(default=0, ge=0)
    exact_cadence_signal_classification: Literal["EXACT_CONFIRMED_PRESSURE", "EXACT_RELIEF_PRESSURE", "AMBIENT_DRIFT"] = "AMBIENT_DRIFT"
    exact_evidence_support_score: float = Field(default=0.0, ge=0.0, le=1.0)
    regime_confidence: float = Field(ge=0.0, le=1.0)
    regime_probabilities: List[RegimeProbability] = Field(default_factory=list)
    epistemic_status: EpistemicStatus
    epistemic_score: float = Field(ge=0.0, le=1.0)
    strategy_pressure_score: float = Field(ge=0.0, le=1.0)
    doctrine_stress_score: float = Field(ge=0.0, le=1.0)
    opportunity_score: float = Field(ge=0.0, le=1.0)
    caution_score: float = Field(ge=0.0, le=1.0)
    strategic_posture: OracleStrategicPosture
    opportunity_factors: List[str] = Field(default_factory=list)
    caution_factors: List[str] = Field(default_factory=list)
    doctrine_pressure_points: List[str] = Field(default_factory=list)
    operator_actions: List[str] = Field(default_factory=list)
    summary_line: str

    model_config = {"extra": "forbid"}


class StrategyPosteriorState(BaseModel):
    strategy_id: str
    strategy_type: str
    exact_evidence_support_score: float = Field(default=0.0, ge=0.0, le=1.0)
    prior_edge_confidence: float = Field(ge=0.0, le=1.0)
    posterior_edge_confidence: float = Field(ge=0.0, le=1.0)
    confidence_delta: float
    degradation_score: float = Field(ge=0.0, le=1.0)
    recovery_score: float = Field(ge=0.0, le=1.0)
    regime_fit: StrategyRegimeFit = "NEUTRAL"
    recommended_action: StrategyAdvisoryAction
    reasons: List[str] = Field(default_factory=list)

    model_config = {"extra": "forbid"}


class StrategyHealthPosteriorReport(BaseModel):
    schema_version: Literal["strategy_health_posterior_report/v1"] = "strategy_health_posterior_report/v1"
    generated_at_utc: datetime
    universe_label: str
    oracle_run_id: str
    input_timestamp_utc: datetime
    dominant_regime: AdvisoryRegime
    strategic_posture: OracleStrategicPosture
    preferred_strategic_backing_source: str | None = None
    preferred_strategic_backing_classification: Literal["SEALED_STRATEGIC_STACK_BACKED", "DOCTRINE_ONLY_LADDER_BACKED", "NO_STRATEGIC_STACK_HISTORY"] | None = None
    exact_evidence_support_score: float = Field(default=0.0, ge=0.0, le=1.0)
    average_posterior_edge_confidence: float = Field(ge=0.0, le=1.0)
    degraded_strategy_ids: List[str] = Field(default_factory=list)
    recovering_strategy_ids: List[str] = Field(default_factory=list)
    operator_actions: List[str] = Field(default_factory=list)
    strategies: List[StrategyPosteriorState] = Field(default_factory=list)
    summary_line: str

    model_config = {"extra": "forbid"}


class OracleRegimeTransitionSignalReport(BaseModel):
    schema_version: Literal["oracle_regime_transition_signal_report/v1"] = "oracle_regime_transition_signal_report/v1"
    generated_at_utc: datetime
    universe_label: str
    oracle_run_id: str
    input_timestamp_utc: datetime
    preferred_strategic_backing_source: str | None = None
    preferred_strategic_backing_classification: Literal["SEALED_STRATEGIC_STACK_BACKED", "DOCTRINE_ONLY_LADDER_BACKED", "NO_STRATEGIC_STACK_HISTORY"] | None = None
    exact_evidence_support_score: float = Field(default=0.0, ge=0.0, le=1.0)
    previous_generated_at_utc: datetime
    current_generated_at_utc: datetime
    previous_dominant_regime: AdvisoryRegime
    current_dominant_regime: AdvisoryRegime
    previous_regime_confidence: float = Field(ge=0.0, le=1.0)
    current_regime_confidence: float = Field(ge=0.0, le=1.0)
    confidence_delta: float
    previous_strategic_posture: OracleStrategicPosture
    current_strategic_posture: OracleStrategicPosture
    transition_classification: OracleStrategicTransitionClassification
    drivers: List[str] = Field(default_factory=list)
    operator_actions: List[str] = Field(default_factory=list)
    summary_line: str

    model_config = {"extra": "forbid"}


class OracleOpportunityQueueItem(BaseModel):
    queue_id: str
    queue_kind: OracleStrategicQueueKind
    priority_score: float = Field(ge=0.0, le=1.0)
    operator_friction_score: float = Field(default=0.0, ge=0.0, le=1.0)
    exact_feedback_confirmation_count: int = Field(default=0, ge=0)
    exact_feedback_relief_count: int = Field(default=0, ge=0)
    exact_cadence_signal_classification: Literal["EXACT_CONFIRMED_PRESSURE", "EXACT_RELIEF_PRESSURE", "AMBIENT_DRIFT"] = "AMBIENT_DRIFT"
    exact_evidence_support_score: float = Field(default=0.0, ge=0.0, le=1.0)
    title: str
    strategy_id: str | None = None
    summary_line: str
    evidence: List[str] = Field(default_factory=list)
    operator_action: str

    model_config = {"extra": "forbid"}


class OracleOpportunityQueueReport(BaseModel):
    schema_version: Literal["oracle_opportunity_queue_report/v1"] = "oracle_opportunity_queue_report/v1"
    generated_at_utc: datetime
    universe_label: str
    oracle_run_id: str
    input_timestamp_utc: datetime
    dominant_regime: AdvisoryRegime
    strategic_posture: OracleStrategicPosture
    history_integrity_status: Literal["CURRENT_ONLY", "SEALED_HISTORY", "MIXED_HISTORY"] = "CURRENT_ONLY"
    sealed_history_observation_count: int = Field(default=0, ge=0)
    unsealed_history_excluded_count: int = Field(default=0, ge=0)
    exact_feedback_confirmation_count: int = Field(default=0, ge=0)
    exact_feedback_relief_count: int = Field(default=0, ge=0)
    exact_cadence_signal_classification: Literal["EXACT_CONFIRMED_PRESSURE", "EXACT_RELIEF_PRESSURE", "AMBIENT_DRIFT"] = "AMBIENT_DRIFT"
    exact_evidence_support_score: float = Field(default=0.0, ge=0.0, le=1.0)
    integrity_operator_friction_score: float = Field(default=0.0, ge=0.0, le=1.0)
    summary_line: str
    items: List[OracleOpportunityQueueItem] = Field(default_factory=list)
    operator_actions: List[str] = Field(default_factory=list)

    model_config = {"extra": "forbid"}
