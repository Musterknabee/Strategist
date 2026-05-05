"""UI-facing backtest forensic review contracts."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, Field


class BacktestForensicStrategyRow(BaseModel):
    strategy_id: str
    status: str
    decision: str | None = None
    review_posture: str
    review_recommendation: str
    promotion_eligible: bool = False
    promotion_blocked_reasons: list[str] = Field(default_factory=list)
    risk_flags: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    blockers: list[str] = Field(default_factory=list)
    data_plane: str = "UNKNOWN"
    data_status: str = "UNKNOWN"
    pit_status: str = "UNKNOWN"
    pit_snapshot_status: str | None = None
    bars_row_count: int | None = None
    gate_matrix: dict[str, Any] = Field(default_factory=dict)
    metrics: dict[str, Any] = Field(default_factory=dict)
    robustness: dict[str, Any] = Field(default_factory=dict)
    execution_realism: dict[str, Any] = Field(default_factory=dict)
    artifacts: dict[str, Any] = Field(default_factory=dict)
    model_config = {"extra": "forbid"}


class BacktestForensicsSummary(BaseModel):
    batch_present: bool
    strategy_count: int = 0
    promotion_eligible_count: int = 0
    blocked_count: int = 0
    paper_only_count: int = 0
    failed_count: int = 0
    needs_evidence_count: int = 0
    synthetic_count: int = 0
    provider_snapshot_count: int = 0
    real_local_count: int = 0
    risk_flag_counts: dict[str, int] = Field(default_factory=dict)
    gate_status_counts: dict[str, dict[str, int]] = Field(default_factory=dict)
    model_config = {"extra": "forbid"}


class BacktestForensicsPayload(BaseModel):
    schema_version: Literal["ui_backtest_forensics/v1"] = "ui_backtest_forensics/v1"
    generated_at_utc: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    read_plane_only: bool = True
    no_live_trading: bool = True
    mutation_authority: Literal["NONE"] = "NONE"
    promotion_authority: Literal["NONE"] = "NONE"
    execution_authority: Literal["NONE"] = "NONE"
    scan_root: str
    summary_path: str | None = None
    degraded: list[str] = Field(default_factory=list)
    batch: dict[str, Any] | None = None
    summary: BacktestForensicsSummary
    strategies: list[BacktestForensicStrategyRow] = Field(default_factory=list)
    raw_strategy_batch_route: str | None = None
    artifact_replay: dict[str, Any] = Field(default_factory=dict)
    model_config = {"extra": "forbid"}


__all__ = ["BacktestForensicStrategyRow", "BacktestForensicsPayload", "BacktestForensicsSummary"]
