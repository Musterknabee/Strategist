from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from strategy_validator.cli.rollout_ops import main
from strategy_validator.control_plane import (
    assess_governance_plane,
    build_operator_decision_execution_request,
    build_operator_escalation_packet_request,
    build_operator_escalation_routing_request,
    build_operator_escalation_sla_request,
    build_operator_control_plane_bundle_request,
    materialize_governance_work_queue_state,
    materialize_operator_control_plane_bundle,
    materialize_operator_decision_execution,
    materialize_operator_escalation_packet,
    materialize_operator_escalation_routing,
    materialize_operator_escalation_sla,
    run_operator_queue_query,
)


@pytest.mark.constitutional
def test_operator_escalation_sla_materializes_urgency_and_due_state(tmp_path: Path) -> None:
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
    execution = materialize_operator_decision_execution(
        build_operator_decision_execution_request(execution_root=tmp_path / 'execution', board_label='ops_board', desired_transition='EXECUTED', actor_label='jp', emitted_at_utc=datetime(2026, 4, 15, 10, 0, tzinfo=UTC)),
        operator_queue_query_result=query,
        board_label='ops_board',
    )
    routing = materialize_operator_escalation_routing(
        build_operator_escalation_routing_request(routing_root=tmp_path / 'routing', board_label='ops_board'),
        decision_execution=execution,
        operator_queue_query_result=query,
        board_label='ops_board',
    )
    packet = materialize_operator_escalation_packet(
        build_operator_escalation_packet_request(packet_root=tmp_path / 'packet', board_label='ops_board'),
        escalation_routing=routing,
        decision_execution=execution,
        operator_queue_query_result=query,
        board_label='ops_board',
    )
    sla = materialize_operator_escalation_sla(
        build_operator_escalation_sla_request(
            sla_root=tmp_path / 'sla',
            board_label='ops_board',
            escalation_started_at_utc=datetime(2026, 4, 15, 9, 0, tzinfo=UTC),
            evaluated_at_utc=datetime(2026, 4, 15, 10, 0, tzinfo=UTC),
        ),
        escalation_packet=packet,
        board_label='ops_board',
    )
    assert sla.schema_version == 'oracle_operator_escalation_sla/v1'
    assert sla.escalated_item_count == 1
    assert sla.urgent_item_count == 1
    assert sla.items[0].aging_status in {'DUE_SOON', 'BREACHED'}
    assert sla.items[0].review_urgency == 'IMMEDIATE'


@pytest.mark.constitutional
def test_oracle_operator_escalation_sla_cli_emits_typed_report(tmp_path: Path) -> None:
    output_path = tmp_path / 'ORACLE_OPERATOR_ESCALATION_SLA_REPORT.json'
    rc = main([
        'oracle-operator-escalation-sla',
        '--issued-at-utc', '2026-04-15T10:00:00Z',
        '--surface-label', 'status pack',
        '--operator-readiness', 'HOLD_FOR_REFRESH',
        '--board-label', 'ops_board',
        '--sla-root', str(tmp_path / 'sla_bundle'),
        '--desired-transition', 'EXECUTED',
        '--actor-label', 'jp',
        '--escalation-started-at-utc', '2026-04-15T09:00:00Z',
        '--output', str(output_path),
    ])
    assert rc == 0
    payload = json.loads(output_path.read_text(encoding='utf-8'))
    assert payload['schema_version'] == 'oracle_operator_escalation_sla/v1'
    assert payload['escalated_item_count'] == 1
    assert payload['urgent_item_count'] == 1
    assert payload['items'][0]['review_urgency'] == 'IMMEDIATE'


@pytest.mark.constitutional
def test_operator_control_plane_bundle_carries_escalation_sla(tmp_path: Path) -> None:
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
    bundle = materialize_operator_control_plane_bundle(
        build_operator_control_plane_bundle_request(bundle_root=tmp_path / 'bundle', board_label='ops_board', emitted_at_utc=datetime(2026, 4, 15, 10, 0, tzinfo=UTC)),
        operator_queue_query_result=query,
    )
    assert 'escalation_sla' in bundle.bundle_sections
    assert bundle.escalation_sla['schema_version'] == 'oracle_operator_escalation_sla/v1'
    assert (tmp_path / 'bundle' / 'escalation_sla' / 'ORACLE_OPERATOR_ESCALATION_SLA.json').exists()
