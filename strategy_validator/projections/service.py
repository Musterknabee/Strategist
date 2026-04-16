from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

from strategy_validator.projections.discovery import (
    ProjectionArtifactDiscoveryMatch,
    ProjectionArtifactQueryReport,
    build_projection_artifact_query_report,
    discover_latest_projection_output,
)


CANONICAL_EVENT_PROJECTION_LABELS: tuple[str, ...] = (
    'oracle_rolling_review',
    'oracle_horizon_view',
    'oracle_derived_view',
)
CANONICAL_EVENT_PROJECTION_FAMILY = 'canonical_event_projection'


@dataclass(frozen=True)
class ProjectionArtifactQuery:
    search_root: Path
    repo_root: Path | None = None
    projection_labels: tuple[str, ...] = ()
    projection_family: str | None = None
    output_artifact_label_contains: str | None = None


@dataclass(frozen=True)
class ProjectionArtifactSelection:
    query: ProjectionArtifactQuery
    output_artifact_path: Path
    match: ProjectionArtifactDiscoveryMatch | None


@dataclass(frozen=True)
class ProjectionArtifactOperatorQueryResult:
    query: ProjectionArtifactQuery
    report: ProjectionArtifactQueryReport

    def to_payload(self) -> dict[str, Any]:
        return {
            'schema_version': self.report.schema_version,
            'search_root': self.report.search_root,
            'projection_labels': list(self.report.projection_labels),
            'projection_family': self.report.projection_family,
            'output_artifact_label_contains': self.report.output_artifact_label_contains,
            'match_count': self.report.match_count,
            'matches': [
                {
                    'index_path': str(item.index_path),
                    'registry_path': str(item.registry_path),
                    'projection_label': item.projection_label,
                    'projection_family': item.projection_family,
                    'projection_version': item.projection_version,
                    'generated_at_utc': item.generated_at_utc,
                    'output_artifact_path': str(item.output_artifact_path),
                    'output_artifact_label': item.output_artifact_label,
                }
                for item in self.report.matches
            ],
        }



def build_projection_artifact_query(
    *,
    search_root: Path,
    repo_root: Path | None = None,
    projection_labels: Sequence[str] = (),
    projection_family: str | None = None,
    output_artifact_label_contains: str | None = None,
) -> ProjectionArtifactQuery:
    return ProjectionArtifactQuery(
        search_root=search_root.resolve(),
        repo_root=repo_root.resolve() if repo_root is not None else None,
        projection_labels=tuple(label for label in projection_labels if label),
        projection_family=projection_family,
        output_artifact_label_contains=output_artifact_label_contains,
    )



def run_projection_artifact_operator_query(query: ProjectionArtifactQuery) -> ProjectionArtifactOperatorQueryResult:
    report = build_projection_artifact_query_report(
        search_root=query.search_root,
        repo_root=query.repo_root,
        projection_labels=query.projection_labels,
        projection_family=query.projection_family,
        output_artifact_label_contains=query.output_artifact_label_contains,
    )
    return ProjectionArtifactOperatorQueryResult(query=query, report=report)



def select_latest_projection_artifact(query: ProjectionArtifactQuery) -> ProjectionArtifactSelection | None:
    path = discover_latest_projection_output(
        search_root=query.search_root,
        repo_root=query.repo_root,
        projection_labels=query.projection_labels,
        projection_family=query.projection_family,
    )
    if path is None:
        return None
    result = run_projection_artifact_operator_query(query)
    selected_match = next((item for item in result.report.matches if item.output_artifact_path == path), None)
    return ProjectionArtifactSelection(query=query, output_artifact_path=path, match=selected_match)



def select_latest_canonical_event_projection(
    *,
    search_root: Path,
    repo_root: Path | None = None,
) -> ProjectionArtifactSelection | None:
    return select_latest_projection_artifact(
        build_projection_artifact_query(
            search_root=search_root,
            repo_root=repo_root,
            projection_labels=CANONICAL_EVENT_PROJECTION_LABELS,
            projection_family=CANONICAL_EVENT_PROJECTION_FAMILY,
        )
    )
