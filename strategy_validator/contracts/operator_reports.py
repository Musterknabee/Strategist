from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field


class OperatorGovernanceReport(BaseModel):
    """Governance-plane summary translated out of kernel decisions for operator use."""

    report_id: str = Field(min_length=1)
    generated_at_utc: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    decision_record_id: str = Field(min_length=1)
    queue_priority: int = Field(ge=0)
    escalation_posture: Literal['NORMAL', 'ELEVATED', 'CRITICAL'] = 'NORMAL'
    routing_class: str = Field(min_length=1)
    operator_summary: str = Field(min_length=1)
    blocking_reasons: list[str] = Field(default_factory=list)

    model_config = {"extra": "forbid"}


class ReleaseReadinessReport(BaseModel):
    """Operator-facing summary over readiness and release publication evidence."""

    report_id: str = Field(min_length=1)
    generated_at_utc: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    readiness_status: str = Field(min_length=1)
    adjudication_allowed: bool
    blocker_codes: list[str] = Field(default_factory=list)
    published_artifact_paths: list[str] = Field(default_factory=list)
    summary_line: str = Field(min_length=1)

    model_config = {"extra": "forbid"}
