"""Batch-level portfolio / correlation summary contracts (research)."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class PortfolioCorrelationSummary(BaseModel):
    schema_version: Literal["portfolio_correlation_summary/v1"] = "portfolio_correlation_summary/v1"
    batch_id: str
    run_id: str
    model_label: str = "BATCH_RETURN_CORRELATION_MODEL"
    strategy_ids: list[str] = Field(default_factory=list)
    correlation_matrix: list[list[float]] = Field(default_factory=list)
    high_correlation_pairs: list[dict[str, str | float]] = Field(default_factory=list)
    average_correlation: float = 0.0
    diversification_score: float = 0.0
    duplicate_alpha_warnings: list[str] = Field(default_factory=list)
    portfolio_gate_status: Literal["DIVERSIFYING", "WARNING", "DUPLICATIVE", "NOT_APPLICABLE"] = (
        "NOT_APPLICABLE"
    )
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    portfolio_summary_evidence_sha256: str = ""
    disclaimer: str = "Correlation on toy equity curves; not production diversification proof."

    model_config = {"extra": "forbid"}


__all__ = ["PortfolioCorrelationSummary"]
