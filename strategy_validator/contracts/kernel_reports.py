from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field


class KernelDecisionReport(BaseModel):
    """Decision-kernel facing summary that preserves adjudication details without operator routing concerns."""

    report_id: str = Field(min_length=1)
    experiment_id: str = Field(min_length=1)
    strategy_id: str = Field(min_length=1)
    generated_at_utc: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    promotion_state: str = Field(min_length=1)
    gate_failures: list[str] = Field(default_factory=list)
    gate_results: list[dict[str, Any]] = Field(default_factory=list)
    benchmark_summary: dict[str, Any] = Field(default_factory=dict)
    execution_realism_summary: dict[str, Any] = Field(default_factory=dict)
    summary_notes: list[str] = Field(default_factory=list)

    model_config = {"extra": "forbid"}
