from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field

from strategy_validator.contracts.experiments import AdjudicationDecision, GateResult


class DecisionRecord(BaseModel):
    """Canonical institutional output for a completed adjudication."""

    record_id: str = Field(min_length=1)
    strategy_id: str = Field(min_length=1)
    experiment_id: str = Field(min_length=1)
    recorded_at_utc: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    decision_class: str = Field(min_length=1)
    promotion_state: str = Field(min_length=1)
    blocking_reasons: list[str] = Field(default_factory=list)
    summary_notes: list[str] = Field(default_factory=list)
    gate_results: list[GateResult] = Field(default_factory=list)
    evidence_references: list[str] = Field(default_factory=list)
    benchmark_summary: dict[str, Any] = Field(default_factory=dict)
    execution_realism_summary: dict[str, Any] = Field(default_factory=dict)
    source_decision: AdjudicationDecision | None = None

    model_config = {"extra": "forbid"}
