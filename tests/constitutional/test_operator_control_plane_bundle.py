from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from strategy_validator.cli.rollout_ops import main
from strategy_validator.control_plane import (
    assess_governance_plane,
    build_operator_control_plane_bundle_request,
    materialize_governance_work_queue_state,
    materialize_operator_control_plane_bundle,
    render_operator_control_plane_bundle_markdown_lines,
    run_operator_queue_query,
)


@pytest.mark.constitutional
def test_operator_control_plane_bundle_materializes_durable_artifact_family(tmp_path: Path) -> None:
    governance_plane = assess_governance_plane(
        evidence_freshness_status='EVIDENCE_CURRENT',
        evidence_integrity_status='INTEGRITY_VERIFIED',
        evidence_coverage_status='COVERAGE_COMPLETE',
        support_verification_status='SUPPORT_VERIFIED',
        support_chain_trust_status='TRUSTED',
        support_chain_remediation_status='NO_REMEDIATION',
        support_chain_remediation_actions=[],
        operator_readiness='READY_FOR_REVIEW',
        surface_label='status pack',
    )
    queue_state = materialize_governance_work_queue_state(governance_plane=governance_plane, issued_at_utc=datetime(2026, 4, 15, 10, 0, tzinfo=UTC))
    query = run_operator_queue_query(governance_work_queue=queue_state)
    bundle = materialize_operator_control_plane_bundle(build_operator_control_plane_bundle_request(bundle_root=tmp_path / 'control_plane_bundle', board_label='ops_board', emitted_at_utc=datetime(2026, 4, 15, 10, 0, tzinfo=UTC)), operator_queue_query_result=query)
    assert bundle.schema_version == 'oracle_operator_control_plane_bundle/v1'
    assert bundle.board_label == 'ops_board'
    assert 'decision_journal' in bundle.bundle_sections
    assert 'feedback_state' in bundle.bundle_sections
    assert 'escalation_routing' in bundle.bundle_sections
    payload = json.loads(Path(bundle.summary_output_path).read_text(encoding='utf-8'))
    assert payload['action_contract']['contract_count'] == 1
    assert payload['decision_journal']['event_count'] >= 1
    assert 'escalation_routing' in payload
    assert 'freeze_release_attestation' in payload
    assert 'chronic_exit_certification' in payload
    assert payload['feedback_state']['work_item_count'] == 1
    assert (tmp_path / 'control_plane_bundle' / 'decision_journal' / 'ORACLE_OPERATOR_DECISION_JOURNAL.json').exists()
    assert (tmp_path / 'control_plane_bundle' / 'action_outcomes' / 'ORACLE_OPERATOR_ACTION_OUTCOME_LEDGER.json').exists()
    assert (tmp_path / 'control_plane_bundle' / 'feedback_state' / 'ORACLE_OPERATOR_FEEDBACK_STATE.json').exists()


@pytest.mark.constitutional
def test_operator_control_plane_bundle_markdown_renders_section_summary(tmp_path: Path) -> None:
    governance_plane = assess_governance_plane(
        evidence_freshness_status='EVIDENCE_CURRENT',
        evidence_integrity_status='INTEGRITY_VERIFIED',
        evidence_coverage_status='COVERAGE_COMPLETE',
        support_verification_status='SUPPORT_VERIFIED',
        support_chain_trust_status='TRUSTED',
        support_chain_remediation_status='NO_REMEDIATION',
        support_chain_remediation_actions=[],
        operator_readiness='READY_FOR_REVIEW',
        surface_label='status pack',
    )
    queue_state = materialize_governance_work_queue_state(governance_plane=governance_plane, issued_at_utc=datetime(2026, 4, 15, 10, 0, tzinfo=UTC))
    bundle = materialize_operator_control_plane_bundle(build_operator_control_plane_bundle_request(bundle_root=tmp_path / 'control_plane_bundle', board_label='ops_board', emitted_at_utc=datetime(2026, 4, 15, 10, 0, tzinfo=UTC)), operator_queue_query_result=run_operator_queue_query(governance_work_queue=queue_state))
    rendered = '\n'.join(render_operator_control_plane_bundle_markdown_lines(bundle))
    assert 'Operator Control Plane Bundle' in rendered
    assert 'Sections:' in rendered
    assert 'Action contracts:' in rendered
    assert 'Freeze release attestation:' in rendered
    assert 'Chronic exit certification:' in rendered


@pytest.mark.constitutional
def test_oracle_operator_control_plane_bundle_cli_emits_typed_report(tmp_path: Path) -> None:
    output_path = tmp_path / 'ORACLE_OPERATOR_CONTROL_PLANE_BUNDLE_REPORT.json'
    bundle_root = tmp_path / 'control_plane_bundle'
    rc = main([
        'oracle-operator-control-plane-bundle',
        '--issued-at-utc', '2026-04-15T10:00:00Z',
        '--surface-label', 'status pack',
        '--board-label', 'ops_board',
        '--bundle-root', str(bundle_root),
        '--outcome-state', 'EXECUTED',
        '--actor-label', 'jp',
        '--output', str(output_path),
    ])
    assert rc == 0
    payload = json.loads(output_path.read_text(encoding='utf-8'))
    assert payload['schema_version'] == 'oracle_operator_control_plane_bundle/v1'
    assert payload['board_label'] == 'ops_board'
    assert payload['action_outcome_ledger']['entries'][0]['actor_label'] == 'jp'
    assert 'chronic_exit_return_bridge' in payload
    assert 'monitored_rejoin_policy' in payload
    assert payload['normalization_bridge_activation']['schema_version'] == 'oracle_operator_normalization_bridge_activation/v1'
    assert payload['chronic_watch_audit_convergence']['schema_version'] == 'oracle_operator_chronic_watch_audit_convergence/v1'
    assert payload['converged_normalization_attestation']['schema_version'] == 'oracle_operator_converged_normalization_attestation/v1'
    assert payload['chronic_origin_restoration_provenance']['schema_version'] == 'oracle_operator_chronic_origin_restoration_provenance/v1'
    assert (bundle_root / 'ORACLE_OPERATOR_CONTROL_PLANE_BUNDLE.json').exists()
    assert (bundle_root / 'ORACLE_OPERATOR_CONTROL_PLANE_BUNDLE.md').exists()
    assert 'provenance_aware_drift_policy' in payload
    assert 'chronic_origin_restoration_audit_overlay' in payload
