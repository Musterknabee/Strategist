from __future__ import annotations

import json
from pathlib import Path

import pytest

from strategy_validator.cli.rollout_ops import main
from strategy_validator.validator.rollout_ops import generate_snapshot_signing_keypair


def _write_annual_lane(path: Path, entries: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', encoding='utf-8') as handle:
        for entry in entries:
            handle.write(json.dumps(entry) + '\n')


@pytest.mark.constitutional
def test_oracle_constitutional_evidence_lane_and_lineage_index_round_trip(tmp_path: Path) -> None:
    repo_root = tmp_path
    private_key = repo_root / 'oracle_private.pem'
    public_key = repo_root / 'oracle_public.pem'
    generate_snapshot_signing_keypair(private_key_path=private_key, public_key_path=public_key)

    annual_lane = repo_root / 'docs' / 'artifacts' / 'oracle' / 'ORACLE_ANNUAL_LANE.jsonl'
    _write_annual_lane(annual_lane, [
        {
            'schema_version': 'oracle_annual_lane_entry/v1',
            'appended_at_utc': '2024-01-13T08:00:00Z',
            'lane_id': 'ORACLE_ANNUAL_LANE',
            'sequence_number': 0,
            'entry_id': 'annual-entry-0',
            'annual_review_id': 'annual-0',
            'previous_entry_hash': None,
            'entry_hash': 'hash-0',
            'manifest_path': 'annual0/ORACLE_ANNUAL_REVIEW_EVIDENCE.json',
            'manifest_sha256': 'a' * 64,
            'annual_review_classification': 'ANNUAL_REPAIR_STRUCTURAL',
            'latest_semiannual_audit_id': 'semi-0',
            'evidence_status': 'VERIFIED',
            'summary_line': 'annual repair structural 0',
        },
        {
            'schema_version': 'oracle_annual_lane_entry/v1',
            'appended_at_utc': '2025-01-13T08:00:00Z',
            'lane_id': 'ORACLE_ANNUAL_LANE',
            'sequence_number': 1,
            'entry_id': 'annual-entry-1',
            'annual_review_id': 'annual-1',
            'previous_entry_hash': 'hash-0',
            'entry_hash': 'hash-1',
            'manifest_path': 'annual1/ORACLE_ANNUAL_REVIEW_EVIDENCE.json',
            'manifest_sha256': 'b' * 64,
            'annual_review_classification': 'ANNUAL_REPAIR_STRUCTURAL',
            'latest_semiannual_audit_id': 'semi-1',
            'evidence_status': 'VERIFIED',
            'summary_line': 'annual repair structural 1',
        },
        {
            'schema_version': 'oracle_annual_lane_entry/v1',
            'appended_at_utc': '2026-01-13T08:00:00Z',
            'lane_id': 'ORACLE_ANNUAL_LANE',
            'sequence_number': 2,
            'entry_id': 'annual-entry-2',
            'annual_review_id': 'annual-2',
            'previous_entry_hash': 'hash-1',
            'entry_hash': 'hash-2',
            'manifest_path': 'annual2/ORACLE_ANNUAL_REVIEW_EVIDENCE.json',
            'manifest_sha256': 'c' * 64,
            'annual_review_classification': 'ANNUAL_REPAIR_STRUCTURAL',
            'latest_semiannual_audit_id': 'semi-2',
            'evidence_status': 'VERIFIED',
            'summary_line': 'annual repair structural 2',
        },
    ])

    closure_dir = repo_root / 'docs' / 'artifacts' / 'final_rollout_closure'
    closure_dir.mkdir(parents=True, exist_ok=True)
    (closure_dir / 'CLOSURE_SNAPSHOT.json').write_text('{}', encoding='utf-8')
    (closure_dir / 'GOVERNED_EXCEPTION_MEMO.json').write_text('{}', encoding='utf-8')

    manifest = repo_root / 'docs' / 'artifacts' / 'oracle' / 'ORACLE_CONSTITUTIONAL_DIGEST_EVIDENCE.json'
    dsse = manifest.with_name('ORACLE_CONSTITUTIONAL_DIGEST_EVIDENCE.dsse.json')
    verification = manifest.with_name('ORACLE_CONSTITUTIONAL_DIGEST_EVIDENCE.verification.json')
    report = manifest.with_name('ORACLE_CONSTITUTIONAL_DIGEST.json')
    markdown = manifest.with_name('ORACLE_CONSTITUTIONAL_DIGEST.md')
    rc = main([
        'oracle-constitutional-digest-evidence',
        '--lane-path', str(annual_lane),
        '--allow-legacy-lane-read',
        '--repo-root', str(repo_root),
        '--window-size', '3',
        '--signing-private-key', str(private_key),
        '--public-key', str(public_key),
        '--report-output', str(report),
        '--markdown-output', str(markdown),
        '--output', str(manifest),
        '--dsse-output', str(dsse),
        '--verification-output', str(verification),
    ])
    assert rc == 0

    constitutional_lane = repo_root / 'docs' / 'artifacts' / 'oracle' / 'ORACLE_CONSTITUTIONAL_LANE.jsonl'
    rc = main([
        'oracle-constitutional-lane-append',
        str(manifest),
        '--repo-root', str(repo_root),
        '--dsse', str(dsse),
        '--public-key', str(public_key),
        '--lane-path', str(constitutional_lane),
    ])
    assert rc == 0

    lineage_json = repo_root / 'docs' / 'artifacts' / 'oracle' / 'ORACLE_DOCTRINE_LINEAGE_INDEX.json'
    lineage_md = repo_root / 'docs' / 'artifacts' / 'oracle' / 'ORACLE_DOCTRINE_LINEAGE_INDEX.md'
    rc = main([
        'oracle-doctrine-lineage-index',
        '--repo-root', str(repo_root),
        '--search-root', str(repo_root / 'docs' / 'artifacts'),
        '--output', str(lineage_json),
        '--markdown-output', str(lineage_md),
    ])
    assert rc == 0

    verification_payload = json.loads(verification.read_text(encoding='utf-8'))
    assert verification_payload['status'] == 'VERIFIED'

    manifest_payload = json.loads(manifest.read_text(encoding='utf-8'))
    assert manifest_payload['constitutional_digest_classification'] == 'CONSTITUTIONAL_REPAIR_CHRONIC'

    lineage_payload = json.loads(lineage_json.read_text(encoding='utf-8'))
    assert any(path.endswith('CLOSURE_SNAPSHOT.json') for path in lineage_payload['closure_snapshot_paths'])
    assert any(path.endswith('ORACLE_CONSTITUTIONAL_DIGEST_EVIDENCE.json') for path in lineage_payload['oracle_constitutional_digest_evidence_paths'])
    assert any(path.endswith('ORACLE_ANNUAL_LANE.jsonl') for path in lineage_payload['annual_lane_paths'])
    assert any(path.endswith('ORACLE_CONSTITUTIONAL_LANE.jsonl') for path in lineage_payload['constitutional_lane_paths'])
    assert 'ORACLE DOCTRINE LINEAGE INDEX' in lineage_md.read_text(encoding='utf-8')


@pytest.mark.constitutional
def test_oracle_constitutional_lane_append_rejects_incomplete_constitutional_evidence(tmp_path: Path) -> None:
    repo_root = tmp_path
    private_key = repo_root / 'oracle_private.pem'
    public_key = repo_root / 'oracle_public.pem'
    generate_snapshot_signing_keypair(private_key_path=private_key, public_key_path=public_key)

    annual_lane = repo_root / 'docs' / 'artifacts' / 'oracle' / 'ORACLE_ANNUAL_LANE.jsonl'
    _write_annual_lane(annual_lane, [
        {
            'schema_version': 'oracle_annual_lane_entry/v1',
            'appended_at_utc': '2026-01-13T08:00:00Z',
            'lane_id': 'ORACLE_ANNUAL_LANE',
            'sequence_number': 0,
            'entry_id': 'annual-entry-0',
            'annual_review_id': 'annual-0',
            'previous_entry_hash': None,
            'entry_hash': 'hash-0',
            'manifest_path': 'annual0/ORACLE_ANNUAL_REVIEW_EVIDENCE.json',
            'manifest_sha256': 'a' * 64,
            'annual_review_classification': 'ANNUAL_EVIDENCE_GAP',
            'latest_semiannual_audit_id': 'semi-0',
            'evidence_status': 'INCOMPLETE',
            'summary_line': 'annual evidence gap',
        },
    ])

    manifest = repo_root / 'constitutional' / 'ORACLE_CONSTITUTIONAL_DIGEST_EVIDENCE.json'
    manifest.parent.mkdir(parents=True, exist_ok=True)
    dsse = manifest.with_name('ORACLE_CONSTITUTIONAL_DIGEST_EVIDENCE.dsse.json')
    verification = manifest.with_name('ORACLE_CONSTITUTIONAL_DIGEST_EVIDENCE.verification.json')
    report = manifest.with_name('ORACLE_CONSTITUTIONAL_DIGEST.json')
    markdown = manifest.with_name('ORACLE_CONSTITUTIONAL_DIGEST.md')
    rc = main([
        'oracle-constitutional-digest-evidence',
        '--lane-path', str(annual_lane),
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

    payload = json.loads(manifest.read_text(encoding='utf-8'))
    payload['subjects'] = payload['subjects'][:-1]
    payload['missing_artifact_paths'] = [str(markdown)]
    manifest.write_text(json.dumps(payload, indent=2), encoding='utf-8')

    constitutional_lane = repo_root / 'docs' / 'artifacts' / 'oracle' / 'ORACLE_CONSTITUTIONAL_LANE.jsonl'
    rc = main([
        'oracle-constitutional-lane-append',
        str(manifest),
        '--repo-root', str(repo_root),
        '--lane-path', str(constitutional_lane),
    ])
    assert rc == 2
    assert not constitutional_lane.exists()
