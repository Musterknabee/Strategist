from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class ApplicationCommand(BaseModel):
    command_id: str | None = None
    requested_at_utc: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    idempotency_key: str | None = None

    model_config = {"extra": "forbid"}


class ApplicationResult(BaseModel):
    command_id: str | None = None
    executed_at_utc: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    idempotency_key: str | None = None

    model_config = {"extra": "forbid"}


class ProjectionQueryCommand(ApplicationCommand):
    search_root: Path
    repo_root: Path | None = None
    projection_labels: tuple[str, ...] = ()
    projection_family: str | None = None
    output_artifact_label_contains: str | None = None


class ProjectionQueryResult(ApplicationResult):
    payload: dict[str, Any] = Field(default_factory=dict)


class RebuildProjectionCommand(ApplicationCommand):
    search_root: Path
    repo_root: Path | None = None
    projection_labels: tuple[str, ...] = ()
    projection_family: str | None = None
    output_artifact_label_contains: str | None = None


class RebuildProjectionResult(ApplicationResult):
    rebuilt_projection_count: int = 0
    snapshot_payloads: list[dict[str, Any]] = Field(default_factory=list)
    verification_payload: dict[str, Any] = Field(default_factory=dict)
