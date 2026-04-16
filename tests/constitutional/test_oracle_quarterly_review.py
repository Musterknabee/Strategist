from __future__ import annotations

import json
from pathlib import Path

import pytest

from strategy_validator.cli.rollout_ops import main
from strategy_validator.validator.rollout_ops import generate_snapshot_signing_keypair


def _write_doctrine_lane(path: Path, entries: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', encoding='utf-8') as handle:
        for entry in entries:
            handle.write(json.dumps(entry) + '\n')


@pytest.mark.constitutional
def test_oracle_monthly_digest_evidence_lane_and_quarterly_review_round_trip(tmp_path: Path) -> None:
    repo_root = tmp_path
    private_key = repo_root / 'oracle_private.pem'
    public_key = repo_root / 'oracle_public.pem'
    generate_snapshot_signing_keypair(private_key_path=private_key, public_key_path=public_key)

    doctrine_lane = repo_root / 'docs' / 'artifacts' / 'oracle' / 'ORACLE_DOCTRINE_LANE.jsonl'
    _write_doctrine_lane(doctrine_lane, [
        {
            'schema_version': 'oracle_doctrine_lane_entry/v1',
            'appended_at_utc': '2026-04-13T08:00:00Z',
            'lane_id': 'ORACLE_DOCTRINE_LANE',
            'sequence_number': 0,
            'entry_id': 'entry-0',
            'drift_id': 'drift-0',
            'previous_entry_hash': None,
            'entry_hash': 'hash-0',
            'manifest_path': 'week1/ORACLE_DOCTRINE_DRIFT_EVIDENCE.json',
            'manifest_sha256': 'a' * 64,
            'drift_classification': 'DOCTRINE_ESCALATION',
            'drift_level': 'MATERIAL',
            'current_doctrine_posture': 'HEIGHTENED_RESEARCH_POSTURE',
            'evidence_status': 'VERIFIED',
            'summary_line': 'heightened doctrine drift',
        },
        {
            'schema_version': 'oracle_doctrine_lane_entry/v1',
            'appended_at_utc': '2026-05-13T08:00:00Z',
            'lane_id': 'ORACLE_DOCTRINE_LANE',
            'sequence_number': 1,
            'entry_id': 'entry-1',
            'drift_id': 'drift-1',
            'previous_entry_hash': 'hash-0',
            'entry_hash': 'hash-1',
            'manifest_path': 'week2/ORACLE_DOCTRINE_DRIFT_EVIDENCE.json',
            'manifest_sha256': 'b' * 64,
            'drift_classification': 'RECURRING_REPAIR',
            'drift_level': 'SEVERE',
            'current_doctrine_posture': 'REPAIR_FIRST',
            'evidence_status': 'VERIFIED',
            'summary_line': 'repair doctrine drift',
        },
        {
            'schema_version': 'oracle_doctrine_lane_entry/v1',
            'appended_at_utc': '2026-06-13T08:00:00Z',
            'lane_id': 'ORACLE_DOCTRINE_LANE',
            'sequence_number': 2,
            'entry_id': 'entry-2',
            'drift_id': 'drift-2',
            'previous_entry_hash': 'hash-1',
            'entry_hash': 'hash-2',
            'manifest_path': 'week3/ORACLE_DOCTRINE_DRIFT_EVIDENCE.json',
            'manifest_sha256': 'c' * 64,
            'drift_classification': 'RECURRING_REPAIR',
            'drift_level': 'SEVERE',
            'current_doctrine_posture': 'REPAIR_FIRST',
            'evidence_status': 'VERIFIED',
            'summary_line': 'repair doctrine drift persisted',
        },
    ])

    monthly_lane = repo_root / 'docs' / 'artifacts' / 'oracle' / 'ORACLE_MONTHLY_LANE.jsonl'
    for month in (1, 2, 3):
        manifest = repo_root / f'month{month}' / 'ORACLE_MONTHLY_DIGEST_EVIDENCE.json'
        manifest.parent.mkdir(parents=True, exist_ok=True)
        dsse = manifest.with_name('ORACLE_MONTHLY_DIGEST_EVIDENCE.dsse.json')
        verification = manifest.with_name('ORACLE_MONTHLY_DIGEST_EVIDENCE.verification.json')
        digest = manifest.with_name('ORACLE_MONTHLY_DIGEST.json')
        markdown = manifest.with_name('ORACLE_MONTHLY_DIGEST.md')
        rc = main([
            'oracle-monthly-digest-evidence',
            '--lane-path', str(doctrine_lane),
        '--allow-legacy-lane-read',
            '--repo-root', str(repo_root),
            '--window-size', str(month),
            '--signing-private-key', str(private_key),
            '--public-key', str(public_key),
            '--report-output', str(digest),
            '--markdown-output', str(markdown),
            '--output', str(manifest),
            '--dsse-output', str(dsse),
            '--verification-output', str(verification),
        ])
        assert rc == 0
        rc = main([
            'oracle-monthly-lane-append',
            str(manifest),
            '--repo-root', str(repo_root),
            '--dsse', str(dsse),
            '--public-key', str(public_key),
            '--lane-path', str(monthly_lane),
        ])
        assert rc == 0

    quarterly_output = monthly_lane.with_name('ORACLE_QUARTERLY_REVIEW.json')
    quarterly_markdown = monthly_lane.with_name('ORACLE_QUARTERLY_REVIEW.md')
    rc = main([
        'oracle-quarterly-review',
        '--lane-path', str(monthly_lane),
        '--allow-legacy-lane-read',
        '--window-size', '3',
        '--output', str(quarterly_output),
        '--markdown-output', str(quarterly_markdown),
    ])
    assert rc == 0
    report = json.loads(quarterly_output.read_text(encoding='utf-8'))
    assert report['quarterly_review_classification'] == 'QUARTERLY_REPAIR_STRUCTURAL'
    assert report['monthly_classification_counts']['DOCTRINE_REPAIR_PERSISTENT'] >= 2
    assert 'ORACLE QUARTERLY REVIEW' in quarterly_markdown.read_text(encoding='utf-8')


@pytest.mark.constitutional
def test_oracle_monthly_lane_append_rejects_incomplete_monthly_evidence(tmp_path: Path) -> None:
    repo_root = tmp_path
    private_key = repo_root / 'oracle_private.pem'
    public_key = repo_root / 'oracle_public.pem'
    generate_snapshot_signing_keypair(private_key_path=private_key, public_key_path=public_key)

    doctrine_lane = repo_root / 'docs' / 'artifacts' / 'oracle' / 'ORACLE_DOCTRINE_LANE.jsonl'
    _write_doctrine_lane(doctrine_lane, [
        {
            'schema_version': 'oracle_doctrine_lane_entry/v1',
            'appended_at_utc': '2026-04-13T08:00:00Z',
            'lane_id': 'ORACLE_DOCTRINE_LANE',
            'sequence_number': 0,
            'entry_id': 'entry-0',
            'drift_id': 'drift-0',
            'previous_entry_hash': None,
            'entry_hash': 'hash-0',
            'manifest_path': 'week1/ORACLE_DOCTRINE_DRIFT_EVIDENCE.json',
            'manifest_sha256': 'a' * 64,
            'drift_classification': 'DOCTRINE_EVIDENCE_GAP',
            'drift_level': 'SEVERE',
            'current_doctrine_posture': 'REPAIR_FIRST',
            'evidence_status': 'INCOMPLETE',
            'summary_line': 'incomplete doctrine drift',
        },
    ])

    manifest = repo_root / 'month' / 'ORACLE_MONTHLY_DIGEST_EVIDENCE.json'
    manifest.parent.mkdir(parents=True, exist_ok=True)
    dsse = manifest.with_name('ORACLE_MONTHLY_DIGEST_EVIDENCE.dsse.json')
    verification = manifest.with_name('ORACLE_MONTHLY_DIGEST_EVIDENCE.verification.json')
    digest = manifest.with_name('ORACLE_MONTHLY_DIGEST.json')
    markdown = manifest.with_name('ORACLE_MONTHLY_DIGEST.md')
    rc = main([
        'oracle-monthly-digest-evidence',
        '--lane-path', str(doctrine_lane),
        '--allow-legacy-lane-read',
        '--repo-root', str(repo_root),
        '--window-size', '1',
        '--signing-private-key', str(private_key),
        '--public-key', str(public_key),
        '--report-output', str(digest),
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

    monthly_lane = repo_root / 'docs' / 'artifacts' / 'oracle' / 'ORACLE_MONTHLY_LANE.jsonl'
    rc = main([
        'oracle-monthly-lane-append',
        str(manifest),
        '--repo-root', str(repo_root),
        '--lane-path', str(monthly_lane),
    ])
    assert rc == 2
    assert not monthly_lane.exists()
