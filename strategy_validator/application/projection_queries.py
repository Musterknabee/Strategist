from __future__ import annotations

from pathlib import Path
from typing import Sequence

from strategy_validator.projections.operator_pack_discovery import (
    OperatorPackQuery,
    build_operator_pack_query,
    discover_latest_operator_pack_match,
    run_operator_pack_query,
)
from strategy_validator.projections.service import (
    ProjectionArtifactQuery,
    build_projection_artifact_query,
    run_projection_artifact_operator_query,
    select_latest_projection_artifact as _select_latest_projection_artifact,
)


def build_projection_query_request(
    *,
    search_root: Path,
    repo_root: Path | None = None,
    projection_labels: Sequence[str] = (),
    projection_family: str | None = None,
    output_artifact_label_contains: str | None = None,
) -> ProjectionArtifactQuery:
    return build_projection_artifact_query(
        search_root=search_root,
        repo_root=repo_root,
        projection_labels=projection_labels,
        projection_family=projection_family,
        output_artifact_label_contains=output_artifact_label_contains,
    )


def query_projection_artifacts(query: ProjectionArtifactQuery):
    return run_projection_artifact_operator_query(query)


def select_latest_projection_artifact(query: ProjectionArtifactQuery):
    return _select_latest_projection_artifact(query)


def build_operator_pack_query_request(
    *,
    search_root: Path,
    repo_root: Path | None = None,
    pack_kinds: Sequence[str] = (),
    trust_statuses: Sequence[str] = (),
    summary_line_contains: str | None = None,
    output_artifact_label_contains: str | None = None,
) -> OperatorPackQuery:
    return build_operator_pack_query(
        search_root=search_root,
        repo_root=repo_root,
        pack_kinds=pack_kinds,
        trust_statuses=trust_statuses,
        summary_line_contains=summary_line_contains,
        output_artifact_label_contains=output_artifact_label_contains,
    )


def query_operator_packs(query: OperatorPackQuery):
    return run_operator_pack_query(query)


def select_latest_operator_pack(query: OperatorPackQuery):
    return discover_latest_operator_pack_match(query)


__all__ = [
    'build_projection_query_request',
    'query_projection_artifacts',
    'select_latest_projection_artifact',
    'build_operator_pack_query_request',
    'query_operator_packs',
    'select_latest_operator_pack',
]
