from __future__ import annotations

import json
from pathlib import Path

from strategy_validator.cli.rollout_ops import main
from strategy_validator.projections.artifact_index import build_projection_artifact_index, build_projection_artifact_index_entry


def test_build_projection_artifact_index_upserts_by_registry_path(tmp_path: Path) -> None:
    repo_root = tmp_path
    registry_path = repo_root / 'docs' / 'artifacts' / 'oracle' / 'ORACLE_HORIZON_WEEKLY.projection.registry.json'
    registry = {
        'projection_label': 'oracle_horizon_view',
        'projection_family': 'canonical_event_projection',
        'projection_version': 'oracle_derived_view_report/v1',
        'generated_at_utc': '2026-04-14T09:00:00+00:00',
        'projection_digest_sha256': 'a' * 64,
        'source_artifact_count': 1,
        'output_artifact_count': 2,
        'source_artifacts': [{'artifact_label': 'oracle_event_log'}],
        'output_artifacts': [{'artifact_label': 'output:ORACLE_HORIZON_WEEKLY.json', 'path': 'docs/artifacts/oracle/ORACLE_HORIZON_WEEKLY.json'}],
    }
    existing = [
        build_projection_artifact_index_entry(registry_path=registry_path, registry=registry, repo_root=repo_root),
    ]
    updated = dict(registry)
    updated['projection_digest_sha256'] = 'b' * 64
    index = build_projection_artifact_index(
        existing_entries=existing,
        registry_path=registry_path,
        registry=updated,
        repo_root=repo_root,
    )
    assert index['schema_version'] == 'oracle_projection_artifact_index/v1'
    assert index['entry_count'] == 1
    assert index['entries'][0]['projection_digest_sha256'] == 'b' * 64
    assert index['entries'][0]['registry_path'] == 'docs/artifacts/oracle/ORACLE_HORIZON_WEEKLY.projection.registry.json'


def test_checkpoint_and_view_commands_update_shared_projection_artifact_index(tmp_path: Path) -> None:
    repo_root = tmp_path
    log_path = repo_root / 'docs' / 'artifacts' / 'oracle' / 'ORACLE_EVENT_LOG.jsonl'
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.write_text(
        json.dumps({
            'schema_version': 'oracle_event_log_entry/v1',
            'appended_at_utc': '2026-04-14T08:10:00Z',
            'lane_id': 'ORACLE_EVENT_LOG',
            'sequence_number': 1,
            'entry_id': 'evidence-1:1',
            'evidence_id': 'evidence-1',
            'previous_entry_hash': None,
            'entry_hash': '9' * 64,
            'manifest_path': 'docs/artifacts/oracle/ORACLE_EVIDENCE_1.json',
            'manifest_sha256': 'a' * 64,
            'linked_closure_id': None,
            'input_timestamp_utc': '2026-04-14T08:10:00Z',
            'dominant_regime': 'TRANSITION',
            'recommended_global_action': 'CANARY_REVIEW',
            'epistemic_status': 'ELEVATED',
            'average_posterior_edge_confidence': 0.58,
            'maintain_count': 0,
            'canary_count': 1,
            'hibernate_count': 0,
            'strategy_ids': ['trend-a'],
            'evidence_status': 'VERIFIED',
            'summary_line': 'watch entry',
        }) + '\n',
        encoding='utf-8',
    )

    horizon_json = log_path.with_name('ORACLE_HORIZON_WEEKLY.json')
    rc = main([
        'oracle-horizon-view', '--log-path', str(log_path), '--horizon', 'weekly', '--output', str(horizon_json)
    ])
    assert rc == 0

    checkpoint_json = log_path.with_name('ORACLE_EVENT_CHECKPOINT.json')
    report_json = log_path.with_name('ORACLE_DERIVED_VIEW.json')
    rc = main([
        'oracle-event-checkpoint',
        '--lane-path', str(log_path),
        '--view-label', 'weekly',
        '--report-output', str(report_json),
        '--output', str(checkpoint_json),
    ])
    assert rc == 0

    index_path = log_path.with_name('ORACLE_PROJECTION_ARTIFACT_INDEX.json')
    index = json.loads(index_path.read_text(encoding='utf-8'))
    assert index['schema_version'] == 'oracle_projection_artifact_index/v1'
    labels = {entry['projection_label'] for entry in index['entries']}
    assert 'oracle_horizon_view' in labels
    assert 'oracle_event_checkpoint' in labels
    checkpoint_entry = next(entry for entry in index['entries'] if entry['projection_label'] == 'oracle_event_checkpoint')
    assert 'output:ORACLE_EVENT_CHECKPOINT.json' in checkpoint_entry['output_artifact_labels']
    assert 'output:ORACLE_DERIVED_VIEW.json' in checkpoint_entry['output_artifact_labels']
