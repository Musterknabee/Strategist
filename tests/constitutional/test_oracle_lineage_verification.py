from __future__ import annotations

import json
from pathlib import Path

import pytest

from strategy_validator.cli.rollout_ops import main


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


@pytest.mark.constitutional
def test_oracle_lineage_verification_reports_fully_sealed_when_all_layers_exist(tmp_path: Path) -> None:
    repo_root = tmp_path
    artifacts = repo_root / 'docs' / 'artifacts'

    _write_json(artifacts / 'final_rollout_closure' / 'CLOSURE_SNAPSHOT.json', {})
    _write_json(artifacts / 'final_rollout_closure' / 'GOVERNED_EXCEPTION_MEMO.json', {})

    oracle_root = artifacts / 'oracle'
    _write_valid_strategic_stack_manifest(oracle_root / 'ORACLE_STRATEGIC_STACK_EVIDENCE.json')
    for filename in [
        'ORACLE_EVIDENCE.json',
        'ORACLE_TRANSITION_EVIDENCE.json',
        'ORACLE_MEMORY_REVIEW_EVIDENCE.json',
        'ORACLE_WEEKLY_DIGEST_EVIDENCE.json',
        'ORACLE_DOCTRINE_DRIFT_EVIDENCE.json',
        'ORACLE_MONTHLY_DIGEST_EVIDENCE.json',
        'ORACLE_QUARTERLY_REVIEW_EVIDENCE.json',
        'ORACLE_SEMIANNUAL_AUDIT_EVIDENCE.json',
        'ORACLE_ANNUAL_REVIEW_EVIDENCE.json',
        'ORACLE_CONSTITUTIONAL_DIGEST_EVIDENCE.json',
    ]:
        _write_json(oracle_root / filename, {})

    _write_jsonl(oracle_root / 'ORACLE_ANNUAL_LANE.jsonl', [
        {'sequence_number': 0, 'entry_hash': 'a' * 64},
    ])
    _write_jsonl(oracle_root / 'ORACLE_CONSTITUTIONAL_LANE.jsonl', [
        {'sequence_number': 0, 'entry_hash': 'b' * 64},
    ])

    output = oracle_root / 'ORACLE_DOCTRINE_LINEAGE_VERIFICATION.json'
    markdown = oracle_root / 'ORACLE_DOCTRINE_LINEAGE_VERIFICATION.md'
    rc = main([
        'oracle-doctrine-lineage-verify',
        '--repo-root', str(repo_root),
        '--search-root', str(artifacts),
        '--output', str(output),
        '--markdown-output', str(markdown),
    ])
    assert rc == 0

    payload = json.loads(output.read_text(encoding='utf-8'))
    assert payload['seal_status'] == 'FULLY_SEALED'
    assert payload['completeness_percent'] == 100
    assert payload['missing_required_layers'] == []
    assert payload['parse_failures'] == []
    rendered = markdown.read_text(encoding='utf-8')
    assert 'ORACLE DOCTRINE LINEAGE VERIFICATION' in rendered
    assert '## Trust explanation' in rendered
    assert 'MISSING_REQUIRED_LAYERS' not in rendered


@pytest.mark.constitutional
def test_oracle_lineage_verification_reports_advisory_only_incomplete_when_ladder_is_sparse(tmp_path: Path) -> None:
    repo_root = tmp_path
    artifacts = repo_root / 'docs' / 'artifacts'
    oracle_root = artifacts / 'oracle'

    _write_json(artifacts / 'final_rollout_closure' / 'CLOSURE_SNAPSHOT.json', {})
    _write_json(oracle_root / 'ORACLE_EVIDENCE.json', {})
    _write_json(oracle_root / 'ORACLE_TRANSITION_EVIDENCE.json', {})

    output = oracle_root / 'ORACLE_DOCTRINE_LINEAGE_VERIFICATION.json'
    rc = main([
        'oracle-doctrine-lineage-verify',
        '--repo-root', str(repo_root),
        '--search-root', str(artifacts),
        '--output', str(output),
    ])
    assert rc == 2

    payload = json.loads(output.read_text(encoding='utf-8'))
    assert payload['seal_status'] == 'ADVISORY_ONLY_INCOMPLETE'
    assert 'oracle_constitutional_digest_evidence' in payload['missing_required_layers']
    assert payload['completeness_percent'] < 100



@pytest.mark.constitutional
def test_oracle_lineage_verification_requires_strategic_stack_for_strategist_grounded_replay(tmp_path: Path) -> None:
    repo_root = tmp_path
    artifacts = repo_root / 'docs' / 'artifacts'
    oracle_root = artifacts / 'oracle'

    _write_json(artifacts / 'final_rollout_closure' / 'CLOSURE_SNAPSHOT.json', {})
    _write_json(artifacts / 'final_rollout_closure' / 'GOVERNED_EXCEPTION_MEMO.json', {})
    for filename in [
        'ORACLE_EVIDENCE.json',
        'ORACLE_TRANSITION_EVIDENCE.json',
        'ORACLE_MEMORY_REVIEW_EVIDENCE.json',
        'ORACLE_WEEKLY_DIGEST_EVIDENCE.json',
        'ORACLE_DOCTRINE_DRIFT_EVIDENCE.json',
        'ORACLE_MONTHLY_DIGEST_EVIDENCE.json',
        'ORACLE_QUARTERLY_REVIEW_EVIDENCE.json',
        'ORACLE_SEMIANNUAL_AUDIT_EVIDENCE.json',
        'ORACLE_ANNUAL_REVIEW_EVIDENCE.json',
        'ORACLE_CONSTITUTIONAL_DIGEST_EVIDENCE.json',
    ]:
        _write_json(oracle_root / filename, {})
    _write_jsonl(oracle_root / 'ORACLE_ANNUAL_LANE.jsonl', [{'sequence_number': 0, 'entry_hash': 'a' * 64}])
    _write_jsonl(oracle_root / 'ORACLE_CONSTITUTIONAL_LANE.jsonl', [{'sequence_number': 0, 'entry_hash': 'b' * 64}])

    output = oracle_root / 'ORACLE_DOCTRINE_LINEAGE_VERIFICATION.json'
    rc = main([
        'oracle-doctrine-lineage-verify',
        '--repo-root', str(repo_root),
        '--search-root', str(artifacts),
        '--output', str(output),
    ])
    assert rc == 0
    payload = json.loads(output.read_text(encoding='utf-8'))
    assert payload['seal_status'] == 'FULLY_SEALED'
    assert payload['strategic_stack_evidence_count'] == 0
    assert payload['strategic_stack_requirement_met'] is False
    assert any('strategic stack evidence' in item.lower() for item in payload['operator_actions'])


@pytest.mark.constitutional
def test_oracle_doctrine_lineage_prefers_artifact_native_backing_metadata(tmp_path: Path) -> None:
    repo_root = tmp_path
    artifacts = repo_root / "docs" / "artifacts"
    oracle_root = artifacts / "oracle"

    _write_json(artifacts / "final_rollout_closure" / "CLOSURE_SNAPSHOT.json", {})
    _write_json(artifacts / "final_rollout_closure" / "GOVERNED_EXCEPTION_MEMO.json", {})
    for filename in [
        "ORACLE_EVIDENCE.json",
        "ORACLE_TRANSITION_EVIDENCE.json",
        "ORACLE_MEMORY_REVIEW_EVIDENCE.json",
        "ORACLE_WEEKLY_DIGEST_EVIDENCE.json",
        "ORACLE_DOCTRINE_DRIFT_EVIDENCE.json",
        "ORACLE_MONTHLY_DIGEST_EVIDENCE.json",
        "ORACLE_QUARTERLY_REVIEW_EVIDENCE.json",
        "ORACLE_SEMIANNUAL_AUDIT_EVIDENCE.json",
        "ORACLE_ANNUAL_REVIEW_EVIDENCE.json",
    ]:
        _write_json(oracle_root / filename, {})
    _write_json(oracle_root / "ORACLE_CONSTITUTIONAL_DIGEST_EVIDENCE.json", {
        "schema_version": "oracle_constitutional_digest_evidence_manifest/v1",
        "generated_at_utc": "2026-04-13T00:00:00Z",
        "constitutional_digest_id": "digest-1",
        "lane_id": "ORACLE_ANNUAL_LANE",
        "execution_authority": "ADVISORY_ONLY",
        "source_annual_lane_path": "docs/artifacts/oracle/ORACLE_ANNUAL_LANE.jsonl",
        "constitutional_digest_classification": "CONSTITUTIONAL_STABLE_BASELINE",
        "strategic_backing_classification": "SEALED_STRATEGIC_STACK_BACKED",
        "strategic_stack_evidence_count": 3,
        "strategic_stack_requirement_met": True,
        "window_entry_count": 1,
        "window_end_sequence_number": 0,
        "latest_annual_review_id": "annual-1",
        "latest_annual_review_classification": "ANNUAL_STABLE_BASELINE",
        "integrity_status": "VERIFIED",
        "subjects": [],
        "missing_artifact_paths": [],
        "summary_line": "synthetic constitutional digest evidence",
    })
    _write_jsonl(oracle_root / "ORACLE_ANNUAL_LANE.jsonl", [{"sequence_number": 0, "entry_hash": "a" * 64}])
    _write_jsonl(oracle_root / "ORACLE_CONSTITUTIONAL_LANE.jsonl", [{
        "schema_version": "oracle_constitutional_lane_entry/v1",
        "appended_at_utc": "2026-04-13T00:00:00Z",
        "lane_id": "ORACLE_CONSTITUTIONAL_LANE",
        "sequence_number": 0,
        "entry_id": "entry-1",
        "constitutional_digest_id": "digest-1",
        "previous_entry_hash": None,
        "entry_hash": "b" * 64,
        "manifest_path": "docs/artifacts/oracle/ORACLE_CONSTITUTIONAL_DIGEST_EVIDENCE.json",
        "manifest_sha256": "c" * 64,
        "constitutional_digest_classification": "CONSTITUTIONAL_STABLE_BASELINE",
        "strategic_backing_classification": "SEALED_STRATEGIC_STACK_BACKED",
        "strategic_stack_evidence_count": 3,
        "strategic_stack_requirement_met": True,
        "latest_annual_review_id": "annual-1",
        "evidence_status": "VERIFIED",
        "summary_line": "synthetic constitutional lane entry"
    }])

    output = oracle_root / "ORACLE_DOCTRINE_LINEAGE_VERIFICATION.json"
    rc = main([
        "oracle-doctrine-lineage-verify",
        "--repo-root", str(repo_root),
        "--search-root", str(artifacts),
        "--output", str(output),
    ])
    assert rc == 0
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["strategic_stack_requirement_met"] is True
    assert payload["strategic_stack_evidence_count"] == 3
    assert payload["preferred_strategic_backing_source"] == "constitutional_lane"
    assert payload["preferred_strategic_backing_classification"] == "SEALED_STRATEGIC_STACK_BACKED"
    assert any("preferring sealed artifact metadata" in item.lower() for item in payload["integrity_warnings"])
