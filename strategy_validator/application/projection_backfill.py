from __future__ import annotations

import hashlib
import json
from typing import Any

from strategy_validator.application.rebuild import rebuild_projection_artifacts
from strategy_validator.contracts.application import RebuildProjectionCommand
from strategy_validator.contracts.projection_snapshots import ProjectionSnapshotManifest
from strategy_validator.projections.registry_protocol import ProjectionRegistryEntry, default_projection_registry


def _canonical_payload_digest(payload: Any) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    ).hexdigest()


def _verification_payload(*, projection_family: str, snapshots: list[ProjectionSnapshotManifest], raw_verification: Any) -> dict[str, Any]:
    snapshot_payloads = [snapshot.model_dump(mode="json") for snapshot in snapshots]
    return {
        "schema_version": "projection_backfill_verification/v1",
        "projection_family": projection_family,
        "snapshot_count": len(snapshot_payloads),
        "snapshot_payload_sha256": _canonical_payload_digest(snapshot_payloads),
        "raw_verification_sha256": _canonical_payload_digest(raw_verification),
        "raw_verification_payload": raw_verification,
    }


def get_projection_registry() -> tuple[ProjectionRegistryEntry, ...]:
    return default_projection_registry()


def backfill_projection_family(command: RebuildProjectionCommand) -> dict[str, Any]:
    result = rebuild_projection_artifacts(command)
    snapshots = [ProjectionSnapshotManifest.model_validate(item) for item in result.snapshot_payloads]
    verification_payload = _verification_payload(
        projection_family=command.projection_family,
        snapshots=snapshots,
        raw_verification=result.verification_payload,
    )
    return {
        'projection_family': command.projection_family,
        'rebuilt_projection_count': result.rebuilt_projection_count,
        'snapshots': [snapshot.model_dump(mode='json') for snapshot in snapshots],
        'verification_payload': verification_payload,
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
