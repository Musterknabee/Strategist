from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from strategy_validator.cli.rollout_ops import main
from strategy_validator.control_plane import (
    assess_governance_plane,
    build_operator_recurrence_tribunal_disposition_request,
    build_operator_reopen_lineage_request,
    build_operator_reopen_recurrence_policy_request,
    build_operator_chronic_instability_packet_request,
    build_operator_recurrence_tribunal_lane_request,
    materialize_governance_work_queue_state,
    materialize_operator_reopen_lineage,
    materialize_operator_reopen_recurrence_policy,
    materialize_operator_chronic_instability_packet,
    materialize_operator_recurrence_tribunal_lane,
    materialize_operator_recurrence_tribunal_disposition,
    run_operator_queue_query,
)


@pytest.mark.constitutional
def test_operator_recurrence_tribunal_disposition_materializes_durable_review_decision(tmp_path: Path) -> None:
    governance_plane = assess_governance_plane(
        evidence_freshness_status='EVIDENCE_CURRENT', evidence_integrity_status='INTEGRITY_VERIFIED', evidence_coverage_status='COVERAGE_COMPLETE',
        support_verification_status='SUPPORT_VERIFIED', support_chain_trust_status='TRUSTED', support_chain_remediation_status='NO_REMEDIATION',
        support_chain_remediation_actions=[], operator_readiness='READY_FOR_REVIEW', surface_label='status pack')
    queue_state = materialize_governance_work_queue_state(governance_plane=governance_plane, issued_at_utc=datetime(2026,4,15,10,0,tzinfo=UTC))
    query = run_operator_queue_query(governance_work_queue=queue_state)
    lineage = materialize_operator_reopen_lineage(build_operator_reopen_lineage_request(lineage_root=tmp_path/'lineage', board_label='ops_board', analyzed_at_utc=datetime(2026,4,15,10,0,tzinfo=UTC), prior_reopen_counts={'work:status_pack:release_readiness': 3}), operator_queue_query_result=query, board_label='ops_board')
    recurrence = materialize_operator_reopen_recurrence_policy(build_operator_reopen_recurrence_policy_request(policy_root=tmp_path/'policy', board_label='ops_board', evaluated_at_utc=datetime(2026,4,15,10,0,tzinfo=UTC)), reopen_lineage=lineage, board_label='ops_board')
    packet = materialize_operator_chronic_instability_packet(build_operator_chronic_instability_packet_request(packet_root=tmp_path/'packet', board_label='ops_board', emitted_at_utc=datetime(2026,4,15,10,0,tzinfo=UTC)), reopen_recurrence_policy=recurrence, board_label='ops_board')
    lane = materialize_operator_recurrence_tribunal_lane(build_operator_recurrence_tribunal_lane_request(tribunal_root=tmp_path/'lane', board_label='ops_board', reviewed_at_utc=datetime(2026,4,15,10,0,tzinfo=UTC)), chronic_instability_packet=packet, board_label='ops_board')
    report = materialize_operator_recurrence_tribunal_disposition(build_operator_recurrence_tribunal_disposition_request(disposition_root=tmp_path/'disposition', board_label='ops_board', reviewed_at_utc=datetime(2026,4,15,10,0,tzinfo=UTC)), recurrence_tribunal_lane=lane, board_label='ops_board')
    assert report.schema_version == 'oracle_operator_recurrence_tribunal_disposition/v1'
    assert report.mandate_required_count >= 1
    payload = json.loads(Path(report.summary_output_path).read_text(encoding='utf-8'))
    assert payload['freeze_return_count'] >= 1


@pytest.mark.constitutional
def test_oracle_operator_recurrence_tribunal_disposition_cli_emits_typed_report(tmp_path: Path) -> None:
    output_path = tmp_path / 'disposition_report.json'
    rc = main(['oracle-operator-recurrence-tribunal-disposition','--issued-at-utc','2026-04-15T10:00:00Z','--surface-label','status pack','--board-label','ops_board','--disposition-root',str(tmp_path/'disposition'),'--prior-reopen-count','work:status_pack:release_readiness=3','--output',str(output_path)])
    assert rc == 0
    payload = json.loads(output_path.read_text(encoding='utf-8'))
    assert payload['schema_version'] == 'oracle_operator_recurrence_tribunal_disposition/v1'
    assert payload['mandate_required_count'] >= 1
