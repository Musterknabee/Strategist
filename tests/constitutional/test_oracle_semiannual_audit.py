from __future__ import annotations

import json
from pathlib import Path

import pytest

from strategy_validator.cli.rollout_ops import main
from strategy_validator.validator.rollout_ops import generate_snapshot_signing_keypair


def _write_monthly_lane(path: Path, entries: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', encoding='utf-8') as handle:
        for entry in entries:
            handle.write(json.dumps(entry) + '\n')


@pytest.mark.constitutional
def test_oracle_quarterly_review_evidence_lane_and_semiannual_audit_round_trip(tmp_path: Path) -> None:
    repo_root = tmp_path
    private_key = repo_root / 'oracle_private.pem'
    public_key = repo_root / 'oracle_public.pem'
    generate_snapshot_signing_keypair(private_key_path=private_key, public_key_path=public_key)

    monthly_lane = repo_root / 'docs' / 'artifacts' / 'oracle' / 'ORACLE_MONTHLY_LANE.jsonl'
    _write_monthly_lane(monthly_lane, [
        {
            'schema_version': 'oracle_monthly_lane_entry/v1',
            'appended_at_utc': '2026-01-13T08:00:00Z',
            'lane_id': 'ORACLE_MONTHLY_LANE',
            'sequence_number': 0,
            'entry_id': 'entry-0',
            'monthly_digest_id': 'month-0',
            'previous_entry_hash': None,
            'entry_hash': 'hash-0',
            'manifest_path': 'month0/ORACLE_MONTHLY_DIGEST_EVIDENCE.json',
            'manifest_sha256': 'a' * 64,
            'doctrine_memory_classification': 'DOCTRINE_REPAIR_PERSISTENT',
            'latest_drift_classification': 'RECURRING_REPAIR',
            'evidence_status': 'VERIFIED',
            'summary_line': 'repair persisted in month 0',
        },
        {
            'schema_version': 'oracle_monthly_lane_entry/v1',
            'appended_at_utc': '2026-02-13T08:00:00Z',
            'lane_id': 'ORACLE_MONTHLY_LANE',
            'sequence_number': 1,
            'entry_id': 'entry-1',
            'monthly_digest_id': 'month-1',
            'previous_entry_hash': 'hash-0',
            'entry_hash': 'hash-1',
            'manifest_path': 'month1/ORACLE_MONTHLY_DIGEST_EVIDENCE.json',
            'manifest_sha256': 'b' * 64,
            'doctrine_memory_classification': 'DOCTRINE_REPAIR_PERSISTENT',
            'latest_drift_classification': 'RECURRING_REPAIR',
            'evidence_status': 'VERIFIED',
            'summary_line': 'repair persisted in month 1',
        },
        {
            'schema_version': 'oracle_monthly_lane_entry/v1',
            'appended_at_utc': '2026-03-13T08:00:00Z',
            'lane_id': 'ORACLE_MONTHLY_LANE',
            'sequence_number': 2,
            'entry_id': 'entry-2',
            'monthly_digest_id': 'month-2',
            'previous_entry_hash': 'hash-1',
            'entry_hash': 'hash-2',
            'manifest_path': 'month2/ORACLE_MONTHLY_DIGEST_EVIDENCE.json',
            'manifest_sha256': 'c' * 64,
            'doctrine_memory_classification': 'DOCTRINE_REPAIR_PERSISTENT',
            'latest_drift_classification': 'RECURRING_REPAIR',
            'evidence_status': 'VERIFIED',
            'summary_line': 'repair persisted in month 2',
        },
        {
            'schema_version': 'oracle_monthly_lane_entry/v1',
            'appended_at_utc': '2026-04-13T08:00:00Z',
            'lane_id': 'ORACLE_MONTHLY_LANE',
            'sequence_number': 3,
            'entry_id': 'entry-3',
            'monthly_digest_id': 'month-3',
            'previous_entry_hash': 'hash-2',
            'entry_hash': 'hash-3',
            'manifest_path': 'month3/ORACLE_MONTHLY_DIGEST_EVIDENCE.json',
            'manifest_sha256': 'd' * 64,
            'doctrine_memory_classification': 'DOCTRINE_REPAIR_PERSISTENT',
            'latest_drift_classification': 'RECURRING_REPAIR',
            'evidence_status': 'VERIFIED',
            'summary_line': 'repair persisted in month 3',
        },
        {
            'schema_version': 'oracle_monthly_lane_entry/v1',
            'appended_at_utc': '2026-05-13T08:00:00Z',
            'lane_id': 'ORACLE_MONTHLY_LANE',
            'sequence_number': 4,
            'entry_id': 'entry-4',
            'monthly_digest_id': 'month-4',
            'previous_entry_hash': 'hash-3',
            'entry_hash': 'hash-4',
            'manifest_path': 'month4/ORACLE_MONTHLY_DIGEST_EVIDENCE.json',
            'manifest_sha256': 'e' * 64,
            'doctrine_memory_classification': 'DOCTRINE_REPAIR_PERSISTENT',
            'latest_drift_classification': 'RECURRING_REPAIR',
            'evidence_status': 'VERIFIED',
            'summary_line': 'repair persisted in month 4',
        },
        {
            'schema_version': 'oracle_monthly_lane_entry/v1',
            'appended_at_utc': '2026-06-13T08:00:00Z',
            'lane_id': 'ORACLE_MONTHLY_LANE',
            'sequence_number': 5,
            'entry_id': 'entry-5',
            'monthly_digest_id': 'month-5',
            'previous_entry_hash': 'hash-4',
            'entry_hash': 'hash-5',
            'manifest_path': 'month5/ORACLE_MONTHLY_DIGEST_EVIDENCE.json',
            'manifest_sha256': 'f' * 64,
            'doctrine_memory_classification': 'DOCTRINE_REPAIR_PERSISTENT',
            'latest_drift_classification': 'RECURRING_REPAIR',
            'evidence_status': 'VERIFIED',
            'summary_line': 'repair persisted in month 5',
        },
    ])

    quarterly_lane = repo_root / 'docs' / 'artifacts' / 'oracle' / 'ORACLE_QUARTERLY_LANE.jsonl'
    for quarter in (3, 4, 5, 6):
        manifest = repo_root / f'quarter{quarter}' / 'ORACLE_QUARTERLY_REVIEW_EVIDENCE.json'
        manifest.parent.mkdir(parents=True, exist_ok=True)
        dsse = manifest.with_name('ORACLE_QUARTERLY_REVIEW_EVIDENCE.dsse.json')
        verification = manifest.with_name('ORACLE_QUARTERLY_REVIEW_EVIDENCE.verification.json')
        report = manifest.with_name('ORACLE_QUARTERLY_REVIEW.json')
        markdown = manifest.with_name('ORACLE_QUARTERLY_REVIEW.md')
        rc = main([
            'oracle-quarterly-review-evidence',
            '--lane-path', str(monthly_lane),
        '--allow-legacy-lane-read',
            '--repo-root', str(repo_root),
            '--window-size', str(quarter if quarter <= 3 else 3),
            '--signing-private-key', str(private_key),
            '--public-key', str(public_key),
            '--report-output', str(report),
            '--markdown-output', str(markdown),
            '--output', str(manifest),
            '--dsse-output', str(dsse),
            '--verification-output', str(verification),
        ])
        assert rc == 0
        rc = main([
            'oracle-quarterly-lane-append',
            str(manifest),
            '--repo-root', str(repo_root),
            '--dsse', str(dsse),
            '--public-key', str(public_key),
            '--lane-path', str(quarterly_lane),
        ])
        assert rc == 0

    semiannual_output = quarterly_lane.with_name('ORACLE_SEMIANNUAL_AUDIT.json')
    semiannual_markdown = quarterly_lane.with_name('ORACLE_SEMIANNUAL_AUDIT.md')
    rc = main([
        'oracle-semiannual-audit',
        '--lane-path', str(quarterly_lane),
        '--allow-legacy-lane-read',
        '--window-size', '2',
        '--output', str(semiannual_output),
        '--markdown-output', str(semiannual_markdown),
    ])
    assert rc == 0
    report = json.loads(semiannual_output.read_text(encoding='utf-8'))
    assert report['semiannual_audit_classification'] == 'SEMIANNUAL_REPAIR_STRUCTURAL'
    assert report['quarterly_classification_counts']['QUARTERLY_REPAIR_STRUCTURAL'] >= 2
    assert 'ORACLE SEMIANNUAL AUDIT' in semiannual_markdown.read_text(encoding='utf-8')


@pytest.mark.constitutional
def test_oracle_quarterly_lane_append_rejects_incomplete_quarterly_evidence(tmp_path: Path) -> None:
    repo_root = tmp_path
    private_key = repo_root / 'oracle_private.pem'
    public_key = repo_root / 'oracle_public.pem'
    generate_snapshot_signing_keypair(private_key_path=private_key, public_key_path=public_key)

    monthly_lane = repo_root / 'docs' / 'artifacts' / 'oracle' / 'ORACLE_MONTHLY_LANE.jsonl'
    _write_monthly_lane(monthly_lane, [
        {
            'schema_version': 'oracle_monthly_lane_entry/v1',
            'appended_at_utc': '2026-01-13T08:00:00Z',
            'lane_id': 'ORACLE_MONTHLY_LANE',
            'sequence_number': 0,
            'entry_id': 'entry-0',
            'monthly_digest_id': 'month-0',
            'previous_entry_hash': None,
            'entry_hash': 'hash-0',
            'manifest_path': 'month0/ORACLE_MONTHLY_DIGEST_EVIDENCE.json',
            'manifest_sha256': 'a' * 64,
            'doctrine_memory_classification': 'DOCTRINE_EVIDENCE_GAP',
            'latest_drift_classification': 'DOCTRINE_EVIDENCE_GAP',
            'evidence_status': 'INCOMPLETE',
            'summary_line': 'monthly evidence gap',
        },
    ])

    manifest = repo_root / 'quarter' / 'ORACLE_QUARTERLY_REVIEW_EVIDENCE.json'
    manifest.parent.mkdir(parents=True, exist_ok=True)
    dsse = manifest.with_name('ORACLE_QUARTERLY_REVIEW_EVIDENCE.dsse.json')
    verification = manifest.with_name('ORACLE_QUARTERLY_REVIEW_EVIDENCE.verification.json')
    report = manifest.with_name('ORACLE_QUARTERLY_REVIEW.json')
    markdown = manifest.with_name('ORACLE_QUARTERLY_REVIEW.md')
    rc = main([
        'oracle-quarterly-review-evidence',
        '--lane-path', str(monthly_lane),
        '--allow-legacy-lane-read',
        '--repo-root', str(repo_root),
        '--window-size', '1',
        '--signing-private-key', str(private_key),
        '--public-key', str(public_key),
        '--report-output', str(report),
        '--markdown-output', str(markdown),
        '--output', str(manifest),
        '--dsse-output', str(dsse),
        '--verification-output', str(verification),
    ])
    assert rc == 0

    evidence = json.loads(manifest.read_text(encoding='utf-8'))
    evidence['subjects'] = evidence['subjects'][:-1]
    evidence['missing_artifact_paths'] = [str(markdown)]
    manifest.write_text(json.dumps(evidence, indent=2), encoding='utf-8')

    quarterly_lane = repo_root / 'docs' / 'artifacts' / 'oracle' / 'ORACLE_QUARTERLY_LANE.jsonl'
    rc = main([
        'oracle-quarterly-lane-append',
        str(manifest),
        '--repo-root', str(repo_root),
        '--lane-path', str(quarterly_lane),
    ])
    assert rc == 2
    assert not quarterly_lane.exists()
