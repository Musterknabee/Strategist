from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from strategy_validator.application.adjudication import build_decision_record
from strategy_validator.application.evidence_verification import (
    compute_payload_digest,
    verify_event_envelope,
    verify_projection_snapshot,
)
from strategy_validator.application.rebuild import rebuild_projection_artifacts
from strategy_validator.application.translators import translate_decision_record_to_governance
from strategy_validator.contracts.application import RebuildProjectionCommand
from strategy_validator.contracts.events import EventEnvelope
from strategy_validator.contracts.experiments import AdjudicationDecision, GateResult
from strategy_validator.contracts.projection_snapshots import ProjectionSnapshotManifest
from strategy_validator.core.enums import PromotionState


def test_event_envelope_verification_round_trip() -> None:
    payload = {'state': 'PROMOTABLE', 'experiment_id': 'exp-1'}
    envelope = EventEnvelope(
        event_type='adjudication.recorded',
        stream_family='promotion_state_stream',
        aggregate_id='exp-1',
        occurred_at=datetime(2026, 1, 1, tzinfo=UTC),
        recorded_at=datetime(2026, 1, 1, tzinfo=UTC),
        payload_digest_sha256=compute_payload_digest(payload),
        payload=payload,
    )
    assert verify_event_envelope(envelope) is True


def test_decision_record_translates_to_governance_priority() -> None:
    decision = AdjudicationDecision(
        previous_state=PromotionState.INVALID,
        new_state=PromotionState.CONDITIONAL,
        gate_results=[GateResult(gate_name='capacity', passed=False, reason='capacity blocked')],
        summary_notes=['needs review'],
    )
    record = build_decision_record(experiment_id='exp-2', strategy_id='strat-2', decision=decision)
    governance_payload = translate_decision_record_to_governance(record)
    assert governance_payload['review_target'] == 'CONSTITUTIONAL_REPAIR_QUEUE'
    assert governance_payload['failed_gate_count'] == 1


def test_projection_rebuild_emits_snapshot_manifest(tmp_path: Path) -> None:
    artifact_dir = tmp_path / 'artifacts'
    artifact_dir.mkdir()
    projection_output = artifact_dir / 'projection.json'
    projection_output.write_text(json.dumps({'ok': True}), encoding='utf-8')
    registry_output = artifact_dir / 'registry.projection.registry.json'
    registry_output.write_text('{}', encoding='utf-8')
    index = artifact_dir / 'ORACLE_PROJECTION_ARTIFACT_INDEX.json'
    index.write_text(
        json.dumps(
            {
                'entries': [
                    {
                        'projection_label': 'oracle_derived_view',
                        'projection_family': 'canonical_event_projection',
                        'projection_version': 'v1',
                        'generated_at_utc': '2026-01-01T00:00:00+00:00',
                        'registry_path': str(registry_output.relative_to(artifact_dir)),
                        'output_artifact_paths': [str(projection_output.relative_to(artifact_dir))],
                        'output_artifact_labels': ['derived-view'],
                    }
                ]
            }
        ),
        encoding='utf-8',
    )

    result = rebuild_projection_artifacts(
        RebuildProjectionCommand(
            search_root=artifact_dir,
            repo_root=artifact_dir,
            projection_labels=('oracle_derived_view',),
            projection_family='canonical_event_projection',
        )
    )
    assert result.rebuilt_projection_count == 1
    snapshot = ProjectionSnapshotManifest.model_validate(result.snapshot_payloads[0])
    assert snapshot.projection_family == 'canonical_event_projection'
    payload = {
        'projection_labels': ['oracle_derived_view'],
        'projection_family': 'canonical_event_projection',
        'matches': [
            {
                'generated_at_utc': '2026-01-01T00:00:00+00:00',
                'output_artifact_path': str(projection_output),
                'index_path': str(index),
            }
        ],
        'match_count': 1,
        'search_root': str(artifact_dir),
    }
    derived_snapshot = ProjectionSnapshotManifest(
        projection_family='canonical_event_projection',
        source_event_range='2026-01-01T00:00:00+00:00..2026-01-01T00:00:00+00:00',
        digest_sha256=compute_payload_digest(payload),
    )
    assert verify_projection_snapshot(derived_snapshot, payload) is True
