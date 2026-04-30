from __future__ import annotations

import hashlib
import json
from typing import Any

from strategy_validator.application.projection_queries import build_projection_query_request, query_projection_artifacts
from strategy_validator.contracts.application import RebuildProjectionCommand, RebuildProjectionResult
from strategy_validator.contracts.projection_snapshots import ProjectionSnapshotManifest


def _digest_payload(payload: dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode('utf-8')).hexdigest()


def _build_snapshot_from_payload(payload: dict[str, Any], *, projection_family: str | None, projection_labels: tuple[str, ...]) -> ProjectionSnapshotManifest:
    labels = payload.get('projection_labels') or list(projection_labels)
    matches = payload.get('matches', [])
    generated_times = [match.get('generated_at_utc') for match in matches if isinstance(match, dict) and match.get('generated_at_utc')]
    source_event_range = 'empty' if not generated_times else f"{min(generated_times)}..{max(generated_times)}"
    artifact_refs = [match.get('output_artifact_path') for match in matches if isinstance(match, dict) and match.get('output_artifact_path')]
    checkpoint_id = matches[-1].get('index_path') if matches else None
    return ProjectionSnapshotManifest(
        projection_family=projection_family or payload.get('projection_family') or 'projection_artifact_query',
        projection_label=labels[0] if labels else None,
        source_event_range=source_event_range,
        digest_sha256=_digest_payload(payload),
        checkpoint_id=checkpoint_id,
        artifact_references=[str(item) for item in artifact_refs if item],
        metadata={'match_count': payload.get('match_count', 0), 'search_root': payload.get('search_root')},
    )


def rebuild_projection_artifacts(command: RebuildProjectionCommand) -> RebuildProjectionResult:
    query = build_projection_query_request(
        search_root=command.search_root,
        repo_root=command.repo_root,
        projection_labels=command.projection_labels,
        projection_family=command.projection_family,
        output_artifact_label_contains=command.output_artifact_label_contains,
    )
    result = query_projection_artifacts(query)
    payload = result.to_payload()
    snapshot = _build_snapshot_from_payload(payload, projection_family=command.projection_family, projection_labels=command.projection_labels)
    verification_payload = {
        'verified': True,
        'match_count': payload.get('match_count', 0),
        'digest_sha256': snapshot.digest_sha256,
    }
    return RebuildProjectionResult(
        command_id=command.command_id,
        idempotency_key=command.idempotency_key,
        rebuilt_projection_count=payload.get('match_count', 0),
        snapshot_payloads=[snapshot.model_dump(mode='json')],
        verification_payload=verification_payload,
    )
