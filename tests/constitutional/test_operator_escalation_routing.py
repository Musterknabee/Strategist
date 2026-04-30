from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from strategy_validator.cli.rollout_ops import main
from strategy_validator.control_plane import (
    assess_governance_plane,
    build_operator_decision_execution_request,
    build_operator_escalation_routing_request,
    materialize_governance_work_queue_state,
    materialize_operator_decision_execution,
    materialize_operator_escalation_routing,
    run_operator_queue_query,
)


@pytest.mark.constitutional
def test_operator_escalation_routing_materializes_typed_destinations(tmp_path: Path) -> None:
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
    assert routing.schema_version == 'oracle_operator_escalation_routing/v1'
    assert routing.escalation_route_count == 1
    assert routing.items[0].routing_status == 'ROUTED_FOR_ESCALATION'
    assert routing.items[0].policy_reason_code in {'CLAIM_INOPERABLE', 'DISPATCH_BLOCKED', 'ESCALATION_ONLY'}


@pytest.mark.constitutional
def test_oracle_operator_escalation_routing_cli_emits_typed_report(tmp_path: Path) -> None:
    output_path = tmp_path / 'ORACLE_OPERATOR_ESCALATION_ROUTING_REPORT.json'
    rc = main([
        'oracle-operator-escalation-routing',
        '--issued-at-utc', '2026-04-15T10:00:00Z',
        '--surface-label', 'status pack',
        '--operator-readiness', 'HOLD_FOR_REFRESH',
        '--board-label', 'ops_board',
        '--routing-root', str(tmp_path / 'routing_bundle'),
        '--desired-transition', 'EXECUTED',
        '--actor-label', 'jp',
        '--output', str(output_path),
    ])
    assert rc == 0
    payload = json.loads(output_path.read_text(encoding='utf-8'))
    assert payload['schema_version'] == 'oracle_operator_escalation_routing/v1'
    assert payload['escalation_route_count'] == 1
    assert payload['items'][0]['routing_status'] == 'ROUTED_FOR_ESCALATION'
