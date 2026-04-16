from __future__ import annotations

from datetime import datetime, timezone

from pydantic import BaseModel, Field


class PublicationArtifactRecord(BaseModel):
    publication_id: str = Field(min_length=1)
    publication_family: str = Field(min_length=1)
    published_at_utc: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    manifest_path: str | None = None
    artifact_paths: list[str] = Field(default_factory=list)
    source_snapshot_ids: list[str] = Field(default_factory=list)
    digest_sha256: str = Field(min_length=1)

    model_config = {"extra": "forbid"}
