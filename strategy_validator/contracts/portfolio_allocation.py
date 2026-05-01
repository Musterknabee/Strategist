"""Portfolio allocation simulator contracts (research/paper only; no orders)."""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


class AllocationMethod(str, Enum):
    equal_weight = "equal_weight"
    inverse_volatility = "inverse_volatility"
    risk_budget = "risk_budget"
    capped_score_weight = "capped_score_weight"


class AllocationGateStatus(str, Enum):
    ALLOCATABLE = "ALLOCATABLE"
    WARNING = "WARNING"
    BLOCKED = "BLOCKED"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class StrategyAllocation(BaseModel):
    strategy_id: str
    weight: float = Field(ge=0.0, le=1.0)
    score: float | None = None
    volatility: float | None = None
    excluded: bool = False
    exclusion_reason: str | None = None

    model_config = {"extra": "forbid"}


class PortfolioRiskSummary(BaseModel):
    expected_volatility_like: float | None = None
    max_drawdown_like: float | None = None
    concentration_hhi: float | None = None
    cluster_warnings: list[str] = Field(default_factory=list)

    model_config = {"extra": "forbid"}


class PortfolioAllocationRequest(BaseModel):
    batch_run_id: str
    capital: float = Field(gt=0)
    method: AllocationMethod = AllocationMethod.equal_weight
    max_weight: float = Field(default=0.35, gt=0.0, le=1.0)
    min_weight: float = Field(default=0.0, ge=0.0, le=1.0)
    max_correlation_cluster_exposure: float = Field(default=0.55, gt=0.0, le=1.0)
    exclude_blocked: bool = True
    exclude_synthetic: bool = True
    duplicative_strategy_ids: list[str] = Field(default_factory=list)

    model_config = {"extra": "forbid"}


class PortfolioAllocationResult(BaseModel):
    schema_version: Literal["portfolio_allocation_result/v1"] = "portfolio_allocation_result/v1"
    generated_at_utc: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    request: PortfolioAllocationRequest
    allocations: list[StrategyAllocation] = Field(default_factory=list)
    excluded: list[dict[str, Any]] = Field(default_factory=list)
    risk_summary: PortfolioRiskSummary = Field(default_factory=PortfolioRiskSummary)
    allocation_gate_status: AllocationGateStatus = AllocationGateStatus.NOT_APPLICABLE
    warnings: list[str] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    evidence_digest: str = ""

    model_config = {"extra": "forbid"}

    @field_validator("generated_at_utc")
    @classmethod
    def _tz(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("generated_at_utc must be timezone-aware")
        return v


__all__ = [
    "AllocationGateStatus",
    "AllocationMethod",
    "PortfolioAllocationRequest",
    "PortfolioAllocationResult",
    "PortfolioRiskSummary",
    "StrategyAllocation",
]
