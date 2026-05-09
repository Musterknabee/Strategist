from __future__ import annotations

from datetime import datetime
from typing import List, Literal

from pydantic import BaseModel, Field

from strategy_validator.contracts.oracle_types import AdvisoryRegime
from strategy_validator.contracts.oracle_strategic_memory_common import (
    OracleStrategicPosture,
    OracleStrategicTransitionClassification,
)


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


__all__ = ['OracleDoctrineAdaptationItem', 'OracleDoctrineAdaptationReport']
