from __future__ import annotations

from datetime import datetime
from typing import List, Literal

from pydantic import BaseModel, Field

from strategy_validator.contracts.oracle_types import AdvisoryRegime
from strategy_validator.contracts.oracle_strategic_memory_common import (
    OracleStrategicPosture,
    OracleThesisCurrentState,
    OracleThesisEvolutionState,
)


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


__all__ = ['OracleThesisMemoryItem', 'OracleThesisMemoryReport']
