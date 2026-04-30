from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from strategy_validator.projections.artifact_registry import (
    build_projection_artifact_registry,
    build_projection_source_descriptor,
)


BRIEFING_PACK_SOURCE_LABELS = (
    "derived_view",
    "constitutional_gate",
    "closure_snapshot",
    "closure_dsse",
    "governed_exception",
    "governed_exception_dsse",
    "strategic_briefing",
    "strategic_narrative",
    "strategic_memory_horizon",
    "contradiction_resolution",
    "strategic_intervention",
    "strategic_campaign",
    "strategic_campaign_execution",
    "thesis_memory",
    "strategy_cohort",
    "doctrine_adaptation",
    "research_priorities",
    "research_execution_memory",
    "thesis_graph",
    "strategic_tensions",
    "scenario_lab",
)


def build_briefing_pack_projection_registry(
    *,
    repo_root: Path,
    generated_at_utc: datetime,
    source_paths: dict[str, Path | None],
    source_payloads: dict[str, Any | None],
    output_paths: list[Path],
) -> dict[str, Any]:
    descriptors = []
    for label in BRIEFING_PACK_SOURCE_LABELS:
        path = source_paths.get(label)
        if path is None:
            continue
        descriptors.append(
            build_projection_source_descriptor(
                artifact_label=label,
                path=path,
                payload=source_payloads.get(label),
                repo_root=repo_root,
            )
        )
    return build_projection_artifact_registry(
        projection_label="oracle_briefing_pack",
        projection_family="operator_projection",
        projection_version="oracle_briefing_pack_report/v1",
        source_descriptors=descriptors,
        output_paths=output_paths,
        repo_root=repo_root,
        generated_at_utc=generated_at_utc,
    )
