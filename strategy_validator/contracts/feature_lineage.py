from __future__ import annotations

from pydantic import BaseModel, Field


class FeatureLineageRecord(BaseModel):
    feature_id: str = Field(min_length=1)
    upstream_source_ids: tuple[str, ...] = ()
    transform_version: str = Field(min_length=1)
    pit_guarantee: bool = True
    revision_provenance: str | None = None
    semantic_owner: str | None = None
    metadata: dict[str, object] = Field(default_factory=dict)

    model_config = {'extra': 'forbid'}
