from __future__ import annotations

from datetime import datetime
from typing import List, Literal

from pydantic import BaseModel, Field

from strategy_validator.contracts.oracle_types import AdvisoryRegime


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

OracleThesisCurrentState = Literal["SUPPORTIVE", "CAUTIONARY", "AT_RISK", "BROKEN", "NEUTRAL"]
OracleThesisEvolutionState = Literal["EMERGING", "STRENGTHENING", "WEAKENING", "REVERSING", "STABLE"]
OracleResearchPriorityKind = Literal[
    "REGIME_INVESTIGATION",
    "STRATEGY_VALIDATION",
    "DOCTRINE_REVIEW",
    "THESIS_REVIEW",
    "SCENARIO_PROBE",
]


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
