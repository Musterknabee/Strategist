from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

from strategy_validator.application.projection_queries import (
    build_projection_query_request,
    query_projection_artifacts,
)


class ProjectionStore(Protocol):
    def list_projection_artifacts(
        self,
        *,
        search_root,
        repo_root=None,
        projection_labels: tuple[str, ...] = (),
        projection_family: str | None = None,
        output_artifact_label_contains: str | None = None,
    ) -> dict[str, Any]: ...


@dataclass(slots=True)
class FilesystemProjectionStore:
    """Filesystem-backed projection-store adapter over current artifact indexes."""

    def list_projection_artifacts(
        self,
        *,
        search_root,
        repo_root=None,
        projection_labels: tuple[str, ...] = (),
        projection_family: str | None = None,
        output_artifact_label_contains: str | None = None,
    ) -> dict[str, Any]:
        request = build_projection_query_request(
            search_root=search_root,
            repo_root=repo_root,
            projection_labels=projection_labels,
            projection_family=projection_family,
            output_artifact_label_contains=output_artifact_label_contains,
        )
        return query_projection_artifacts(request).to_payload()
