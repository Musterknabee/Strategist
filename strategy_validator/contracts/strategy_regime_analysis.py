"""Simple deterministic regime analysis contracts (research)."""
from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


class MarketRegime(str, Enum):
    UP_TREND = "UP_TREND"
    DOWN_TREND = "DOWN_TREND"
    SIDEWAYS = "SIDEWAYS"
    HIGH_VOLATILITY = "HIGH_VOLATILITY"
    LOW_VOLATILITY = "LOW_VOLATILITY"


class RegimeStat(BaseModel):
    regime: str
    bar_count: int
    mean_strategy_log_return: float
    cumulative_strategy_return: float

    model_config = {"extra": "forbid"}


class RegimeAnalysisResult(BaseModel):
    schema_version: Literal["strategy_regime_analysis_result/v1"] = "strategy_regime_analysis_result/v1"
    strategy_id: str
    batch_id: str
    run_id: str
    model_label: str = "DETERMINISTIC_REGIME_MODEL"
    regime_count: int = 0
    regimes: list[RegimeStat] = Field(default_factory=list)
    best_regime: str = ""
    worst_regime: str = ""
    failed_regime_count: int = 0
    gate_status: Literal["PROVEN", "WARNING", "BLOCKED", "NOT_APPLICABLE"] = "NOT_APPLICABLE"
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    regime_analysis_evidence_sha256: str = ""

    model_config = {"extra": "forbid"}


__all__ = ["MarketRegime", "RegimeAnalysisResult", "RegimeStat"]
