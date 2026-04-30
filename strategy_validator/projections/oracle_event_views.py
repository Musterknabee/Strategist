from __future__ import annotations

from pathlib import Path
from typing import Any

from strategy_validator.projections.artifact_registry import write_projection_artifact_registry_with_index
from strategy_validator.projections.query_build import build_single_source_projection_registry


def build_oracle_event_view_projection_registry(
    *,
    projection_label: str,
    projection_version: str,
    lane_path: Path,
    report_payload: Any,
    output_paths: list[Path],
    repo_root: Path | None,
    generated_at_utc,
    index_output_path: Path | None = None,
) -> dict[str, Any]:
    return build_single_source_projection_registry(
        projection_label=projection_label,
        projection_family="canonical_event_projection",
        projection_version=projection_version,
        source_label="oracle_event_log",
        source_path=lane_path,
        source_payload={"schema_version": "oracle_event_log_lane/jsonl"},
        output_paths=output_paths,
        repo_root=repo_root,
        generated_at_utc=generated_at_utc,
    )


def emit_oracle_event_view_projection_registry(
    *,
    registry_output_path: Path,
    projection_label: str,
    projection_version: str,
    lane_path: Path,
    report_payload: Any,
    output_paths: list[Path],
    repo_root: Path | None,
    generated_at_utc,
    index_output_path: Path | None = None,
) -> dict[str, Any]:
    registry = build_oracle_event_view_projection_registry(
        projection_label=projection_label,
        projection_version=projection_version,
        lane_path=lane_path,
        report_payload=report_payload,
        output_paths=output_paths,
        repo_root=repo_root,
        generated_at_utc=generated_at_utc,
    )
    write_projection_artifact_registry_with_index(
        registry_output_path,
        registry,
        repo_root=repo_root,
        index_path=index_output_path,
        generated_at_utc=generated_at_utc,
    )
    return registry
