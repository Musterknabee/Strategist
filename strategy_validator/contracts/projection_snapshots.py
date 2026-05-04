from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field


class ProjectionSnapshotManifest(BaseModel):
    projection_family: str = Field(min_length=1)
    projection_label: str | None = None
    source_event_range: str = Field(min_length=1)
    rebuild_timestamp_utc: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    schema_version: str = Field(default='projection_snapshot_manifest/v1', min_length=1)
    digest_sha256: str = Field(min_length=1)
    checkpoint_id: str | None = None
    artifact_references: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)

    model_config = {"extra": "forbid"}
