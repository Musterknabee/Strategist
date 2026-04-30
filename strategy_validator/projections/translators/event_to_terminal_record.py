from __future__ import annotations

from strategy_validator.projections.discovery import ProjectionArtifactDiscoveryMatch


def translate_projection_match_to_terminal_record_payload(match: ProjectionArtifactDiscoveryMatch) -> dict[str, str | None]:
    return {
        'projection_label': match.projection_label,
        'projection_family': match.projection_family,
        'generated_at_utc': match.generated_at_utc,
        'output_artifact_path': str(match.output_artifact_path),
        'output_artifact_label': match.output_artifact_label,
    }
