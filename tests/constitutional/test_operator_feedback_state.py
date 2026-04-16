from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from strategy_validator.cli.rollout_ops import main
from strategy_validator.control_plane import (
    assess_governance_plane,
    build_operator_action_outcome_ledger_request,
    build_operator_feedback_state_request,
    materialize_governance_work_queue_state,
    materialize_operator_action_outcome_ledger,
    materialize_operator_feedback_state,
    run_operator_queue_query,
)


@pytest.mark.constitutional
def test_operator_feedback_state_materializes_current_state(tmp_path: Path) -> None:
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
    ledger = materialize_operator_action_outcome_ledger(
        build_operator_action_outcome_ledger_request(ledger_root=tmp_path / 'outcomes', board_label='ops_board', outcome_state='EXECUTED', actor_label='jp', emitted_at_utc=datetime(2026, 4, 15, 10, 0, tzinfo=UTC)),
        operator_queue_query_result=query,
        board_label='ops_board',
    )
    state = materialize_operator_feedback_state(
        build_operator_feedback_state_request(state_root=tmp_path / 'state', board_label='ops_board', emitted_at_utc=datetime(2026, 4, 15, 10, 0, tzinfo=UTC)),
        operator_queue_query_result=query,
        action_outcome_ledger=ledger,
        board_label='ops_board',
    )
    assert state.work_item_count == 1
    assert state.items[0].current_state == 'EXECUTED'
    assert state.items[0].actor_label == 'jp'


@pytest.mark.constitutional
def test_oracle_operator_feedback_state_cli_emits_typed_report(tmp_path: Path) -> None:
    output_path = tmp_path / 'ORACLE_OPERATOR_FEEDBACK_STATE_REPORT.json'
    rc = main([
        'oracle-operator-feedback-state',
        '--issued-at-utc', '2026-04-15T10:00:00Z',
        '--surface-label', 'status pack',
        '--board-label', 'ops_board',
        '--state-root', str(tmp_path / 'state_bundle'),
        '--outcome-state', 'EXECUTED',
        '--actor-label', 'jp',
        '--output', str(output_path),
    ])
    assert rc == 0
    payload = json.loads(output_path.read_text(encoding='utf-8'))
    assert payload['schema_version'] == 'oracle_operator_feedback_state/v1'
    assert payload['items'][0]['current_state'] == 'EXECUTED'
