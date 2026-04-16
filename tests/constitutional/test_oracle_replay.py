from __future__ import annotations

import json
from pathlib import Path

import pytest

from strategy_validator.cli.rollout_ops import main


NOW1 = '2026-04-13T08:10:00Z'
NOW2 = '2026-04-14T08:10:00Z'
NOW3 = '2026-04-15T08:10:00Z'


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', encoding='utf-8') as handle:
        for row in rows:
            handle.write(json.dumps(row, separators=(',', ':')) + '\n')


def _event_row(*, seq: int, entry_id: str, ts: str, prev_hash: str | None, entry_hash: str, regime: str, action: str, epistemic: str, summary: str) -> dict:
    return {
        'schema_version': 'oracle_event_log_entry/v1',
        'appended_at_utc': ts,
        'lane_id': 'ORACLE_EVENT_LOG',
        'sequence_number': seq,
        'entry_id': entry_id,
        'evidence_id': entry_id.split(':')[0],
        'previous_entry_hash': prev_hash,
        'entry_hash': entry_hash,
        'manifest_path': f'docs/artifacts/oracle/{entry_id}.json',
        'manifest_sha256': entry_hash[::-1],
        'linked_closure_id': None,
        'input_timestamp_utc': ts,
        'dominant_regime': regime,
        'recommended_global_action': action,
        'epistemic_status': epistemic,
        'average_posterior_edge_confidence': 0.61,
        'maintain_count': 1 if action == 'OBSERVE' else 0,
        'canary_count': 1 if action == 'CANARY_REVIEW' else 0,
        'hibernate_count': 1 if action == 'DEFENSIVE_POSTURE' else 0,
        'strategy_ids': ['trend-a'],
        'evidence_status': 'VERIFIED',
        'summary_line': summary,
    }


@pytest.mark.constitutional
def test_oracle_compacted_state_inspect_reports_current_then_stale(tmp_path: Path) -> None:
    repo_root = tmp_path
    oracle_root = repo_root / 'docs' / 'artifacts' / 'oracle'
    log_path = oracle_root / 'ORACLE_EVENT_LOG.jsonl'
    metadata_path = oracle_root / 'ORACLE_WEEKLY.checkpoint.metadata.json'
    report_path = oracle_root / 'ORACLE_WEEKLY.json'
    inspect_json = oracle_root / 'ORACLE_COMPACTED_STATE_INSPECTION_REPORT.json'
    inspect_md = oracle_root / 'ORACLE_COMPACTED_STATE_INSPECTION_REPORT.md'

    _write_jsonl(
        log_path,
        [
            _event_row(seq=0, entry_id='evidence-0:0', ts=NOW1, prev_hash=None, entry_hash='a' * 64, regime='RISK_ON_LOW_VOL', action='OBSERVE', epistemic='NOMINAL', summary='baseline'),
            _event_row(seq=1, entry_id='evidence-1:1', ts=NOW2, prev_hash='a' * 64, entry_hash='b' * 64, regime='TRANSITION', action='CANARY_REVIEW', epistemic='ELEVATED', summary='watch'),
        ],
    )

    rc = main([
        'oracle-rolling-review',
        '--log-path', str(log_path),
        '--horizon', 'weekly',
        '--window-size', '2',
        '--output', str(report_path),
        '--checkpoint-metadata-output', str(metadata_path),
    ])
    assert rc == 0

    rc = main([
        'oracle-compacted-state-inspect',
        '--log-path', str(log_path),
        '--checkpoint-metadata', str(metadata_path),
        '--output', str(inspect_json),
        '--markdown-output', str(inspect_md),
    ])
    assert rc == 0
    report = json.loads(inspect_json.read_text(encoding='utf-8'))
    assert report['schema_version'] == 'oracle_compacted_state_inspection_report/v1'
    assert report['replay_status'] == 'CURRENT'
    assert report['cached_window_entry_ids'] == ['evidence-0:0', 'evidence-1:1']
    assert 'Oracle Compacted State Inspection' in inspect_md.read_text(encoding='utf-8')

    with log_path.open('a', encoding='utf-8') as handle:
        handle.write(json.dumps(_event_row(seq=2, entry_id='evidence-2:2', ts=NOW3, prev_hash='b' * 64, entry_hash='c' * 64, regime='RISK_OFF_HIGH_VOL', action='DEFENSIVE_POSTURE', epistemic='UNKNOWN_UNKNOWNS', summary='defensive'), separators=(',', ':')) + '\n')

    rc = main([
        'oracle-compacted-state-inspect',
        '--log-path', str(log_path),
        '--checkpoint-metadata', str(metadata_path),
        '--output', str(inspect_json),
    ])
    assert rc == 0
    report = json.loads(inspect_json.read_text(encoding='utf-8'))
    assert report['replay_status'] == 'STALE'
    assert any('grown beyond the compacted checkpoint offset' in finding for finding in report['findings'])


@pytest.mark.constitutional
def test_oracle_replay_audit_detects_consistent_then_drifted_checkpoint_metadata(tmp_path: Path) -> None:
    repo_root = tmp_path
    oracle_root = repo_root / 'docs' / 'artifacts' / 'oracle'
    log_path = oracle_root / 'ORACLE_EVENT_LOG.jsonl'
    metadata_path = oracle_root / 'ORACLE_WEEKLY.checkpoint.metadata.json'
    report_path = oracle_root / 'ORACLE_WEEKLY.json'
    checkpoint_manifest = oracle_root / 'ORACLE_EVENT_CHECKPOINT.json'
    checkpoint_verification = oracle_root / 'ORACLE_EVENT_CHECKPOINT.verification.json'
    audit_json = oracle_root / 'ORACLE_REPLAY_AUDIT_REPORT.json'
    audit_md = oracle_root / 'ORACLE_REPLAY_AUDIT_REPORT.md'

    _write_jsonl(
        log_path,
        [
            _event_row(seq=0, entry_id='evidence-0:0', ts=NOW1, prev_hash=None, entry_hash='d' * 64, regime='RISK_ON_LOW_VOL', action='OBSERVE', epistemic='NOMINAL', summary='baseline'),
            _event_row(seq=1, entry_id='evidence-1:1', ts=NOW2, prev_hash='d' * 64, entry_hash='e' * 64, regime='TRANSITION', action='CANARY_REVIEW', epistemic='ELEVATED', summary='watch'),
        ],
    )

    rc = main([
        'oracle-horizon-checkpoint',
        '--repo-root', str(repo_root),
        '--log-path', str(log_path),
        '--horizon', 'weekly',
        '--report-output', str(report_path),
        '--checkpoint-metadata-output', str(metadata_path),
        '--output', str(checkpoint_manifest),
        '--verification-output', str(checkpoint_verification),
    ])
    assert rc == 0

    rc = main([
        'oracle-replay-audit',
        '--log-path', str(log_path),
        '--checkpoint-metadata', str(metadata_path),
        '--checkpoint-manifest', str(checkpoint_manifest),
        '--checkpoint-verification', str(checkpoint_verification),
        '--output', str(audit_json),
        '--markdown-output', str(audit_md),
    ])
    assert rc == 0
    report = json.loads(audit_json.read_text(encoding='utf-8'))
    assert report['schema_version'] == 'oracle_replay_audit_report/v1'
    assert report['replay_status'] == 'CONSISTENT'
    assert report['compared_entry_ids'] == ['evidence-0:0', 'evidence-1:1']
    assert 'Oracle Replay Audit' in audit_md.read_text(encoding='utf-8')

    metadata = json.loads(metadata_path.read_text(encoding='utf-8'))
    metadata['cached_window_entries'][0]['entry_id'] = 'tampered-entry:0'
    metadata_path.write_text(json.dumps(metadata, indent=2), encoding='utf-8')

    rc = main([
        'oracle-replay-audit',
        '--log-path', str(log_path),
        '--checkpoint-metadata', str(metadata_path),
        '--checkpoint-manifest', str(checkpoint_manifest),
        '--checkpoint-verification', str(checkpoint_verification),
        '--output', str(audit_json),
    ])
    assert rc == 2
    report = json.loads(audit_json.read_text(encoding='utf-8'))
    assert report['replay_status'] in {'DRIFTED', 'CORRUPTED'}
    assert any('cached checkpoint window does not match canonical Event Log replay' in finding for finding in report['findings'])


@pytest.mark.constitutional
def test_oracle_compacted_state_rebuild_repairs_tampered_metadata(tmp_path: Path) -> None:
    repo_root = tmp_path
    oracle_root = repo_root / 'docs' / 'artifacts' / 'oracle'
    log_path = oracle_root / 'ORACLE_EVENT_LOG.jsonl'
    metadata_path = oracle_root / 'ORACLE_WEEKLY.checkpoint.metadata.json'
    report_path = oracle_root / 'ORACLE_WEEKLY.json'
    rebuild_json = oracle_root / 'ORACLE_COMPACTED_STATE_REBUILD_REPORT.json'
    rebuild_md = oracle_root / 'ORACLE_COMPACTED_STATE_REBUILD_REPORT.md'

    _write_jsonl(
        log_path,
        [
            _event_row(seq=0, entry_id='evidence-0:0', ts=NOW1, prev_hash=None, entry_hash='1' * 64, regime='RISK_ON_LOW_VOL', action='OBSERVE', epistemic='NOMINAL', summary='baseline'),
            _event_row(seq=1, entry_id='evidence-1:1', ts=NOW2, prev_hash='1' * 64, entry_hash='2' * 64, regime='TRANSITION', action='CANARY_REVIEW', epistemic='ELEVATED', summary='watch'),
            _event_row(seq=2, entry_id='evidence-2:2', ts=NOW3, prev_hash='2' * 64, entry_hash='3' * 64, regime='RISK_OFF_HIGH_VOL', action='DEFENSIVE_POSTURE', epistemic='UNKNOWN_UNKNOWNS', summary='defensive'),
        ],
    )

    rc = main([
        'oracle-rolling-review',
        '--log-path', str(log_path),
        '--horizon', 'weekly',
        '--window-size', '2',
        '--output', str(report_path),
        '--checkpoint-metadata-output', str(metadata_path),
    ])
    assert rc == 0

    metadata = json.loads(metadata_path.read_text(encoding='utf-8'))
    metadata['source_event_log_path'] = str((repo_root / 'wrong.jsonl').resolve())
    metadata['cached_window_entries'][0]['entry_id'] = 'tampered-entry:0'
    metadata_path.write_text(json.dumps(metadata, indent=2), encoding='utf-8')

    rc = main([
        'oracle-compacted-state-rebuild',
        '--log-path', str(log_path),
        '--checkpoint-metadata', str(metadata_path),
        '--output', str(rebuild_json),
        '--markdown-output', str(rebuild_md),
    ])
    assert rc == 0
    report = json.loads(rebuild_json.read_text(encoding='utf-8'))
    assert report['schema_version'] == 'oracle_compacted_state_rebuild_report/v1'
    assert report['previous_replay_status'] == 'CORRUPTED'
    assert report['rebuilt_entry_ids'] == ['evidence-1:1', 'evidence-2:2']
    assert len(report['compacted_window_digest_sha256']) == 64
    rebuilt_metadata = json.loads(metadata_path.read_text(encoding='utf-8'))
    assert rebuilt_metadata['source_event_log_path'] == str(log_path.resolve())
    rebuilt_ids = [row['entry_id'] for row in rebuilt_metadata['cached_window_entries']]
    assert rebuilt_ids == ['evidence-1:1', 'evidence-2:2']
    assert 'Oracle Compacted State Rebuild' in rebuild_md.read_text(encoding='utf-8')


@pytest.mark.constitutional
def test_oracle_replay_audit_rebuild_parity_detects_derived_report_drift(tmp_path: Path) -> None:
    repo_root = tmp_path
    oracle_root = repo_root / 'docs' / 'artifacts' / 'oracle'
    log_path = oracle_root / 'ORACLE_EVENT_LOG.jsonl'
    metadata_path = oracle_root / 'ORACLE_WEEKLY.checkpoint.metadata.json'
    report_path = oracle_root / 'ORACLE_WEEKLY_DERIVED_VIEW.json'
    checkpoint_manifest = oracle_root / 'ORACLE_EVENT_CHECKPOINT.json'
    checkpoint_verification = oracle_root / 'ORACLE_EVENT_CHECKPOINT.verification.json'
    audit_json = oracle_root / 'ORACLE_REPLAY_AUDIT_REPORT.json'

    _write_jsonl(
        log_path,
        [
            _event_row(seq=0, entry_id='evidence-0:0', ts=NOW1, prev_hash=None, entry_hash='4' * 64, regime='RISK_ON_LOW_VOL', action='OBSERVE', epistemic='NOMINAL', summary='baseline'),
            _event_row(seq=1, entry_id='evidence-1:1', ts=NOW2, prev_hash='4' * 64, entry_hash='5' * 64, regime='TRANSITION', action='CANARY_REVIEW', epistemic='ELEVATED', summary='watch'),
            _event_row(seq=2, entry_id='evidence-2:2', ts=NOW3, prev_hash='5' * 64, entry_hash='6' * 64, regime='TRANSITION', action='CANARY_REVIEW', epistemic='ELEVATED', summary='steady watch'),
        ],
    )

    rc = main([
        'oracle-horizon-checkpoint',
        '--repo-root', str(repo_root),
        '--log-path', str(log_path),
        '--horizon', 'weekly',
        '--window-size', '2',
        '--report-output', str(report_path),
        '--checkpoint-metadata-output', str(metadata_path),
        '--output', str(checkpoint_manifest),
        '--verification-output', str(checkpoint_verification),
    ])
    assert rc == 0

    rc = main([
        'oracle-replay-audit',
        '--log-path', str(log_path),
        '--checkpoint-metadata', str(metadata_path),
        '--checkpoint-manifest', str(checkpoint_manifest),
        '--checkpoint-verification', str(checkpoint_verification),
        '--rebuild-parity',
        '--output', str(audit_json),
    ])
    assert rc == 0
    report = json.loads(audit_json.read_text(encoding='utf-8'))
    source_status = {item['source_id']: item['status'] for item in report['sources']}
    assert source_status['rebuilt_checkpoint_metadata'] == 'CONSISTENT'
    assert source_status['derived_view_report'] == 'CONSISTENT'
    assert len(report['rebuilt_window_digest_sha256']) == 64

    derived = json.loads(report_path.read_text(encoding='utf-8'))
    derived['summary_line'] = 'tampered summary line'
    report_path.write_text(json.dumps(derived, indent=2), encoding='utf-8')

    rc = main([
        'oracle-replay-audit',
        '--log-path', str(log_path),
        '--checkpoint-metadata', str(metadata_path),
        '--checkpoint-manifest', str(checkpoint_manifest),
        '--checkpoint-verification', str(checkpoint_verification),
        '--rebuild-parity',
        '--output', str(audit_json),
    ])
    assert rc == 2
    report = json.loads(audit_json.read_text(encoding='utf-8'))
    source_status = {item['source_id']: item['status'] for item in report['sources']}
    assert source_status['rebuilt_checkpoint_metadata'] == 'CONSISTENT'
    assert source_status['derived_view_report'] == 'DRIFTED'
    assert any('derived view report does not match deterministic replay' in finding for finding in report['findings'])
