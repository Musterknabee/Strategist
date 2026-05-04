"""Execution realism evidence contracts (research/paper; not live execution)."""
from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field, field_validator

MODEL_LABEL = "CONSERVATIVE_LOCAL_BAR_MODEL"


class ExecutionRealismGateStatus(str, Enum):
    PROVEN = "PROVEN"
    WARNING = "WARNING"
    BLOCKED = "BLOCKED"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class ExecutionRealismAssumptions(BaseModel):
    """Declared on StrategyCandidateSpec (parsed from execution_assumptions keys)."""

    starting_capital: float = Field(gt=0)
    max_participation_rate: float = Field(gt=0, le=1)
    fee_bps: float = Field(ge=0)
    slippage_bps: float = Field(ge=0)
    min_average_daily_volume: float = Field(ge=0, description="Minimum acceptable mean daily dollar volume from bars.")
    allow_short: bool = False
    borrow_required: bool = False
    borrow_liquidity_evidence_ack: bool = Field(
        default=False,
        description="Operator attestation that borrow/short liquidity was reviewed (research only).",
    )

    model_config = {"extra": "forbid"}

class LiquidityCheckResult(BaseModel):
    status: Literal["PASS", "WARN", "BLOCK"]
    average_daily_dollar_volume: float
    threshold: float
    detail: str = ""

    model_config = {"extra": "forbid"}


class SlippageModelResult(BaseModel):
    model_label: str = MODEL_LABEL
    slippage_bps_assumed: float
    implied_daily_drag_vs_capital: float = Field(
        default=0.0,
        description="Rough fraction of starting capital lost to slippage per unit turnover day.",
    )

    model_config = {"extra": "forbid"}


class FeeModelResult(BaseModel):
    model_label: str = MODEL_LABEL
    fee_bps_assumed: float
    implied_daily_drag_vs_capital: float = 0.0

    model_config = {"extra": "forbid"}


class CapacityEstimate(BaseModel):
    capacity_notional: float = Field(description="Headline notional capacity at max participation vs avg dollar volume.")
    headroom_vs_estimate: float = 0.0

    model_config = {"extra": "forbid"}


class ExecutionRealismResult(BaseModel):
    schema_version: Literal["strategy_execution_realism_result/v1"] = "strategy_execution_realism_result/v1"
    strategy_id: str
    batch_id: str
    run_id: str
    model_label: str = MODEL_LABEL
    assumptions: ExecutionRealismAssumptions | None = None
    average_daily_volume: float | None = None
    average_daily_dollar_volume: float | None = None
    estimated_participation_rate: float | None = None
    turnover_estimate: float | None = None
    estimated_slippage_bps: float | None = None
    estimated_fees_bps: float | None = None
    slippage_drag_daily_usd: float | None = None
    fee_drag_daily_usd: float | None = None
    liquidity: LiquidityCheckResult | None = None
    slippage_model: SlippageModelResult | None = None
    fee_model: FeeModelResult | None = None
    capacity: CapacityEstimate | None = None
    liquidity_status: str = "UNKNOWN"
    borrow_status: str | None = None
    market_data_freshness_status: str = "UNKNOWN"
    gate_status: ExecutionRealismGateStatus = ExecutionRealismGateStatus.BLOCKED
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    evidence_digest: str = ""

    model_config = {"extra": "forbid"}


__all__ = [
    "MODEL_LABEL",
    "CapacityEstimate",
    "ExecutionRealismAssumptions",
    "ExecutionRealismGateStatus",
    "ExecutionRealismResult",
    "FeeModelResult",
    "LiquidityCheckResult",
    "SlippageModelResult",
]
