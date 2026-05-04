"""Walk-forward robustness evidence contracts (research; not full CPCV)."""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field

ROBUSTNESS_MODEL_LABEL = "WALK_FORWARD_LOCAL_BAR_MODEL"
DSR_LIKE_MODEL_LABEL = "DSR_LIKE_HEURISTIC"
PBO_LIKE_MODEL_LABEL = "PBO_LIKE_HEURISTIC"


class RobustnessGateStatus(str, Enum):
    PROVEN = "PROVEN"
    WARNING = "WARNING"
    BLOCKED = "BLOCKED"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class RobustnessAssumptions(BaseModel):
    fold_count: int = Field(default=4, ge=2)
    min_train_bars: int = Field(default=20, ge=1)
    min_test_bars: int = Field(default=5, ge=1)
    min_positive_fold_ratio: float = Field(default=0.5, ge=0.0, le=1.0)
    max_worst_fold_return: float = Field(default=-0.10, le=0.0)
    max_pbo_like_score: float = Field(default=0.70, ge=0.0, le=1.0)
    min_dsr_like_score: float = Field(default=0.10, ge=-1.0, le=1.0)

    model_config = {"extra": "forbid"}


class WalkForwardFoldResult(BaseModel):
    fold_index: int
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
    max_drawdown: float
    positive_test_return: bool

    model_config = {"extra": "forbid"}


class RobustnessResult(BaseModel):
    schema_version: Literal["strategy_robustness_result/v1"] = "strategy_robustness_result/v1"
    strategy_id: str
    batch_id: str
    run_id: str
    model_label: str = ROBUSTNESS_MODEL_LABEL
    dsr_like_model_label: str = DSR_LIKE_MODEL_LABEL
    pbo_like_model_label: str = PBO_LIKE_MODEL_LABEL
    sample_count: int = 0
    fold_count: int = 0
    folds: list[WalkForwardFoldResult] = Field(default_factory=list)
    median_test_return: float = 0.0
    median_test_sharpe_like: float = 0.0
    worst_fold_return: float = 0.0
    positive_fold_ratio: float = 0.0
    pbo_like_score: float = 0.0
    dsr_like_score: float = 0.0
    gate_status: RobustnessGateStatus = RobustnessGateStatus.BLOCKED
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    robustness_evidence_sha256: str = ""

    model_config = {"extra": "forbid"}


_ROBUSTNESS_SPEC_KEYS = frozenset(RobustnessAssumptions.model_fields.keys())

__all__ = [
    "DSR_LIKE_MODEL_LABEL",
    "PBO_LIKE_MODEL_LABEL",
    "ROBUSTNESS_MODEL_LABEL",
    "RobustnessAssumptions",
    "RobustnessGateStatus",
    "RobustnessResult",
    "WalkForwardFoldResult",
    "_ROBUSTNESS_SPEC_KEYS",
]
