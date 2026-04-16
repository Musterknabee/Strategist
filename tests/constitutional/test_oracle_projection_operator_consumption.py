from __future__ import annotations

import json
from pathlib import Path

from strategy_validator.cli.rollout_ops import main
from strategy_validator.validator.oracle_briefing import build_oracle_briefing_pack
from strategy_validator.validator.oracle_diagnostics import build_oracle_incident_pack


def _write_minimal_event_log(log_path: Path) -> None:
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


def test_briefing_pack_discovers_indexed_projection_output_without_canonical_filename(tmp_path: Path) -> None:
    repo_root = tmp_path
    search_root = repo_root / 'docs' / 'artifacts' / 'oracle'
    log_path = search_root / 'ORACLE_EVENT_LOG.jsonl'
    _write_minimal_event_log(log_path)

    custom_report_path = search_root / 'views' / 'LATEST_OPERATOR_POSTURE.json'
    rc = main([
        'oracle-horizon-view', '--log-path', str(log_path), '--horizon', 'weekly', '--output', str(custom_report_path)
    ])
    assert rc == 0
    briefing = build_oracle_briefing_pack(repo_root=repo_root, search_root=search_root)
    derived_lineage = next(item for item in briefing.artifact_lineage if item.artifact_label == 'derived_view')
    assert Path(derived_lineage.source_path).resolve() == custom_report_path.resolve()


def test_incident_pack_discovers_indexed_projection_output_without_canonical_filename(tmp_path: Path) -> None:
    repo_root = tmp_path
    search_root = repo_root / 'docs' / 'artifacts' / 'oracle'
    log_path = search_root / 'ORACLE_EVENT_LOG.jsonl'
    _write_minimal_event_log(log_path)

    custom_report_path = search_root / 'nested' / 'LATEST_REVIEW_SIGNAL.json'
    rc = main([
        'oracle-rolling-review', '--log-path', str(log_path), '--horizon', 'weekly', '--output', str(custom_report_path)
    ])
    assert rc == 0
    incident = build_oracle_incident_pack(repo_root=repo_root, search_root=search_root)
    derived_artifact = next(item for item in incident.artifacts if item.artifact_kind == 'derived_view_report')
    assert Path(derived_artifact.source_path).resolve() == custom_report_path.resolve()


def test_oracle_projection_artifact_query_cli_reads_shared_index(tmp_path: Path) -> None:
    repo_root = tmp_path
    search_root = repo_root / 'docs' / 'artifacts' / 'oracle'
    log_path = search_root / 'ORACLE_EVENT_LOG.jsonl'
    _write_minimal_event_log(log_path)

    custom_report_path = search_root / 'custom' / 'LATEST_SIGNAL_VIEW.json'
    rc = main([
        'oracle-horizon-view', '--log-path', str(log_path), '--horizon', 'weekly', '--output', str(custom_report_path)
    ])
    assert rc == 0

    output_path = search_root / 'ORACLE_PROJECTION_ARTIFACT_QUERY_REPORT.json'
    rc = main([
        'oracle-projection-artifact-query',
        '--search-root', str(search_root),
        '--repo-root', str(repo_root),
        '--projection-label', 'oracle_horizon_view',
        '--projection-family', 'canonical_event_projection',
        '--output-artifact-label-contains', 'LATEST_SIGNAL_VIEW',
        '--output', str(output_path),
    ])
    assert rc == 0
    payload = json.loads(output_path.read_text(encoding='utf-8'))
    assert payload['schema_version'] == 'oracle_projection_artifact_query_report/v1'
    assert payload['match_count'] == 1
    assert payload['matches'][0]['projection_label'] == 'oracle_horizon_view'
    assert Path(payload['matches'][0]['output_artifact_path']).resolve() == custom_report_path.resolve()
