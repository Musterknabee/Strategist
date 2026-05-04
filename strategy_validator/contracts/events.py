from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class EventEnvelope(BaseModel):
    """Canonical application-facing event envelope for ledger and projection flows."""

    event_id: str = Field(default_factory=lambda: f"evt-{uuid4().hex}")
    event_type: str = Field(min_length=1)
    stream_family: str = Field(min_length=1)
    aggregate_id: str = Field(min_length=1)
    occurred_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    recorded_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    schema_version: str = Field(default='event_envelope/v1', min_length=1)
    actor_id: str | None = None
    authority: str | None = None
    correlation_id: str | None = None
    causal_event_id: str | None = None
    payload_digest_sha256: str = Field(min_length=1)
    payload: dict[str, Any] = Field(default_factory=dict)

    model_config = {"extra": "forbid"}
