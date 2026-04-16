from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from strategy_validator.cli.rollout_ops import main
from strategy_validator.control_plane import (
    assess_governance_plane,
    build_operator_control_plane_bundle_request,
    build_operator_reentry_acceptance_request,
    build_operator_reentry_assignment_request,
    build_operator_reentry_completion_request,
    build_operator_reentry_queue_state_request,
    build_operator_reentry_reassignment_request,
    materialize_governance_work_queue_state,
    materialize_operator_control_plane_bundle,
    materialize_operator_reentry_acceptance,
    materialize_operator_reentry_assignment,
    materialize_operator_reentry_completion,
    materialize_operator_reentry_queue_state,
    materialize_operator_reentry_reassignment,
    run_operator_queue_query,
)


@pytest.mark.constitutional
def test_operator_reentry_completion_materializes_completion_and_return_to_normal(tmp_path: Path) -> None:
    governance_plane = assess_governance_plane(
        evidence_freshness_status='EVIDENCE_CURRENT',
        evidence_integrity_status='INTEGRITY_VERIFIED',
        evidence_coverage_status='COVERAGE_COMPLETE',
        support_verification_status='SUPPORT_VERIFIED',
        support_chain_trust_status='TRUSTED',
        support_chain_remediation_status='REMEDIATION_REQUIRED',
        support_chain_remediation_actions=['repair dispatch guard'],
        operator_readiness='READY_FOR_REVIEW',
        surface_label='status pack',
    )
    queue_state = materialize_governance_work_queue_state(
        governance_plane=governance_plane,
        issued_at_utc=datetime(2026, 4, 15, 10, 0, tzinfo=UTC),
    )
    query = run_operator_queue_query(governance_work_queue=queue_state)
    reentry = materialize_operator_reentry_queue_state(
        build_operator_reentry_queue_state_request(reentry_root=tmp_path / 'reentry', board_label='ops_board', reopened_at_utc=datetime(2026, 4, 15, 10, 0, tzinfo=UTC)),
        operator_queue_query_result=query,
        board_label='ops_board',
    )
    assignment = materialize_operator_reentry_assignment(
        build_operator_reentry_assignment_request(assignment_root=tmp_path / 'assignment', board_label='ops_board', assigned_at_utc=datetime(2026, 4, 15, 10, 0, tzinfo=UTC)),
        reentry_queue_state=reentry,
        board_label='ops_board',
    )
    acceptance = materialize_operator_reentry_acceptance(
        build_operator_reentry_acceptance_request(acceptance_root=tmp_path / 'acceptance', board_label='ops_board', accepted_at_utc=datetime(2026, 4, 15, 10, 0, tzinfo=UTC)),
        reentry_assignment=assignment,
        board_label='ops_board',
    )
    reassignment = materialize_operator_reentry_reassignment(
        build_operator_reentry_reassignment_request(reassignment_root=tmp_path / 'reassignment', board_label='ops_board', evaluated_at_utc=datetime(2026, 4, 15, 10, 5, tzinfo=UTC)),
        operator_queue_query_result=query,
        board_label='ops_board',
    )
    report = materialize_operator_reentry_completion(
        build_operator_reentry_completion_request(completion_root=tmp_path / 'completion', board_label='ops_board', completed_at_utc=datetime(2026, 4, 15, 10, 5, tzinfo=UTC)),
        reentry_reassignment=reassignment,
        reentry_acceptance=acceptance,
        board_label='ops_board',
    )

    assert report.schema_version == 'oracle_operator_reentry_completion/v1'
    assert report.total_item_count >= 1
    payload = json.loads(Path(report.summary_output_path).read_text(encoding='utf-8'))
    assert payload['items'][0]['completion_state'] in {
        'REMEDIATION_COMPLETED_VERIFIED',
        'REMEDIATION_OPEN_PENDING_ACKNOWLEDGEMENT',
        'REMEDIATION_CYCLE_CLOSED_REASSIGNED',
        'REMEDIATION_CYCLE_ESCALATED',
        'REMEDIATION_CYCLE_PREPARED_FOR_REASSIGNMENT',
    }


@pytest.mark.constitutional
def test_oracle_operator_reentry_completion_cli_emits_typed_report(tmp_path: Path) -> None:
    output_path = tmp_path / 'ORACLE_OPERATOR_REENTRY_COMPLETION_REPORT.json'
    rc = main([
        'oracle-operator-reentry-completion',
        '--issued-at-utc', '2026-04-15T10:05:00Z',
        '--accepted-at-utc', '2026-04-15T10:00:00Z',
        '--surface-label', 'status pack',
        '--board-label', 'ops_board',
        '--completion-root', str(tmp_path / 'completion'),
        '--output', str(output_path),
    ])
    assert rc == 0
    payload = json.loads(output_path.read_text(encoding='utf-8'))
    assert payload['schema_version'] == 'oracle_operator_reentry_completion/v1'
    assert (tmp_path / 'completion' / 'ORACLE_OPERATOR_REENTRY_COMPLETION.json').exists()


@pytest.mark.constitutional
def test_control_plane_bundle_includes_reentry_completion(tmp_path: Path) -> None:
    governance_plane = assess_governance_plane(
        evidence_freshness_status='EVIDENCE_CURRENT',
        evidence_integrity_status='INTEGRITY_VERIFIED',
        evidence_coverage_status='COVERAGE_COMPLETE',
        support_verification_status='SUPPORT_VERIFIED',
        support_chain_trust_status='TRUSTED',
        support_chain_remediation_status='REMEDIATION_REQUIRED',
        support_chain_remediation_actions=['repair dispatch guard'],
        operator_readiness='READY_FOR_REVIEW',
        surface_label='status pack',
    )
    queue_state = materialize_governance_work_queue_state(
        governance_plane=governance_plane,
        issued_at_utc=datetime(2026, 4, 15, 10, 5, tzinfo=UTC),
    )
    bundle_root = tmp_path / 'bundle'
    bundle = materialize_operator_control_plane_bundle(
        build_operator_control_plane_bundle_request(bundle_root=bundle_root, board_label='ops_board', emitted_at_utc=datetime(2026, 4, 15, 10, 5, tzinfo=UTC)),
        operator_queue_query_result=run_operator_queue_query(governance_work_queue=queue_state),
    )
    payload = json.loads(Path(bundle.summary_output_path).read_text(encoding='utf-8'))
    assert 'reentry_completion' in bundle.bundle_sections
    assert payload['reentry_completion']['schema_version'] == 'oracle_operator_reentry_completion/v1'
    assert (bundle_root / 'reentry_completion' / 'ORACLE_OPERATOR_REENTRY_COMPLETION.json').exists()
