from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from strategy_validator.cli.rollout_ops import main
from strategy_validator.control_plane import (
    build_operator_chronic_watch_handoff_request,
    build_operator_chronic_watch_outcome_request,
    build_operator_monitored_rejoin_activation_request,
    build_operator_monitored_rejoin_normalization_bridge_request,
    build_operator_monitored_rejoin_policy_request,
    build_operator_chronic_exit_return_bridge_request,
    build_operator_chronic_exit_certification_request,
    build_operator_freeze_release_attestation_request,
    build_operator_freeze_release_gate_request,
    build_operator_chronic_remediation_satisfaction_request,
    build_operator_chronic_remediation_mandate_ledger_request,
    build_operator_recurrence_tribunal_disposition_request,
    build_operator_recurrence_tribunal_lane_request,
    build_operator_chronic_instability_packet_request,
    build_operator_reopen_recurrence_policy_request,
    build_operator_reopen_lineage_request,
    assess_governance_plane,
    materialize_governance_work_queue_state,
    run_operator_queue_query,
    materialize_operator_chronic_watch_handoff,
    materialize_operator_chronic_watch_outcome,
    materialize_operator_monitored_rejoin_activation,
    materialize_operator_monitored_rejoin_normalization_bridge,
    materialize_operator_monitored_rejoin_policy,
    materialize_operator_chronic_exit_return_bridge,
    materialize_operator_chronic_exit_certification,
    materialize_operator_freeze_release_attestation,
    materialize_operator_freeze_release_gate,
    materialize_operator_chronic_remediation_satisfaction,
    materialize_operator_chronic_remediation_mandate_ledger,
    materialize_operator_recurrence_tribunal_disposition,
    materialize_operator_recurrence_tribunal_lane,
    materialize_operator_chronic_instability_packet,
    materialize_operator_reopen_recurrence_policy,
    materialize_operator_reopen_lineage,
)


def _watch_outcome(tmp_path: Path):
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
    disposition = materialize_operator_recurrence_tribunal_disposition(build_operator_recurrence_tribunal_disposition_request(disposition_root=tmp_path/'disposition', board_label='ops_board', reviewed_at_utc=datetime(2026,4,15,10,0,tzinfo=UTC)), recurrence_tribunal_lane=lane, board_label='ops_board')
    ledger = materialize_operator_chronic_remediation_mandate_ledger(build_operator_chronic_remediation_mandate_ledger_request(ledger_root=tmp_path/'ledger', board_label='ops_board', mandated_at_utc=datetime(2026,4,15,10,0,tzinfo=UTC)), recurrence_tribunal_disposition=disposition, board_label='ops_board')
    satisfaction = materialize_operator_chronic_remediation_satisfaction(build_operator_chronic_remediation_satisfaction_request(satisfaction_root=tmp_path/'satisfaction', board_label='ops_board', evaluated_at_utc=datetime(2026,4,15,10,0,tzinfo=UTC)), chronic_remediation_mandate_ledger=ledger, board_label='ops_board')
    gate = materialize_operator_freeze_release_gate(build_operator_freeze_release_gate_request(gate_root=tmp_path/'gate', board_label='ops_board', reviewed_at_utc=datetime(2026,4,15,10,0,tzinfo=UTC)), chronic_remediation_satisfaction=satisfaction, board_label='ops_board')
    attestation = materialize_operator_freeze_release_attestation(build_operator_freeze_release_attestation_request(attestation_root=tmp_path/'attestation', board_label='ops_board', attested_at_utc=datetime(2026,4,15,10,0,tzinfo=UTC)), freeze_release_gate=gate, board_label='ops_board')
    certification = materialize_operator_chronic_exit_certification(build_operator_chronic_exit_certification_request(certification_root=tmp_path/'certification', board_label='ops_board', certified_at_utc=datetime(2026,4,15,10,0,tzinfo=UTC)), freeze_release_attestation=attestation, board_label='ops_board')
    bridge = materialize_operator_chronic_exit_return_bridge(build_operator_chronic_exit_return_bridge_request(bridge_root=tmp_path/'bridge', board_label='ops_board', bridged_at_utc=datetime(2026,4,15,10,0,tzinfo=UTC)), chronic_exit_certification=certification, board_label='ops_board')
    policy = materialize_operator_monitored_rejoin_policy(build_operator_monitored_rejoin_policy_request(policy_root=tmp_path/'rejoin_policy', board_label='ops_board', evaluated_at_utc=datetime(2026,4,15,10,0,tzinfo=UTC)), chronic_exit_return_bridge=bridge, board_label='ops_board')
    activation = materialize_operator_monitored_rejoin_activation(build_operator_monitored_rejoin_activation_request(activation_root=tmp_path/'activation', board_label='ops_board', activated_at_utc=datetime(2026,4,15,10,0,tzinfo=UTC)), monitored_rejoin_policy=policy, board_label='ops_board')
    handoff = materialize_operator_chronic_watch_handoff(build_operator_chronic_watch_handoff_request(handoff_root=tmp_path/'handoff', board_label='ops_board', handed_off_at_utc=datetime(2026,4,15,10,0,tzinfo=UTC)), monitored_rejoin_activation=activation, board_label='ops_board')
    return materialize_operator_chronic_watch_outcome(build_operator_chronic_watch_outcome_request(outcome_root=tmp_path/'outcome', board_label='ops_board', evaluated_at_utc=datetime(2026,4,17,10,40,tzinfo=UTC)), chronic_watch_handoff=handoff, board_label='ops_board')


@pytest.mark.constitutional
def test_monitored_rejoin_normalization_bridge_materializes_typed_bridge(tmp_path: Path) -> None:
    outcome = _watch_outcome(tmp_path)
    report = materialize_operator_monitored_rejoin_normalization_bridge(build_operator_monitored_rejoin_normalization_bridge_request(bridge_root=tmp_path/'bridge', board_label='ops_board', bridged_at_utc=datetime(2026,4,17,10,40,tzinfo=UTC)), chronic_watch_outcome=outcome, board_label='ops_board')
    assert report.schema_version == 'oracle_operator_monitored_rejoin_normalization_bridge/v1'
    assert report.normalization_bridge_count >= 1
    payload = json.loads(Path(report.summary_output_path).read_text(encoding='utf-8'))
    assert payload['bridge_count'] >= 1


@pytest.mark.constitutional
def test_oracle_operator_monitored_rejoin_normalization_bridge_cli_emits_typed_report(tmp_path: Path) -> None:
    output_path = tmp_path / 'bridge_report.json'
    rc = main(['oracle-operator-monitored-rejoin-normalization-bridge','--issued-at-utc','2026-04-17T10:40:00Z','--surface-label','status pack','--board-label','ops_board','--bridge-root',str(tmp_path/'bridge'),'--prior-reopen-count','work:status_pack:release_readiness=3','--output',str(output_path)])
    assert rc == 0
    payload = json.loads(output_path.read_text(encoding='utf-8'))
    assert payload['schema_version'] == 'oracle_operator_monitored_rejoin_normalization_bridge/v1'
    assert payload['normalization_bridge_count'] >= 1
