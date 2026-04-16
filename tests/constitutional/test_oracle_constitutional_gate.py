from __future__ import annotations

import json
from pathlib import Path

import pytest

from strategy_validator.cli.rollout_ops import main


REQUIRED_FILENAMES = [
    'ORACLE_EVIDENCE.json',
    'ORACLE_TRANSITION_EVIDENCE.json',
    'ORACLE_MEMORY_REVIEW_EVIDENCE.json',
    'ORACLE_WEEKLY_DIGEST_EVIDENCE.json',
    'ORACLE_DOCTRINE_DRIFT_EVIDENCE.json',
    'ORACLE_MONTHLY_DIGEST_EVIDENCE.json',
    'ORACLE_QUARTERLY_REVIEW_EVIDENCE.json',
    'ORACLE_SEMIANNUAL_AUDIT_EVIDENCE.json',
    'ORACLE_ANNUAL_REVIEW_EVIDENCE.json',
]


def _write_json(path: Path, payload: dict | list) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding='utf-8')


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', encoding='utf-8') as handle:
        for row in rows:
            handle.write(json.dumps(row) + "\n")


def _write_valid_strategic_stack_manifest(path: Path) -> None:
    _write_json(
        path,
        {
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
        },
    )


def _write_valid_constitutional_manifest(path: Path, *, classification: str = 'CONSTITUTIONAL_STABLE_BASELINE') -> None:
    _write_json(
        path,
        {
            'schema_version': 'oracle_constitutional_digest_evidence_manifest/v1',
            'generated_at_utc': '2026-04-13T00:00:00Z',
            'constitutional_digest_id': 'digest-1',
            'lane_id': 'ORACLE_ANNUAL_LANE',
            'execution_authority': 'ADVISORY_ONLY',
            'source_annual_lane_path': 'docs/artifacts/oracle/ORACLE_ANNUAL_LANE.jsonl',
            'constitutional_digest_classification': classification,
            'window_entry_count': 1,
            'window_end_sequence_number': 0,
            'latest_annual_review_id': 'annual-1',
            'latest_annual_review_classification': 'ANNUAL_STABLE_BASELINE',
            'integrity_status': 'VERIFIED',
            'subjects': [],
            'missing_artifact_paths': [],
            'summary_line': 'synthetic constitutional digest evidence',
        },
    )


@pytest.mark.constitutional
def test_oracle_constitutional_gate_trusts_fully_sealed_ladder(tmp_path: Path) -> None:
    repo_root = tmp_path
    artifacts = repo_root / 'docs' / 'artifacts'
    oracle_root = artifacts / 'oracle'

    _write_json(artifacts / 'final_rollout_closure' / 'CLOSURE_SNAPSHOT.json', {})
    for filename in REQUIRED_FILENAMES:
        _write_json(oracle_root / filename, {})
    _write_valid_constitutional_manifest(oracle_root / 'ORACLE_CONSTITUTIONAL_DIGEST_EVIDENCE.json')
    _write_valid_strategic_stack_manifest(oracle_root / 'ORACLE_STRATEGIC_STACK_EVIDENCE.json')
    _write_jsonl(oracle_root / 'ORACLE_ANNUAL_LANE.jsonl', [{'sequence_number': 0, 'entry_hash': 'a' * 64}])
    _write_jsonl(oracle_root / 'ORACLE_CONSTITUTIONAL_LANE.jsonl', [{'sequence_number': 0, 'entry_hash': 'b' * 64}])

    output = oracle_root / 'ORACLE_CONSTITUTIONAL_GATE_REPORT.json'
    markdown = oracle_root / 'ORACLE_CONSTITUTIONAL_GATE_REPORT.md'
    rc = main([
        'oracle-constitutional-gate',
        str(oracle_root / 'ORACLE_CONSTITUTIONAL_DIGEST_EVIDENCE.json'),
        '--repo-root', str(repo_root),
        '--search-root', str(artifacts),
        '--output', str(output),
        '--markdown-output', str(markdown),
    ])
    assert rc == 0

    payload = json.loads(output.read_text(encoding='utf-8'))
    assert payload['trust_status'] == 'TRUSTED'
    assert payload['trusted_for_constitutional_use'] is True
    assert payload['lineage_seal_status'] == 'FULLY_SEALED'
    gate_markdown = markdown.read_text(encoding='utf-8')
    assert 'ORACLE CONSTITUTIONAL GATE' in gate_markdown
    assert 'Trust banner:' in gate_markdown
    assert 'Lineage reason:' in gate_markdown
    assert '## Trust explanation' in gate_markdown
    assert 'THRESHOLD_MET' in gate_markdown


@pytest.mark.constitutional
def test_oracle_constitutional_gate_restricts_replayable_ladder_until_threshold_is_lowered(tmp_path: Path) -> None:
    repo_root = tmp_path
    artifacts = repo_root / 'docs' / 'artifacts'
    oracle_root = artifacts / 'oracle'

    for filename in REQUIRED_FILENAMES:
        _write_json(oracle_root / filename, {})
    _write_valid_constitutional_manifest(oracle_root / 'ORACLE_CONSTITUTIONAL_DIGEST_EVIDENCE.json')
    _write_jsonl(oracle_root / 'ORACLE_ANNUAL_LANE.jsonl', [{'sequence_number': 0, 'entry_hash': 'a' * 64}])
    _write_jsonl(oracle_root / 'ORACLE_CONSTITUTIONAL_LANE.jsonl', [{'sequence_number': 0, 'entry_hash': 'b' * 64}])

    restricted_output = oracle_root / 'ORACLE_CONSTITUTIONAL_GATE_REPORT.default.json'
    rc = main([
        'oracle-constitutional-gate',
        str(oracle_root / 'ORACLE_CONSTITUTIONAL_DIGEST_EVIDENCE.json'),
        '--repo-root', str(repo_root),
        '--search-root', str(artifacts),
        '--output', str(restricted_output),
    ])
    assert rc == 2
    restricted = json.loads(restricted_output.read_text(encoding='utf-8'))
    assert restricted['trust_status'] == 'TRUST_RESTRICTED'
    assert restricted['trusted_for_constitutional_use'] is False
    assert restricted['lineage_seal_status'] == 'CONSTITUTIONALLY_REPLAYABLE'

    _write_valid_strategic_stack_manifest(oracle_root / 'ORACLE_STRATEGIC_STACK_EVIDENCE.json')
    trusted_output = oracle_root / 'ORACLE_CONSTITUTIONAL_GATE_REPORT.replayable.json'
    rc = main([
        'oracle-constitutional-gate',
        str(oracle_root / 'ORACLE_CONSTITUTIONAL_DIGEST_EVIDENCE.json'),
        '--repo-root', str(repo_root),
        '--search-root', str(artifacts),
        '--minimum-required-seal-status', 'CONSTITUTIONALLY_REPLAYABLE',
        '--output', str(trusted_output),
    ])
    assert rc == 0
    trusted = json.loads(trusted_output.read_text(encoding='utf-8'))
    assert trusted['trust_status'] == 'TRUSTED'
    assert trusted['trusted_for_constitutional_use'] is True
    assert trusted['minimum_required_seal_status'] == 'CONSTITUTIONALLY_REPLAYABLE'



@pytest.mark.constitutional
def test_oracle_constitutional_gate_restricts_without_strategic_stack_evidence_even_when_ladder_is_present(tmp_path: Path) -> None:
    repo_root = tmp_path
    artifacts = repo_root / 'docs' / 'artifacts'
    oracle_root = artifacts / 'oracle'

    _write_json(artifacts / 'final_rollout_closure' / 'CLOSURE_SNAPSHOT.json', {})
    for filename in REQUIRED_FILENAMES:
        _write_json(oracle_root / filename, {})
    _write_valid_constitutional_manifest(oracle_root / 'ORACLE_CONSTITUTIONAL_DIGEST_EVIDENCE.json')
    _write_jsonl(oracle_root / 'ORACLE_ANNUAL_LANE.jsonl', [{'sequence_number': 0, 'entry_hash': 'a' * 64}])
    _write_jsonl(oracle_root / 'ORACLE_CONSTITUTIONAL_LANE.jsonl', [{'sequence_number': 0, 'entry_hash': 'b' * 64}])

    output = oracle_root / 'ORACLE_CONSTITUTIONAL_GATE_REPORT.restricted.json'
    rc = main([
        'oracle-constitutional-gate',
        str(oracle_root / 'ORACLE_CONSTITUTIONAL_DIGEST_EVIDENCE.json'),
        '--repo-root', str(repo_root),
        '--search-root', str(artifacts),
        '--minimum-required-seal-status', 'FULLY_SEALED',
        '--output', str(output),
    ])
    assert rc == 2
    payload = json.loads(output.read_text(encoding='utf-8'))
    assert payload['lineage_seal_status'] == 'FULLY_SEALED'
    assert payload['strategic_stack_evidence_count'] == 0
    assert payload['strategic_stack_requirement_met'] is False
    assert payload['trust_status'] == 'TRUST_RESTRICTED'
    assert any('strategic stack evidence' in item.lower() for item in payload['blocking_reasons'])


@pytest.mark.constitutional
def test_oracle_constitutional_gate_prefers_artifact_native_backing_metadata(tmp_path: Path) -> None:
    repo_root = tmp_path
    artifacts = repo_root / 'docs' / 'artifacts'
    oracle_root = artifacts / 'oracle'

    _write_json(artifacts / 'final_rollout_closure' / 'CLOSURE_SNAPSHOT.json', {})
    for filename in REQUIRED_FILENAMES:
        _write_json(oracle_root / filename, {})
    _write_valid_constitutional_manifest(
        oracle_root / 'ORACLE_CONSTITUTIONAL_DIGEST_EVIDENCE.json',
        classification='CONSTITUTIONAL_STABLE_BASELINE',
    )
    _write_jsonl(oracle_root / 'ORACLE_ANNUAL_LANE.jsonl', [{'sequence_number': 0, 'entry_hash': 'a' * 64}])
    _write_jsonl(oracle_root / 'ORACLE_CONSTITUTIONAL_LANE.jsonl', [{
        'schema_version': 'oracle_constitutional_lane_entry/v1',
        'appended_at_utc': '2026-04-13T00:00:00Z',
        'lane_id': 'ORACLE_CONSTITUTIONAL_LANE',
        'sequence_number': 0,
        'entry_id': 'entry-1',
        'constitutional_digest_id': 'digest-1',
        'previous_entry_hash': None,
        'entry_hash': 'b' * 64,
        'manifest_path': 'docs/artifacts/oracle/ORACLE_CONSTITUTIONAL_DIGEST_EVIDENCE.json',
        'manifest_sha256': 'c' * 64,
        'constitutional_digest_classification': 'CONSTITUTIONAL_STABLE_BASELINE',
        'strategic_backing_classification': 'SEALED_STRATEGIC_STACK_BACKED',
        'strategic_stack_evidence_count': 2,
        'strategic_stack_requirement_met': True,
        'latest_annual_review_id': 'annual-1',
        'evidence_status': 'VERIFIED',
        'summary_line': 'synthetic constitutional lane entry',
    }])

    output = oracle_root / 'ORACLE_CONSTITUTIONAL_GATE_REPORT.preferred.json'
    rc = main([
        'oracle-constitutional-gate',
        str(oracle_root / 'ORACLE_CONSTITUTIONAL_DIGEST_EVIDENCE.json'),
        '--repo-root', str(repo_root),
        '--search-root', str(artifacts),
        '--minimum-required-seal-status', 'FULLY_SEALED',
        '--output', str(output),
    ])
    assert rc == 0
    payload = json.loads(output.read_text(encoding='utf-8'))
    assert payload['trust_status'] == 'TRUSTED'
    assert payload['strategic_stack_requirement_met'] is True
    assert payload['strategic_stack_evidence_count'] == 2
    assert payload['preferred_strategic_backing_source'] == 'constitutional_lane'
    assert payload['preferred_strategic_backing_classification'] == 'SEALED_STRATEGIC_STACK_BACKED'
