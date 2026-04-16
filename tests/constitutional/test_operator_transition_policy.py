from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from strategy_validator.cli.rollout_ops import main
from strategy_validator.control_plane import (
    assess_governance_plane,
    build_operator_transition_policy_request,
    materialize_governance_work_queue_state,
    materialize_operator_transition_policy,
    run_operator_queue_query,
)


@pytest.mark.constitutional
def test_operator_transition_policy_materializes_governed_transitions() -> None:
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
    policy = materialize_operator_transition_policy(build_operator_transition_policy_request(board_label='ops_board'), operator_queue_query_result=query, board_label='ops_board')
    assert policy.policy_count == 1
    assert policy.items[0].policy_decision == 'ALLOW_EXECUTION'
    assert 'EXECUTED' in policy.items[0].allowed_transitions


@pytest.mark.constitutional
def test_oracle_operator_transition_policy_cli_emits_typed_report(tmp_path: Path) -> None:
    output_path = tmp_path / 'ORACLE_OPERATOR_TRANSITION_POLICY.json'
    rc = main([
        'oracle-operator-transition-policy',
        '--issued-at-utc', '2026-04-15T10:00:00Z',
        '--surface-label', 'status pack',
        '--board-label', 'ops_board',
        '--output', str(output_path),
    ])
    assert rc == 0
    payload = json.loads(output_path.read_text(encoding='utf-8'))
    assert payload['schema_version'] == 'oracle_operator_transition_policy/v1'
    assert payload['items'][0]['default_transition'] == 'EXECUTED'
