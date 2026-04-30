from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from strategy_validator.cli.rollout_ops import main
from strategy_validator.control_plane import (
    assess_governance_plane,
    build_operator_control_plane_bundle_request,
    build_operator_escalation_closure_request,
    build_operator_supervisor_review_request,
    materialize_governance_work_queue_state,
    materialize_operator_control_plane_bundle,
    materialize_operator_escalation_closure,
    materialize_operator_supervisor_review,
    run_operator_queue_query,
)


@pytest.mark.constitutional
def test_operator_escalation_closure_materializes_closed_loop_status(tmp_path: Path) -> None:
    governance_plane = assess_governance_plane(
        evidence_freshness_status='EVIDENCE_CURRENT',
        evidence_integrity_status='INTEGRITY_VERIFIED',
        evidence_coverage_status='COVERAGE_COMPLETE',
        support_verification_status='SUPPORT_VERIFIED',
        support_chain_trust_status='TRUSTED',
        support_chain_remediation_status='NO_REMEDIATION',
        support_chain_remediation_actions=[],
        operator_readiness='HOLD_FOR_REFRESH',
        surface_label='status pack',
    )
    queue_state = materialize_governance_work_queue_state(governance_plane=governance_plane, issued_at_utc=datetime(2026,4,15,10,0,tzinfo=UTC))
    query = run_operator_queue_query(governance_work_queue=queue_state)
    review = materialize_operator_supervisor_review(build_operator_supervisor_review_request(review_root=tmp_path/'review', board_label='ops_board', reviewed_at_utc=datetime(2026,4,15,10,0,tzinfo=UTC)), operator_queue_query_result=query, board_label='ops_board')
    closure = materialize_operator_escalation_closure(build_operator_escalation_closure_request(closure_root=tmp_path/'closure', board_label='ops_board', closed_at_utc=datetime(2026,4,15,10,0,tzinfo=UTC)), supervisor_review=review, board_label='ops_board')
    assert closure.schema_version == 'oracle_operator_escalation_closure/v1'
    assert closure.total_item_count == review.total_review_count
    assert closure.requeued_count + closure.resolved_count + closure.open_count == closure.total_item_count
    payload = json.loads(Path(closure.summary_output_path).read_text(encoding='utf-8'))
    assert payload['items'][0]['closure_status'] in {'ESCALATION_CLOSED_RESOLVED', 'ESCALATION_CLOSED_REQUEUED', 'ESCALATION_REMAINS_OPEN'}


@pytest.mark.constitutional
def test_oracle_operator_escalation_closure_cli_emits_typed_report(tmp_path: Path) -> None:
    output_path = tmp_path/'ORACLE_OPERATOR_ESCALATION_CLOSURE_REPORT.json'
    rc = main([
        'oracle-operator-escalation-closure',
        '--issued-at-utc', '2026-04-15T10:00:00Z',
        '--surface-label', 'status pack',
        '--operator-readiness', 'HOLD_FOR_REFRESH',
        '--board-label', 'ops_board',
        '--closure-root', str(tmp_path/'closure'),
        '--output', str(output_path),
    ])
    assert rc == 0
    payload = json.loads(output_path.read_text(encoding='utf-8'))
    assert payload['schema_version'] == 'oracle_operator_escalation_closure/v1'
    assert (tmp_path/'closure'/'ORACLE_OPERATOR_ESCALATION_CLOSURE.json').exists()


@pytest.mark.constitutional
def test_operator_control_plane_bundle_carries_supervisor_review_and_closure(tmp_path: Path) -> None:
    governance_plane = assess_governance_plane(
        evidence_freshness_status='EVIDENCE_CURRENT',
        evidence_integrity_status='INTEGRITY_VERIFIED',
        evidence_coverage_status='COVERAGE_COMPLETE',
        support_verification_status='SUPPORT_VERIFIED',
        support_chain_trust_status='TRUSTED',
        support_chain_remediation_status='NO_REMEDIATION',
        support_chain_remediation_actions=[],
        operator_readiness='HOLD_FOR_REFRESH',
        surface_label='status pack',
    )
    queue_state = materialize_governance_work_queue_state(governance_plane=governance_plane, issued_at_utc=datetime(2026,4,15,10,0,tzinfo=UTC))
    bundle = materialize_operator_control_plane_bundle(
        build_operator_control_plane_bundle_request(bundle_root=tmp_path/'bundle', board_label='ops_board', emitted_at_utc=datetime(2026,4,15,10,0,tzinfo=UTC)),
        operator_queue_query_result=run_operator_queue_query(governance_work_queue=queue_state),
    )
    assert 'supervisor_review' in bundle.bundle_sections
    assert 'escalation_closure' in bundle.bundle_sections
    assert bundle.supervisor_review['schema_version'] == 'oracle_operator_supervisor_review/v1'
    assert bundle.escalation_closure['schema_version'] == 'oracle_operator_escalation_closure/v1'
    assert (tmp_path/'bundle'/'supervisor_review'/'ORACLE_OPERATOR_SUPERVISOR_REVIEW.json').exists()
    assert (tmp_path/'bundle'/'escalation_closure'/'ORACLE_OPERATOR_ESCALATION_CLOSURE.json').exists()
