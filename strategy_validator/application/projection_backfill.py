from __future__ import annotations

from typing import Any

from strategy_validator.application.rebuild import rebuild_projection_artifacts
from strategy_validator.contracts.application import RebuildProjectionCommand
from strategy_validator.contracts.projection_snapshots import ProjectionSnapshotManifest
from strategy_validator.projections.registry_protocol import ProjectionRegistryEntry, default_projection_registry


def get_projection_registry() -> tuple[ProjectionRegistryEntry, ...]:
    return default_projection_registry()


def backfill_projection_family(command: RebuildProjectionCommand) -> dict[str, Any]:
    result = rebuild_projection_artifacts(command)
    snapshots = [ProjectionSnapshotManifest.model_validate(item) for item in result.snapshot_payloads]
    return {
        'projection_family': command.projection_family,
        'rebuilt_projection_count': result.rebuilt_projection_count,
        'snapshots': [snapshot.model_dump(mode='json') for snapshot in snapshots],
        'verification_payload': result.verification_payload,
    }


def backfill_all_registered_projections(*, search_root, repo_root=None) -> dict[str, Any]:
    registry = get_projection_registry()
    families: list[dict[str, Any]] = []
    for entry in registry:
        families.append(
            backfill_projection_family(
                RebuildProjectionCommand(
                    search_root=search_root,
                    repo_root=repo_root,
                    projection_labels=(entry.projection_label,),
                    projection_family=entry.projection_family,
                )
            )
        )
    return {
        'registered_projection_count': len(registry),
        'families': families,
    }
