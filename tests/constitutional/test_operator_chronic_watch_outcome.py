from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from strategy_validator.cli.rollout_ops import main
from strategy_validator.control_plane import (
    assess_governance_plane,
    build_operator_chronic_watch_handoff_request,
    build_operator_chronic_watch_outcome_request,
    build_operator_control_plane_bundle_request,
    build_operator_monitored_rejoin_activation_request,
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
    materialize_governance_work_queue_state,
    materialize_operator_chronic_watch_handoff,
    materialize_operator_chronic_watch_outcome,
    materialize_operator_control_plane_bundle,
    materialize_operator_monitored_rejoin_activation,
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
    render_operator_control_plane_bundle_markdown_lines,
    run_operator_queue_query,
)


def _handoff(tmp_path: Path, *, evaluated_at: datetime):
    governance_plane = assess_governance_plane(
        evidence_freshness_status='EVIDENCE_CURRENT', evidence_integrity_status='INTEGRITY_VERIFIED', evidence_coverage_status='COVERAGE_COMPLETE',
        support_verification_status='SUPPORT_VERIFIED', support_chain_trust_status='TRUSTED', support_chain_remediation_status='NO_REMEDIATION',
        support_chain_remediation_actions=[], operator_readiness='READY_FOR_REVIEW', surface_label='status pack')
    queue_state = materialize_governance_work_queue_state(governance_plane=governance_plane, issued_at_utc=datetime(2026,4,15,10,0,tzinfo=UTC))
    query = run_operator_queue_query(governance_work_queue=queue_state)
    lineage = materialize_operator_reopen_lineage(build_operator_reopen_lineage_request(lineage_root=tmp_path/'lineage', board_label='ops_board', analyzed_at_utc=evaluated_at, prior_reopen_counts={'work:status_pack:release_readiness': 3}), operator_queue_query_result=query, board_label='ops_board')
    recurrence = materialize_operator_reopen_recurrence_policy(build_operator_reopen_recurrence_policy_request(policy_root=tmp_path/'policy', board_label='ops_board', evaluated_at_utc=evaluated_at), reopen_lineage=lineage, board_label='ops_board')
    packet = materialize_operator_chronic_instability_packet(build_operator_chronic_instability_packet_request(packet_root=tmp_path/'packet', board_label='ops_board', emitted_at_utc=evaluated_at), reopen_recurrence_policy=recurrence, board_label='ops_board')
    lane = materialize_operator_recurrence_tribunal_lane(build_operator_recurrence_tribunal_lane_request(tribunal_root=tmp_path/'lane', board_label='ops_board', reviewed_at_utc=evaluated_at), chronic_instability_packet=packet, board_label='ops_board')
    disposition = materialize_operator_recurrence_tribunal_disposition(build_operator_recurrence_tribunal_disposition_request(disposition_root=tmp_path/'disposition', board_label='ops_board', reviewed_at_utc=evaluated_at), recurrence_tribunal_lane=lane, board_label='ops_board')
    ledger = materialize_operator_chronic_remediation_mandate_ledger(build_operator_chronic_remediation_mandate_ledger_request(ledger_root=tmp_path/'ledger', board_label='ops_board', mandated_at_utc=evaluated_at), recurrence_tribunal_disposition=disposition, board_label='ops_board')
    satisfaction = materialize_operator_chronic_remediation_satisfaction(build_operator_chronic_remediation_satisfaction_request(satisfaction_root=tmp_path/'satisfaction', board_label='ops_board', evaluated_at_utc=evaluated_at), chronic_remediation_mandate_ledger=ledger, board_label='ops_board')
    gate = materialize_operator_freeze_release_gate(build_operator_freeze_release_gate_request(gate_root=tmp_path/'gate', board_label='ops_board', reviewed_at_utc=evaluated_at), chronic_remediation_satisfaction=satisfaction, board_label='ops_board')
    attestation = materialize_operator_freeze_release_attestation(build_operator_freeze_release_attestation_request(attestation_root=tmp_path/'attestation', board_label='ops_board', attested_at_utc=evaluated_at), freeze_release_gate=gate, board_label='ops_board')
    certification = materialize_operator_chronic_exit_certification(build_operator_chronic_exit_certification_request(certification_root=tmp_path/'certification', board_label='ops_board', certified_at_utc=evaluated_at), freeze_release_attestation=attestation, board_label='ops_board')
    bridge = materialize_operator_chronic_exit_return_bridge(build_operator_chronic_exit_return_bridge_request(bridge_root=tmp_path/'bridge', board_label='ops_board', bridged_at_utc=evaluated_at), chronic_exit_certification=certification, board_label='ops_board')
    policy = materialize_operator_monitored_rejoin_policy(build_operator_monitored_rejoin_policy_request(policy_root=tmp_path/'rejoin_policy', board_label='ops_board', evaluated_at_utc=evaluated_at), chronic_exit_return_bridge=bridge, board_label='ops_board')
    activation = materialize_operator_monitored_rejoin_activation(build_operator_monitored_rejoin_activation_request(activation_root=tmp_path/'activation', board_label='ops_board', activated_at_utc=evaluated_at), monitored_rejoin_policy=policy, board_label='ops_board')
    return materialize_operator_chronic_watch_handoff(build_operator_chronic_watch_handoff_request(handoff_root=tmp_path/'handoff', board_label='ops_board', handed_off_at_utc=evaluated_at), monitored_rejoin_activation=activation, board_label='ops_board')


@pytest.mark.constitutional
def test_operator_chronic_watch_outcome_materializes_stable_result(tmp_path: Path) -> None:
    evaluated_at = datetime(2026,4,17,10,40,tzinfo=UTC)
    handoff = _handoff(tmp_path, evaluated_at=datetime(2026,4,15,10,0,tzinfo=UTC))
    report = materialize_operator_chronic_watch_outcome(build_operator_chronic_watch_outcome_request(outcome_root=tmp_path/'outcome', board_label='ops_board', evaluated_at_utc=evaluated_at), chronic_watch_handoff=handoff, board_label='ops_board')
    assert report.schema_version == 'oracle_operator_chronic_watch_outcome/v1'
    assert report.stable_count >= 1
    payload = json.loads(Path(report.summary_output_path).read_text(encoding='utf-8'))
    assert payload['normalization_ready_count'] >= 1


@pytest.mark.constitutional
def test_operator_control_plane_bundle_includes_watch_outcome_and_normalization_bridge(tmp_path: Path) -> None:
    governance_plane = assess_governance_plane(
        evidence_freshness_status='EVIDENCE_CURRENT', evidence_integrity_status='INTEGRITY_VERIFIED', evidence_coverage_status='COVERAGE_COMPLETE',
        support_verification_status='SUPPORT_VERIFIED', support_chain_trust_status='TRUSTED', support_chain_remediation_status='NO_REMEDIATION',
        support_chain_remediation_actions=[], operator_readiness='READY_FOR_REVIEW', surface_label='status pack')
    queue_state = materialize_governance_work_queue_state(governance_plane=governance_plane, issued_at_utc=datetime(2026,4,15,10,0,tzinfo=UTC))
    query = run_operator_queue_query(governance_work_queue=queue_state)
    bundle = materialize_operator_control_plane_bundle(
        build_operator_control_plane_bundle_request(bundle_root=tmp_path/'bundle', board_label='ops_board', emitted_at_utc=datetime(2026,4,17,10,40,tzinfo=UTC)),
        operator_queue_query_result=query,
        reopen_lineage_request=build_operator_reopen_lineage_request(lineage_root=tmp_path/'bundle'/'reopen_lineage', board_label='ops_board', analyzed_at_utc=datetime(2026,4,17,10,40,tzinfo=UTC), prior_reopen_counts={'work:status_pack:release_readiness': 3}),
    )
    rendered = '\n'.join(render_operator_control_plane_bundle_markdown_lines(bundle))
    assert bundle.chronic_watch_outcome['stable_count'] >= 1
    assert bundle.monitored_rejoin_normalization_bridge['normalization_bridge_count'] >= 1
    assert 'Chronic watch outcome' in rendered
    assert 'Monitored rejoin normalization bridge' in rendered


@pytest.mark.constitutional
def test_oracle_operator_chronic_watch_outcome_cli_emits_typed_report(tmp_path: Path) -> None:
    output_path = tmp_path / 'outcome_report.json'
    rc = main(['oracle-operator-chronic-watch-outcome','--issued-at-utc','2026-04-17T10:40:00Z','--surface-label','status pack','--board-label','ops_board','--outcome-root',str(tmp_path/'outcome'),'--prior-reopen-count','work:status_pack:release_readiness=3','--output',str(output_path)])
    assert rc == 0
    payload = json.loads(output_path.read_text(encoding='utf-8'))
    assert payload['schema_version'] == 'oracle_operator_chronic_watch_outcome/v1'
    assert payload['normalization_ready_count'] >= 1
