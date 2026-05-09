from __future__ import annotations

from datetime import datetime
from typing import List, Literal

from pydantic import BaseModel, Field

from strategy_validator.contracts.oracle_types import AdvisoryRegime
from strategy_validator.contracts.oracle_strategic_memory_common import OracleStrategicPosture


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


__all__ = ['OracleContradictionResolutionItem', 'OracleContradictionResolutionReport', 'OracleStrategicInterventionItem', 'OracleStrategicInterventionReport']
