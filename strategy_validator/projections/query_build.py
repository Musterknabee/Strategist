from __future__ import annotations

from pathlib import Path
from typing import Any

from strategy_validator.projections.artifact_registry import build_projection_artifact_registry, build_projection_source_descriptor


def build_single_source_projection_registry(
    *,
    projection_label: str,
    projection_family: str,
    projection_version: str,
    source_label: str,
    source_path: Path,
    source_payload: Any | None = None,
    output_paths: list[Path],
    repo_root: Path | None = None,
    generated_at_utc=None,
) -> dict[str, Any]:
    descriptor = build_projection_source_descriptor(
        artifact_label=source_label,
        path=source_path,
        payload=source_payload,
        repo_root=repo_root,
    )
    return build_projection_artifact_registry(
        projection_label=projection_label,
        projection_family=projection_family,
        projection_version=projection_version,
        source_descriptors=[descriptor],
        output_paths=output_paths,
        repo_root=repo_root,
        generated_at_utc=generated_at_utc,
    )
