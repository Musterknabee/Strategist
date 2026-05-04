"""CPCV-inspired robustness contracts (research; bounded heuristic)."""
from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator

from strategy_validator.contracts.strategy_robustness import RobustnessGateStatus

CPCV_ROBUSTNESS_MODEL_LABEL = "CPCV_PURGED_COMBINATORIAL_LOCAL_BAR"


class CPCVConfig(BaseModel):
    n_groups: int = Field(default=4, ge=2, le=16)
    n_test_groups: int = Field(default=2, ge=1, le=8)
    purge_bars: int = Field(default=3, ge=0, le=500)
    embargo_bars: int = Field(default=3, ge=0, le=500)
    min_train_bars: int = Field(default=30, ge=5)
    min_test_bars: int = Field(default=10, ge=2)
    max_paths: int = Field(default=24, ge=1, le=64)
    max_pbo_like_score: float = Field(default=0.70, ge=0.0, le=1.0)
    min_dsr_like_score: float = Field(default=0.10, ge=-1.0, le=1.0)
    min_positive_path_ratio: float = Field(default=0.45, ge=0.0, le=1.0)
    max_worst_path_return: float = Field(default=-0.12, le=0.0)

    model_config = {"extra": "forbid"}


class CPCVSplit(BaseModel):
    path_index: int
    train_indices: tuple[int, ...]
    test_indices: tuple[int, ...]

    model_config = {"extra": "forbid"}


class CPCVPathResult(BaseModel):
    path_index: int
    train_start_utc: datetime
    train_end_utc: datetime
    test_start_utc: datetime
    test_end_utc: datetime
    train_bar_count: int
    test_bar_count: int
    train_return: float
    test_return: float
    train_sharpe_like: float
    test_sharpe_like: float
    max_drawdown_test: float

    model_config = {"extra": "forbid"}

    @field_validator(
        "train_start_utc",
        "train_end_utc",
        "test_start_utc",
        "test_end_utc",
    )
    @classmethod
    def _tz(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("datetime must be timezone-aware")
        return v


class CPCVRobustnessResult(BaseModel):
    schema_version: Literal["strategy_cpcv_result/v1"] = "strategy_cpcv_result/v1"
    strategy_id: str
    batch_id: str
    run_id: str
    model_label: str = CPCV_ROBUSTNESS_MODEL_LABEL
    sample_count: int = 0
    path_count: int = 0
    paths: list[CPCVPathResult] = Field(default_factory=list)
    median_test_return: float = 0.0
    median_test_sharpe_like: float = 0.0
    worst_path_return: float = 0.0
    positive_path_ratio: float = 0.0
    pbo_like_score: float = 0.0
    dsr_like_score: float = 0.0
    trials_penalty: float = 0.0
    gate_status: RobustnessGateStatus = RobustnessGateStatus.BLOCKED
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    cpcv_evidence_sha256: str = ""

    model_config = {"extra": "forbid"}


__all__ = [
    "CPCVConfig",
    "CPCVPathResult",
    "CPCVRobustnessResult",
    "CPCVSplit",
    "CPCV_ROBUSTNESS_MODEL_LABEL",
]
