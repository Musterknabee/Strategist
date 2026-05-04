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
