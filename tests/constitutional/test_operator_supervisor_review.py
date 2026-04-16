from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from strategy_validator.cli.rollout_ops import main
from strategy_validator.control_plane import (
    assess_governance_plane,
    build_operator_escalation_packet_request,
    build_operator_escalation_routing_request,
    build_operator_escalation_sla_request,
    build_operator_supervisor_review_request,
    materialize_governance_work_queue_state,
    materialize_operator_escalation_packet,
    materialize_operator_escalation_routing,
    materialize_operator_escalation_sla,
    materialize_operator_supervisor_review,
    run_operator_queue_query,
)


@pytest.mark.constitutional
def test_operator_supervisor_review_materializes_dispositions(tmp_path: Path) -> None:
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
    queue_state = materialize_governance_work_queue_state(governance_plane=governance_plane, issued_at_utc=datetime(2026, 4, 15, 10, 0, tzinfo=UTC))
    query = run_operator_queue_query(governance_work_queue=queue_state)
    routing = materialize_operator_escalation_routing(build_operator_escalation_routing_request(routing_root=tmp_path/'routing', board_label='ops_board'), operator_queue_query_result=query, board_label='ops_board')
    packet = materialize_operator_escalation_packet(build_operator_escalation_packet_request(packet_root=tmp_path/'packet', board_label='ops_board'), escalation_routing=routing, operator_queue_query_result=query, board_label='ops_board')
    sla = materialize_operator_escalation_sla(build_operator_escalation_sla_request(sla_root=tmp_path/'sla', board_label='ops_board', evaluated_at_utc=datetime(2026,4,15,10,0,tzinfo=UTC), escalation_started_at_utc=datetime(2026,4,15,9,0,tzinfo=UTC)), escalation_packet=packet, board_label='ops_board')
    review = materialize_operator_supervisor_review(build_operator_supervisor_review_request(review_root=tmp_path/'review', board_label='ops_board', reviewed_at_utc=datetime(2026,4,15,10,0,tzinfo=UTC)), escalation_packet=packet, escalation_sla=sla, board_label='ops_board')
    assert review.schema_version == 'oracle_operator_supervisor_review/v1'
    assert review.total_review_count == len(packet.items)
    assert review.requeue_count >= 1
    payload = json.loads(Path(review.summary_output_path).read_text(encoding='utf-8'))
    assert payload['items'][0]['closure_recommendation'] in {'RETURN_TO_OPERATOR', 'KEEP_ESCALATED', 'RESOLVE_ESCALATION'}


@pytest.mark.constitutional
def test_oracle_operator_supervisor_review_cli_emits_typed_report(tmp_path: Path) -> None:
    output_path = tmp_path/'ORACLE_OPERATOR_SUPERVISOR_REVIEW_REPORT.json'
    rc = main([
        'oracle-operator-supervisor-review',
        '--issued-at-utc', '2026-04-15T10:00:00Z',
        '--surface-label', 'status pack',
        '--operator-readiness', 'HOLD_FOR_REFRESH',
        '--board-label', 'ops_board',
        '--review-root', str(tmp_path/'review'),
        '--output', str(output_path),
    ])
    assert rc == 0
    payload = json.loads(output_path.read_text(encoding='utf-8'))
    assert payload['schema_version'] == 'oracle_operator_supervisor_review/v1'
    assert (tmp_path/'review'/'ORACLE_OPERATOR_SUPERVISOR_REVIEW.json').exists()
