"""Strategy thesis and falsification manifest contracts."""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator, model_validator


class ThesisSupportStatus(str, Enum):
    SUPPORTED = "SUPPORTED"
    WEAKLY_SUPPORTED = "WEAKLY_SUPPORTED"
    INCONCLUSIVE = "INCONCLUSIVE"
    FALSIFIED = "FALSIFIED"
    NOT_EVALUATED = "NOT_EVALUATED"


class ExpectedEdge(BaseModel):
    description: str = Field(min_length=1)
    expected_metric: str = "total_return"
    expected_direction: Literal["positive", "negative", "neutral"] = "positive"
    minimum_evidence_days: int = Field(default=30, ge=1)

    model_config = {"extra": "forbid"}


class ExpectedFailureMode(BaseModel):
    regime: str = Field(min_length=1)
    description: str = ""
    expected_symptom: str = ""

    model_config = {"extra": "forbid"}


class FalsificationCriterion(BaseModel):
    criterion_id: str = Field(min_length=1)
    metric: str = Field(min_length=1)
    operator: Literal["lt", "lte", "gt", "gte", "eq"]
    threshold: float | str | bool
    description: str = ""
    hard_kill: bool = True

    model_config = {"extra": "forbid"}


class ThesisEvidenceRequirement(BaseModel):
    requirement_id: str = Field(min_length=1)
    evidence_kind: str = Field(min_length=1)
    required: bool = True
    description: str = ""

    model_config = {"extra": "forbid"}


class StrategyThesis(BaseModel):
    schema_version: Literal["strategy_thesis/v1"] = "strategy_thesis/v1"
    strategy_id: str = Field(min_length=1)
    thesis_id: str = Field(min_length=1)
    hypothesis: str = Field(min_length=1)
    economic_rationale: str = Field(min_length=1)
    market_inefficiency: str = Field(min_length=1)
    expected_regimes: list[str] = Field(default_factory=list)
    expected_failure_regimes: list[ExpectedFailureMode] = Field(default_factory=list)
    expected_edge: ExpectedEdge
    required_evidence: list[ThesisEvidenceRequirement] = Field(default_factory=list)
    falsification_criteria: list[FalsificationCriterion] = Field(default_factory=list)
    author: str = "operator"
    created_at_utc: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    thesis_sha256: str = ""
    disclaimer: str = "Research thesis only; no live trading or profitability guarantee."

    model_config = {"extra": "forbid"}

    @field_validator("created_at_utc")
    @classmethod
    def _tz_created(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("created_at_utc must be timezone-aware")
        return v




class GeneratedStrategyThesisArtifact(BaseModel):
    strategy_id: str = Field(min_length=1)
    strategy_type: str | None = None
    thesis_id: str = Field(min_length=1)
    thesis_path: str = Field(min_length=1)
    thesis_sha256: str = Field(min_length=1)
    support_status: ThesisSupportStatus | None = None
    evaluation_path: str | None = None
    evaluation_sha256: str | None = None
    generated_from_status: str = Field(default="UNKNOWN")
    promotion_eligible: bool = False
    expected_primary_edge: str = "total_return"
    candidate_mutations: list[str] = Field(default_factory=list)
    operator_actions: list[str] = Field(default_factory=list)

    model_config = {"extra": "forbid"}


class StrategyThesisGenerationReport(BaseModel):
    schema_version: Literal["strategy_thesis_generation_report/v1"] = "strategy_thesis_generation_report/v1"
    batch_id: str = Field(min_length=1)
    run_id: str = Field(min_length=1)
    generated_at_utc: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    read_plane_only: bool = True
    no_live_trading: bool = True
    source_batch_summary_path: str = Field(min_length=1)
    generated_count: int = Field(ge=0)
    evaluated_count: int = Field(default=0, ge=0)
    generated_theses: list[GeneratedStrategyThesisArtifact] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    operator_actions: list[str] = Field(default_factory=list)
    report_sha256: str = ""
    disclaimer: str = "Oracle-generated theses are research hypotheses only; they are not live trading approval or profitability guarantees."

    model_config = {"extra": "forbid"}

    @field_validator("generated_at_utc")
    @classmethod
    def _tz_generated(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("generated_at_utc must be timezone-aware")
        return v


class ThesisEvaluation(BaseModel):
    schema_version: Literal["strategy_thesis_evaluation/v1"] = "strategy_thesis_evaluation/v1"
    thesis_id: str
    strategy_id: str
    evaluated_at_utc: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    support_status: ThesisSupportStatus = ThesisSupportStatus.NOT_EVALUATED
    evidence_refs: list[dict[str, Any]] = Field(default_factory=list)
    contradictions: list[str] = Field(default_factory=list)
    missing_evidence: list[str] = Field(default_factory=list)
    falsified_criteria: list[FalsificationCriterion] = Field(default_factory=list)
    triggered_kill_criteria: list[str] = Field(default_factory=list)
    evidence_summary: dict[str, Any] = Field(default_factory=dict)
    evaluation_sha256: str = ""
    disclaimer: str = "Thesis evaluation is paper/research evidence only; it is not a live trading approval."

    model_config = {"extra": "forbid"}

    @field_validator("evaluated_at_utc")
    @classmethod
    def _tz_eval(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("evaluated_at_utc must be timezone-aware")
        return v


__all__ = [
    "ExpectedEdge",
    "ExpectedFailureMode",
    "FalsificationCriterion",
    "GeneratedStrategyThesisArtifact",
    "StrategyThesis",
    "StrategyThesisGenerationReport",
    "ThesisEvaluation",
    "ThesisEvidenceRequirement",
    "ThesisSupportStatus",
]
