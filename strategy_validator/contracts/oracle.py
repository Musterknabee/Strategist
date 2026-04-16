from __future__ import annotations

from datetime import datetime
from typing import Optional, List, Literal

from pydantic import BaseModel, Field

from strategy_validator.contracts.operational import EvidenceResourceDescriptor

AdvisoryRegime = Literal[
    "RISK_ON_LOW_VOL",
    "TRANSITION",
    "RISK_OFF_HIGH_VOL",
    "LIQUIDITY_STRESS",
]

EpistemicStatus = Literal["NOMINAL", "ELEVATED", "UNKNOWN_UNKNOWNS"]
StrategyAdvisoryAction = Literal["MAINTAIN", "CANARY", "HIBERNATE"]
GlobalAdvisoryAction = Literal["OBSERVE", "CANARY_REVIEW", "DEFENSIVE_POSTURE"]
OracleDriftLevel = Literal["STABLE", "MODERATE", "MATERIAL", "SEVERE"]
OracleTransitionClassification = Literal[
    "STATE_STABLE",
    "REGIME_DRIFT",
    "STRATEGY_DRIFT",
    "GLOBAL_ACTION_ESCALATION",
    "EPISTEMIC_ESCALATION",
    "EVIDENCE_GAP",
]
OracleEvidenceStatus = Literal["VERIFIED", "UNVERIFIED", "INCOMPLETE"]
OracleSupportVerificationStatus = Literal["VERIFIED", "UNVERIFIED", "INCOMPLETE", "ABSENT"]

OracleMemoryReviewClassification = Literal[
    "STABLE_RESEARCH_POSTURE",
    "HEIGHTENED_RESEARCH_POSTURE",
    "REPAIR_FIRST",
    "DEFENSIVE_RESEARCH_POSTURE",
    "STRATEGY_RETRAIN_REVIEW",
]

OracleDoctrineDriftClassification = Literal[
    "DOCTRINE_STABLE",
    "DOCTRINE_ESCALATION",
    "DOCTRINE_RELIEF",
    "RECURRING_REPAIR",
    "RECURRING_RETRAIN",
    "DOCTRINE_EVIDENCE_GAP",
]

OracleDoctrineMemoryClassification = Literal[
    "DOCTRINE_STABLE_BASELINE",
    "DOCTRINE_HEIGHTENED_WATCH",
    "DOCTRINE_REPAIR_PERSISTENT",
    "DOCTRINE_RETRAIN_PERSISTENT",
    "DOCTRINE_DEFENSIVE_PERSISTENT",
    "DOCTRINE_EVIDENCE_GAP",
]

OracleQuarterlyReviewClassification = Literal[
    "QUARTERLY_STABLE_BASELINE",
    "QUARTERLY_HEIGHTENED_WATCH",
    "QUARTERLY_REPAIR_STRUCTURAL",
    "QUARTERLY_RETRAIN_STRUCTURAL",
    "QUARTERLY_DEFENSIVE_STRUCTURAL",
    "QUARTERLY_EVIDENCE_GAP",
]

OracleSemiannualAuditClassification = Literal[
    "SEMIANNUAL_STABLE_BASELINE",
    "SEMIANNUAL_HEIGHTENED_WATCH",
    "SEMIANNUAL_REPAIR_STRUCTURAL",
    "SEMIANNUAL_RETRAIN_STRUCTURAL",
    "SEMIANNUAL_DEFENSIVE_STRUCTURAL",
    "SEMIANNUAL_EVIDENCE_GAP",
]

OracleAnnualReviewClassification = Literal[
    "ANNUAL_STABLE_BASELINE",
    "ANNUAL_HEIGHTENED_WATCH",
    "ANNUAL_REPAIR_STRUCTURAL",
    "ANNUAL_RETRAIN_STRUCTURAL",
    "ANNUAL_DEFENSIVE_STRUCTURAL",
    "ANNUAL_EVIDENCE_GAP",
]

OracleConstitutionalDigestClassification = Literal[
    "CONSTITUTIONAL_STABLE_BASELINE",
    "CONSTITUTIONAL_HEIGHTENED_WATCH",
    "CONSTITUTIONAL_REPAIR_CHRONIC",
    "CONSTITUTIONAL_RETRAIN_CHRONIC",
    "CONSTITUTIONAL_DEFENSIVE_CHRONIC",
    "CONSTITUTIONAL_EVIDENCE_GAP",
]

OracleDoctrineLineageSealStatus = Literal[
    "FULLY_SEALED",
    "CONSTITUTIONALLY_REPLAYABLE",
    "PARTIALLY_SEALED",
    "ADVISORY_ONLY_INCOMPLETE",
]

OracleConstitutionalTrustStatus = Literal[
    "TRUSTED",
    "TRUST_RESTRICTED",
    "UNTRUSTED",
]

OracleExplanationCategory = Literal["trust", "lineage", "evidence", "policy", "authority", "operator_action", "warning"]

OracleOperatorReadiness = Literal["READY_FOR_REVIEW", "REVIEW_WITH_CAUTION", "HOLD_FOR_REFRESH"]
OracleArtifactIntegrityStatus = Literal["VERIFIED", "MIXED", "UNVERIFIED", "UNKNOWN"]
OracleArtifactCoverageStatus = Literal["COMPLETE", "PARTIAL", "MISSING", "UNKNOWN"]
OracleSupportChainRemediationStatus = Literal["NO_REMEDIATION", "REMEDIATION_RECOMMENDED", "REMEDIATION_REQUIRED"]
OracleReliancePosture = Literal["ROUTINE_ADVISORY", "CAUTIOUS_ADVISORY_ONLY", "REPAIR_FIRST"]
OracleEscalationLane = Literal["STANDARD_OPERATOR_FLOW", "HEIGHTENED_OPERATOR_ESCALATION", "CONSTITUTIONAL_REPAIR_ESCALATION"]
OraclePropagationPosture = Literal["DOWNSTREAM_PROPAGATION_ALLOWED", "REVIEW_ONLY_PROPAGATION", "LOCAL_ONLY_DO_NOT_PROPAGATE"]
OracleAutomationPosture = Literal["AUTOMATION_ELIGIBLE", "AUTOMATION_REVIEW_REQUIRED", "HUMAN_ONLY_NO_AUTOMATION"]
OracleGovernancePlaneStatus = Literal["GOVERNANCE_READY", "GOVERNANCE_RESTRICTED", "GOVERNANCE_BLOCKED"]
OracleGovernanceDimension = Literal["SUPPORT_CHAIN_TRUST", "REMEDIATION", "READINESS", "RELIANCE", "ESCALATION", "PROPAGATION", "AUTOMATION"]
OracleGovernancePrimarySeverity = Literal["READY", "RESTRICTING", "BLOCKING"]
OracleGovernancePriorityBand = Literal["ROUTINE_PRIORITY", "ELEVATED_PRIORITY", "CRITICAL_PRIORITY"]
OracleGovernanceReviewTarget = Literal["ROUTINE_REVIEW_QUEUE", "HEIGHTENED_REVIEW_QUEUE", "CONSTITUTIONAL_REPAIR_QUEUE"]
OracleGovernanceDispatchPosture = Literal["DISPATCH_ALLOWED", "DISPATCH_REVIEW_ONLY", "DISPATCH_BLOCKED"]
OracleGovernanceDispatchTimeliness = Literal["DISPATCH_ACTIVE", "DISPATCH_DUE_SOON", "DISPATCH_OVERDUE"]
OracleGovernanceDispatchClaimUrgency = Literal["CLAIM_NOW", "CLAIM_SOON", "DO_NOT_CLAIM"]
OracleGovernanceClaimCode = Literal["CLAIM_PERMISSION_BLOCKED", "CLAIM_OVERDUE", "CLAIM_DUE_SOON", "CLAIM_ROUTINE", "CLAIM_IMMEDIATE"]
OracleGovernanceClaimWorkerLane = Literal["IMMEDIATE_CLAIM_WORKER", "NEAR_DUE_CLAIM_WORKER", "ROUTINE_CLAIM_WORKER", "BLOCKED_CLAIM_HOLDING"]
OracleGovernanceClaimDisposition = Literal["CLAIM_HOLD", "CLAIM_ESCALATE", "CLAIM_PRIORITIZE", "CLAIM_QUEUE_PROMPT", "CLAIM_QUEUE_ROUTINE"]
OracleGovernanceClaimActionSeverity = Literal["ROUTINE", "PROMPT", "URGENT", "BLOCKED"]
OracleGovernanceClaimLeaseMode = Literal["NO_LEASE", "SHORT_LEASE", "STANDARD_LEASE"]
OracleGovernanceClaimLeaseRenewalPosture = Literal["NO_RENEWAL", "RENEW_SOON", "RENEW_NOW"]
OracleGovernanceClaimLeaseAction = Literal["NO_LEASE_ACTION", "ACQUIRE_LEASE_NOW", "MAINTAIN_LEASE", "RENEW_LEASE_NOW", "RELEASE_LEASE"]
OracleGovernanceClaimLeaseCoverage = Literal["NO_LEASE_COVERAGE", "LEASE_PARTIAL_COVERAGE", "LEASE_FULL_COVERAGE"]
OracleGovernanceClaimLeaseHealth = Literal["LEASE_BLOCKED", "LEASE_DEGRADED", "LEASE_HEALTHY"]
OracleGovernanceClaimProcessPosture = Literal["PROCESS_BLOCKED", "PROCESS_READY_AFTER_LEASE", "PROCESS_READY_NOW", "PROCESS_QUEUE_ONLY"]
OracleGovernanceClaimOperability = Literal["CLAIM_OPERABLE", "CLAIM_CONSTRAINED", "CLAIM_INOPERABLE"]


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


class OracleEvidenceManifest(BaseModel):
    schema_version: Literal["oracle_evidence_manifest/v1"] = "oracle_evidence_manifest/v1"
    generated_at_utc: datetime
    evidence_id: str
    universe_label: str
    input_timestamp_utc: datetime
    execution_authority: Literal["ADVISORY_ONLY"] = "ADVISORY_ONLY"
    dominant_regime: AdvisoryRegime
    recommended_global_action: GlobalAdvisoryAction
    epistemic_status: EpistemicStatus
    linked_closure_id: str | None = None
    linked_closure_snapshot_path: str | None = None
    integrity_status: Literal["VERIFIED", "INCOMPLETE"]
    subjects: List[EvidenceResourceDescriptor] = Field(default_factory=list)
    missing_artifact_paths: List[str] = Field(default_factory=list)
    summary_line: str

    model_config = {"extra": "forbid"}


class OracleEvidenceVerification(BaseModel):
    verified_at_utc: datetime
    manifest_path: str
    status: OracleEvidenceStatus = "UNVERIFIED"
    artifact_digests_verified: bool = False
    signature_verified: bool = False
    linked_closure_present: bool = False
    verified_subject_count: int = 0
    digest_mismatches: List[str] = Field(default_factory=list)
    missing_artifact_paths: List[str] = Field(default_factory=list)
    notes: List[str] = Field(default_factory=list)

    model_config = {"extra": "forbid"}


class OracleRegimeTransition(BaseModel):
    previous_dominant_regime: AdvisoryRegime
    current_dominant_regime: AdvisoryRegime
    previous_dominant_probability: float = Field(ge=0.0, le=1.0)
    current_dominant_probability: float = Field(ge=0.0, le=1.0)
    dominant_changed: bool = False
    drift_level: OracleDriftLevel = "STABLE"
    drivers: List[str] = Field(default_factory=list)

    model_config = {"extra": "forbid"}


class StrategyAdvisoryTransition(BaseModel):
    strategy_id: str
    strategy_type: str
    previous_action: StrategyAdvisoryAction
    current_action: StrategyAdvisoryAction
    previous_posterior_edge_confidence: float = Field(ge=0.0, le=1.0)
    current_posterior_edge_confidence: float = Field(ge=0.0, le=1.0)
    posterior_delta: float
    action_changed: bool = False
    drift_level: OracleDriftLevel = "STABLE"
    reasons: List[str] = Field(default_factory=list)

    model_config = {"extra": "forbid"}


class OracleStateTransitionReport(BaseModel):
    schema_version: Literal["oracle_state_transition_report/v1"] = "oracle_state_transition_report/v1"
    generated_at_utc: datetime
    previous_evidence_id: str
    current_evidence_id: str
    universe_label: str
    execution_authority: Literal["ADVISORY_ONLY"] = "ADVISORY_ONLY"
    previous_input_timestamp_utc: datetime
    current_input_timestamp_utc: datetime
    previous_verification_status: OracleEvidenceStatus
    current_verification_status: OracleEvidenceStatus
    comparison_status: OracleEvidenceStatus
    previous_linked_closure_id: str | None = None
    current_linked_closure_id: str | None = None
    previous_recommended_global_action: GlobalAdvisoryAction
    current_recommended_global_action: GlobalAdvisoryAction
    previous_epistemic_status: EpistemicStatus
    current_epistemic_status: EpistemicStatus
    regime_transition: OracleRegimeTransition
    strategy_transitions: List[StrategyAdvisoryTransition] = Field(default_factory=list)
    introduced_strategy_ids: List[str] = Field(default_factory=list)
    removed_strategy_ids: List[str] = Field(default_factory=list)
    transition_classification: OracleTransitionClassification = "STATE_STABLE"
    drift_score: float = Field(ge=0.0, le=1.0)
    operator_actions: List[str] = Field(default_factory=list)
    summary_line: str

    model_config = {"extra": "forbid"}


class OracleTransitionEvidenceManifest(BaseModel):
    schema_version: Literal["oracle_transition_evidence_manifest/v1"] = "oracle_transition_evidence_manifest/v1"
    generated_at_utc: datetime
    transition_id: str
    universe_label: str
    execution_authority: Literal["ADVISORY_ONLY"] = "ADVISORY_ONLY"
    previous_evidence_id: str
    current_evidence_id: str
    previous_linked_closure_id: str | None = None
    current_linked_closure_id: str | None = None
    transition_classification: OracleTransitionClassification
    drift_score: float = Field(ge=0.0, le=1.0)
    integrity_status: Literal["VERIFIED", "INCOMPLETE"]
    subjects: List[EvidenceResourceDescriptor] = Field(default_factory=list)
    missing_artifact_paths: List[str] = Field(default_factory=list)
    summary_line: str

    model_config = {"extra": "forbid"}


class OracleTransitionEvidenceVerification(BaseModel):
    verified_at_utc: datetime
    manifest_path: str
    status: OracleEvidenceStatus = "UNVERIFIED"
    artifact_digests_verified: bool = False
    signature_verified: bool = False
    verified_subject_count: int = 0
    digest_mismatches: List[str] = Field(default_factory=list)
    missing_artifact_paths: List[str] = Field(default_factory=list)
    notes: List[str] = Field(default_factory=list)

    model_config = {"extra": "forbid"}


class OracleMemoryLaneEntry(BaseModel):
    schema_version: Literal["oracle_memory_lane_entry/v1"] = "oracle_memory_lane_entry/v1"
    appended_at_utc: datetime
    lane_id: str
    sequence_number: int = Field(ge=0)
    entry_id: str
    transition_id: str
    previous_entry_hash: str | None = None
    entry_hash: str
    manifest_path: str
    manifest_sha256: str
    transition_classification: OracleTransitionClassification
    drift_score: float = Field(ge=0.0, le=1.0)
    current_input_timestamp_utc: datetime
    current_epistemic_status: EpistemicStatus
    current_recommended_global_action: GlobalAdvisoryAction
    evidence_status: OracleEvidenceStatus
    summary_line: str

    model_config = {"extra": "forbid"}


class OracleMemoryLaneSummary(BaseModel):
    schema_version: Literal["oracle_memory_lane_summary/v1"] = "oracle_memory_lane_summary/v1"
    generated_at_utc: datetime
    lane_id: str
    entry_count: int = Field(ge=0)
    first_input_timestamp_utc: datetime | None = None
    last_input_timestamp_utc: datetime | None = None
    latest_transition_classification: OracleTransitionClassification | None = None
    latest_global_action: GlobalAdvisoryAction | None = None
    latest_epistemic_status: EpistemicStatus | None = None
    severe_drift_count: int = Field(ge=0)
    evidence_gap_count: int = Field(ge=0)
    classification_counts: dict[str, int] = Field(default_factory=dict)
    operator_actions: List[str] = Field(default_factory=list)
    summary_line: str

    model_config = {"extra": "forbid"}


class OracleMemoryReviewReport(BaseModel):
    schema_version: Literal["oracle_memory_review_report/v1"] = "oracle_memory_review_report/v1"
    generated_at_utc: datetime
    lane_id: str
    window_entry_count: int = Field(ge=0)
    window_start_sequence_number: int | None = None
    window_end_sequence_number: int | None = None
    first_input_timestamp_utc: datetime | None = None
    last_input_timestamp_utc: datetime | None = None
    latest_transition_classification: OracleTransitionClassification | None = None
    latest_global_action: GlobalAdvisoryAction | None = None
    latest_epistemic_status: EpistemicStatus | None = None
    review_classification: OracleMemoryReviewClassification
    evidence_gap_count: int = Field(ge=0)
    epistemic_escalation_count: int = Field(ge=0)
    global_action_escalation_count: int = Field(ge=0)
    severe_or_material_drift_count: int = Field(ge=0)
    strategy_retrain_candidate_ids: List[str] = Field(default_factory=list)
    observed_transition_ids: List[str] = Field(default_factory=list)
    triggers: List[str] = Field(default_factory=list)
    operator_actions: List[str] = Field(default_factory=list)
    summary_line: str

    model_config = {"extra": "forbid"}


class OracleMemoryReviewEvidenceManifest(BaseModel):
    schema_version: Literal["oracle_memory_review_evidence_manifest/v1"] = "oracle_memory_review_evidence_manifest/v1"
    generated_at_utc: datetime
    review_id: str
    lane_id: str
    execution_authority: Literal["ADVISORY_ONLY"] = "ADVISORY_ONLY"
    source_memory_lane_path: str
    review_classification: OracleMemoryReviewClassification
    window_entry_count: int = Field(ge=0)
    window_end_sequence_number: int | None = None
    latest_global_action: GlobalAdvisoryAction | None = None
    latest_epistemic_status: EpistemicStatus | None = None
    integrity_status: Literal["VERIFIED", "INCOMPLETE"]
    subjects: List[EvidenceResourceDescriptor] = Field(default_factory=list)
    missing_artifact_paths: List[str] = Field(default_factory=list)
    summary_line: str

    model_config = {"extra": "forbid"}


class OracleMemoryReviewEvidenceVerification(BaseModel):
    verified_at_utc: datetime
    manifest_path: str
    status: OracleEvidenceStatus = "UNVERIFIED"
    artifact_digests_verified: bool = False
    signature_verified: bool = False
    verified_subject_count: int = 0
    digest_mismatches: List[str] = Field(default_factory=list)
    missing_artifact_paths: List[str] = Field(default_factory=list)
    notes: List[str] = Field(default_factory=list)

    model_config = {"extra": "forbid"}


class OracleReviewLaneEntry(BaseModel):
    schema_version: Literal["oracle_review_lane_entry/v1"] = "oracle_review_lane_entry/v1"
    appended_at_utc: datetime
    lane_id: str
    sequence_number: int = Field(ge=0)
    entry_id: str
    review_id: str
    previous_entry_hash: str | None = None
    entry_hash: str
    manifest_path: str
    manifest_sha256: str
    review_classification: OracleMemoryReviewClassification
    window_end_sequence_number: int | None = None
    latest_global_action: GlobalAdvisoryAction | None = None
    latest_epistemic_status: EpistemicStatus | None = None
    evidence_status: OracleEvidenceStatus
    summary_line: str

    model_config = {"extra": "forbid"}


class OracleWeeklyDigestReport(BaseModel):
    schema_version: Literal["oracle_weekly_digest_report/v1"] = "oracle_weekly_digest_report/v1"
    generated_at_utc: datetime
    lane_id: str
    exact_evidence_support_score: float = Field(default=0.0, ge=0.0, le=1.0)
    exact_feedback_confirmation_count: int = Field(default=0, ge=0)
    exact_feedback_relief_count: int = Field(default=0, ge=0)
    window_review_count: int = Field(ge=0)
    window_start_sequence_number: int | None = None
    window_end_sequence_number: int | None = None
    latest_review_classification: OracleMemoryReviewClassification | None = None
    latest_global_action: GlobalAdvisoryAction | None = None
    latest_epistemic_status: EpistemicStatus | None = None
    doctrine_posture: OracleMemoryReviewClassification
    classification_counts: dict[str, int] = Field(default_factory=dict)
    recurring_patterns: List[str] = Field(default_factory=list)
    observed_review_ids: List[str] = Field(default_factory=list)
    operator_actions: List[str] = Field(default_factory=list)
    summary_line: str

    model_config = {"extra": "forbid"}


class OracleWeeklyDigestEvidenceManifest(BaseModel):
    schema_version: Literal["oracle_weekly_digest_evidence_manifest/v1"] = "oracle_weekly_digest_evidence_manifest/v1"
    generated_at_utc: datetime
    digest_id: str
    lane_id: str
    exact_evidence_support_score: float = Field(default=0.0, ge=0.0, le=1.0)
    exact_feedback_confirmation_count: int = Field(default=0, ge=0)
    exact_feedback_relief_count: int = Field(default=0, ge=0)
    execution_authority: Literal["ADVISORY_ONLY"] = "ADVISORY_ONLY"
    source_review_lane_path: str
    doctrine_posture: OracleMemoryReviewClassification
    window_review_count: int = Field(ge=0)
    window_end_sequence_number: int | None = None
    latest_review_classification: OracleMemoryReviewClassification | None = None
    latest_global_action: GlobalAdvisoryAction | None = None
    latest_epistemic_status: EpistemicStatus | None = None
    integrity_status: Literal["VERIFIED", "INCOMPLETE"]
    subjects: List[EvidenceResourceDescriptor] = Field(default_factory=list)
    missing_artifact_paths: List[str] = Field(default_factory=list)
    summary_line: str

    model_config = {"extra": "forbid"}


class OracleWeeklyDigestEvidenceVerification(BaseModel):
    verified_at_utc: datetime
    manifest_path: str
    status: OracleEvidenceStatus = "UNVERIFIED"
    artifact_digests_verified: bool = False
    signature_verified: bool = False
    verified_subject_count: int = 0
    digest_mismatches: List[str] = Field(default_factory=list)
    missing_artifact_paths: List[str] = Field(default_factory=list)
    notes: List[str] = Field(default_factory=list)

    model_config = {"extra": "forbid"}


class OracleDoctrineDriftReport(BaseModel):
    schema_version: Literal["oracle_doctrine_drift_report/v1"] = "oracle_doctrine_drift_report/v1"
    generated_at_utc: datetime
    previous_digest_id: str
    current_digest_id: str
    lane_id: str
    execution_authority: Literal["ADVISORY_ONLY"] = "ADVISORY_ONLY"
    previous_verification_status: OracleEvidenceStatus
    current_verification_status: OracleEvidenceStatus
    comparison_status: OracleEvidenceStatus
    previous_doctrine_posture: OracleMemoryReviewClassification
    current_doctrine_posture: OracleMemoryReviewClassification
    previous_latest_review_classification: OracleMemoryReviewClassification | None = None
    current_latest_review_classification: OracleMemoryReviewClassification | None = None
    previous_latest_global_action: GlobalAdvisoryAction | None = None
    current_latest_global_action: GlobalAdvisoryAction | None = None
    previous_latest_epistemic_status: EpistemicStatus | None = None
    current_latest_epistemic_status: EpistemicStatus | None = None
    recurring_pattern_overlap_count: int = Field(ge=0)
    recurring_pattern_shift_count: int = Field(ge=0)
    drift_classification: OracleDoctrineDriftClassification
    drift_level: OracleDriftLevel
    operator_actions: List[str] = Field(default_factory=list)
    summary_line: str

    model_config = {"extra": "forbid"}


class OracleDoctrineDriftEvidenceManifest(BaseModel):
    schema_version: Literal["oracle_doctrine_drift_evidence_manifest/v1"] = "oracle_doctrine_drift_evidence_manifest/v1"
    generated_at_utc: datetime
    drift_id: str
    lane_id: str
    execution_authority: Literal["ADVISORY_ONLY"] = "ADVISORY_ONLY"
    source_previous_digest_path: str
    source_current_digest_path: str
    drift_classification: OracleDoctrineDriftClassification
    drift_level: OracleDriftLevel
    previous_doctrine_posture: OracleMemoryReviewClassification
    current_doctrine_posture: OracleMemoryReviewClassification
    integrity_status: Literal["VERIFIED", "INCOMPLETE"]
    subjects: List[EvidenceResourceDescriptor] = Field(default_factory=list)
    missing_artifact_paths: List[str] = Field(default_factory=list)
    summary_line: str

    model_config = {"extra": "forbid"}


class OracleDoctrineDriftEvidenceVerification(BaseModel):
    verified_at_utc: datetime
    manifest_path: str
    status: OracleEvidenceStatus = "UNVERIFIED"
    artifact_digests_verified: bool = False
    signature_verified: bool = False
    verified_subject_count: int = 0
    digest_mismatches: List[str] = Field(default_factory=list)
    missing_artifact_paths: List[str] = Field(default_factory=list)
    notes: List[str] = Field(default_factory=list)

    model_config = {"extra": "forbid"}


class OracleDoctrineLaneEntry(BaseModel):
    schema_version: Literal["oracle_doctrine_lane_entry/v1"] = "oracle_doctrine_lane_entry/v1"
    appended_at_utc: datetime
    lane_id: str
    sequence_number: int = Field(ge=0)
    entry_id: str
    drift_id: str
    previous_entry_hash: str | None = None
    entry_hash: str
    manifest_path: str
    manifest_sha256: str
    drift_classification: OracleDoctrineDriftClassification
    drift_level: OracleDriftLevel
    current_doctrine_posture: OracleMemoryReviewClassification
    evidence_status: OracleEvidenceStatus
    summary_line: str

    model_config = {"extra": "forbid"}


class OracleMonthlyDigestReport(BaseModel):
    schema_version: Literal["oracle_monthly_digest_report/v1"] = "oracle_monthly_digest_report/v1"
    generated_at_utc: datetime
    lane_id: str
    exact_evidence_support_score: float = Field(default=0.0, ge=0.0, le=1.0)
    exact_feedback_confirmation_count: int = Field(default=0, ge=0)
    exact_feedback_relief_count: int = Field(default=0, ge=0)
    window_entry_count: int = Field(ge=0)
    window_start_sequence_number: int | None = None
    window_end_sequence_number: int | None = None
    latest_drift_classification: OracleDoctrineDriftClassification | None = None
    latest_current_doctrine_posture: OracleMemoryReviewClassification | None = None
    doctrine_memory_classification: OracleDoctrineMemoryClassification
    drift_classification_counts: dict[str, int] = Field(default_factory=dict)
    recurring_patterns: List[str] = Field(default_factory=list)
    observed_drift_ids: List[str] = Field(default_factory=list)
    operator_actions: List[str] = Field(default_factory=list)
    summary_line: str

    model_config = {"extra": "forbid"}


class OracleMonthlyDigestEvidenceManifest(BaseModel):
    schema_version: Literal["oracle_monthly_digest_evidence_manifest/v1"] = "oracle_monthly_digest_evidence_manifest/v1"
    generated_at_utc: datetime
    monthly_digest_id: str
    lane_id: str
    exact_evidence_support_score: float = Field(default=0.0, ge=0.0, le=1.0)
    exact_feedback_confirmation_count: int = Field(default=0, ge=0)
    exact_feedback_relief_count: int = Field(default=0, ge=0)
    execution_authority: Literal["ADVISORY_ONLY"] = "ADVISORY_ONLY"
    source_doctrine_lane_path: str
    doctrine_memory_classification: OracleDoctrineMemoryClassification
    window_entry_count: int = Field(ge=0)
    window_end_sequence_number: int | None = None
    latest_drift_classification: OracleDoctrineDriftClassification | None = None
    latest_current_doctrine_posture: OracleMemoryReviewClassification | None = None
    integrity_status: Literal["VERIFIED", "INCOMPLETE"]
    subjects: List[EvidenceResourceDescriptor] = Field(default_factory=list)
    missing_artifact_paths: List[str] = Field(default_factory=list)
    summary_line: str

    model_config = {"extra": "forbid"}


class OracleMonthlyDigestEvidenceVerification(BaseModel):
    verified_at_utc: datetime
    manifest_path: str
    status: OracleEvidenceStatus = "UNVERIFIED"
    artifact_digests_verified: bool = False
    signature_verified: bool = False
    verified_subject_count: int = 0
    digest_mismatches: List[str] = Field(default_factory=list)
    missing_artifact_paths: List[str] = Field(default_factory=list)
    notes: List[str] = Field(default_factory=list)

    model_config = {"extra": "forbid"}


class OracleMonthlyLaneEntry(BaseModel):
    schema_version: Literal["oracle_monthly_lane_entry/v1"] = "oracle_monthly_lane_entry/v1"
    appended_at_utc: datetime
    lane_id: str
    exact_evidence_support_score: float = Field(default=0.0, ge=0.0, le=1.0)
    exact_feedback_confirmation_count: int = Field(default=0, ge=0)
    exact_feedback_relief_count: int = Field(default=0, ge=0)
    sequence_number: int = Field(ge=0)
    entry_id: str
    monthly_digest_id: str
    previous_entry_hash: str | None = None
    entry_hash: str
    manifest_path: str
    manifest_sha256: str
    doctrine_memory_classification: OracleDoctrineMemoryClassification
    latest_drift_classification: OracleDoctrineDriftClassification | None = None
    evidence_status: OracleEvidenceStatus
    summary_line: str

    model_config = {"extra": "forbid"}


class OracleQuarterlyReviewReport(BaseModel):
    schema_version: Literal["oracle_quarterly_review_report/v1"] = "oracle_quarterly_review_report/v1"
    generated_at_utc: datetime
    lane_id: str
    exact_evidence_support_score: float = Field(default=0.0, ge=0.0, le=1.0)
    exact_feedback_confirmation_count: int = Field(default=0, ge=0)
    exact_feedback_relief_count: int = Field(default=0, ge=0)
    window_entry_count: int = Field(ge=0)
    window_start_sequence_number: int | None = None
    window_end_sequence_number: int | None = None
    latest_monthly_digest_id: str | None = None
    latest_doctrine_memory_classification: OracleDoctrineMemoryClassification | None = None
    latest_drift_classification: OracleDoctrineDriftClassification | None = None
    quarterly_review_classification: OracleQuarterlyReviewClassification
    monthly_classification_counts: dict[str, int] = Field(default_factory=dict)
    observed_monthly_digest_ids: List[str] = Field(default_factory=list)
    recurring_patterns: List[str] = Field(default_factory=list)
    operator_actions: List[str] = Field(default_factory=list)
    summary_line: str

    model_config = {"extra": "forbid"}


class OracleQuarterlyReviewEvidenceManifest(BaseModel):
    schema_version: Literal["oracle_quarterly_review_evidence_manifest/v1"] = "oracle_quarterly_review_evidence_manifest/v1"
    generated_at_utc: datetime
    quarterly_review_id: str
    lane_id: str
    exact_evidence_support_score: float = Field(default=0.0, ge=0.0, le=1.0)
    exact_feedback_confirmation_count: int = Field(default=0, ge=0)
    exact_feedback_relief_count: int = Field(default=0, ge=0)
    execution_authority: Literal["ADVISORY_ONLY"] = "ADVISORY_ONLY"
    source_monthly_lane_path: str
    quarterly_review_classification: OracleQuarterlyReviewClassification
    window_entry_count: int = Field(ge=0)
    window_end_sequence_number: int | None = None
    latest_monthly_digest_id: str | None = None
    latest_doctrine_memory_classification: OracleDoctrineMemoryClassification | None = None
    latest_drift_classification: OracleDoctrineDriftClassification | None = None
    integrity_status: Literal["VERIFIED", "INCOMPLETE"]
    subjects: List[EvidenceResourceDescriptor] = Field(default_factory=list)
    missing_artifact_paths: List[str] = Field(default_factory=list)
    summary_line: str

    model_config = {"extra": "forbid"}


class OracleQuarterlyReviewEvidenceVerification(BaseModel):
    verified_at_utc: datetime
    manifest_path: str
    status: OracleEvidenceStatus = "UNVERIFIED"
    artifact_digests_verified: bool = False
    signature_verified: bool = False
    verified_subject_count: int = Field(ge=0)
    digest_mismatches: List[str] = Field(default_factory=list)
    missing_artifact_paths: List[str] = Field(default_factory=list)
    notes: List[str] = Field(default_factory=list)

    model_config = {"extra": "forbid"}


class OracleQuarterlyLaneEntry(BaseModel):
    schema_version: Literal["oracle_quarterly_lane_entry/v1"] = "oracle_quarterly_lane_entry/v1"
    appended_at_utc: datetime
    lane_id: str
    exact_evidence_support_score: float = Field(default=0.0, ge=0.0, le=1.0)
    exact_feedback_confirmation_count: int = Field(default=0, ge=0)
    exact_feedback_relief_count: int = Field(default=0, ge=0)
    sequence_number: int = Field(ge=0)
    entry_id: str
    quarterly_review_id: str
    previous_entry_hash: str | None = None
    entry_hash: str
    manifest_path: str
    manifest_sha256: str
    quarterly_review_classification: OracleQuarterlyReviewClassification
    latest_monthly_digest_id: str | None = None
    evidence_status: OracleEvidenceStatus
    summary_line: str

    model_config = {"extra": "forbid"}


class OracleSemiannualAuditReport(BaseModel):
    schema_version: Literal["oracle_semiannual_audit_report/v1"] = "oracle_semiannual_audit_report/v1"
    generated_at_utc: datetime
    lane_id: str
    exact_evidence_support_score: float = Field(default=0.0, ge=0.0, le=1.0)
    exact_feedback_confirmation_count: int = Field(default=0, ge=0)
    exact_feedback_relief_count: int = Field(default=0, ge=0)
    window_entry_count: int = Field(ge=0)
    window_start_sequence_number: int | None = None
    window_end_sequence_number: int | None = None
    latest_quarterly_review_id: str | None = None
    latest_quarterly_review_classification: OracleQuarterlyReviewClassification | None = None
    semiannual_audit_classification: OracleSemiannualAuditClassification
    strategic_backing_classification: Literal["SEALED_STRATEGIC_STACK_BACKED", "DOCTRINE_ONLY_LADDER_BACKED", "NO_STRATEGIC_STACK_HISTORY"] = "NO_STRATEGIC_STACK_HISTORY"
    strategic_stack_evidence_count: int = Field(default=0, ge=0)
    strategic_stack_requirement_met: bool = False
    quarterly_classification_counts: dict[str, int] = Field(default_factory=dict)
    observed_quarterly_review_ids: List[str] = Field(default_factory=list)
    recurring_patterns: List[str] = Field(default_factory=list)
    operator_actions: List[str] = Field(default_factory=list)
    summary_line: str

    model_config = {"extra": "forbid"}


class OracleSemiannualAuditEvidenceManifest(BaseModel):
    schema_version: Literal["oracle_semiannual_audit_evidence_manifest/v1"] = "oracle_semiannual_audit_evidence_manifest/v1"
    generated_at_utc: datetime
    semiannual_audit_id: str
    lane_id: str
    exact_evidence_support_score: float = Field(default=0.0, ge=0.0, le=1.0)
    exact_feedback_confirmation_count: int = Field(default=0, ge=0)
    exact_feedback_relief_count: int = Field(default=0, ge=0)
    execution_authority: Literal["ADVISORY_ONLY"] = "ADVISORY_ONLY"
    source_quarterly_lane_path: str
    semiannual_audit_classification: OracleSemiannualAuditClassification
    strategic_backing_classification: Literal["SEALED_STRATEGIC_STACK_BACKED", "DOCTRINE_ONLY_LADDER_BACKED", "NO_STRATEGIC_STACK_HISTORY"] = "NO_STRATEGIC_STACK_HISTORY"
    strategic_stack_evidence_count: int = Field(default=0, ge=0)
    strategic_stack_requirement_met: bool = False
    window_entry_count: int = Field(ge=0)
    window_end_sequence_number: int | None = None
    latest_quarterly_review_id: str | None = None
    latest_quarterly_review_classification: OracleQuarterlyReviewClassification | None = None
    integrity_status: Literal["VERIFIED", "INCOMPLETE"]
    subjects: List[EvidenceResourceDescriptor] = Field(default_factory=list)
    missing_artifact_paths: List[str] = Field(default_factory=list)
    summary_line: str

    model_config = {"extra": "forbid"}


class OracleSemiannualAuditEvidenceVerification(BaseModel):
    verified_at_utc: datetime
    manifest_path: str
    status: OracleEvidenceStatus = "UNVERIFIED"
    artifact_digests_verified: bool = False
    signature_verified: bool = False
    verified_subject_count: int = Field(ge=0)
    digest_mismatches: List[str] = Field(default_factory=list)
    missing_artifact_paths: List[str] = Field(default_factory=list)
    notes: List[str] = Field(default_factory=list)

    model_config = {"extra": "forbid"}


class OracleSemiannualLaneEntry(BaseModel):
    schema_version: Literal["oracle_semiannual_lane_entry/v1"] = "oracle_semiannual_lane_entry/v1"
    appended_at_utc: datetime
    lane_id: str
    exact_evidence_support_score: float = Field(default=0.0, ge=0.0, le=1.0)
    exact_feedback_confirmation_count: int = Field(default=0, ge=0)
    exact_feedback_relief_count: int = Field(default=0, ge=0)
    sequence_number: int = Field(ge=0)
    entry_id: str
    semiannual_audit_id: str
    previous_entry_hash: str | None = None
    entry_hash: str
    manifest_path: str
    manifest_sha256: str
    semiannual_audit_classification: OracleSemiannualAuditClassification
    strategic_backing_classification: Literal["SEALED_STRATEGIC_STACK_BACKED", "DOCTRINE_ONLY_LADDER_BACKED", "NO_STRATEGIC_STACK_HISTORY"] = "NO_STRATEGIC_STACK_HISTORY"
    strategic_stack_evidence_count: int = Field(default=0, ge=0)
    strategic_stack_requirement_met: bool = False
    latest_quarterly_review_id: str | None = None
    evidence_status: OracleEvidenceStatus
    summary_line: str

    model_config = {"extra": "forbid"}


class OracleAnnualReviewReport(BaseModel):
    schema_version: Literal["oracle_annual_review_report/v1"] = "oracle_annual_review_report/v1"
    generated_at_utc: datetime
    lane_id: str
    exact_evidence_support_score: float = Field(default=0.0, ge=0.0, le=1.0)
    exact_feedback_confirmation_count: int = Field(default=0, ge=0)
    exact_feedback_relief_count: int = Field(default=0, ge=0)
    window_entry_count: int = Field(ge=0)
    window_start_sequence_number: int | None = None
    window_end_sequence_number: int | None = None
    latest_semiannual_audit_id: str | None = None
    latest_semiannual_audit_classification: OracleSemiannualAuditClassification | None = None
    annual_review_classification: OracleAnnualReviewClassification
    strategic_backing_classification: Literal["SEALED_STRATEGIC_STACK_BACKED", "DOCTRINE_ONLY_LADDER_BACKED", "NO_STRATEGIC_STACK_HISTORY"] = "NO_STRATEGIC_STACK_HISTORY"
    strategic_stack_evidence_count: int = Field(default=0, ge=0)
    strategic_stack_requirement_met: bool = False
    semiannual_classification_counts: dict[str, int] = Field(default_factory=dict)
    observed_semiannual_audit_ids: List[str] = Field(default_factory=list)
    recurring_patterns: List[str] = Field(default_factory=list)
    operator_actions: List[str] = Field(default_factory=list)
    summary_line: str

    model_config = {"extra": "forbid"}


class OracleAnnualReviewEvidenceManifest(BaseModel):
    schema_version: Literal["oracle_annual_review_evidence_manifest/v1"] = "oracle_annual_review_evidence_manifest/v1"
    generated_at_utc: datetime
    annual_review_id: str
    lane_id: str
    exact_evidence_support_score: float = Field(default=0.0, ge=0.0, le=1.0)
    exact_feedback_confirmation_count: int = Field(default=0, ge=0)
    exact_feedback_relief_count: int = Field(default=0, ge=0)
    execution_authority: Literal["ADVISORY_ONLY"] = "ADVISORY_ONLY"
    source_semiannual_lane_path: str
    annual_review_classification: OracleAnnualReviewClassification
    strategic_backing_classification: Literal["SEALED_STRATEGIC_STACK_BACKED", "DOCTRINE_ONLY_LADDER_BACKED", "NO_STRATEGIC_STACK_HISTORY"] = "NO_STRATEGIC_STACK_HISTORY"
    strategic_stack_evidence_count: int = Field(default=0, ge=0)
    strategic_stack_requirement_met: bool = False
    window_entry_count: int = Field(ge=0)
    window_end_sequence_number: int | None = None
    latest_semiannual_audit_id: str | None = None
    latest_semiannual_audit_classification: OracleSemiannualAuditClassification | None = None
    integrity_status: Literal["VERIFIED", "INCOMPLETE"]
    subjects: List[EvidenceResourceDescriptor] = Field(default_factory=list)
    missing_artifact_paths: List[str] = Field(default_factory=list)
    summary_line: str

    model_config = {"extra": "forbid"}


class OracleAnnualReviewEvidenceVerification(BaseModel):
    verified_at_utc: datetime
    manifest_path: str
    status: OracleEvidenceStatus = "UNVERIFIED"
    artifact_digests_verified: bool = False
    signature_verified: bool = False
    verified_subject_count: int = Field(ge=0)
    digest_mismatches: List[str] = Field(default_factory=list)
    missing_artifact_paths: List[str] = Field(default_factory=list)
    notes: List[str] = Field(default_factory=list)

    model_config = {"extra": "forbid"}


class OracleAnnualLaneEntry(BaseModel):
    schema_version: Literal["oracle_annual_lane_entry/v1"] = "oracle_annual_lane_entry/v1"
    appended_at_utc: datetime
    lane_id: str
    exact_evidence_support_score: float = Field(default=0.0, ge=0.0, le=1.0)
    exact_feedback_confirmation_count: int = Field(default=0, ge=0)
    exact_feedback_relief_count: int = Field(default=0, ge=0)
    sequence_number: int = Field(ge=0)
    entry_id: str
    annual_review_id: str
    previous_entry_hash: str | None = None
    entry_hash: str
    manifest_path: str
    manifest_sha256: str
    annual_review_classification: OracleAnnualReviewClassification
    strategic_backing_classification: Literal["SEALED_STRATEGIC_STACK_BACKED", "DOCTRINE_ONLY_LADDER_BACKED", "NO_STRATEGIC_STACK_HISTORY"] = "NO_STRATEGIC_STACK_HISTORY"
    strategic_stack_evidence_count: int = Field(default=0, ge=0)
    strategic_stack_requirement_met: bool = False
    latest_semiannual_audit_id: str | None = None
    evidence_status: OracleEvidenceStatus
    summary_line: str

    model_config = {"extra": "forbid"}


class OracleConstitutionalDigestReport(BaseModel):
    schema_version: Literal["oracle_constitutional_digest_report/v1"] = "oracle_constitutional_digest_report/v1"
    generated_at_utc: datetime
    lane_id: str
    exact_evidence_support_score: float = Field(default=0.0, ge=0.0, le=1.0)
    exact_feedback_confirmation_count: int = Field(default=0, ge=0)
    exact_feedback_relief_count: int = Field(default=0, ge=0)
    window_entry_count: int = Field(ge=0)
    window_start_sequence_number: int | None = None
    window_end_sequence_number: int | None = None
    latest_annual_review_id: str | None = None
    latest_annual_review_classification: OracleAnnualReviewClassification | None = None
    constitutional_digest_classification: OracleConstitutionalDigestClassification
    strategic_backing_classification: Literal["SEALED_STRATEGIC_STACK_BACKED", "DOCTRINE_ONLY_LADDER_BACKED", "NO_STRATEGIC_STACK_HISTORY"] = "NO_STRATEGIC_STACK_HISTORY"
    strategic_stack_evidence_count: int = Field(default=0, ge=0)
    strategic_stack_requirement_met: bool = False
    annual_classification_counts: dict[str, int] = Field(default_factory=dict)
    observed_annual_review_ids: List[str] = Field(default_factory=list)
    recurring_patterns: List[str] = Field(default_factory=list)
    operator_actions: List[str] = Field(default_factory=list)
    summary_line: str

    model_config = {"extra": "forbid"}


class OracleConstitutionalDigestEvidenceManifest(BaseModel):
    schema_version: Literal["oracle_constitutional_digest_evidence_manifest/v1"] = "oracle_constitutional_digest_evidence_manifest/v1"
    generated_at_utc: datetime
    constitutional_digest_id: str
    lane_id: str
    exact_evidence_support_score: float = Field(default=0.0, ge=0.0, le=1.0)
    exact_feedback_confirmation_count: int = Field(default=0, ge=0)
    exact_feedback_relief_count: int = Field(default=0, ge=0)
    execution_authority: Literal["ADVISORY_ONLY"] = "ADVISORY_ONLY"
    source_annual_lane_path: str
    constitutional_digest_classification: OracleConstitutionalDigestClassification
    strategic_backing_classification: Literal["SEALED_STRATEGIC_STACK_BACKED", "DOCTRINE_ONLY_LADDER_BACKED", "NO_STRATEGIC_STACK_HISTORY"] = "NO_STRATEGIC_STACK_HISTORY"
    strategic_stack_evidence_count: int = Field(default=0, ge=0)
    strategic_stack_requirement_met: bool = False
    window_entry_count: int = Field(ge=0)
    window_end_sequence_number: int | None = None
    latest_annual_review_id: str | None = None
    latest_annual_review_classification: OracleAnnualReviewClassification | None = None
    integrity_status: Literal["VERIFIED", "INCOMPLETE"]
    subjects: List[EvidenceResourceDescriptor] = Field(default_factory=list)
    missing_artifact_paths: List[str] = Field(default_factory=list)
    summary_line: str

    model_config = {"extra": "forbid"}


class OracleConstitutionalDigestEvidenceVerification(BaseModel):
    verified_at_utc: datetime
    manifest_path: str
    status: OracleEvidenceStatus = "UNVERIFIED"
    artifact_digests_verified: bool = False
    signature_verified: bool = False
    verified_subject_count: int = Field(ge=0)
    digest_mismatches: List[str] = Field(default_factory=list)
    missing_artifact_paths: List[str] = Field(default_factory=list)
    notes: List[str] = Field(default_factory=list)

    model_config = {"extra": "forbid"}


class OracleConstitutionalLaneEntry(BaseModel):
    schema_version: Literal["oracle_constitutional_lane_entry/v1"] = "oracle_constitutional_lane_entry/v1"
    appended_at_utc: datetime
    lane_id: str
    exact_evidence_support_score: float = Field(default=0.0, ge=0.0, le=1.0)
    exact_feedback_confirmation_count: int = Field(default=0, ge=0)
    exact_feedback_relief_count: int = Field(default=0, ge=0)
    sequence_number: int = Field(ge=0)
    entry_id: str
    constitutional_digest_id: str
    previous_entry_hash: str | None = None
    entry_hash: str
    manifest_path: str
    manifest_sha256: str
    constitutional_digest_classification: OracleConstitutionalDigestClassification
    strategic_backing_classification: Literal["SEALED_STRATEGIC_STACK_BACKED", "DOCTRINE_ONLY_LADDER_BACKED", "NO_STRATEGIC_STACK_HISTORY"] = "NO_STRATEGIC_STACK_HISTORY"
    strategic_stack_evidence_count: int = Field(default=0, ge=0)
    strategic_stack_requirement_met: bool = False
    latest_annual_review_id: str | None = None
    evidence_status: OracleEvidenceStatus
    summary_line: str

    model_config = {"extra": "forbid"}


class OracleDoctrineLineageIndex(BaseModel):
    schema_version: Literal["oracle_doctrine_lineage_index/v1"] = "oracle_doctrine_lineage_index/v1"
    generated_at_utc: datetime
    repo_root: str
    search_root: str
    preferred_strategic_backing_source: str | None = None
    preferred_strategic_backing_classification: Literal["SEALED_STRATEGIC_STACK_BACKED", "DOCTRINE_ONLY_LADDER_BACKED", "NO_STRATEGIC_STACK_HISTORY"] | None = None
    preferred_strategic_stack_evidence_count: int | None = Field(default=None, ge=0)
    preferred_strategic_stack_requirement_met: bool | None = None
    closure_snapshot_paths: List[str] = Field(default_factory=list)
    governed_exception_paths: List[str] = Field(default_factory=list)
    oracle_evidence_manifest_paths: List[str] = Field(default_factory=list)
    oracle_transition_evidence_paths: List[str] = Field(default_factory=list)
    oracle_memory_review_evidence_paths: List[str] = Field(default_factory=list)
    oracle_weekly_digest_evidence_paths: List[str] = Field(default_factory=list)
    oracle_doctrine_drift_evidence_paths: List[str] = Field(default_factory=list)
    oracle_monthly_digest_evidence_paths: List[str] = Field(default_factory=list)
    oracle_quarterly_review_evidence_paths: List[str] = Field(default_factory=list)
    oracle_semiannual_audit_evidence_paths: List[str] = Field(default_factory=list)
    oracle_annual_review_evidence_paths: List[str] = Field(default_factory=list)
    oracle_constitutional_digest_evidence_paths: List[str] = Field(default_factory=list)
    oracle_strategic_stack_evidence_paths: List[str] = Field(default_factory=list)
    annual_lane_paths: List[str] = Field(default_factory=list)
    constitutional_lane_paths: List[str] = Field(default_factory=list)
    integrity_warnings: List[str] = Field(default_factory=list)
    summary_line: str

    model_config = {"extra": "forbid"}


class OracleDoctrineLineageVerification(BaseModel):
    schema_version: Literal["oracle_doctrine_lineage_verification/v1"] = "oracle_doctrine_lineage_verification/v1"
    verified_at_utc: datetime
    repo_root: str
    search_root: str
    preferred_strategic_backing_source: str | None = None
    exact_evidence_support_score: float = Field(default=0.0, ge=0.0, le=1.0)
    exact_feedback_confirmation_count: int = Field(default=0, ge=0)
    exact_feedback_relief_count: int = Field(default=0, ge=0)
    preferred_strategic_backing_classification: Literal["SEALED_STRATEGIC_STACK_BACKED", "DOCTRINE_ONLY_LADDER_BACKED", "NO_STRATEGIC_STACK_HISTORY"] | None = None
    seal_status: OracleDoctrineLineageSealStatus
    completeness_score: float = Field(ge=0.0, le=1.0)
    completeness_percent: int = Field(ge=0, le=100)
    required_layer_count: int = Field(ge=0)
    valid_required_layer_count: int = Field(ge=0)
    layer_presence: dict[str, bool] = Field(default_factory=dict)
    layer_validity: dict[str, bool] = Field(default_factory=dict)
    strategic_stack_evidence_count: int = Field(default=0, ge=0)
    strategic_stack_layer_valid: bool = False
    strategic_stack_requirement_met: bool = False
    missing_required_layers: List[str] = Field(default_factory=list)
    missing_optional_layers: List[str] = Field(default_factory=list)
    parse_failures: List[str] = Field(default_factory=list)
    integrity_warnings: List[str] = Field(default_factory=list)
    operator_actions: List[str] = Field(default_factory=list)
    summary_line: str

    model_config = {"extra": "forbid"}


class OracleConstitutionalGateReport(BaseModel):
    schema_version: Literal["oracle_constitutional_gate_report/v1"] = "oracle_constitutional_gate_report/v1"
    generated_at_utc: datetime
    repo_root: str
    search_root: str
    preferred_strategic_backing_source: str | None = None
    exact_evidence_support_score: float = Field(default=0.0, ge=0.0, le=1.0)
    exact_feedback_confirmation_count: int = Field(default=0, ge=0)
    exact_feedback_relief_count: int = Field(default=0, ge=0)
    preferred_strategic_backing_classification: Literal["SEALED_STRATEGIC_STACK_BACKED", "DOCTRINE_ONLY_LADDER_BACKED", "NO_STRATEGIC_STACK_HISTORY"] | None = None
    manifest_path: str
    minimum_required_seal_status: OracleDoctrineLineageSealStatus
    lineage_seal_status: OracleDoctrineLineageSealStatus
    lineage_completeness_percent: int = Field(ge=0, le=100)
    constitutional_digest_classification: OracleConstitutionalDigestClassification | None = None
    manifest_verification_status: OracleEvidenceStatus
    strategic_stack_evidence_count: int = Field(default=0, ge=0)
    strategic_stack_requirement_met: bool = False
    trust_status: OracleConstitutionalTrustStatus
    trusted_for_constitutional_use: bool = False
    blocking_reasons: List[str] = Field(default_factory=list)
    operator_actions: List[str] = Field(default_factory=list)
    facts: List[str] = Field(default_factory=list)
    summary_line: str

    model_config = {"extra": "forbid"}


class OracleEventLogQuerySpec(BaseModel):
    schema_version: Literal["oracle_event_log_query_spec/v1"] = "oracle_event_log_query_spec/v1"
    start_input_timestamp_utc: datetime | None = None
    end_input_timestamp_utc: datetime | None = None
    strategy_ids: List[str] = Field(default_factory=list)
    dominant_regimes: List[AdvisoryRegime] = Field(default_factory=list)
    epistemic_statuses: List[EpistemicStatus] = Field(default_factory=list)
    max_entries: int | None = Field(default=None, ge=1)

    model_config = {"extra": "forbid"}


class OracleEventLogEntry(BaseModel):
    schema_version: Literal["oracle_event_log_entry/v1"] = "oracle_event_log_entry/v1"
    appended_at_utc: datetime
    lane_id: str
    sequence_number: int = Field(ge=0)
    entry_id: str
    evidence_id: str
    previous_entry_hash: str | None = None
    entry_hash: str
    manifest_path: str
    manifest_sha256: str
    linked_closure_id: str | None = None
    input_timestamp_utc: datetime
    dominant_regime: AdvisoryRegime
    recommended_global_action: GlobalAdvisoryAction
    epistemic_status: EpistemicStatus
    average_posterior_edge_confidence: float = Field(ge=0.0, le=1.0)
    maintain_count: int = Field(ge=0)
    canary_count: int = Field(ge=0)
    hibernate_count: int = Field(ge=0)
    strategy_ids: List[str] = Field(default_factory=list)
    evidence_status: OracleEvidenceStatus
    summary_line: str

    model_config = {"extra": "forbid"}


class OracleDerivedViewReport(BaseModel):
    schema_version: Literal["oracle_derived_view_report/v1"] = "oracle_derived_view_report/v1"
    generated_at_utc: datetime
    lane_id: str
    view_label: str
    window_entry_count: int = Field(ge=0)
    window_start_sequence_number: int | None = None
    window_end_sequence_number: int | None = None
    first_input_timestamp_utc: datetime | None = None
    last_input_timestamp_utc: datetime | None = None
    latest_event_id: str | None = None
    latest_dominant_regime: AdvisoryRegime | None = None
    latest_global_action: GlobalAdvisoryAction | None = None
    latest_epistemic_status: EpistemicStatus | None = None
    derived_classification: OracleDerivedViewClassification
    classification_counts: dict[str, int] = Field(default_factory=dict)
    regime_counts: dict[str, int] = Field(default_factory=dict)
    global_action_counts: dict[str, int] = Field(default_factory=dict)
    epistemic_counts: dict[str, int] = Field(default_factory=dict)
    evidence_gap_count: int = Field(ge=0)
    elevated_or_unknown_count: int = Field(ge=0)
    defensive_posture_count: int = Field(ge=0)
    retrain_pressure_count: int = Field(ge=0)
    average_posterior_edge_confidence: float = Field(ge=0.0, le=1.0)
    observed_entry_ids: List[str] = Field(default_factory=list)
    operator_actions: List[str] = Field(default_factory=list)
    summary_line: str

    model_config = {"extra": "forbid"}


class OracleDerivedViewCheckpointMetadata(BaseModel):
    schema_version: Literal["oracle_derived_view_checkpoint_metadata/v1"] = "oracle_derived_view_checkpoint_metadata/v1"
    generated_at_utc: datetime
    lane_id: str
    view_label: str
    window_size: int = Field(ge=1)
    source_event_log_path: str
    query_spec: OracleEventLogQuerySpec = Field(default_factory=OracleEventLogQuerySpec)
    file_size_bytes: int = Field(ge=0)
    file_offset_bytes: int = Field(ge=0)
    last_event_log_sequence_number: int | None = None
    last_event_log_entry_hash: str | None = None
    cached_window_entries: List[OracleEventLogEntry] = Field(default_factory=list)
    summary_line: str

    model_config = {"extra": "forbid"}


class OracleEventCheckpointManifest(BaseModel):
    schema_version: Literal["oracle_event_checkpoint_manifest/v1"] = "oracle_event_checkpoint_manifest/v1"
    generated_at_utc: datetime
    checkpoint_id: str
    lane_id: str
    view_label: str
    source_event_log_path: str
    execution_authority: Literal["ADVISORY_ONLY"] = "ADVISORY_ONLY"
    derived_classification: OracleDerivedViewClassification
    window_entry_count: int = Field(ge=0)
    window_start_sequence_number: int | None = None
    window_end_sequence_number: int | None = None
    last_entry_hash: str | None = None
    latest_event_id: str | None = None
    integrity_status: Literal["VERIFIED", "INCOMPLETE"]
    subjects: List[EvidenceResourceDescriptor] = Field(default_factory=list)
    missing_artifact_paths: List[str] = Field(default_factory=list)
    summary_line: str

    model_config = {"extra": "forbid"}


class OracleEventCheckpointVerification(BaseModel):
    verified_at_utc: datetime
    manifest_path: str
    status: OracleEvidenceStatus = "UNVERIFIED"
    artifact_digests_verified: bool = False
    signature_verified: bool = False
    verified_subject_count: int = Field(ge=0)
    digest_mismatches: List[str] = Field(default_factory=list)
    missing_artifact_paths: List[str] = Field(default_factory=list)
    notes: List[str] = Field(default_factory=list)

    model_config = {"extra": "forbid"}


class OracleExplanationNode(BaseModel):
    node_id: str
    parent_node_id: str | None = None
    category: OracleExplanationCategory
    conclusion: str
    detail: str
    facts: List[str] = Field(default_factory=list)

    model_config = {"extra": "forbid"}


class OracleTrustExplanationReport(BaseModel):
    schema_version: Literal["oracle_trust_explanation_report/v1"] = "oracle_trust_explanation_report/v1"
    generated_at_utc: datetime
    explanation_kind: Literal["derived_view", "event_checkpoint", "lineage_verification", "constitutional_gate"]
    subject_schema_version: str
    subject_path: str | None = None
    trust_status: OracleConstitutionalTrustStatus
    preferred_strategic_backing_source: str | None = None
    exact_feedback_confirmation_count: int = Field(default=0, ge=0)
    exact_feedback_relief_count: int = Field(default=0, ge=0)
    preferred_strategic_backing_classification: Literal["SEALED_STRATEGIC_STACK_BACKED", "DOCTRINE_ONLY_LADDER_BACKED", "NO_STRATEGIC_STACK_HISTORY"] | None = None
    exact_evidence_support_score: float = Field(default=0.0, ge=0.0, le=1.0)
    summary_line: str
    nodes: List[OracleExplanationNode] = Field(default_factory=list)

    model_config = {"extra": "forbid"}


class OracleOperatorDiagnosticReport(BaseModel):
    schema_version: Literal["oracle_operator_diagnostic_report/v1"] = "oracle_operator_diagnostic_report/v1"
    generated_at_utc: datetime
    diagnostic_kind: Literal["why_restricted", "why_blocked"]
    subject_path: str | None = None
    trust_status: OracleConstitutionalTrustStatus
    blocked: bool = False
    preferred_strategic_backing_source: str | None = None
    exact_feedback_confirmation_count: int = Field(default=0, ge=0)
    exact_feedback_relief_count: int = Field(default=0, ge=0)
    preferred_strategic_backing_classification: Literal["SEALED_STRATEGIC_STACK_BACKED", "DOCTRINE_ONLY_LADDER_BACKED", "NO_STRATEGIC_STACK_HISTORY"] | None = None
    summary_line: str
    reasons: List[str] = Field(default_factory=list)
    operator_actions: List[str] = Field(default_factory=list)
    explanation: OracleTrustExplanationReport | None = None

    model_config = {"extra": "forbid"}


class OracleStatusPackSection(BaseModel):
    section_id: Literal["lineage", "oracle_posture", "constitutional_gate", "closure_attestation", "governed_exception", "temporal_lane"]
    status: str
    summary_line: str
    preferred_strategic_backing_source: str | None = None
    exact_feedback_confirmation_count: int = Field(default=0, ge=0)
    exact_feedback_relief_count: int = Field(default=0, ge=0)
    exact_cadence_signal_classification: Literal["EXACT_CONFIRMED_PRESSURE", "EXACT_RELIEF_PRESSURE", "AMBIENT_DRIFT"] = "AMBIENT_DRIFT"
    preferred_strategic_backing_classification: Literal["SEALED_STRATEGIC_STACK_BACKED", "DOCTRINE_ONLY_LADDER_BACKED", "NO_STRATEGIC_STACK_HISTORY"] | None = None
    facts: List[str] = Field(default_factory=list)
    operator_actions: List[str] = Field(default_factory=list)
    explanation: OracleTrustExplanationReport | None = None

    model_config = {"extra": "forbid"}


class OracleOperatorWorkboardItemReport(BaseModel):
    work_item_key: str
    queue_key: str
    review_target: str
    priority_band: str
    review_due_by_utc: datetime
    review_sort_key: str
    action_owner_lane: str
    claim_operability: str
    dispatch_posture: str
    urgency: str
    score: int
    summary_line: str
    recommended_actions: List[str] = Field(default_factory=list)

    model_config = {"extra": "forbid"}


class OracleOperatorWorkboardReport(BaseModel):
    schema_version: Literal["oracle_operator_workboard/v1"] = "oracle_operator_workboard/v1"
    board_label: str
    queue_key: str
    review_target: str
    priority_band: str
    review_due_by_utc: datetime
    review_sort_key: str
    work_item_count: int = Field(ge=0)
    summary_line: str
    queue_summary_line: str
    recommended_next_actions: List[str] = Field(default_factory=list)
    entries: List[OracleOperatorWorkboardItemReport] = Field(default_factory=list)

    model_config = {"extra": "forbid"}


class OracleStatusPackReport(BaseModel):
    schema_version: Literal["oracle_status_pack_report/v1"] = "oracle_status_pack_report/v1"
    generated_at_utc: datetime
    repo_root: str
    search_root: str
    trust_status: OracleConstitutionalTrustStatus
    preferred_strategic_backing_source: str | None = None
    exact_feedback_confirmation_count: int = Field(default=0, ge=0)
    exact_feedback_relief_count: int = Field(default=0, ge=0)
    exact_cadence_signal_classification: Literal["EXACT_CONFIRMED_PRESSURE", "EXACT_RELIEF_PRESSURE", "AMBIENT_DRIFT"] = "AMBIENT_DRIFT"
    preferred_strategic_backing_classification: Literal["SEALED_STRATEGIC_STACK_BACKED", "DOCTRINE_ONLY_LADDER_BACKED", "NO_STRATEGIC_STACK_HISTORY"] | None = None
    active_governed_exception_ids: List[str] = Field(default_factory=list)
    summary_line: str
    operator_actions: List[str] = Field(default_factory=list)
    sections: List[OracleStatusPackSection] = Field(default_factory=list)
    operator_workboard: OracleOperatorWorkboardReport | None = None
    provenance_digest_sha256: str = ""

    model_config = {"extra": "forbid"}


class OracleIncidentPackArtifact(BaseModel):
    artifact_kind: str
    source_path: str
    sha256: str
    pack_path: str | None = None
    summary_line: str = ""
    required: bool = False

    model_config = {"extra": "forbid"}


class OracleIncidentPackReport(BaseModel):
    schema_version: Literal["oracle_incident_pack_report/v1"] = "oracle_incident_pack_report/v1"
    generated_at_utc: datetime
    repo_root: str
    search_root: str
    trust_status: OracleConstitutionalTrustStatus
    incident_kind: Literal["restricted", "untrusted", "blocked", "trusted_context"]
    blocked: bool = False
    exact_feedback_confirmation_count: int = Field(default=0, ge=0)
    exact_feedback_relief_count: int = Field(default=0, ge=0)
    exact_cadence_signal_classification: Literal["EXACT_CONFIRMED_PRESSURE", "EXACT_RELIEF_PRESSURE", "AMBIENT_DRIFT"] = "AMBIENT_DRIFT"
    summary_line: str
    recommended_next_actions: List[str] = Field(default_factory=list)
    primary_diagnostic: OracleOperatorDiagnosticReport | None = None
    status_pack: OracleStatusPackReport
    artifacts: List[OracleIncidentPackArtifact] = Field(default_factory=list)
    operator_workboard: OracleOperatorWorkboardReport | None = None
    provenance_digest_sha256: str = ""

    model_config = {"extra": "forbid"}


class OracleCompactedStateRebuildReport(BaseModel):
    schema_version: Literal["oracle_compacted_state_rebuild_report/v1"] = "oracle_compacted_state_rebuild_report/v1"
    generated_at_utc: datetime
    lane_path: str
    checkpoint_metadata_path: str
    source_event_log_path: str
    view_label: str
    previous_replay_status: Literal["CURRENT", "STALE", "DRIFTED", "CORRUPTED", "SOURCE_MISSING"] | None = None
    previous_metadata_found: bool = False
    rebuilt_window_entry_count: int = Field(ge=0)
    rebuilt_entry_ids: List[str] = Field(default_factory=list)
    rebuilt_file_offset_bytes: int = Field(ge=0)
    rebuilt_last_event_log_sequence_number: int | None = None
    rebuilt_last_event_log_entry_hash: str | None = None
    compacted_window_digest_sha256: str = ""
    summary_line: str
    findings: List[str] = Field(default_factory=list)
    operator_actions: List[str] = Field(default_factory=list)

    model_config = {"extra": "forbid"}


class OracleBriefingSection(BaseModel):
    section_id: Literal["trust_banner", "regime_state", "strategy_health", "strategic_posture", "strategic_narrative", "belief_drift_timeline", "opportunity_queue", "strategy_cohorts", "thesis_evolution", "thesis_graph", "strategic_tensions", "contradiction_resolution", "intervention_simulation", "strategic_campaigns", "campaign_execution", "scenario_lab", "doctrine_adaptation", "research_priorities", "investigation_outcomes", "doctrine_posture", "closure_posture", "operator_queue", "open_risks", "active_exceptions"]
    title: str
    status: str
    summary_line: str
    preferred_strategic_backing_source: str | None = None
    exact_feedback_confirmation_count: int = Field(default=0, ge=0)
    exact_feedback_relief_count: int = Field(default=0, ge=0)
    exact_cadence_signal_classification: Literal["EXACT_CONFIRMED_PRESSURE", "EXACT_RELIEF_PRESSURE", "AMBIENT_DRIFT"] = "AMBIENT_DRIFT"
    preferred_strategic_backing_classification: Literal["SEALED_STRATEGIC_STACK_BACKED", "DOCTRINE_ONLY_LADDER_BACKED", "NO_STRATEGIC_STACK_HISTORY"] | None = None
    facts: List[str] = Field(default_factory=list)
    operator_actions: List[str] = Field(default_factory=list)
    provenance_refs: List[str] = Field(default_factory=list)

    model_config = {"extra": "forbid"}


class OracleBriefingPackReport(BaseModel):
    schema_version: Literal["oracle_briefing_pack_report/v1"] = "oracle_briefing_pack_report/v1"
    generated_at_utc: datetime
    repo_root: str
    search_root: str
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
    trust_status: OracleConstitutionalTrustStatus
    preferred_strategic_backing_source: str | None = None
    exact_feedback_confirmation_count: int = Field(default=0, ge=0)
    exact_feedback_relief_count: int = Field(default=0, ge=0)
    exact_cadence_signal_classification: Literal["EXACT_CONFIRMED_PRESSURE", "EXACT_RELIEF_PRESSURE", "AMBIENT_DRIFT"] = "AMBIENT_DRIFT"
    preferred_strategic_backing_classification: Literal["SEALED_STRATEGIC_STACK_BACKED", "DOCTRINE_ONLY_LADDER_BACKED", "NO_STRATEGIC_STACK_HISTORY"] | None = None
    summary_line: str
    status_pack_digest_sha256: str
    incident_pack_digest_sha256: str | None = None
    sections: List[OracleBriefingSection] = Field(default_factory=list)
    operator_actions: List[str] = Field(default_factory=list)
    provenance_digest_sha256: str = ""

    model_config = {"extra": "forbid"}


class OracleCompactedStateInspectionReport(BaseModel):
    schema_version: Literal["oracle_compacted_state_inspection_report/v1"] = "oracle_compacted_state_inspection_report/v1"
    generated_at_utc: datetime
    lane_path: str
    checkpoint_metadata_path: str
    view_label: str
    source_event_log_path: str
    replay_status: Literal["CURRENT", "STALE", "DRIFTED", "CORRUPTED", "SOURCE_MISSING"]
    current_file_size_bytes: int = Field(ge=0)
    metadata_file_size_bytes: int = Field(ge=0)
    metadata_file_offset_bytes: int = Field(ge=0)
    last_event_log_sequence_number: int | None = None
    last_event_log_entry_hash: str | None = None
    cached_window_entry_count: int = Field(ge=0)
    cached_window_entry_ids: List[str] = Field(default_factory=list)
    query_spec: OracleEventLogQuerySpec = Field(default_factory=OracleEventLogQuerySpec)
    compacted_window_digest_sha256: str = ""
    summary_line: str
    findings: List[str] = Field(default_factory=list)
    operator_actions: List[str] = Field(default_factory=list)

    model_config = {"extra": "forbid"}


class OracleReplayAuditSource(BaseModel):
    source_id: Literal["canonical_event_log", "checkpoint_metadata", "checkpoint_manifest", "checkpoint_verification", "rebuilt_checkpoint_metadata", "derived_view_report"]
    status: Literal["CONSISTENT", "STALE", "DRIFTED", "CORRUPTED", "SKIPPED"]
    summary_line: str
    details: List[str] = Field(default_factory=list)

    model_config = {"extra": "forbid"}


class OracleReplayAuditReport(BaseModel):
    schema_version: Literal["oracle_replay_audit_report/v1"] = "oracle_replay_audit_report/v1"
    generated_at_utc: datetime
    lane_path: str
    checkpoint_metadata_path: str
    report_path: str | None = None
    checkpoint_manifest_path: str | None = None
    checkpoint_verification_path: str | None = None
    replay_status: Literal["CONSISTENT", "STALE", "DRIFTED", "CORRUPTED", "SOURCE_MISSING"]
    canonical_window_digest_sha256: str = ""
    compacted_window_digest_sha256: str = ""
    rebuilt_window_digest_sha256: str = ""
    compared_entry_ids: List[str] = Field(default_factory=list)
    findings: List[str] = Field(default_factory=list)
    operator_actions: List[str] = Field(default_factory=list)
    sources: List[OracleReplayAuditSource] = Field(default_factory=list)
    summary_line: str

    model_config = {"extra": "forbid"}


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


class OracleThesisMemoryItem(BaseModel):
    thesis_id: str
    thesis_label: str
    thesis_kind: Literal["REGIME", "LIQUIDITY", "DOCTRINE", "STRATEGY"]
    current_state: OracleThesisCurrentState
    evolution_state: OracleThesisEvolutionState
    confidence_score: float = Field(ge=0.0, le=1.0)
    exact_evidence_support_score: float = Field(default=0.0, ge=0.0, le=1.0)
    previous_confidence_score: float | None = Field(default=None, ge=0.0, le=1.0)
    strategy_ids: List[str] = Field(default_factory=list)
    evidence_for: List[str] = Field(default_factory=list)
    evidence_against: List[str] = Field(default_factory=list)
    recommended_research_action: str
    summary_line: str

    model_config = {"extra": "forbid"}


class OracleThesisMemoryReport(BaseModel):
    schema_version: Literal["oracle_thesis_memory_report/v1"] = "oracle_thesis_memory_report/v1"
    generated_at_utc: datetime
    universe_label: str
    oracle_run_id: str
    input_timestamp_utc: datetime
    dominant_regime: AdvisoryRegime
    strategic_posture: OracleStrategicPosture
    preferred_strategic_backing_source: str | None = None
    preferred_strategic_backing_classification: Literal["SEALED_STRATEGIC_STACK_BACKED", "DOCTRINE_ONLY_LADDER_BACKED", "NO_STRATEGIC_STACK_HISTORY"] | None = None
    exact_evidence_support_score: float = Field(default=0.0, ge=0.0, le=1.0)
    summary_line: str
    strengthening_thesis_ids: List[str] = Field(default_factory=list)
    weakening_thesis_ids: List[str] = Field(default_factory=list)
    items: List[OracleThesisMemoryItem] = Field(default_factory=list)
    operator_actions: List[str] = Field(default_factory=list)

    model_config = {"extra": "forbid"}


class OracleDoctrineAdaptationItem(BaseModel):
    clause_id: str
    clause_label: str
    adaptation_state: Literal["MONITOR", "REVIEW", "ADAPT", "FREEZE"]
    stress_score: float = Field(ge=0.0, le=1.0)
    review_priority_score: float = Field(ge=0.0, le=1.0)
    exact_evidence_support_score: float = Field(default=0.0, ge=0.0, le=1.0)
    weakening_assumptions: List[str] = Field(default_factory=list)
    pressure_sources: List[str] = Field(default_factory=list)
    recommended_adaptation: str
    summary_line: str

    model_config = {"extra": "forbid"}


class OracleDoctrineAdaptationReport(BaseModel):
    schema_version: Literal["oracle_doctrine_adaptation_report/v1"] = "oracle_doctrine_adaptation_report/v1"
    generated_at_utc: datetime
    universe_label: str
    oracle_run_id: str
    input_timestamp_utc: datetime
    dominant_regime: AdvisoryRegime
    strategic_posture: OracleStrategicPosture
    transition_classification: OracleStrategicTransitionClassification | None = None
    history_integrity_status: Literal["CURRENT_ONLY", "SEALED_HISTORY", "MIXED_HISTORY"] = "CURRENT_ONLY"
    sealed_history_observation_count: int = Field(default=0, ge=0)
    unsealed_history_excluded_count: int = Field(default=0, ge=0)
    preferred_strategic_backing_source: str | None = None
    preferred_strategic_backing_classification: Literal["SEALED_STRATEGIC_STACK_BACKED", "DOCTRINE_ONLY_LADDER_BACKED", "NO_STRATEGIC_STACK_HISTORY"] | None = None
    exact_evidence_support_score: float = Field(default=0.0, ge=0.0, le=1.0)
    summary_line: str
    top_review_clause_ids: List[str] = Field(default_factory=list)
    freeze_recommended: bool = False
    items: List[OracleDoctrineAdaptationItem] = Field(default_factory=list)
    operator_actions: List[str] = Field(default_factory=list)

    model_config = {"extra": "forbid"}


class OracleResearchPriorityItem(BaseModel):
    priority_id: str
    priority_kind: OracleResearchPriorityKind
    urgency_score: float = Field(ge=0.0, le=1.0)
    exact_feedback_confirmation_count: int = Field(default=0, ge=0)
    exact_feedback_relief_count: int = Field(default=0, ge=0)
    exact_cadence_signal_classification: Literal["EXACT_CONFIRMED_PRESSURE", "EXACT_RELIEF_PRESSURE", "AMBIENT_DRIFT"] = "AMBIENT_DRIFT"
    exact_evidence_support_score: float = Field(default=0.0, ge=0.0, le=1.0)
    integrity_penalty_score: float = Field(default=0.0, ge=0.0, le=1.0)
    title: str
    summary_line: str
    related_strategy_ids: List[str] = Field(default_factory=list)
    evidence: List[str] = Field(default_factory=list)
    recommended_investigation: str

    model_config = {"extra": "forbid"}


class OracleResearchPriorityReport(BaseModel):
    schema_version: Literal["oracle_research_priority_report/v1"] = "oracle_research_priority_report/v1"
    generated_at_utc: datetime
    universe_label: str
    oracle_run_id: str
    input_timestamp_utc: datetime
    dominant_regime: AdvisoryRegime
    strategic_posture: OracleStrategicPosture
    transition_classification: OracleStrategicTransitionClassification | None = None
    history_integrity_status: Literal["CURRENT_ONLY", "SEALED_HISTORY", "MIXED_HISTORY"] = "CURRENT_ONLY"
    sealed_history_observation_count: int = Field(default=0, ge=0)
    unsealed_history_excluded_count: int = Field(default=0, ge=0)
    preferred_strategic_backing_source: str | None = None
    preferred_strategic_backing_classification: Literal["SEALED_STRATEGIC_STACK_BACKED", "DOCTRINE_ONLY_LADDER_BACKED", "NO_STRATEGIC_STACK_HISTORY"] | None = None
    exact_feedback_confirmation_count: int = Field(default=0, ge=0)
    exact_feedback_relief_count: int = Field(default=0, ge=0)
    exact_cadence_signal_classification: Literal["EXACT_CONFIRMED_PRESSURE", "EXACT_RELIEF_PRESSURE", "AMBIENT_DRIFT"] = "AMBIENT_DRIFT"
    exact_evidence_support_score: float = Field(default=0.0, ge=0.0, le=1.0)
    integrity_penalty_score: float = Field(default=0.0, ge=0.0, le=1.0)
    summary_line: str
    highest_priority_id: str | None = None
    items: List[OracleResearchPriorityItem] = Field(default_factory=list)
    operator_actions: List[str] = Field(default_factory=list)

    model_config = {"extra": "forbid"}


class OracleInvestigationOutcomeInputItem(BaseModel):
    outcome_id: str
    priority_id: str
    execution_state: Literal["PLANNED", "IN_PROGRESS", "COMPLETED", "DEFERRED", "ABORTED"]
    outcome_disposition: Literal["CONFIRMED", "MIXED", "REFUTED", "ESCALATED", "INCONCLUSIVE"] | None = None
    related_strategy_ids: List[str] = Field(default_factory=list)
    thesis_ids: List[str] = Field(default_factory=list)
    doctrine_clause_ids: List[str] = Field(default_factory=list)
    thesis_effect: Literal["STRENGTHENS", "WEAKENS", "NO_CHANGE", "REVIEW_REQUIRED"] = "NO_CHANGE"
    doctrine_effect: Literal["RELIEVES", "PRESSURES", "NO_CHANGE", "FREEZE_CANDIDATE"] = "NO_CHANGE"
    cohort_effect: Literal["PROMOTES", "DEMOTES", "NO_CHANGE", "WATCH"] = "NO_CHANGE"
    confidence_impact: float = Field(default=0.0, ge=-1.0, le=1.0)
    urgency_impact: float = Field(default=0.0, ge=-1.0, le=1.0)
    finding_summary: str
    evidence: List[str] = Field(default_factory=list)
    next_action: str

    model_config = {"extra": "forbid"}


class OracleInvestigationOutcomeInput(BaseModel):
    schema_version: Literal["oracle_investigation_outcome_input/v1"] = "oracle_investigation_outcome_input/v1"
    generated_at_utc: datetime
    universe_label: str
    items: List[OracleInvestigationOutcomeInputItem] = Field(default_factory=list)

    model_config = {"extra": "forbid"}


class OracleResearchExecutionMemoryItem(BaseModel):
    execution_id: str
    priority_id: str
    priority_kind: OracleResearchPriorityKind
    execution_state: Literal["PLANNED", "IN_PROGRESS", "COMPLETED", "DEFERRED", "ABORTED"]
    outcome_disposition: Literal["CONFIRMED", "MIXED", "REFUTED", "ESCALATED", "INCONCLUSIVE"] | None = None
    thesis_effect: Literal["STRENGTHENS", "WEAKENS", "NO_CHANGE", "REVIEW_REQUIRED"] = "NO_CHANGE"
    doctrine_effect: Literal["RELIEVES", "PRESSURES", "NO_CHANGE", "FREEZE_CANDIDATE"] = "NO_CHANGE"
    cohort_effect: Literal["PROMOTES", "DEMOTES", "NO_CHANGE", "WATCH"] = "NO_CHANGE"
    exact_evidence_support_score: float = Field(default=0.0, ge=0.0, le=1.0)
    confidence_impact: float = Field(default=0.0, ge=-1.0, le=1.0)
    urgency_impact: float = Field(default=0.0, ge=-1.0, le=1.0)
    related_strategy_ids: List[str] = Field(default_factory=list)
    thesis_ids: List[str] = Field(default_factory=list)
    doctrine_clause_ids: List[str] = Field(default_factory=list)
    finding_summary: str
    evidence: List[str] = Field(default_factory=list)
    next_action: str
    summary_line: str

    model_config = {"extra": "forbid"}


class OracleResearchExecutionMemoryReport(BaseModel):
    schema_version: Literal["oracle_research_execution_memory_report/v1"] = "oracle_research_execution_memory_report/v1"
    generated_at_utc: datetime
    universe_label: str
    oracle_run_id: str
    input_timestamp_utc: datetime
    preferred_strategic_backing_source: str | None = None
    preferred_strategic_backing_classification: Literal["SEALED_STRATEGIC_STACK_BACKED", "DOCTRINE_ONLY_LADDER_BACKED", "NO_STRATEGIC_STACK_HISTORY"] | None = None
    exact_evidence_support_score: float = Field(default=0.0, ge=0.0, le=1.0)
    summary_line: str
    completed_priority_ids: List[str] = Field(default_factory=list)
    deferred_priority_ids: List[str] = Field(default_factory=list)
    escalated_priority_ids: List[str] = Field(default_factory=list)
    items: List[OracleResearchExecutionMemoryItem] = Field(default_factory=list)
    operator_actions: List[str] = Field(default_factory=list)

    model_config = {"extra": "forbid"}


class OracleThesisGraphNode(BaseModel):
    node_id: str
    node_kind: Literal["THESIS", "DOCTRINE_CLAUSE", "STRATEGY_COHORT", "RESEARCH_PRIORITY", "INVESTIGATION_OUTCOME"]
    label: str
    status: str
    cascade_risk_score: float = Field(ge=0.0, le=1.0)
    exact_evidence_support_score: float = Field(default=0.0, ge=0.0, le=1.0)
    connected_node_ids: List[str] = Field(default_factory=list)
    evidence: List[str] = Field(default_factory=list)
    summary_line: str

    model_config = {"extra": "forbid"}


class OracleThesisGraphEdge(BaseModel):
    edge_id: str
    source_node_id: str
    target_node_id: str
    relation_kind: Literal["SUPPORTS", "WEAKENS", "PRESSURES", "RELIEVES", "INVESTIGATES", "PROMOTES", "DEMOTES", "DEPENDS_ON"]
    influence_score: float = Field(ge=0.0, le=1.0)
    summary_line: str

    model_config = {"extra": "forbid"}


class OracleThesisGraphReport(BaseModel):
    schema_version: Literal["oracle_thesis_graph_report/v1"] = "oracle_thesis_graph_report/v1"
    generated_at_utc: datetime
    universe_label: str
    oracle_run_id: str
    input_timestamp_utc: datetime
    dominant_regime: AdvisoryRegime
    strategic_posture: OracleStrategicPosture
    preferred_strategic_backing_source: str | None = None
    preferred_strategic_backing_classification: Literal["SEALED_STRATEGIC_STACK_BACKED", "DOCTRINE_ONLY_LADDER_BACKED", "NO_STRATEGIC_STACK_HISTORY"] | None = None
    exact_evidence_support_score: float = Field(default=0.0, ge=0.0, le=1.0)
    summary_line: str
    highest_cascade_risk_node_ids: List[str] = Field(default_factory=list)
    nodes: List[OracleThesisGraphNode] = Field(default_factory=list)
    edges: List[OracleThesisGraphEdge] = Field(default_factory=list)
    operator_actions: List[str] = Field(default_factory=list)

    model_config = {"extra": "forbid"}


class OracleStrategicTensionItem(BaseModel):
    tension_id: str
    tension_kind: Literal["POSTURE_CONSENSUS", "OPPORTUNITY_CONSENSUS", "POSTURE_VS_RISK_STACK", "LEAD_COHORT_FRAGILITY", "GRAPH_CASCADE_VS_POSTURE", "RESEARCH_PRIORITY_VS_POSTURE", "EXECUTION_OUTCOME_FEEDBACK"]
    alignment_state: Literal["CONSENSUS", "TENSION", "SEVERE_TENSION"]
    exact_evidence_support_score: float = Field(default=0.0, ge=0.0, le=1.0)
    severity_score: float = Field(ge=0.0, le=1.0)
    title: str
    summary_line: str
    evidence: List[str] = Field(default_factory=list)
    related_strategy_ids: List[str] = Field(default_factory=list)
    resolution_guidance: str

    model_config = {"extra": "forbid"}


class OracleStrategicTensionReport(BaseModel):
    schema_version: Literal["oracle_strategic_tension_report/v1"] = "oracle_strategic_tension_report/v1"
    generated_at_utc: datetime
    universe_label: str
    oracle_run_id: str
    input_timestamp_utc: datetime
    dominant_regime: AdvisoryRegime
    strategic_posture: OracleStrategicPosture
    preferred_strategic_backing_source: str | None = None
    preferred_strategic_backing_classification: Literal["SEALED_STRATEGIC_STACK_BACKED", "DOCTRINE_ONLY_LADDER_BACKED", "NO_STRATEGIC_STACK_HISTORY"] | None = None
    exact_evidence_support_score: float = Field(default=0.0, ge=0.0, le=1.0)
    summary_line: str
    consensus_strength_score: float = Field(ge=0.0, le=1.0)
    highest_severity_tension_id: str | None = None
    tension_item_ids: List[str] = Field(default_factory=list)
    consensus_item_ids: List[str] = Field(default_factory=list)
    items: List[OracleStrategicTensionItem] = Field(default_factory=list)
    operator_actions: List[str] = Field(default_factory=list)

    model_config = {"extra": "forbid"}


class OracleStrategicNarrativeItem(BaseModel):
    narrative_id: str
    conviction_state: Literal["HIGH_CONVICTION", "GUARDED_CONVICTION", "FRAGILE_CONVICTION", "BROKEN_CONVICTION"]
    driver_kind: Literal["REGIME_DRIVER", "STRATEGY_DRIVER", "DOCTRINE_DRIVER", "SCENARIO_DRIVER", "CONTRADICTION_DRIVER", "INVESTIGATION_DRIVER"]
    exact_feedback_confirmation_count: int = Field(default=0, ge=0)
    exact_feedback_relief_count: int = Field(default=0, ge=0)
    exact_cadence_signal_classification: Literal["EXACT_CONFIRMED_PRESSURE", "EXACT_RELIEF_PRESSURE", "AMBIENT_DRIFT"] = "AMBIENT_DRIFT"
    exact_evidence_support_score: float = Field(default=0.0, ge=0.0, le=1.0)
    rank_score: float = Field(ge=0.0, le=1.0)
    title: str
    summary_line: str
    evidence: List[str] = Field(default_factory=list)
    related_strategy_ids: List[str] = Field(default_factory=list)
    trust_bias: Literal["TRUST_MORE", "HOLD", "TRUST_LESS"] = "HOLD"
    operator_guidance: str

    model_config = {"extra": "forbid"}


class OracleStrategicNarrativeReport(BaseModel):
    schema_version: Literal["oracle_strategic_narrative_report/v1"] = "oracle_strategic_narrative_report/v1"
    generated_at_utc: datetime
    universe_label: str
    oracle_run_id: str
    input_timestamp_utc: datetime
    dominant_regime: AdvisoryRegime
    strategic_posture: OracleStrategicPosture
    preferred_strategic_backing_source: str | None = None
    preferred_strategic_backing_classification: Literal["SEALED_STRATEGIC_STACK_BACKED", "DOCTRINE_ONLY_LADDER_BACKED", "NO_STRATEGIC_STACK_HISTORY"] | None = None
    exact_feedback_confirmation_count: int = Field(default=0, ge=0)
    exact_feedback_relief_count: int = Field(default=0, ge=0)
    exact_cadence_signal_classification: Literal["EXACT_CONFIRMED_PRESSURE", "EXACT_RELIEF_PRESSURE", "AMBIENT_DRIFT"] = "AMBIENT_DRIFT"
    exact_evidence_support_score: float = Field(default=0.0, ge=0.0, le=1.0)
    conviction_state: Literal["HIGH_CONVICTION", "GUARDED_CONVICTION", "FRAGILE_CONVICTION", "BROKEN_CONVICTION"]
    conviction_score: float = Field(ge=0.0, le=1.0)
    fragility_score: float = Field(ge=0.0, le=1.0)
    summary_line: str
    highest_ranked_narrative_id: str | None = None
    items: List[OracleStrategicNarrativeItem] = Field(default_factory=list)
    operator_actions: List[str] = Field(default_factory=list)

    model_config = {"extra": "forbid"}


class OracleStrategicMemoryPoint(BaseModel):
    point_id: str
    generated_at_utc: datetime
    oracle_run_id: str
    input_timestamp_utc: datetime
    dominant_regime: AdvisoryRegime
    strategic_posture: OracleStrategicPosture
    conviction_state: Literal["HIGH_CONVICTION", "GUARDED_CONVICTION", "FRAGILE_CONVICTION", "BROKEN_CONVICTION"]
    conviction_score: float = Field(ge=0.0, le=1.0)
    fragility_score: float = Field(ge=0.0, le=1.0)
    top_driver_kind: Literal["REGIME_DRIVER", "STRATEGY_DRIVER", "DOCTRINE_DRIVER", "SCENARIO_DRIVER", "CONTRADICTION_DRIVER", "INVESTIGATION_DRIVER"] | None = None
    top_driver_title: str | None = None
    top_driver_rank_score: float = Field(default=0.0, ge=0.0, le=1.0)
    summary_line: str

    model_config = {"extra": "forbid"}


class OracleStrategicDriverDriftItem(BaseModel):
    driver_kind: Literal["REGIME_DRIVER", "STRATEGY_DRIVER", "DOCTRINE_DRIVER", "SCENARIO_DRIVER", "CONTRADICTION_DRIVER", "INVESTIGATION_DRIVER"]
    baseline_rank_score: float = Field(ge=0.0, le=1.0)
    current_rank_score: float = Field(ge=0.0, le=1.0)
    drift_delta: float = Field(ge=-1.0, le=1.0)
    drift_direction: Literal["RISING", "FALLING", "STABLE"]
    summary_line: str

    model_config = {"extra": "forbid"}


class OracleStrategicMemoryHorizonReport(BaseModel):
    schema_version: Literal["oracle_strategic_memory_horizon_report/v1"] = "oracle_strategic_memory_horizon_report/v1"
    generated_at_utc: datetime
    universe_label: str
    oracle_run_id: str
    input_timestamp_utc: datetime
    horizon_observation_count: int = Field(ge=1)
    sealed_history_observation_count: int = Field(default=0, ge=0)
    unsealed_history_excluded_count: int = Field(default=0, ge=0)
    history_integrity_status: Literal["CURRENT_ONLY", "SEALED_HISTORY", "MIXED_HISTORY"] = "CURRENT_ONLY"
    source_stack_manifest_paths: List[str] = Field(default_factory=list)
    current_conviction_state: Literal["HIGH_CONVICTION", "GUARDED_CONVICTION", "FRAGILE_CONVICTION", "BROKEN_CONVICTION"]
    current_conviction_score: float = Field(ge=0.0, le=1.0)
    conviction_score_delta: float = Field(ge=-1.0, le=1.0)
    fragility_score_delta: float = Field(ge=-1.0, le=1.0)
    drift_state: Literal["FIRST_OBSERVATION", "STRENGTHENING", "SOFTENING", "REVERSING", "VOLATILE", "STABLE"]
    summary_line: str
    strongest_rising_driver_kind: Literal["REGIME_DRIVER", "STRATEGY_DRIVER", "DOCTRINE_DRIVER", "SCENARIO_DRIVER", "CONTRADICTION_DRIVER", "INVESTIGATION_DRIVER"] | None = None
    strongest_falling_driver_kind: Literal["REGIME_DRIVER", "STRATEGY_DRIVER", "DOCTRINE_DRIVER", "SCENARIO_DRIVER", "INVESTIGATION_DRIVER", "CONTRADICTION_DRIVER"] | None = None
    points: List[OracleStrategicMemoryPoint] = Field(default_factory=list)
    driver_drifts: List[OracleStrategicDriverDriftItem] = Field(default_factory=list)
    operator_actions: List[str] = Field(default_factory=list)

    model_config = {"extra": "forbid"}



class OracleContradictionResolutionItem(BaseModel):
    resolution_id: str
    resolution_kind: Literal["POSTURE_RISK_CONTRADICTION", "COHORT_CONTRADICTION", "CASCADE_CONTRADICTION", "DOCTRINE_CONTRADICTION", "INVESTIGATION_CONTRADICTION", "CONSENSUS_VALIDATION"]
    source_tension_id: str | None = None
    exact_feedback_confirmation_count: int = Field(default=0, ge=0)
    exact_feedback_relief_count: int = Field(default=0, ge=0)
    exact_cadence_signal_classification: Literal["EXACT_CONFIRMED_PRESSURE", "EXACT_RELIEF_PRESSURE", "AMBIENT_DRIFT"] = "AMBIENT_DRIFT"
    exact_evidence_support_score: float = Field(default=0.0, ge=0.0, le=1.0)
    resolution_priority_score: float = Field(ge=0.0, le=1.0)
    expected_conviction_gain_score: float = Field(ge=0.0, le=1.0)
    fragility_reduction_score: float = Field(ge=0.0, le=1.0)
    cascade_relief_score: float = Field(ge=0.0, le=1.0)
    title: str
    summary_line: str
    evidence: List[str] = Field(default_factory=list)
    related_strategy_ids: List[str] = Field(default_factory=list)
    recommended_resolution: str

    model_config = {"extra": "forbid"}


class OracleContradictionResolutionReport(BaseModel):
    schema_version: Literal["oracle_contradiction_resolution_report/v1"] = "oracle_contradiction_resolution_report/v1"
    generated_at_utc: datetime
    universe_label: str
    oracle_run_id: str
    input_timestamp_utc: datetime
    dominant_regime: AdvisoryRegime
    strategic_posture: OracleStrategicPosture
    conviction_state: Literal["HIGH_CONVICTION", "GUARDED_CONVICTION", "FRAGILE_CONVICTION", "BROKEN_CONVICTION"]
    conviction_score: float = Field(ge=0.0, le=1.0)
    fragility_score: float = Field(ge=0.0, le=1.0)
    drift_state: Literal["FIRST_OBSERVATION", "STRENGTHENING", "SOFTENING", "REVERSING", "VOLATILE", "STABLE"]
    history_integrity_status: Literal["CURRENT_ONLY", "SEALED_HISTORY", "MIXED_HISTORY"] = "CURRENT_ONLY"
    sealed_history_observation_count: int = Field(default=0, ge=0)
    unsealed_history_excluded_count: int = Field(default=0, ge=0)
    exact_feedback_confirmation_count: int = Field(default=0, ge=0)
    exact_feedback_relief_count: int = Field(default=0, ge=0)
    exact_cadence_signal_classification: Literal["EXACT_CONFIRMED_PRESSURE", "EXACT_RELIEF_PRESSURE", "AMBIENT_DRIFT"] = "AMBIENT_DRIFT"
    exact_evidence_support_score: float = Field(default=0.0, ge=0.0, le=1.0)
    integrity_penalty_score: float = Field(default=0.0, ge=0.0, le=1.0)
    summary_line: str
    highest_priority_resolution_id: str | None = None
    items: List[OracleContradictionResolutionItem] = Field(default_factory=list)
    operator_actions: List[str] = Field(default_factory=list)

    model_config = {"extra": "forbid"}


class OracleStrategicInterventionItem(BaseModel):
    intervention_id: str
    intervention_kind: Literal["RESOLVE_CONTRADICTION", "VALIDATE_CONSENSUS", "DOCTRINE_RELIEF", "COHORT_STABILIZATION", "SCENARIO_HEDGE"]
    source_resolution_id: str | None = None
    exact_feedback_confirmation_count: int = Field(default=0, ge=0)
    exact_feedback_relief_count: int = Field(default=0, ge=0)
    exact_cadence_signal_classification: Literal["EXACT_CONFIRMED_PRESSURE", "EXACT_RELIEF_PRESSURE", "AMBIENT_DRIFT"] = "AMBIENT_DRIFT"
    integrity_penalty_score: float = Field(default=0.0, ge=0.0, le=1.0)
    exact_evidence_support_score: float = Field(default=0.0, ge=0.0, le=1.0)
    projected_conviction_gain_score: float = Field(ge=0.0, le=1.0)
    projected_fragility_reduction_score: float = Field(ge=0.0, le=1.0)
    projected_queue_pressure_relief_score: float = Field(ge=0.0, le=1.0)
    projected_doctrine_stress_relief_score: float = Field(ge=0.0, le=1.0)
    projected_cohort_resilience_gain_score: float = Field(ge=0.0, le=1.0)
    projected_cascade_relief_score: float = Field(ge=0.0, le=1.0)
    projected_conviction_state: Literal["HIGH_CONVICTION", "GUARDED_CONVICTION", "FRAGILE_CONVICTION", "BROKEN_CONVICTION"]
    title: str
    summary_line: str
    evidence: List[str] = Field(default_factory=list)
    related_strategy_ids: List[str] = Field(default_factory=list)
    recommended_intervention: str

    model_config = {"extra": "forbid"}


class OracleStrategicInterventionReport(BaseModel):
    schema_version: Literal["oracle_strategic_intervention_report/v1"] = "oracle_strategic_intervention_report/v1"
    generated_at_utc: datetime
    universe_label: str
    oracle_run_id: str
    input_timestamp_utc: datetime
    dominant_regime: AdvisoryRegime
    strategic_posture: OracleStrategicPosture
    exact_feedback_confirmation_count: int = Field(default=0, ge=0)
    exact_feedback_relief_count: int = Field(default=0, ge=0)
    exact_cadence_signal_classification: Literal["EXACT_CONFIRMED_PRESSURE", "EXACT_RELIEF_PRESSURE", "AMBIENT_DRIFT"] = "AMBIENT_DRIFT"
    history_integrity_status: Literal["CURRENT_ONLY", "SEALED_HISTORY", "MIXED_HISTORY"] = "CURRENT_ONLY"
    sealed_history_observation_count: int = Field(default=0, ge=0)
    unsealed_history_excluded_count: int = Field(default=0, ge=0)
    preferred_strategic_backing_source: str | None = None
    preferred_strategic_backing_classification: Literal["SEALED_STRATEGIC_STACK_BACKED", "DOCTRINE_ONLY_LADDER_BACKED", "NO_STRATEGIC_STACK_HISTORY"] | None = None
    exact_evidence_support_score: float = Field(default=0.0, ge=0.0, le=1.0)
    integrity_penalty_score: float = Field(default=0.0, ge=0.0, le=1.0)
    baseline_conviction_state: Literal["HIGH_CONVICTION", "GUARDED_CONVICTION", "FRAGILE_CONVICTION", "BROKEN_CONVICTION"]
    baseline_conviction_score: float = Field(ge=0.0, le=1.0)
    baseline_fragility_score: float = Field(ge=0.0, le=1.0)
    baseline_drift_state: Literal["FIRST_OBSERVATION", "STRENGTHENING", "SOFTENING", "REVERSING", "VOLATILE", "STABLE"]
    summary_line: str
    highest_impact_intervention_id: str | None = None
    items: List[OracleStrategicInterventionItem] = Field(default_factory=list)
    operator_actions: List[str] = Field(default_factory=list)

    model_config = {"extra": "forbid"}


class OracleStrategicCampaignStep(BaseModel):
    step_id: str
    step_kind: Literal["INTERVENTION", "INVESTIGATION", "DOCTRINE_ACTION", "SCENARIO_HEDGE", "VALIDATION"]
    title: str
    summary_line: str
    depends_on_step_ids: List[str] = Field(default_factory=list)
    target_ids: List[str] = Field(default_factory=list)

    model_config = {"extra": "forbid"}


class OracleStrategicCampaignItem(BaseModel):
    campaign_id: str
    objective_kind: Literal["CONVICTION_REPAIR", "DOCTRINE_STABILIZATION", "COHORT_RECOVERY", "THESIS_VALIDATION", "OPPORTUNITY_EXPANSION"]
    exact_feedback_confirmation_count: int = Field(default=0, ge=0)
    exact_feedback_relief_count: int = Field(default=0, ge=0)
    exact_cadence_signal_classification: Literal["EXACT_CONFIRMED_PRESSURE", "EXACT_RELIEF_PRESSURE", "AMBIENT_DRIFT"] = "AMBIENT_DRIFT"
    exact_evidence_support_score: float = Field(default=0.0, ge=0.0, le=1.0)
    integrity_penalty_score: float = Field(default=0.0, ge=0.0, le=1.0)
    operator_friction_score: float = Field(default=0.0, ge=0.0, le=1.0)
    priority_score: float = Field(ge=0.0, le=1.0)
    expected_conviction_gain_score: float = Field(ge=0.0, le=1.0)
    expected_fragility_reduction_score: float = Field(ge=0.0, le=1.0)
    expected_queue_pressure_relief_score: float = Field(ge=0.0, le=1.0)
    expected_doctrine_relief_score: float = Field(ge=0.0, le=1.0)
    expected_cohort_resilience_gain_score: float = Field(ge=0.0, le=1.0)
    title: str
    summary_line: str
    evidence: List[str] = Field(default_factory=list)
    related_strategy_ids: List[str] = Field(default_factory=list)
    source_intervention_ids: List[str] = Field(default_factory=list)
    source_priority_ids: List[str] = Field(default_factory=list)
    steps: List[OracleStrategicCampaignStep] = Field(default_factory=list)
    recommended_campaign: str

    model_config = {"extra": "forbid"}


class OracleStrategicCampaignReport(BaseModel):
    schema_version: Literal["oracle_strategic_campaign_report/v1"] = "oracle_strategic_campaign_report/v1"
    generated_at_utc: datetime
    universe_label: str
    oracle_run_id: str
    input_timestamp_utc: datetime
    dominant_regime: AdvisoryRegime
    strategic_posture: OracleStrategicPosture
    exact_feedback_confirmation_count: int = Field(default=0, ge=0)
    exact_feedback_relief_count: int = Field(default=0, ge=0)
    exact_cadence_signal_classification: Literal["EXACT_CONFIRMED_PRESSURE", "EXACT_RELIEF_PRESSURE", "AMBIENT_DRIFT"] = "AMBIENT_DRIFT"
    history_integrity_status: Literal["CURRENT_ONLY", "SEALED_HISTORY", "MIXED_HISTORY"] = "CURRENT_ONLY"
    sealed_history_observation_count: int = Field(default=0, ge=0)
    unsealed_history_excluded_count: int = Field(default=0, ge=0)
    preferred_strategic_backing_source: str | None = None
    preferred_strategic_backing_classification: Literal["SEALED_STRATEGIC_STACK_BACKED", "DOCTRINE_ONLY_LADDER_BACKED", "NO_STRATEGIC_STACK_HISTORY"] | None = None
    exact_evidence_support_score: float = Field(default=0.0, ge=0.0, le=1.0)
    integrity_penalty_score: float = Field(default=0.0, ge=0.0, le=1.0)
    integrity_operator_friction_score: float = Field(default=0.0, ge=0.0, le=1.0)
    baseline_conviction_state: Literal["HIGH_CONVICTION", "GUARDED_CONVICTION", "FRAGILE_CONVICTION", "BROKEN_CONVICTION"]
    baseline_conviction_score: float = Field(ge=0.0, le=1.0)
    baseline_fragility_score: float = Field(ge=0.0, le=1.0)
    summary_line: str
    highest_priority_campaign_id: str | None = None
    items: List[OracleStrategicCampaignItem] = Field(default_factory=list)
    operator_actions: List[str] = Field(default_factory=list)

    model_config = {"extra": "forbid"}


class OracleStrategicCampaignExecutionUpdateItem(BaseModel):
    campaign_id: str
    execution_state: Literal["QUEUED", "ACTIVE", "BLOCKED", "DRIFTING", "COMPLETED", "INVALIDATED"]
    completed_step_ids: List[str] = Field(default_factory=list)
    blocked_step_ids: List[str] = Field(default_factory=list)
    note: str = ""
    evidence: List[str] = Field(default_factory=list)
    recommended_next_step: str = ""

    model_config = {"extra": "forbid"}


class OracleStrategicCampaignExecutionInput(BaseModel):
    schema_version: Literal["oracle_strategic_campaign_execution_input/v1"] = "oracle_strategic_campaign_execution_input/v1"
    generated_at_utc: datetime
    universe_label: str
    items: List[OracleStrategicCampaignExecutionUpdateItem] = Field(default_factory=list)

    model_config = {"extra": "forbid"}


class OracleStrategicCampaignExecutionItem(BaseModel):
    campaign_id: str
    objective_kind: Literal["CONVICTION_REPAIR", "DOCTRINE_STABILIZATION", "COHORT_RECOVERY", "THESIS_VALIDATION", "OPPORTUNITY_EXPANSION"]
    execution_state: Literal["QUEUED", "ACTIVE", "BLOCKED", "DRIFTING", "COMPLETED", "INVALIDATED"]
    exact_evidence_support_score: float = Field(default=0.0, ge=0.0, le=1.0)
    exact_feedback_confirmation_count: int = Field(default=0, ge=0)
    exact_feedback_relief_count: int = Field(default=0, ge=0)
    exact_cadence_signal_classification: Literal["EXACT_CONFIRMED_PRESSURE", "EXACT_RELIEF_PRESSURE", "AMBIENT_DRIFT"] = "AMBIENT_DRIFT"
    priority_score: float = Field(ge=0.0, le=1.0)
    progress_score: float = Field(ge=0.0, le=1.0)
    blocker_score: float = Field(ge=0.0, le=1.0)
    drift_score: float = Field(ge=0.0, le=1.0)
    invalidation_score: float = Field(ge=0.0, le=1.0)
    operator_friction_score: float = Field(default=0.0, ge=0.0, le=1.0)
    title: str
    summary_line: str
    completed_step_ids: List[str] = Field(default_factory=list)
    pending_step_ids: List[str] = Field(default_factory=list)
    blocked_step_ids: List[str] = Field(default_factory=list)
    source_priority_ids: List[str] = Field(default_factory=list)
    source_execution_ids: List[str] = Field(default_factory=list)
    related_strategy_ids: List[str] = Field(default_factory=list)
    evidence: List[str] = Field(default_factory=list)
    recommended_next_step: str

    model_config = {"extra": "forbid"}


class OracleStrategicCampaignExecutionReport(BaseModel):
    schema_version: Literal["oracle_strategic_campaign_execution_report/v1"] = "oracle_strategic_campaign_execution_report/v1"
    generated_at_utc: datetime
    universe_label: str
    oracle_run_id: str
    input_timestamp_utc: datetime
    dominant_regime: AdvisoryRegime
    strategic_posture: OracleStrategicPosture
    baseline_conviction_state: Literal["HIGH_CONVICTION", "GUARDED_CONVICTION", "FRAGILE_CONVICTION", "BROKEN_CONVICTION"]
    baseline_conviction_score: float = Field(ge=0.0, le=1.0)
    baseline_fragility_score: float = Field(ge=0.0, le=1.0)
    history_integrity_status: Literal["CURRENT_ONLY", "SEALED_HISTORY", "MIXED_HISTORY"] = "CURRENT_ONLY"
    sealed_history_observation_count: int = Field(default=0, ge=0)
    unsealed_history_excluded_count: int = Field(default=0, ge=0)
    preferred_strategic_backing_source: str | None = None
    preferred_strategic_backing_classification: Literal["SEALED_STRATEGIC_STACK_BACKED", "DOCTRINE_ONLY_LADDER_BACKED", "NO_STRATEGIC_STACK_HISTORY"] | None = None
    exact_evidence_support_score: float = Field(default=0.0, ge=0.0, le=1.0)
    exact_feedback_confirmation_count: int = Field(default=0, ge=0)
    exact_feedback_relief_count: int = Field(default=0, ge=0)
    exact_cadence_signal_classification: Literal["EXACT_CONFIRMED_PRESSURE", "EXACT_RELIEF_PRESSURE", "AMBIENT_DRIFT"] = "AMBIENT_DRIFT"
    integrity_operator_friction_score: float = Field(default=0.0, ge=0.0, le=1.0)
    summary_line: str
    active_campaign_ids: List[str] = Field(default_factory=list)
    blocked_campaign_ids: List[str] = Field(default_factory=list)
    drifting_campaign_ids: List[str] = Field(default_factory=list)
    completed_campaign_ids: List[str] = Field(default_factory=list)
    invalidated_campaign_ids: List[str] = Field(default_factory=list)
    items: List[OracleStrategicCampaignExecutionItem] = Field(default_factory=list)
    operator_actions: List[str] = Field(default_factory=list)

    model_config = {"extra": "forbid"}


class OracleStrategicBriefingSection(BaseModel):
    section_id: Literal["what_changed", "strategic_posture", "strategic_narrative", "belief_drift_timeline", "opportunity_queue", "caution_queue", "doctrine_pressure", "doctrine_adaptation", "research_priorities", "investigation_outcomes", "strategy_health", "strategy_cohorts", "thesis_evolution", "thesis_graph", "strategic_tensions", "contradiction_resolution", "intervention_simulation", "strategic_campaigns", "campaign_execution", "scenario_lab"]
    title: str
    status: str
    summary_line: str
    preferred_strategic_backing_source: str | None = None
    exact_feedback_confirmation_count: int = Field(default=0, ge=0)
    exact_feedback_relief_count: int = Field(default=0, ge=0)
    exact_cadence_signal_classification: Literal["EXACT_CONFIRMED_PRESSURE", "EXACT_RELIEF_PRESSURE", "AMBIENT_DRIFT"] = "AMBIENT_DRIFT"
    preferred_strategic_backing_classification: Literal["SEALED_STRATEGIC_STACK_BACKED", "DOCTRINE_ONLY_LADDER_BACKED", "NO_STRATEGIC_STACK_HISTORY"] | None = None
    preferred_strategic_artifact_evidence_manifest: str | None = None
    preferred_strategic_artifact_evidence_kind: Literal["doctrine_adaptation", "research_priorities", "strategic_intervention", "strategic_campaign", "strategic_campaign_execution"] | None = None
    preferred_strategic_artifact_evidence_status: OracleEvidenceStatus | None = None
    facts: List[str] = Field(default_factory=list)
    operator_actions: List[str] = Field(default_factory=list)
    provenance_refs: List[str] = Field(default_factory=list)

    model_config = {"extra": "forbid"}


class OracleStrategicBriefingReport(BaseModel):
    schema_version: Literal["oracle_strategic_briefing_report/v1"] = "oracle_strategic_briefing_report/v1"
    generated_at_utc: datetime
    universe_label: str
    oracle_run_id: str
    input_timestamp_utc: datetime
    dominant_regime: AdvisoryRegime
    strategic_posture: OracleStrategicPosture
    transition_classification: OracleStrategicTransitionClassification | None = None
    preferred_strategic_backing_source: str | None = None
    exact_feedback_confirmation_count: int = Field(default=0, ge=0)
    exact_feedback_relief_count: int = Field(default=0, ge=0)
    exact_cadence_signal_classification: Literal["EXACT_CONFIRMED_PRESSURE", "EXACT_RELIEF_PRESSURE", "AMBIENT_DRIFT"] = "AMBIENT_DRIFT"
    preferred_strategic_backing_classification: Literal["SEALED_STRATEGIC_STACK_BACKED", "DOCTRINE_ONLY_LADDER_BACKED", "NO_STRATEGIC_STACK_HISTORY"] | None = None
    summary_line: str
    sections: List[OracleStrategicBriefingSection] = Field(default_factory=list)
    operator_actions: List[str] = Field(default_factory=list)

    model_config = {"extra": "forbid"}


class OracleStrategicStackEvidenceManifest(BaseModel):
    schema_version: Literal["oracle_strategic_stack_evidence_manifest/v1"] = "oracle_strategic_stack_evidence_manifest/v1"
    generated_at_utc: datetime
    stack_id: str
    oracle_run_id: str
    universe_label: str
    input_timestamp_utc: datetime
    execution_authority: Literal["ADVISORY_ONLY"] = "ADVISORY_ONLY"
    dominant_regime: AdvisoryRegime
    strategic_posture: OracleStrategicPosture
    briefing_schema_version: str
    integrity_status: Literal["VERIFIED", "INCOMPLETE"]
    subjects: List[EvidenceResourceDescriptor] = Field(default_factory=list)
    missing_artifact_paths: List[str] = Field(default_factory=list)
    summary_line: str

    model_config = {"extra": "forbid"}




class OracleStrategicArtifactEvidenceManifest(BaseModel):
    schema_version: Literal["oracle_strategic_artifact_evidence_manifest/v1"] = "oracle_strategic_artifact_evidence_manifest/v1"
    generated_at_utc: datetime
    artifact_kind: Literal["doctrine_adaptation", "research_priorities", "strategic_intervention", "strategic_campaign", "strategic_campaign_execution"]
    report_schema_version: str
    oracle_run_id: str
    universe_label: str
    input_timestamp_utc: datetime
    execution_authority: Literal["ADVISORY_ONLY"] = "ADVISORY_ONLY"
    preferred_strategic_backing_source: str | None = None
    preferred_strategic_backing_classification: Literal["SEALED_STRATEGIC_STACK_BACKED", "DOCTRINE_ONLY_LADDER_BACKED", "NO_STRATEGIC_STACK_HISTORY"] | None = None
    integrity_status: Literal["VERIFIED", "INCOMPLETE"]
    subjects: List[EvidenceResourceDescriptor] = Field(default_factory=list)
    missing_artifact_paths: List[str] = Field(default_factory=list)
    summary_line: str

    model_config = {"extra": "forbid"}


class OracleStrategicArtifactEvidenceVerification(BaseModel):
    verified_at_utc: datetime
    manifest_path: str
    status: OracleEvidenceStatus = "UNVERIFIED"
    artifact_digests_verified: bool = False
    signature_verified: bool = False
    verified_subject_count: int = 0
    digest_mismatches: List[str] = Field(default_factory=list)
    missing_artifact_paths: List[str] = Field(default_factory=list)
    notes: List[str] = Field(default_factory=list)

    model_config = {"extra": "forbid"}

class OracleStrategicStackEvidenceVerification(BaseModel):
    verified_at_utc: datetime
    manifest_path: str
    status: OracleEvidenceStatus = "UNVERIFIED"
    artifact_digests_verified: bool = False
    signature_verified: bool = False
    verified_subject_count: int = 0
    digest_mismatches: List[str] = Field(default_factory=list)
    missing_artifact_paths: List[str] = Field(default_factory=list)
    notes: List[str] = Field(default_factory=list)

    model_config = {"extra": "forbid"}


class OracleScenarioShock(BaseModel):
    scenario_id: str
    title: str
    scenario_kind: OracleScenarioKind
    summary: str
    inflation_hawkishness_shift: float = 0.0
    geopolitical_risk_shift: float = Field(default=0.0, ge=-1.0, le=1.0)
    narrative_contradiction_delta: int = 0
    doctrine_conflict_shift: float = Field(default=0.0, ge=-1.0, le=1.0)
    vpin_shift: float = Field(default=0.0, ge=-1.0, le=1.0)
    order_flow_shift: float = Field(default=0.0, ge=-1.0, le=1.0)
    spread_variance_shift: float = -3.0
    liquidity_thinning_shift: float = Field(default=0.0, ge=-1.0, le=1.0)
    yield_curve_slope_shift_bps: float = 0.0
    high_yield_credit_spread_shift_bps: float = 0.0
    equity_bond_correlation_shift: float = Field(default=0.0, ge=-2.0, le=2.0)
    cross_asset_stress_shift: float = Field(default=0.0, ge=-1.0, le=1.0)
    realized_volatility_zscore_shift: float = -5.0
    realized_live_sharpe_shift: float = -5.0
    recent_win_rate_shift: float = Field(default=0.0, ge=-1.0, le=1.0)
    drawdown_fraction_shift: float = Field(default=0.0, ge=-1.0, le=1.0)

    model_config = {"extra": "forbid"}


class OracleScenarioPlanInput(BaseModel):
    schema_version: Literal["oracle_scenario_plan_input/v1"] = "oracle_scenario_plan_input/v1"
    generated_for_utc: datetime
    universe_label: str
    scenarios: List[OracleScenarioShock] = Field(default_factory=list)

    model_config = {"extra": "forbid"}


class OracleScenarioOutcome(BaseModel):
    scenario_id: str
    title: str
    scenario_kind: OracleScenarioKind
    exact_evidence_support_score: float = Field(default=0.0, ge=0.0, le=1.0)
    resulting_dominant_regime: AdvisoryRegime
    resulting_strategic_posture: OracleStrategicPosture
    transition_classification: OracleStrategicTransitionClassification
    doctrine_stress_delta: float
    caution_delta: float
    opportunity_delta: float
    average_posterior_delta: float
    leading_queue_item_title: str | None = None
    leading_queue_kind: OracleStrategicQueueKind | None = None
    summary_line: str
    operator_action: str
    evidence: List[str] = Field(default_factory=list)

    model_config = {"extra": "forbid"}


class OracleScenarioLabReport(BaseModel):
    schema_version: Literal["oracle_scenario_lab_report/v1"] = "oracle_scenario_lab_report/v1"
    generated_at_utc: datetime
    universe_label: str
    oracle_run_id: str
    input_timestamp_utc: datetime
    baseline_dominant_regime: AdvisoryRegime
    baseline_strategic_posture: OracleStrategicPosture
    preferred_strategic_backing_source: str | None = None
    preferred_strategic_backing_classification: Literal["SEALED_STRATEGIC_STACK_BACKED", "DOCTRINE_ONLY_LADDER_BACKED", "NO_STRATEGIC_STACK_HISTORY"] | None = None
    exact_evidence_support_score: float = Field(default=0.0, ge=0.0, le=1.0)
    baseline_average_posterior_edge_confidence: float = Field(ge=0.0, le=1.0)
    summary_line: str
    scenarios: List[OracleScenarioOutcome] = Field(default_factory=list)
    highest_downside_scenario_id: str | None = None
    highest_upside_scenario_id: str | None = None
    operator_actions: List[str] = Field(default_factory=list)

    model_config = {"extra": "forbid"}


class OracleStrategyCohortItem(BaseModel):
    strategy_id: str
    strategy_type: str
    cohort_bucket: OracleStrategyCohortBucket
    exact_evidence_support_score: float = Field(default=0.0, ge=0.0, le=1.0)
    cohort_rank_score: float = Field(ge=0.0, le=1.0)
    resilience_score: float = Field(ge=0.0, le=1.0)
    current_posterior_edge_confidence: float = Field(ge=0.0, le=1.0)
    scenario_average_posterior: float = Field(ge=0.0, le=1.0)
    scenario_downside_floor: float = Field(ge=0.0, le=1.0)
    transition_sensitivity_score: float = Field(ge=0.0, le=1.0)
    thesis_pressure_score: float = Field(ge=0.0, le=1.0)
    queue_pressure_score: float = Field(ge=0.0, le=1.0)
    summary_line: str
    evidence: List[str] = Field(default_factory=list)
    operator_action: str

    model_config = {"extra": "forbid"}


class OracleStrategyCohortReport(BaseModel):
    schema_version: Literal["oracle_strategy_cohort_report/v1"] = "oracle_strategy_cohort_report/v1"
    generated_at_utc: datetime
    universe_label: str
    oracle_run_id: str
    input_timestamp_utc: datetime
    dominant_regime: AdvisoryRegime
    strategic_posture: OracleStrategicPosture
    preferred_strategic_backing_source: str | None = None
    preferred_strategic_backing_classification: Literal["SEALED_STRATEGIC_STACK_BACKED", "DOCTRINE_ONLY_LADDER_BACKED", "NO_STRATEGIC_STACK_HISTORY"] | None = None
    exact_evidence_support_score: float = Field(default=0.0, ge=0.0, le=1.0)
    transition_classification: OracleStrategicTransitionClassification | None = None
    summary_line: str
    lead_strategy_ids: List[str] = Field(default_factory=list)
    pressured_strategy_ids: List[str] = Field(default_factory=list)
    items: List[OracleStrategyCohortItem] = Field(default_factory=list)
    operator_actions: List[str] = Field(default_factory=list)

    model_config = {"extra": "forbid"}
