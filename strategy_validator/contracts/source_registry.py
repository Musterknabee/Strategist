from __future__ import annotations

from datetime import datetime, timezone

from pydantic import BaseModel, Field


class SourceRegistryRecord(BaseModel):
    source_id: str = Field(min_length=1)
    source_system: str = Field(min_length=1)
    snapshot_reference: str = Field(min_length=1)
    schema_id: str = Field(min_length=1)
    trust_posture: str = Field(default='unknown', min_length=1)
    revision: str | None = None
    registered_at_utc: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict[str, object] = Field(default_factory=dict)

    model_config = {'extra': 'forbid'}
