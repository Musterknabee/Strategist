"""Local bar data quality gate contracts (research)."""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


class DataQualityGateStatus(str, Enum):
    PROVEN = "PROVEN"
    WARNING = "WARNING"
    BLOCKED = "BLOCKED"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class DataQualityIssue(BaseModel):
    code: str
    severity: Literal["BLOCKER", "WARNING"]
    detail: str

    model_config = {"extra": "forbid"}


class DataQualityResult(BaseModel):
    schema_version: Literal["strategy_data_quality_result/v1"] = "strategy_data_quality_result/v1"
    strategy_id: str
    batch_id: str
    run_id: str
    model_label: str = "LOCAL_BAR_DATA_QUALITY_MODEL"
    row_count: int = 0
    symbol_count: int = 0
    timestamp_min_utc: datetime | None = None
    timestamp_max_utc: datetime | None = None
    missing_close_count: int = 0
    missing_volume_count: int = 0
    duplicate_timestamp_count: int = 0
    future_row_count: int = 0
    bad_ohlc_count: int = 0
    zero_or_negative_price_count: int = 0
    zero_volume_count: int = 0
    outlier_return_count: int = 0
    timezone_status: str = "UTC_NORMALIZED"
    gate_status: DataQualityGateStatus = DataQualityGateStatus.BLOCKED
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    issues: list[DataQualityIssue] = Field(default_factory=list)
    data_quality_evidence_sha256: str = ""

    model_config = {"extra": "forbid"}


__all__ = [
    "DataQualityGateStatus",
    "DataQualityIssue",
    "DataQualityResult",
]
