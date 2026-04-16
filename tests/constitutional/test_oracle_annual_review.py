from __future__ import annotations

import json
from pathlib import Path

import pytest

from strategy_validator.cli.rollout_ops import main
from strategy_validator.validator.rollout_ops import generate_snapshot_signing_keypair


def _write_quarterly_lane(path: Path, entries: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', encoding='utf-8') as handle:
        for entry in entries:
            handle.write(json.dumps(entry) + '\n')


@pytest.mark.constitutional
def test_oracle_semiannual_evidence_lane_and_annual_review_round_trip(tmp_path: Path) -> None:
    repo_root = tmp_path
    private_key = repo_root / 'oracle_private.pem'
    public_key = repo_root / 'oracle_public.pem'
    generate_snapshot_signing_keypair(private_key_path=private_key, public_key_path=public_key)

    quarterly_lane = repo_root / 'docs' / 'artifacts' / 'oracle' / 'ORACLE_QUARTERLY_LANE.jsonl'
    _write_quarterly_lane(quarterly_lane, [
        {
            'schema_version': 'oracle_quarterly_lane_entry/v1',
            'appended_at_utc': '2026-01-13T08:00:00Z',
            'lane_id': 'ORACLE_QUARTERLY_LANE',
            'sequence_number': 0,
            'entry_id': 'quarter-entry-0',
            'quarterly_review_id': 'quarter-0',
            'previous_entry_hash': None,
            'entry_hash': 'hash-0',
            'manifest_path': 'quarter0/ORACLE_QUARTERLY_REVIEW_EVIDENCE.json',
            'manifest_sha256': 'a' * 64,
            'quarterly_review_classification': 'QUARTERLY_REPAIR_STRUCTURAL',
            'latest_monthly_digest_id': 'month-0',
            'evidence_status': 'VERIFIED',
            'summary_line': 'repair structural quarter 0',
        },
        {
            'schema_version': 'oracle_quarterly_lane_entry/v1',
            'appended_at_utc': '2026-04-13T08:00:00Z',
            'lane_id': 'ORACLE_QUARTERLY_LANE',
            'sequence_number': 1,
            'entry_id': 'quarter-entry-1',
            'quarterly_review_id': 'quarter-1',
            'previous_entry_hash': 'hash-0',
            'entry_hash': 'hash-1',
            'manifest_path': 'quarter1/ORACLE_QUARTERLY_REVIEW_EVIDENCE.json',
            'manifest_sha256': 'b' * 64,
            'quarterly_review_classification': 'QUARTERLY_REPAIR_STRUCTURAL',
            'latest_monthly_digest_id': 'month-1',
            'evidence_status': 'VERIFIED',
            'summary_line': 'repair structural quarter 1',
        },
        {
            'schema_version': 'oracle_quarterly_lane_entry/v1',
            'appended_at_utc': '2026-07-13T08:00:00Z',
            'lane_id': 'ORACLE_QUARTERLY_LANE',
            'sequence_number': 2,
            'entry_id': 'quarter-entry-2',
            'quarterly_review_id': 'quarter-2',
            'previous_entry_hash': 'hash-1',
            'entry_hash': 'hash-2',
            'manifest_path': 'quarter2/ORACLE_QUARTERLY_REVIEW_EVIDENCE.json',
            'manifest_sha256': 'c' * 64,
            'quarterly_review_classification': 'QUARTERLY_REPAIR_STRUCTURAL',
            'latest_monthly_digest_id': 'month-2',
            'evidence_status': 'VERIFIED',
            'summary_line': 'repair structural quarter 2',
        },
        {
            'schema_version': 'oracle_quarterly_lane_entry/v1',
            'appended_at_utc': '2026-10-13T08:00:00Z',
            'lane_id': 'ORACLE_QUARTERLY_LANE',
            'sequence_number': 3,
            'entry_id': 'quarter-entry-3',
            'quarterly_review_id': 'quarter-3',
            'previous_entry_hash': 'hash-2',
            'entry_hash': 'hash-3',
            'manifest_path': 'quarter3/ORACLE_QUARTERLY_REVIEW_EVIDENCE.json',
            'manifest_sha256': 'd' * 64,
            'quarterly_review_classification': 'QUARTERLY_REPAIR_STRUCTURAL',
            'latest_monthly_digest_id': 'month-3',
            'evidence_status': 'VERIFIED',
            'summary_line': 'repair structural quarter 3',
        },
    ])

    semiannual_lane = repo_root / 'docs' / 'artifacts' / 'oracle' / 'ORACLE_SEMIANNUAL_LANE.jsonl'
    for idx in range(2):
        manifest = repo_root / f'semiannual{idx}' / 'ORACLE_SEMIANNUAL_AUDIT_EVIDENCE.json'
        manifest.parent.mkdir(parents=True, exist_ok=True)
        dsse = manifest.with_name('ORACLE_SEMIANNUAL_AUDIT_EVIDENCE.dsse.json')
        verification = manifest.with_name('ORACLE_SEMIANNUAL_AUDIT_EVIDENCE.verification.json')
        report = manifest.with_name('ORACLE_SEMIANNUAL_AUDIT.json')
        markdown = manifest.with_name('ORACLE_SEMIANNUAL_AUDIT.md')
        rc = main([
            'oracle-semiannual-audit-evidence',
            '--lane-path', str(quarterly_lane),
        '--allow-legacy-lane-read',
            '--repo-root', str(repo_root),
            '--window-size', '2',
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
            'oracle-semiannual-lane-append',
            str(manifest),
            '--repo-root', str(repo_root),
            '--dsse', str(dsse),
            '--public-key', str(public_key),
            '--lane-path', str(semiannual_lane),
        ])
        assert rc == 0

    annual_output = semiannual_lane.with_name('ORACLE_ANNUAL_REVIEW.json')
    annual_markdown = semiannual_lane.with_name('ORACLE_ANNUAL_REVIEW.md')
    rc = main([
        'oracle-annual-review',
        '--lane-path', str(semiannual_lane),
        '--allow-legacy-lane-read',
        '--window-size', '2',
        '--output', str(annual_output),
        '--markdown-output', str(annual_markdown),
    ])
    assert rc == 0
    report = json.loads(annual_output.read_text(encoding='utf-8'))
    assert report['annual_review_classification'] == 'ANNUAL_REPAIR_STRUCTURAL'
    assert report['semiannual_classification_counts']['SEMIANNUAL_REPAIR_STRUCTURAL'] >= 2
    assert 'ORACLE ANNUAL REVIEW' in annual_markdown.read_text(encoding='utf-8')


@pytest.mark.constitutional
def test_oracle_semiannual_lane_append_rejects_incomplete_semiannual_evidence(tmp_path: Path) -> None:
    repo_root = tmp_path
    private_key = repo_root / 'oracle_private.pem'
    public_key = repo_root / 'oracle_public.pem'
    generate_snapshot_signing_keypair(private_key_path=private_key, public_key_path=public_key)

    quarterly_lane = repo_root / 'docs' / 'artifacts' / 'oracle' / 'ORACLE_QUARTERLY_LANE.jsonl'
    _write_quarterly_lane(quarterly_lane, [
        {
            'schema_version': 'oracle_quarterly_lane_entry/v1',
            'appended_at_utc': '2026-01-13T08:00:00Z',
            'lane_id': 'ORACLE_QUARTERLY_LANE',
            'sequence_number': 0,
            'entry_id': 'quarter-entry-0',
            'quarterly_review_id': 'quarter-0',
            'previous_entry_hash': None,
            'entry_hash': 'hash-0',
            'manifest_path': 'quarter0/ORACLE_QUARTERLY_REVIEW_EVIDENCE.json',
            'manifest_sha256': 'a' * 64,
            'quarterly_review_classification': 'QUARTERLY_EVIDENCE_GAP',
            'latest_monthly_digest_id': 'month-0',
            'evidence_status': 'INCOMPLETE',
            'summary_line': 'quarterly evidence gap',
        },
    ])

    manifest = repo_root / 'semiannual' / 'ORACLE_SEMIANNUAL_AUDIT_EVIDENCE.json'
    manifest.parent.mkdir(parents=True, exist_ok=True)
    dsse = manifest.with_name('ORACLE_SEMIANNUAL_AUDIT_EVIDENCE.dsse.json')
    verification = manifest.with_name('ORACLE_SEMIANNUAL_AUDIT_EVIDENCE.verification.json')
    report = manifest.with_name('ORACLE_SEMIANNUAL_AUDIT.json')
    markdown = manifest.with_name('ORACLE_SEMIANNUAL_AUDIT.md')
    rc = main([
        'oracle-semiannual-audit-evidence',
        '--lane-path', str(quarterly_lane),
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

    semiannual_lane = repo_root / 'docs' / 'artifacts' / 'oracle' / 'ORACLE_SEMIANNUAL_LANE.jsonl'
    rc = main([
        'oracle-semiannual-lane-append',
        str(manifest),
        '--repo-root', str(repo_root),
        '--lane-path', str(semiannual_lane),
    ])
    assert rc == 2
    assert not semiannual_lane.exists()
