"""Research cycle scheduler contracts (paper-only; no trading authority)."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, Field


class UiResearchCycleTriggerRequest(BaseModel):
    operator_id: str = Field(default="operator", min_length=1)
    mode: Literal["light", "heavy"] = "light"
    idempotency_key: str | None = None


class ResearchCycleSchedulerState(BaseModel):
    schema_version: Literal["research_cycle_scheduler_state/v1"] = "research_cycle_scheduler_state/v1"
    updated_at_utc: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    daemon_pid: int | None = None
    daemon_started_at_utc: datetime | None = None
    interval_seconds: int = 3600
    heavy_every: int = 12
    iteration: int = 0
    last_cycle_started_at_utc: datetime | None = None
    last_cycle_finished_at_utc: datetime | None = None
    last_cycle_mode: Literal["light", "heavy"] | None = None
    last_cycle_ok: bool | None = None
    last_cycle_run_id: str | None = None
    last_cycle_error: str | None = None
    last_batch_spec: str | None = None
    pending_trigger_count: int = 0
    allow_network: bool = False


__all__ = ["ResearchCycleSchedulerState", "UiResearchCycleTriggerRequest"]
