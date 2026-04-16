from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from strategy_validator.cli.rollout_ops import main
from strategy_validator.contracts.oracle import OracleConstitutionalGateReport
from strategy_validator.validator.oracle_diagnostics import build_oracle_operator_diagnostic_from_report
from strategy_validator.validator.oracle_trust import trust_banner_for_constitutional_gate, trust_banner_for_lineage_verification


_NOW = datetime(2026, 4, 13, tzinfo=timezone.utc)
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


@pytest.mark.constitutional
def test_constitutional_digest_surfaces_exact_cadence_feedback(tmp_path: Path) -> None:
    repo_root = tmp_path
    annual_lane = repo_root / 'docs' / 'artifacts' / 'oracle' / 'ORACLE_ANNUAL_LANE.jsonl'
    _write_jsonl(annual_lane, [{
        'schema_version': 'oracle_annual_lane_entry/v1',
        'appended_at_utc': '2026-04-13T08:00:00Z',
        'lane_id': 'ORACLE_ANNUAL_LANE',
        'exact_evidence_support_score': 1.0,
        'exact_feedback_confirmation_count': 6,
        'exact_feedback_relief_count': 0,
        'sequence_number': 0,
        'entry_id': 'annual-entry-0',
        'annual_review_id': 'annual-0',
        'previous_entry_hash': None,
        'entry_hash': 'a' * 64,
        'manifest_path': 'annual0/ORACLE_ANNUAL_REVIEW_EVIDENCE.json',
        'manifest_sha256': 'b' * 64,
        'annual_review_classification': 'ANNUAL_STABLE_BASELINE',
        'latest_semiannual_audit_id': 'semi-0',
        'evidence_status': 'VERIFIED',
        'summary_line': 'annual stable baseline',
    }])

    output = annual_lane.with_name('ORACLE_CONSTITUTIONAL_DIGEST.json')
    markdown = annual_lane.with_name('ORACLE_CONSTITUTIONAL_DIGEST.md')
    rc = main([
        'oracle-constitutional-digest',
        '--lane-path', str(annual_lane),
        '--allow-legacy-lane-read',
        '--window-size', '1',
        '--output', str(output),
        '--markdown-output', str(markdown),
    ])
    assert rc == 0
    payload = json.loads(output.read_text(encoding='utf-8'))
    assert payload['exact_evidence_support_score'] == pytest.approx(1.0)
    assert payload['exact_feedback_confirmation_count'] == 6
    assert payload['exact_feedback_relief_count'] == 0
    assert 'exact_confirm=6' in payload['summary_line']
    rendered = markdown.read_text(encoding='utf-8')
    assert 'Exact feedback confirmations: 6' in rendered


@pytest.mark.constitutional
def test_lineage_and_gate_reasons_surface_exact_cadence_feedback(tmp_path: Path) -> None:
    repo_root = tmp_path
    artifacts = repo_root / 'docs' / 'artifacts'
    oracle_root = artifacts / 'oracle'

    _write_json(artifacts / 'final_rollout_closure' / 'CLOSURE_SNAPSHOT.json', {})
    for filename in REQUIRED_FILENAMES:
        _write_json(oracle_root / filename, {})
    _write_json(
        oracle_root / 'ORACLE_CONSTITUTIONAL_DIGEST_EVIDENCE.json',
        {
            'schema_version': 'oracle_constitutional_digest_evidence_manifest/v1',
            'generated_at_utc': '2026-04-13T00:00:00Z',
            'constitutional_digest_id': 'digest-1',
            'lane_id': 'ORACLE_ANNUAL_LANE',
            'exact_evidence_support_score': 1.0,
            'exact_feedback_confirmation_count': 5,
            'exact_feedback_relief_count': 0,
            'execution_authority': 'ADVISORY_ONLY',
            'source_annual_lane_path': 'docs/artifacts/oracle/ORACLE_ANNUAL_LANE.jsonl',
            'constitutional_digest_classification': 'CONSTITUTIONAL_STABLE_BASELINE',
            'strategic_backing_classification': 'SEALED_STRATEGIC_STACK_BACKED',
            'strategic_stack_evidence_count': 2,
            'strategic_stack_requirement_met': True,
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
    _write_jsonl(oracle_root / 'ORACLE_ANNUAL_LANE.jsonl', [{'sequence_number': 0, 'entry_hash': 'a' * 64}])
    _write_jsonl(oracle_root / 'ORACLE_CONSTITUTIONAL_LANE.jsonl', [{
        'schema_version': 'oracle_constitutional_lane_entry/v1',
        'appended_at_utc': '2026-04-13T00:00:00Z',
        'lane_id': 'ORACLE_CONSTITUTIONAL_LANE',
        'exact_evidence_support_score': 1.0,
        'exact_feedback_confirmation_count': 5,
        'exact_feedback_relief_count': 0,
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

    lineage_output = oracle_root / 'ORACLE_DOCTRINE_LINEAGE_VERIFICATION.json'
    rc = main([
        'oracle-doctrine-lineage-verify',
        '--repo-root', str(repo_root),
        '--search-root', str(artifacts),
        '--output', str(lineage_output),
    ])
    assert rc == 0
    lineage_payload = json.loads(lineage_output.read_text(encoding='utf-8'))
    assert lineage_payload['exact_evidence_support_score'] == pytest.approx(1.0)
    assert lineage_payload['exact_feedback_confirmation_count'] == 5
    assert 'exact_confirm=5' in lineage_payload['summary_line']

    gate_output = oracle_root / 'ORACLE_CONSTITUTIONAL_GATE_REPORT.json'
    rc = main([
        'oracle-constitutional-gate',
        str(oracle_root / 'ORACLE_CONSTITUTIONAL_DIGEST_EVIDENCE.json'),
        '--repo-root', str(repo_root),
        '--search-root', str(artifacts),
        '--minimum-required-seal-status', 'CONSTITUTIONALLY_REPLAYABLE',
        '--output', str(gate_output),
    ])
    assert rc == 0
    gate_payload = json.loads(gate_output.read_text(encoding='utf-8'))
    assert gate_payload['exact_feedback_confirmation_count'] == 5
    assert 'exact_confirm=5' in gate_payload['summary_line']

    banner = trust_banner_for_lineage_verification(type('V', (), lineage_payload)())
    assert 'confirmations `5`' in banner.lineage_reason
    gate_report = OracleConstitutionalGateReport.model_validate(gate_payload)
    gate_banner = trust_banner_for_constitutional_gate(gate_report)
    assert 'confirmations `5`' in gate_banner.lineage_reason

    diagnostic = build_oracle_operator_diagnostic_from_report(gate_output, repo_root=repo_root)
    assert diagnostic.exact_feedback_confirmation_count == 5
    assert any('exact_feedback_confirmation_count=5' in reason for reason in diagnostic.reasons)
