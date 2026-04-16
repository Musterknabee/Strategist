from __future__ import annotations

import json
from pathlib import Path

import pytest

from strategy_validator.cli.rollout_ops import main
from strategy_validator.validator.rollout_ops import generate_snapshot_signing_keypair
from strategy_validator.validator.oracle_doctrine_engine import generate_oracle_annual_review, generate_oracle_semiannual_audit, generate_oracle_quarterly_review
from strategy_validator.validator.oracle_review_engine import generate_oracle_weekly_digest


def _write_semiannual_lane(path: Path, entries: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', encoding='utf-8') as handle:
        for entry in entries:
            handle.write(json.dumps(entry) + '\n')


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', encoding='utf-8') as handle:
        for row in rows:
            handle.write(json.dumps(row) + "\n")


@pytest.mark.constitutional
def test_oracle_annual_evidence_lane_and_constitutional_digest_round_trip(tmp_path: Path) -> None:
    repo_root = tmp_path
    private_key = repo_root / 'oracle_private.pem'
    public_key = repo_root / 'oracle_public.pem'
    generate_snapshot_signing_keypair(private_key_path=private_key, public_key_path=public_key)

    semiannual_lane = repo_root / 'docs' / 'artifacts' / 'oracle' / 'ORACLE_SEMIANNUAL_LANE.jsonl'
    _write_semiannual_lane(semiannual_lane, [
        {
            'schema_version': 'oracle_semiannual_lane_entry/v1',
            'appended_at_utc': '2024-01-13T08:00:00Z',
            'lane_id': 'ORACLE_SEMIANNUAL_LANE',
            'sequence_number': 0,
            'entry_id': 'semi-entry-0',
            'semiannual_audit_id': 'semi-0',
            'previous_entry_hash': None,
            'entry_hash': 'hash-0',
            'manifest_path': 'semi0/ORACLE_SEMIANNUAL_AUDIT_EVIDENCE.json',
            'manifest_sha256': 'a' * 64,
            'semiannual_audit_classification': 'SEMIANNUAL_REPAIR_STRUCTURAL',
            'latest_quarterly_review_id': 'quarter-0',
            'evidence_status': 'VERIFIED',
            'summary_line': 'semiannual repair structural 0',
        },
        {
            'schema_version': 'oracle_semiannual_lane_entry/v1',
            'appended_at_utc': '2024-07-13T08:00:00Z',
            'lane_id': 'ORACLE_SEMIANNUAL_LANE',
            'sequence_number': 1,
            'entry_id': 'semi-entry-1',
            'semiannual_audit_id': 'semi-1',
            'previous_entry_hash': 'hash-0',
            'entry_hash': 'hash-1',
            'manifest_path': 'semi1/ORACLE_SEMIANNUAL_AUDIT_EVIDENCE.json',
            'manifest_sha256': 'b' * 64,
            'semiannual_audit_classification': 'SEMIANNUAL_REPAIR_STRUCTURAL',
            'latest_quarterly_review_id': 'quarter-1',
            'evidence_status': 'VERIFIED',
            'summary_line': 'semiannual repair structural 1',
        },
        {
            'schema_version': 'oracle_semiannual_lane_entry/v1',
            'appended_at_utc': '2025-01-13T08:00:00Z',
            'lane_id': 'ORACLE_SEMIANNUAL_LANE',
            'sequence_number': 2,
            'entry_id': 'semi-entry-2',
            'semiannual_audit_id': 'semi-2',
            'previous_entry_hash': 'hash-1',
            'entry_hash': 'hash-2',
            'manifest_path': 'semi2/ORACLE_SEMIANNUAL_AUDIT_EVIDENCE.json',
            'manifest_sha256': 'c' * 64,
            'semiannual_audit_classification': 'SEMIANNUAL_REPAIR_STRUCTURAL',
            'latest_quarterly_review_id': 'quarter-2',
            'evidence_status': 'VERIFIED',
            'summary_line': 'semiannual repair structural 2',
        },
        {
            'schema_version': 'oracle_semiannual_lane_entry/v1',
            'appended_at_utc': '2025-07-13T08:00:00Z',
            'lane_id': 'ORACLE_SEMIANNUAL_LANE',
            'sequence_number': 3,
            'entry_id': 'semi-entry-3',
            'semiannual_audit_id': 'semi-3',
            'previous_entry_hash': 'hash-2',
            'entry_hash': 'hash-3',
            'manifest_path': 'semi3/ORACLE_SEMIANNUAL_AUDIT_EVIDENCE.json',
            'manifest_sha256': 'd' * 64,
            'semiannual_audit_classification': 'SEMIANNUAL_REPAIR_STRUCTURAL',
            'latest_quarterly_review_id': 'quarter-3',
            'evidence_status': 'VERIFIED',
            'summary_line': 'semiannual repair structural 3',
        },
    ])

    annual_lane = repo_root / 'docs' / 'artifacts' / 'oracle' / 'ORACLE_ANNUAL_LANE.jsonl'
    for idx in range(2):
        manifest = repo_root / f'annual{idx}' / 'ORACLE_ANNUAL_REVIEW_EVIDENCE.json'
        manifest.parent.mkdir(parents=True, exist_ok=True)
        dsse = manifest.with_name('ORACLE_ANNUAL_REVIEW_EVIDENCE.dsse.json')
        verification = manifest.with_name('ORACLE_ANNUAL_REVIEW_EVIDENCE.verification.json')
        report = manifest.with_name('ORACLE_ANNUAL_REVIEW.json')
        markdown = manifest.with_name('ORACLE_ANNUAL_REVIEW.md')
        rc = main([
            'oracle-annual-review-evidence',
            '--lane-path', str(semiannual_lane),
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
            'oracle-annual-lane-append',
            str(manifest),
            '--repo-root', str(repo_root),
            '--dsse', str(dsse),
            '--public-key', str(public_key),
            '--lane-path', str(annual_lane),
        ])
        assert rc == 0

    digest_output = annual_lane.with_name('ORACLE_CONSTITUTIONAL_DIGEST.json')
    digest_markdown = annual_lane.with_name('ORACLE_CONSTITUTIONAL_DIGEST.md')
    rc = main([
        'oracle-constitutional-digest',
        '--lane-path', str(annual_lane),
        '--allow-legacy-lane-read',
        '--window-size', '2',
        '--output', str(digest_output),
        '--markdown-output', str(digest_markdown),
    ])
    assert rc == 0
    report = json.loads(digest_output.read_text(encoding='utf-8'))
    assert report['constitutional_digest_classification'] == 'CONSTITUTIONAL_REPAIR_CHRONIC'
    assert report['annual_classification_counts']['ANNUAL_REPAIR_STRUCTURAL'] >= 2
    assert 'ORACLE CONSTITUTIONAL DIGEST' in digest_markdown.read_text(encoding='utf-8')


@pytest.mark.constitutional
def test_oracle_annual_lane_append_rejects_incomplete_annual_evidence(tmp_path: Path) -> None:
    repo_root = tmp_path
    private_key = repo_root / 'oracle_private.pem'
    public_key = repo_root / 'oracle_public.pem'
    generate_snapshot_signing_keypair(private_key_path=private_key, public_key_path=public_key)

    semiannual_lane = repo_root / 'docs' / 'artifacts' / 'oracle' / 'ORACLE_SEMIANNUAL_LANE.jsonl'
    _write_semiannual_lane(semiannual_lane, [
        {
            'schema_version': 'oracle_semiannual_lane_entry/v1',
            'appended_at_utc': '2025-07-13T08:00:00Z',
            'lane_id': 'ORACLE_SEMIANNUAL_LANE',
            'sequence_number': 0,
            'entry_id': 'semi-entry-0',
            'semiannual_audit_id': 'semi-0',
            'previous_entry_hash': None,
            'entry_hash': 'hash-0',
            'manifest_path': 'semi0/ORACLE_SEMIANNUAL_AUDIT_EVIDENCE.json',
            'manifest_sha256': 'a' * 64,
            'semiannual_audit_classification': 'SEMIANNUAL_EVIDENCE_GAP',
            'latest_quarterly_review_id': 'quarter-0',
            'evidence_status': 'INCOMPLETE',
            'summary_line': 'semiannual evidence gap',
        },
    ])

    manifest = repo_root / 'annual' / 'ORACLE_ANNUAL_REVIEW_EVIDENCE.json'
    manifest.parent.mkdir(parents=True, exist_ok=True)
    dsse = manifest.with_name('ORACLE_ANNUAL_REVIEW_EVIDENCE.dsse.json')
    verification = manifest.with_name('ORACLE_ANNUAL_REVIEW_EVIDENCE.verification.json')
    report = manifest.with_name('ORACLE_ANNUAL_REVIEW.json')
    markdown = manifest.with_name('ORACLE_ANNUAL_REVIEW.md')
    rc = main([
        'oracle-annual-review-evidence',
        '--lane-path', str(semiannual_lane),
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

    annual_lane = repo_root / 'docs' / 'artifacts' / 'oracle' / 'ORACLE_ANNUAL_LANE.jsonl'
    rc = main([
        'oracle-annual-lane-append',
        str(manifest),
        '--repo-root', str(repo_root),
        '--lane-path', str(annual_lane),
    ])
    assert rc == 2
    assert not annual_lane.exists()


@pytest.mark.constitutional
def test_oracle_constitutional_digest_surfaces_doctrine_only_vs_sealed_strategic_backing(tmp_path: Path) -> None:
    repo_root = tmp_path
    annual_lane = repo_root / 'docs' / 'artifacts' / 'oracle' / 'ORACLE_ANNUAL_LANE.jsonl'
    annual_lane.parent.mkdir(parents=True, exist_ok=True)
    annual_lane.write_text(
        json.dumps({
            'schema_version': 'oracle_annual_lane_entry/v1',
            'appended_at_utc': '2026-04-13T08:00:00Z',
            'lane_id': 'ORACLE_ANNUAL_LANE',
            'sequence_number': 0,
            'entry_id': 'annual-entry-0',
            'annual_review_id': 'annual-0',
            'previous_entry_hash': None,
            'entry_hash': 'a' * 64,
            'manifest_path': 'annual0/ORACLE_ANNUAL_REVIEW_EVIDENCE.json',
            'manifest_sha256': 'b' * 64,
            'annual_review_classification': 'ANNUAL_REPAIR_STRUCTURAL',
            'latest_semiannual_audit_id': 'semi-0',
            'evidence_status': 'VERIFIED',
            'summary_line': 'annual repair structural',
        }) + '\n',
        encoding='utf-8',
    )

    doctrine_only_output = annual_lane.with_name('ORACLE_CONSTITUTIONAL_DIGEST.doctrine_only.json')
    rc = main([
        'oracle-constitutional-digest',
        '--lane-path', str(annual_lane),
        '--allow-legacy-lane-read',
        '--window-size', '1',
        '--output', str(doctrine_only_output),
    ])
    assert rc == 0
    doctrine_only = json.loads(doctrine_only_output.read_text(encoding='utf-8'))
    assert doctrine_only['strategic_backing_classification'] == 'DOCTRINE_ONLY_LADDER_BACKED'
    assert doctrine_only['strategic_stack_evidence_count'] == 0
    assert doctrine_only['strategic_stack_requirement_met'] is False
    assert 'backing=DOCTRINE_ONLY_LADDER_BACKED' in doctrine_only['summary_line']

    strategic_manifest = annual_lane.parent / 'ORACLE_STRATEGIC_STACK_EVIDENCE.json'
    strategic_manifest.write_text(json.dumps({
        'schema_version': 'oracle_strategic_stack_evidence_manifest/v1',
        'generated_at_utc': '2026-04-13T00:00:00Z',
        'stack_id': 'stack-1',
        'oracle_run_id': 'run-1',
        'universe_label': 'US_EQ_FACTORS',
        'input_timestamp_utc': '2026-04-13T08:00:00Z',
        'execution_authority': 'ADVISORY_ONLY',
        'dominant_regime': 'TRANSITION',
        'strategic_posture': 'DEFENSIVE_RESEARCH',
        'briefing_schema_version': 'oracle_strategic_briefing_report/v1',
        'integrity_status': 'VERIFIED',
        'subjects': [],
        'missing_artifact_paths': [],
        'summary_line': 'sealed strategic stack evidence',
    }, indent=2), encoding='utf-8')

    sealed_output = annual_lane.with_name('ORACLE_CONSTITUTIONAL_DIGEST.sealed.json')
    sealed_markdown = annual_lane.with_name('ORACLE_CONSTITUTIONAL_DIGEST.sealed.md')
    rc = main([
        'oracle-constitutional-digest',
        '--lane-path', str(annual_lane),
        '--allow-legacy-lane-read',
        '--window-size', '1',
        '--output', str(sealed_output),
        '--markdown-output', str(sealed_markdown),
    ])
    assert rc == 0
    sealed = json.loads(sealed_output.read_text(encoding='utf-8'))
    assert sealed['strategic_backing_classification'] == 'SEALED_STRATEGIC_STACK_BACKED'
    assert sealed['strategic_stack_evidence_count'] == 1
    assert sealed['strategic_stack_requirement_met'] is True
    sealed_md = sealed_markdown.read_text(encoding='utf-8')
    assert 'Strategic backing classification: SEALED_STRATEGIC_STACK_BACKED' in sealed_md


@pytest.mark.constitutional
def test_oracle_semiannual_audit_surfaces_doctrine_only_vs_sealed_strategic_backing(tmp_path: Path) -> None:
    repo_root = tmp_path
    quarterly_lane = repo_root / 'docs' / 'artifacts' / 'oracle' / 'ORACLE_QUARTERLY_LANE.jsonl'
    _write_jsonl(quarterly_lane, [{
        'schema_version': 'oracle_quarterly_lane_entry/v1',
        'appended_at_utc': '2026-04-13T08:00:00Z',
        'lane_id': 'ORACLE_QUARTERLY_LANE',
        'sequence_number': 0,
        'entry_id': 'quarter-entry-0',
        'quarterly_review_id': 'quarter-0',
        'previous_entry_hash': None,
        'entry_hash': 'a' * 64,
        'manifest_path': 'quarter0/ORACLE_QUARTERLY_REVIEW_EVIDENCE.json',
        'manifest_sha256': 'b' * 64,
        'quarterly_review_classification': 'QUARTERLY_REPAIR_STRUCTURAL',
        'latest_monthly_digest_id': 'month-0',
        'evidence_status': 'VERIFIED',
        'summary_line': 'quarterly repair structural',
    }])

    doctrine_only = generate_oracle_semiannual_audit(
        lane_path=quarterly_lane,
        window_size=1,
        repo_root=repo_root,
    ).model_dump(mode='json')
    assert doctrine_only['strategic_backing_classification'] == 'DOCTRINE_ONLY_LADDER_BACKED'
    assert doctrine_only['strategic_stack_evidence_count'] == 0
    assert doctrine_only['strategic_stack_requirement_met'] is False
    assert 'backing=DOCTRINE_ONLY_LADDER_BACKED' in doctrine_only['summary_line']

    strategic_manifest = quarterly_lane.parent / 'ORACLE_STRATEGIC_STACK_EVIDENCE.json'
    strategic_manifest.write_text(json.dumps({
        'schema_version': 'oracle_strategic_stack_evidence_manifest/v1',
        'generated_at_utc': '2026-04-13T00:00:00Z',
        'stack_id': 'stack-1',
        'oracle_run_id': 'run-1',
        'universe_label': 'US_EQ_FACTORS',
        'input_timestamp_utc': '2026-04-13T08:00:00Z',
        'execution_authority': 'ADVISORY_ONLY',
        'dominant_regime': 'TRANSITION',
        'strategic_posture': 'DEFENSIVE_RESEARCH',
        'briefing_schema_version': 'oracle_strategic_briefing_report/v1',
        'integrity_status': 'VERIFIED',
        'subjects': [],
        'missing_artifact_paths': [],
        'summary_line': 'synthetic strategic stack evidence',
    }, indent=2), encoding='utf-8')

    sealed = generate_oracle_semiannual_audit(
        lane_path=quarterly_lane,
        window_size=1,
        repo_root=repo_root,
    ).model_dump(mode='json')
    assert sealed['strategic_backing_classification'] == 'SEALED_STRATEGIC_STACK_BACKED'
    assert sealed['strategic_stack_evidence_count'] == 1
    assert sealed['strategic_stack_requirement_met'] is True


@pytest.mark.constitutional
def test_oracle_annual_review_surfaces_doctrine_only_vs_sealed_strategic_backing(tmp_path: Path) -> None:
    repo_root = tmp_path
    semiannual_lane = repo_root / 'docs' / 'artifacts' / 'oracle' / 'ORACLE_SEMIANNUAL_LANE.jsonl'
    _write_jsonl(semiannual_lane, [{
        'schema_version': 'oracle_semiannual_lane_entry/v1',
        'appended_at_utc': '2026-04-13T08:00:00Z',
        'lane_id': 'ORACLE_SEMIANNUAL_LANE',
        'sequence_number': 0,
        'entry_id': 'semi-entry-0',
        'semiannual_audit_id': 'semi-0',
        'previous_entry_hash': None,
        'entry_hash': 'a' * 64,
        'manifest_path': 'semi0/ORACLE_SEMIANNUAL_AUDIT_EVIDENCE.json',
        'manifest_sha256': 'b' * 64,
        'semiannual_audit_classification': 'SEMIANNUAL_REPAIR_STRUCTURAL',
        'latest_quarterly_review_id': 'quarter-0',
        'evidence_status': 'VERIFIED',
        'summary_line': 'semiannual repair structural',
    }])

    doctrine_only = generate_oracle_annual_review(
        lane_path=semiannual_lane,
        window_size=1,
        repo_root=repo_root,
    ).model_dump(mode='json')
    assert doctrine_only['strategic_backing_classification'] == 'DOCTRINE_ONLY_LADDER_BACKED'
    assert doctrine_only['strategic_stack_evidence_count'] == 0
    assert doctrine_only['strategic_stack_requirement_met'] is False
    assert 'backing=DOCTRINE_ONLY_LADDER_BACKED' in doctrine_only['summary_line']

    strategic_manifest = semiannual_lane.parent / 'ORACLE_STRATEGIC_STACK_EVIDENCE.json'
    strategic_manifest.write_text(json.dumps({
        'schema_version': 'oracle_strategic_stack_evidence_manifest/v1',
        'generated_at_utc': '2026-04-13T00:00:00Z',
        'stack_id': 'stack-1',
        'oracle_run_id': 'run-1',
        'universe_label': 'US_EQ_FACTORS',
        'input_timestamp_utc': '2026-04-13T08:00:00Z',
        'execution_authority': 'ADVISORY_ONLY',
        'dominant_regime': 'TRANSITION',
        'strategic_posture': 'DEFENSIVE_RESEARCH',
        'briefing_schema_version': 'oracle_strategic_briefing_report/v1',
        'integrity_status': 'VERIFIED',
        'subjects': [],
        'missing_artifact_paths': [],
        'summary_line': 'synthetic strategic stack evidence',
    }, indent=2), encoding='utf-8')

    sealed = generate_oracle_annual_review(
        lane_path=semiannual_lane,
        window_size=1,
        repo_root=repo_root,
    ).model_dump(mode='json')
    assert sealed['strategic_backing_classification'] == 'SEALED_STRATEGIC_STACK_BACKED'
    assert sealed['strategic_stack_evidence_count'] == 1
    assert sealed['strategic_stack_requirement_met'] is True


@pytest.mark.constitutional
def test_oracle_review_evidence_and_lane_entries_carry_strategic_backing_metadata(tmp_path: Path) -> None:
    repo_root = tmp_path
    private_key = repo_root / 'oracle_private.pem'
    public_key = repo_root / 'oracle_public.pem'
    generate_snapshot_signing_keypair(private_key_path=private_key, public_key_path=public_key)

    quarterly_lane = repo_root / 'docs' / 'artifacts' / 'oracle' / 'ORACLE_QUARTERLY_LANE.jsonl'
    _write_jsonl(quarterly_lane, [{
        'schema_version': 'oracle_quarterly_lane_entry/v1',
        'appended_at_utc': '2026-04-13T08:00:00Z',
        'lane_id': 'ORACLE_QUARTERLY_LANE',
        'sequence_number': 0,
        'entry_id': 'quarter-entry-0',
        'quarterly_review_id': 'quarter-0',
        'previous_entry_hash': None,
        'entry_hash': 'a' * 64,
        'manifest_path': 'quarter0/ORACLE_QUARTERLY_REVIEW_EVIDENCE.json',
        'manifest_sha256': 'b' * 64,
        'quarterly_review_classification': 'QUARTERLY_REPAIR_STRUCTURAL',
        'latest_monthly_digest_id': 'month-0',
        'evidence_status': 'VERIFIED',
        'summary_line': 'quarterly repair structural',
    }])
    strategic_manifest = quarterly_lane.parent / 'ORACLE_STRATEGIC_STACK_EVIDENCE.json'
    strategic_manifest.write_text(json.dumps({
        'schema_version': 'oracle_strategic_stack_evidence_manifest/v1',
        'generated_at_utc': '2026-04-13T00:00:00Z',
        'stack_id': 'stack-1',
        'oracle_run_id': 'run-1',
        'universe_label': 'US_EQ_FACTORS',
        'input_timestamp_utc': '2026-04-13T08:00:00Z',
        'execution_authority': 'ADVISORY_ONLY',
        'dominant_regime': 'TRANSITION',
        'strategic_posture': 'DEFENSIVE_RESEARCH',
        'briefing_schema_version': 'oracle_strategic_briefing_report/v1',
        'integrity_status': 'VERIFIED',
        'subjects': [],
        'missing_artifact_paths': [],
        'summary_line': 'synthetic strategic stack evidence',
    }, indent=2), encoding='utf-8')

    semi_manifest = repo_root / 'semi' / 'ORACLE_SEMIANNUAL_AUDIT_EVIDENCE.json'
    semi_dsse = semi_manifest.with_name('ORACLE_SEMIANNUAL_AUDIT_EVIDENCE.dsse.json')
    semi_verification = semi_manifest.with_name('ORACLE_SEMIANNUAL_AUDIT_EVIDENCE.verification.json')
    semi_report = semi_manifest.with_name('ORACLE_SEMIANNUAL_AUDIT.json')
    semi_markdown = semi_manifest.with_name('ORACLE_SEMIANNUAL_AUDIT.md')
    rc = main([
        'oracle-semiannual-audit-evidence',
        '--lane-path', str(quarterly_lane),
        '--allow-legacy-lane-read',
        '--repo-root', str(repo_root),
        '--window-size', '1',
        '--signing-private-key', str(private_key),
        '--public-key', str(public_key),
        '--report-output', str(semi_report),
        '--markdown-output', str(semi_markdown),
        '--output', str(semi_manifest),
        '--dsse-output', str(semi_dsse),
        '--verification-output', str(semi_verification),
    ])
    assert rc == 0
    semi_payload = json.loads(semi_manifest.read_text(encoding='utf-8'))
    assert semi_payload['strategic_backing_classification'] == 'SEALED_STRATEGIC_STACK_BACKED'
    assert semi_payload['strategic_stack_evidence_count'] == 1
    assert semi_payload['strategic_stack_requirement_met'] is True

    semi_lane = repo_root / 'docs' / 'artifacts' / 'oracle' / 'ORACLE_SEMIANNUAL_LANE.jsonl'
    rc = main([
        'oracle-semiannual-lane-append',
        str(semi_manifest),
        '--repo-root', str(repo_root),
        '--dsse', str(semi_dsse),
        '--public-key', str(public_key),
        '--lane-path', str(semi_lane),
    ])
    assert rc == 0
    semi_entry = json.loads(semi_lane.read_text(encoding='utf-8').splitlines()[-1])
    assert semi_entry['strategic_backing_classification'] == 'SEALED_STRATEGIC_STACK_BACKED'
    assert semi_entry['strategic_stack_evidence_count'] == 1
    assert semi_entry['strategic_stack_requirement_met'] is True

    annual_manifest = repo_root / 'annual' / 'ORACLE_ANNUAL_REVIEW_EVIDENCE.json'
    annual_dsse = annual_manifest.with_name('ORACLE_ANNUAL_REVIEW_EVIDENCE.dsse.json')
    annual_verification = annual_manifest.with_name('ORACLE_ANNUAL_REVIEW_EVIDENCE.verification.json')
    annual_report = annual_manifest.with_name('ORACLE_ANNUAL_REVIEW.json')
    annual_markdown = annual_manifest.with_name('ORACLE_ANNUAL_REVIEW.md')
    rc = main([
        'oracle-annual-review-evidence',
        '--lane-path', str(semi_lane),
        '--allow-legacy-lane-read',
        '--repo-root', str(repo_root),
        '--window-size', '1',
        '--signing-private-key', str(private_key),
        '--public-key', str(public_key),
        '--report-output', str(annual_report),
        '--markdown-output', str(annual_markdown),
        '--output', str(annual_manifest),
        '--dsse-output', str(annual_dsse),
        '--verification-output', str(annual_verification),
    ])
    assert rc == 0
    annual_payload = json.loads(annual_manifest.read_text(encoding='utf-8'))
    assert annual_payload['strategic_backing_classification'] == 'SEALED_STRATEGIC_STACK_BACKED'
    assert annual_payload['strategic_stack_evidence_count'] == 1
    assert annual_payload['strategic_stack_requirement_met'] is True

    annual_lane = repo_root / 'docs' / 'artifacts' / 'oracle' / 'ORACLE_ANNUAL_LANE.jsonl'
    rc = main([
        'oracle-annual-lane-append',
        str(annual_manifest),
        '--repo-root', str(repo_root),
        '--dsse', str(annual_dsse),
        '--public-key', str(public_key),
        '--lane-path', str(annual_lane),
    ])
    assert rc == 0
    annual_entry = json.loads(annual_lane.read_text(encoding='utf-8').splitlines()[-1])
    assert annual_entry['strategic_backing_classification'] == 'SEALED_STRATEGIC_STACK_BACKED'
    assert annual_entry['strategic_stack_evidence_count'] == 1
    assert annual_entry['strategic_stack_requirement_met'] is True


@pytest.mark.constitutional
def test_oracle_weekly_digest_uses_exact_feedback_to_escalate_cadence(tmp_path: Path) -> None:
    review_lane = tmp_path / 'docs' / 'artifacts' / 'oracle' / 'ORACLE_REVIEW_LANE.jsonl'
    _write_jsonl(review_lane, [
        {
            'schema_version': 'oracle_review_lane_entry/v1',
            'appended_at_utc': '2026-04-01T08:00:00Z',
            'lane_id': 'ORACLE_REVIEW_LANE',
            'sequence_number': 0,
            'entry_id': 'review-entry-0',
            'review_id': 'review-0',
            'previous_entry_hash': None,
            'entry_hash': 'a' * 64,
            'manifest_path': 'review0/ORACLE_MEMORY_REVIEW_EVIDENCE.json',
            'manifest_sha256': 'b' * 64,
            'review_classification': 'STABLE_RESEARCH_POSTURE',
            'window_end_sequence_number': 10,
            'latest_global_action': 'OBSERVE',
            'latest_epistemic_status': 'ELEVATED',
            'evidence_status': 'VERIFIED',
            'summary_line': 'stable review',
        }
    ])
    reports_dir = tmp_path / 'docs' / 'artifacts' / 'oracle' / 'doctrine'
    reports_dir.mkdir(parents=True, exist_ok=True)
    for idx in range(2):
        report_path = reports_dir / f'ORACLE_DOCTRINE_ADAPTATION_{idx}.json'
        report_path.write_text(json.dumps({
            'schema_version': 'oracle_doctrine_adaptation_report/v1',
            'generated_at_utc': f'2026-04-0{idx + 1}T09:00:00Z',
            'universe_label': 'GLOBAL_MACRO',
            'oracle_run_id': f'run-{idx}',
            'input_timestamp_utc': f'2026-04-0{idx + 1}T08:00:00Z',
            'dominant_regime': 'TRANSITION',
            'strategic_posture': 'CAUTION_BIASED',
            'transition_classification': 'STABLE_REGIME',
            'history_integrity_status': 'SEALED_HISTORY',
            'sealed_history_observation_count': 2,
            'unsealed_history_excluded_count': 0,
            'preferred_strategic_backing_source': 'strategic_artifact_evidence_manifest',
            'preferred_strategic_backing_classification': 'SEALED_STRATEGIC_STACK_BACKED',
            'exact_evidence_support_score': 0.99,
            'summary_line': 'supported doctrine adaptation',
            'top_review_clause_ids': ['doctrine-risk'],
            'freeze_recommended': False,
            'items': [{
                'clause_id': 'doctrine-risk',
                'clause_label': 'Doctrine Risk',
                'adaptation_state': 'REVIEW',
                'stress_score': 0.78,
                'review_priority_score': 0.82,
                'exact_evidence_support_score': 0.99,
                'weakening_assumptions': ['stress persists'],
                'pressure_sources': ['execution confirmation'],
                'recommended_adaptation': 'Increase review cadence.',
                'summary_line': 'pressure confirmed',
            }],
            'operator_actions': ['Escalate doctrine review cadence.'],
        }, indent=2), encoding='utf-8')

    digest = generate_oracle_weekly_digest(lane_path=review_lane, window_size=2, repo_root=tmp_path, search_root=tmp_path)
    assert digest.exact_evidence_support_score >= 0.99
    assert digest.exact_feedback_confirmation_count >= 2
    assert any('exact sealed confirmations' in action.lower() for action in digest.operator_actions)
    assert 'exact_confirm=' in digest.summary_line


@pytest.mark.constitutional
def test_oracle_quarterly_review_uses_exact_feedback_to_soften_or_escalate_cadence(tmp_path: Path) -> None:
    monthly_lane = tmp_path / 'docs' / 'artifacts' / 'oracle' / 'ORACLE_MONTHLY_LANE.jsonl'
    _write_jsonl(monthly_lane, [
        {
            'schema_version': 'oracle_monthly_lane_entry/v1',
            'appended_at_utc': '2026-01-01T08:00:00Z',
            'lane_id': 'ORACLE_MONTHLY_LANE',
            'exact_evidence_support_score': 0.0,
            'exact_feedback_confirmation_count': 0,
            'exact_feedback_relief_count': 0,
            'sequence_number': 0,
            'entry_id': 'monthly-entry-0',
            'monthly_digest_id': 'monthly-0',
            'previous_entry_hash': None,
            'entry_hash': 'a' * 64,
            'manifest_path': 'monthly0/ORACLE_MONTHLY_DIGEST_EVIDENCE.json',
            'manifest_sha256': 'b' * 64,
            'doctrine_memory_classification': 'DOCTRINE_STABLE_BASELINE',
            'latest_drift_classification': 'DOCTRINE_RELIEF',
            'evidence_status': 'VERIFIED',
            'summary_line': 'stable monthly',
        },
        {
            'schema_version': 'oracle_monthly_lane_entry/v1',
            'appended_at_utc': '2026-02-01T08:00:00Z',
            'lane_id': 'ORACLE_MONTHLY_LANE',
            'exact_evidence_support_score': 0.0,
            'exact_feedback_confirmation_count': 0,
            'exact_feedback_relief_count': 0,
            'sequence_number': 1,
            'entry_id': 'monthly-entry-1',
            'monthly_digest_id': 'monthly-1',
            'previous_entry_hash': 'a' * 64,
            'entry_hash': 'c' * 64,
            'manifest_path': 'monthly1/ORACLE_MONTHLY_DIGEST_EVIDENCE.json',
            'manifest_sha256': 'd' * 64,
            'doctrine_memory_classification': 'DOCTRINE_STABLE_BASELINE',
            'latest_drift_classification': 'DOCTRINE_RELIEF',
            'evidence_status': 'VERIFIED',
            'summary_line': 'stable monthly',
        },
    ])
    reports_dir = tmp_path / 'docs' / 'artifacts' / 'oracle' / 'doctrine'
    reports_dir.mkdir(parents=True, exist_ok=True)
    for idx in range(4):
        report_path = reports_dir / f'ORACLE_DOCTRINE_ADAPTATION_RELIEF_{idx}.json'
        report_path.write_text(json.dumps({
            'schema_version': 'oracle_doctrine_adaptation_report/v1',
            'generated_at_utc': f'2026-03-{idx + 1:02d}T09:00:00Z',
            'universe_label': 'GLOBAL_MACRO',
            'oracle_run_id': f'relief-run-{idx}',
            'input_timestamp_utc': f'2026-03-{idx + 1:02d}T08:00:00Z',
            'dominant_regime': 'TRANSITION',
            'strategic_posture': 'CAUTION_BIASED',
            'transition_classification': 'STABLE_REGIME',
            'history_integrity_status': 'SEALED_HISTORY',
            'sealed_history_observation_count': 2,
            'unsealed_history_excluded_count': 0,
            'preferred_strategic_backing_source': 'strategic_artifact_evidence_manifest',
            'preferred_strategic_backing_classification': 'SEALED_STRATEGIC_STACK_BACKED',
            'exact_evidence_support_score': 0.99,
            'summary_line': 'relieving doctrine adaptation',
            'top_review_clause_ids': ['doctrine-risk'],
            'freeze_recommended': False,
            'items': [{
                'clause_id': 'doctrine-risk',
                'clause_label': 'Doctrine Risk',
                'adaptation_state': 'MONITOR',
                'stress_score': 0.18,
                'review_priority_score': 0.20,
                'exact_evidence_support_score': 0.99,
                'weakening_assumptions': ['pressure receded'],
                'pressure_sources': ['sealed relief'],
                'recommended_adaptation': 'Relax cadence slightly.',
                'summary_line': 'relief confirmed',
            }],
            'operator_actions': ['Relax cadence for supported clause only.'],
        }, indent=2), encoding='utf-8')

    report = generate_oracle_quarterly_review(lane_path=monthly_lane, window_size=2, repo_root=tmp_path, search_root=tmp_path)
    assert report.exact_evidence_support_score >= 0.99
    assert report.exact_feedback_relief_count >= 4
    assert any('relieving outcomes' in action.lower() for action in report.operator_actions)
    assert 'exact_relief=' in report.summary_line
