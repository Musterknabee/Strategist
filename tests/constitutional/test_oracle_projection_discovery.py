from __future__ import annotations

import json
from pathlib import Path

from strategy_validator.cli.rollout_ops import main
from strategy_validator.projections.discovery import discover_latest_projection_output, find_projection_artifact_match
from strategy_validator.validator.oracle_diagnostics import build_oracle_status_pack


def test_discover_latest_projection_output_prefers_projection_priority_from_index(tmp_path: Path) -> None:
    repo_root = tmp_path
    search_root = repo_root / 'docs' / 'artifacts' / 'oracle'
    search_root.mkdir(parents=True, exist_ok=True)

    rolling_review_path = search_root / 'custom' / 'LATEST_SIGNAL_VIEW.json'
    rolling_review_path.parent.mkdir(parents=True, exist_ok=True)
    rolling_review_path.write_text('{}\n', encoding='utf-8')
    horizon_view_path = search_root / 'custom' / 'LATEST_HORIZON_VIEW.json'
    horizon_view_path.write_text('{}\n', encoding='utf-8')

    index_path = search_root / 'ORACLE_PROJECTION_ARTIFACT_INDEX.json'
    index_payload = {
        'schema_version': 'oracle_projection_artifact_index/v1',
        'generated_at_utc': '2026-04-14T10:00:00+00:00',
        'entry_count': 2,
        'entries': [
            {
                'registry_path': 'docs/artifacts/oracle/custom/ROLLING_REVIEW.projection.registry.json',
                'projection_label': 'oracle_rolling_review',
                'projection_family': 'canonical_event_projection',
                'projection_version': 'oracle_derived_view_report/v1',
                'generated_at_utc': '2026-04-14T09:00:00+00:00',
                'projection_digest_sha256': 'a' * 64,
                'source_artifact_count': 1,
                'output_artifact_count': 1,
                'source_artifact_labels': ['oracle_event_log'],
                'output_artifact_labels': ['output:LATEST_SIGNAL_VIEW.json'],
                'output_artifact_paths': ['docs/artifacts/oracle/custom/LATEST_SIGNAL_VIEW.json'],
            },
            {
                'registry_path': 'docs/artifacts/oracle/custom/HORIZON_WEEKLY.projection.registry.json',
                'projection_label': 'oracle_horizon_view',
                'projection_family': 'canonical_event_projection',
                'projection_version': 'oracle_derived_view_report/v1',
                'generated_at_utc': '2026-04-14T11:00:00+00:00',
                'projection_digest_sha256': 'b' * 64,
                'source_artifact_count': 1,
                'output_artifact_count': 1,
                'source_artifact_labels': ['oracle_event_log'],
                'output_artifact_labels': ['output:LATEST_HORIZON_VIEW.json'],
                'output_artifact_paths': ['docs/artifacts/oracle/custom/LATEST_HORIZON_VIEW.json'],
            },
        ],
    }
    index_path.write_text(json.dumps(index_payload, indent=2) + '\n', encoding='utf-8')

    match = find_projection_artifact_match(
        search_root=search_root,
        repo_root=repo_root,
        projection_labels=('oracle_rolling_review', 'oracle_horizon_view'),
        projection_family='canonical_event_projection',
    )
    assert match is not None
    assert match.projection_label == 'oracle_rolling_review'
    assert match.output_artifact_path == rolling_review_path.resolve()

    discovered = discover_latest_projection_output(
        search_root=search_root,
        repo_root=repo_root,
        projection_labels=('oracle_rolling_review', 'oracle_horizon_view'),
        projection_family='canonical_event_projection',
    )
    assert discovered == rolling_review_path.resolve()


def test_status_pack_discovers_indexed_projection_output_without_canonical_filename(tmp_path: Path) -> None:
    repo_root = tmp_path
    search_root = repo_root / 'docs' / 'artifacts' / 'oracle'
    search_root.mkdir(parents=True, exist_ok=True)
    log_path = search_root / 'ORACLE_EVENT_LOG.jsonl'
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

    custom_report_path = search_root / 'views' / 'LATEST_OPERATOR_POSTURE.json'
    custom_report_path.parent.mkdir(parents=True, exist_ok=True)
    rc = main([
        'oracle-horizon-view', '--log-path', str(log_path), '--horizon', 'weekly', '--output', str(custom_report_path)
    ])
    assert rc == 0
    assert custom_report_path.exists()
    assert not (search_root / 'ORACLE_HORIZON_VIEW.json').exists()
    assert not (search_root / 'ORACLE_DERIVED_VIEW.json').exists()
    assert not (search_root / 'ORACLE_ROLLING_REVIEW.json').exists()

    report = build_oracle_status_pack(repo_root=repo_root, search_root=search_root)
    oracle_posture = next(section for section in report.sections if section.section_id == 'oracle_posture')
    assert any(str(custom_report_path.resolve()) in fact for fact in oracle_posture.facts)
    assert report.trust_status in {'TRUSTED', 'TRUST_RESTRICTED', 'UNTRUSTED'}
