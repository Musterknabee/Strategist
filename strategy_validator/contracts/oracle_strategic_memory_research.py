from __future__ import annotations

from datetime import datetime
from typing import List, Literal

from pydantic import BaseModel, Field

from strategy_validator.contracts.oracle_types import AdvisoryRegime
from strategy_validator.contracts.oracle_strategic_memory_common import (
    OracleResearchPriorityKind,
    OracleStrategicPosture,
    OracleStrategicTransitionClassification,
)


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


__all__ = ['OracleResearchPriorityItem', 'OracleResearchPriorityReport', 'OracleInvestigationOutcomeInputItem', 'OracleInvestigationOutcomeInput', 'OracleResearchExecutionMemoryItem', 'OracleResearchExecutionMemoryReport']
