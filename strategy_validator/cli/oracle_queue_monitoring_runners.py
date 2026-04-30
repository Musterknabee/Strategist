from __future__ import annotations

from strategy_validator.cli.oracle_queue_runner_common import *
from strategy_validator.cli.oracle_queue_runner_common import _build_queue_state, _emit_payload, _parse_prior_reopen_counts

def cmd_oracle_operator_chronic_exit_return_bridge(ns: argparse.Namespace) -> int:
    queue_state = _build_queue_state(ns)
    query = run_operator_queue_query(operator_queue_snapshot=materialize_operator_queue_snapshot(governance_work_queue=queue_state))
    payload = materialize_operator_chronic_exit_return_bridge(
        build_operator_chronic_exit_return_bridge_request(bridge_root=Path(ns.bridge_root), board_label=ns.board_label, bridged_at_utc=parse_utc(ns.issued_at_utc)),
        chronic_exit_certification=materialize_operator_chronic_exit_certification(
            build_operator_chronic_exit_certification_request(certification_root=Path(ns.bridge_root) / 'chronic_exit_certification', board_label=ns.board_label, certified_at_utc=parse_utc(ns.issued_at_utc)),
            freeze_release_attestation=materialize_operator_freeze_release_attestation(
                build_operator_freeze_release_attestation_request(attestation_root=Path(ns.bridge_root) / 'chronic_exit_certification' / 'freeze_release_attestation', board_label=ns.board_label, attested_at_utc=parse_utc(ns.issued_at_utc)),
                freeze_release_gate=materialize_operator_freeze_release_gate(
                    build_operator_freeze_release_gate_request(gate_root=Path(ns.bridge_root) / 'chronic_exit_certification' / 'freeze_release_attestation' / 'freeze_release_gate', board_label=ns.board_label, reviewed_at_utc=parse_utc(ns.issued_at_utc)),
                    chronic_remediation_satisfaction=materialize_operator_chronic_remediation_satisfaction(
                        build_operator_chronic_remediation_satisfaction_request(satisfaction_root=Path(ns.bridge_root) / 'chronic_exit_certification' / 'freeze_release_attestation' / 'freeze_release_gate' / 'chronic_remediation_satisfaction', board_label=ns.board_label, evaluated_at_utc=parse_utc(ns.issued_at_utc)),
                        chronic_remediation_mandate_ledger=materialize_operator_chronic_remediation_mandate_ledger(
                            build_operator_chronic_remediation_mandate_ledger_request(ledger_root=Path(ns.bridge_root) / 'chronic_exit_certification' / 'freeze_release_attestation' / 'freeze_release_gate' / 'chronic_remediation_satisfaction' / 'chronic_remediation_mandate_ledger', board_label=ns.board_label, mandated_at_utc=parse_utc(ns.issued_at_utc)),
                            recurrence_tribunal_disposition=materialize_operator_recurrence_tribunal_disposition(
                                build_operator_recurrence_tribunal_disposition_request(disposition_root=Path(ns.bridge_root) / 'chronic_exit_certification' / 'freeze_release_attestation' / 'freeze_release_gate' / 'chronic_remediation_satisfaction' / 'chronic_remediation_mandate_ledger' / 'recurrence_tribunal_disposition', board_label=ns.board_label, reviewed_at_utc=parse_utc(ns.issued_at_utc)),
                                recurrence_tribunal_lane=materialize_operator_recurrence_tribunal_lane(
                                    build_operator_recurrence_tribunal_lane_request(tribunal_root=Path(ns.bridge_root) / 'chronic_exit_certification' / 'freeze_release_attestation' / 'freeze_release_gate' / 'chronic_remediation_satisfaction' / 'chronic_remediation_mandate_ledger' / 'recurrence_tribunal_disposition' / 'recurrence_tribunal_lane', board_label=ns.board_label, reviewed_at_utc=parse_utc(ns.issued_at_utc)),
                                    chronic_instability_packet=materialize_operator_chronic_instability_packet(
                                        build_operator_chronic_instability_packet_request(packet_root=Path(ns.bridge_root) / 'chronic_exit_certification' / 'freeze_release_attestation' / 'freeze_release_gate' / 'chronic_remediation_satisfaction' / 'chronic_remediation_mandate_ledger' / 'recurrence_tribunal_disposition' / 'recurrence_tribunal_lane' / 'chronic_instability_packet', board_label=ns.board_label, emitted_at_utc=parse_utc(ns.issued_at_utc)),
                                        reopen_recurrence_policy=materialize_operator_reopen_recurrence_policy(
                                            build_operator_reopen_recurrence_policy_request(policy_root=Path(ns.bridge_root) / 'chronic_exit_certification' / 'freeze_release_attestation' / 'freeze_release_gate' / 'chronic_remediation_satisfaction' / 'chronic_remediation_mandate_ledger' / 'recurrence_tribunal_disposition' / 'recurrence_tribunal_lane' / 'chronic_instability_packet' / 'reopen_recurrence_policy', board_label=ns.board_label, evaluated_at_utc=parse_utc(ns.issued_at_utc)),
                                            reopen_lineage=materialize_operator_reopen_lineage(
                                                build_operator_reopen_lineage_request(lineage_root=Path(ns.bridge_root) / 'chronic_exit_certification' / 'freeze_release_attestation' / 'freeze_release_gate' / 'chronic_remediation_satisfaction' / 'chronic_remediation_mandate_ledger' / 'recurrence_tribunal_disposition' / 'recurrence_tribunal_lane' / 'chronic_instability_packet' / 'reopen_recurrence_policy' / 'reopen_lineage', board_label=ns.board_label, analyzed_at_utc=parse_utc(ns.issued_at_utc), prior_reopen_counts=_parse_prior_reopen_counts(ns.prior_reopen_count)),
                                                operator_queue_query_result=query,
                                                board_label=ns.board_label,
                                            ),
                                            board_label=ns.board_label,
                                        ),
                                        board_label=ns.board_label,
                                    ),
                                    board_label=ns.board_label,
                                ),
                                board_label=ns.board_label,
                            ),
                            board_label=ns.board_label,
                        ),
                        board_label=ns.board_label,
                    ),
                    board_label=ns.board_label,
                ),
                board_label=ns.board_label,
            ),
            board_label=ns.board_label,
        ),
        board_label=ns.board_label,
    ).to_payload()
    return _emit_payload(payload, ns.output)
def cmd_oracle_operator_monitored_rejoin_policy(ns: argparse.Namespace) -> int:
    queue_state = _build_queue_state(ns)
    query = run_operator_queue_query(operator_queue_snapshot=materialize_operator_queue_snapshot(governance_work_queue=queue_state))
    payload = materialize_operator_monitored_rejoin_policy(
        build_operator_monitored_rejoin_policy_request(policy_root=Path(ns.policy_root), board_label=ns.board_label, evaluated_at_utc=parse_utc(ns.issued_at_utc)),
        chronic_exit_return_bridge=materialize_operator_chronic_exit_return_bridge(
            build_operator_chronic_exit_return_bridge_request(bridge_root=Path(ns.policy_root) / 'chronic_exit_return_bridge', board_label=ns.board_label, bridged_at_utc=parse_utc(ns.issued_at_utc)),
            chronic_exit_certification=materialize_operator_chronic_exit_certification(
                build_operator_chronic_exit_certification_request(certification_root=Path(ns.policy_root) / 'chronic_exit_return_bridge' / 'chronic_exit_certification', board_label=ns.board_label, certified_at_utc=parse_utc(ns.issued_at_utc)),
                freeze_release_attestation=materialize_operator_freeze_release_attestation(
                    build_operator_freeze_release_attestation_request(attestation_root=Path(ns.policy_root) / 'chronic_exit_return_bridge' / 'chronic_exit_certification' / 'freeze_release_attestation', board_label=ns.board_label, attested_at_utc=parse_utc(ns.issued_at_utc)),
                    freeze_release_gate=materialize_operator_freeze_release_gate(
                        build_operator_freeze_release_gate_request(gate_root=Path(ns.policy_root) / 'chronic_exit_return_bridge' / 'chronic_exit_certification' / 'freeze_release_attestation' / 'freeze_release_gate', board_label=ns.board_label, reviewed_at_utc=parse_utc(ns.issued_at_utc)),
                        chronic_remediation_satisfaction=materialize_operator_chronic_remediation_satisfaction(
                            build_operator_chronic_remediation_satisfaction_request(satisfaction_root=Path(ns.policy_root) / 'chronic_exit_return_bridge' / 'chronic_exit_certification' / 'freeze_release_attestation' / 'freeze_release_gate' / 'chronic_remediation_satisfaction', board_label=ns.board_label, evaluated_at_utc=parse_utc(ns.issued_at_utc)),
                            chronic_remediation_mandate_ledger=materialize_operator_chronic_remediation_mandate_ledger(
                                build_operator_chronic_remediation_mandate_ledger_request(ledger_root=Path(ns.policy_root) / 'chronic_exit_return_bridge' / 'chronic_exit_certification' / 'freeze_release_attestation' / 'freeze_release_gate' / 'chronic_remediation_satisfaction' / 'chronic_remediation_mandate_ledger', board_label=ns.board_label, mandated_at_utc=parse_utc(ns.issued_at_utc)),
                                recurrence_tribunal_disposition=materialize_operator_recurrence_tribunal_disposition(
                                    build_operator_recurrence_tribunal_disposition_request(disposition_root=Path(ns.policy_root) / 'chronic_exit_return_bridge' / 'chronic_exit_certification' / 'freeze_release_attestation' / 'freeze_release_gate' / 'chronic_remediation_satisfaction' / 'chronic_remediation_mandate_ledger' / 'recurrence_tribunal_disposition', board_label=ns.board_label, reviewed_at_utc=parse_utc(ns.issued_at_utc)),
                                    recurrence_tribunal_lane=materialize_operator_recurrence_tribunal_lane(
                                        build_operator_recurrence_tribunal_lane_request(tribunal_root=Path(ns.policy_root) / 'chronic_exit_return_bridge' / 'chronic_exit_certification' / 'freeze_release_attestation' / 'freeze_release_gate' / 'chronic_remediation_satisfaction' / 'chronic_remediation_mandate_ledger' / 'recurrence_tribunal_disposition' / 'recurrence_tribunal_lane', board_label=ns.board_label, reviewed_at_utc=parse_utc(ns.issued_at_utc)),
                                        chronic_instability_packet=materialize_operator_chronic_instability_packet(
                                            build_operator_chronic_instability_packet_request(packet_root=Path(ns.policy_root) / 'chronic_exit_return_bridge' / 'chronic_exit_certification' / 'freeze_release_attestation' / 'freeze_release_gate' / 'chronic_remediation_satisfaction' / 'chronic_remediation_mandate_ledger' / 'recurrence_tribunal_disposition' / 'recurrence_tribunal_lane' / 'chronic_instability_packet', board_label=ns.board_label, emitted_at_utc=parse_utc(ns.issued_at_utc)),
                                            reopen_recurrence_policy=materialize_operator_reopen_recurrence_policy(
                                                build_operator_reopen_recurrence_policy_request(policy_root=Path(ns.policy_root) / 'chronic_exit_return_bridge' / 'chronic_exit_certification' / 'freeze_release_attestation' / 'freeze_release_gate' / 'chronic_remediation_satisfaction' / 'chronic_remediation_mandate_ledger' / 'recurrence_tribunal_disposition' / 'recurrence_tribunal_lane' / 'chronic_instability_packet' / 'reopen_recurrence_policy', board_label=ns.board_label, evaluated_at_utc=parse_utc(ns.issued_at_utc)),
                                                reopen_lineage=materialize_operator_reopen_lineage(
                                                    build_operator_reopen_lineage_request(lineage_root=Path(ns.policy_root) / 'chronic_exit_return_bridge' / 'chronic_exit_certification' / 'freeze_release_attestation' / 'freeze_release_gate' / 'chronic_remediation_satisfaction' / 'chronic_remediation_mandate_ledger' / 'recurrence_tribunal_disposition' / 'recurrence_tribunal_lane' / 'chronic_instability_packet' / 'reopen_recurrence_policy' / 'reopen_lineage', board_label=ns.board_label, analyzed_at_utc=parse_utc(ns.issued_at_utc), prior_reopen_counts=_parse_prior_reopen_counts(ns.prior_reopen_count)),
                                                    operator_queue_query_result=query,
                                                    board_label=ns.board_label,
                                                ),
                                                board_label=ns.board_label,
                                            ),
                                            board_label=ns.board_label,
                                        ),
                                        board_label=ns.board_label,
                                    ),
                                    board_label=ns.board_label,
                                ),
                                board_label=ns.board_label,
                            ),
                            board_label=ns.board_label,
                        ),
                        board_label=ns.board_label,
                    ),
                    board_label=ns.board_label,
                ),
                board_label=ns.board_label,
            ),
            board_label=ns.board_label,
        ),
        board_label=ns.board_label,
    ).to_payload()
    return _emit_payload(payload, ns.output)
def cmd_oracle_operator_monitored_rejoin_activation(ns: argparse.Namespace) -> int:
    queue_state = _build_queue_state(ns)
    query = run_operator_queue_query(operator_queue_snapshot=materialize_operator_queue_snapshot(governance_work_queue=queue_state))
    payload = materialize_operator_monitored_rejoin_activation(
        build_operator_monitored_rejoin_activation_request(activation_root=Path(ns.activation_root), board_label=ns.board_label, activator_label='chronic-rejoin-activator', activated_at_utc=parse_utc(ns.issued_at_utc)),
        monitored_rejoin_policy=materialize_operator_monitored_rejoin_policy(
            build_operator_monitored_rejoin_policy_request(policy_root=Path(ns.activation_root) / 'monitored_rejoin_policy', board_label=ns.board_label, evaluated_at_utc=parse_utc(ns.issued_at_utc)),
            chronic_exit_return_bridge=materialize_operator_chronic_exit_return_bridge(
                build_operator_chronic_exit_return_bridge_request(bridge_root=Path(ns.activation_root) / 'monitored_rejoin_policy' / 'chronic_exit_return_bridge', board_label=ns.board_label, bridged_at_utc=parse_utc(ns.issued_at_utc)),
                chronic_exit_certification=materialize_operator_chronic_exit_certification(
                    build_operator_chronic_exit_certification_request(certification_root=Path(ns.activation_root) / 'monitored_rejoin_policy' / 'chronic_exit_return_bridge' / 'chronic_exit_certification', board_label=ns.board_label, certified_at_utc=parse_utc(ns.issued_at_utc)),
                    freeze_release_attestation=materialize_operator_freeze_release_attestation(
                        build_operator_freeze_release_attestation_request(attestation_root=Path(ns.activation_root) / 'monitored_rejoin_policy' / 'chronic_exit_return_bridge' / 'chronic_exit_certification' / 'freeze_release_attestation', board_label=ns.board_label, attested_at_utc=parse_utc(ns.issued_at_utc)),
                        freeze_release_gate=materialize_operator_freeze_release_gate(
                            build_operator_freeze_release_gate_request(gate_root=Path(ns.activation_root) / 'monitored_rejoin_policy' / 'chronic_exit_return_bridge' / 'chronic_exit_certification' / 'freeze_release_attestation' / 'freeze_release_gate', board_label=ns.board_label, reviewed_at_utc=parse_utc(ns.issued_at_utc)),
                            chronic_remediation_satisfaction=materialize_operator_chronic_remediation_satisfaction(
                                build_operator_chronic_remediation_satisfaction_request(satisfaction_root=Path(ns.activation_root) / 'monitored_rejoin_policy' / 'chronic_exit_return_bridge' / 'chronic_exit_certification' / 'freeze_release_attestation' / 'freeze_release_gate' / 'chronic_remediation_satisfaction', board_label=ns.board_label, evaluated_at_utc=parse_utc(ns.issued_at_utc)),
                                chronic_remediation_mandate_ledger=materialize_operator_chronic_remediation_mandate_ledger(
                                    build_operator_chronic_remediation_mandate_ledger_request(ledger_root=Path(ns.activation_root) / 'monitored_rejoin_policy' / 'chronic_exit_return_bridge' / 'chronic_exit_certification' / 'freeze_release_attestation' / 'freeze_release_gate' / 'chronic_remediation_satisfaction' / 'chronic_remediation_mandate_ledger', board_label=ns.board_label, mandated_at_utc=parse_utc(ns.issued_at_utc)),
                                    recurrence_tribunal_disposition=materialize_operator_recurrence_tribunal_disposition(
                                        build_operator_recurrence_tribunal_disposition_request(disposition_root=Path(ns.activation_root) / 'monitored_rejoin_policy' / 'chronic_exit_return_bridge' / 'chronic_exit_certification' / 'freeze_release_attestation' / 'freeze_release_gate' / 'chronic_remediation_satisfaction' / 'chronic_remediation_mandate_ledger' / 'recurrence_tribunal_disposition', board_label=ns.board_label, reviewed_at_utc=parse_utc(ns.issued_at_utc)),
                                        recurrence_tribunal_lane=materialize_operator_recurrence_tribunal_lane(
                                            build_operator_recurrence_tribunal_lane_request(tribunal_root=Path(ns.activation_root) / 'monitored_rejoin_policy' / 'chronic_exit_return_bridge' / 'chronic_exit_certification' / 'freeze_release_attestation' / 'freeze_release_gate' / 'chronic_remediation_satisfaction' / 'chronic_remediation_mandate_ledger' / 'recurrence_tribunal_disposition' / 'recurrence_tribunal_lane', board_label=ns.board_label, reviewed_at_utc=parse_utc(ns.issued_at_utc)),
                                            chronic_instability_packet=materialize_operator_chronic_instability_packet(
                                                build_operator_chronic_instability_packet_request(packet_root=Path(ns.activation_root) / 'monitored_rejoin_policy' / 'chronic_exit_return_bridge' / 'chronic_exit_certification' / 'freeze_release_attestation' / 'freeze_release_gate' / 'chronic_remediation_satisfaction' / 'chronic_remediation_mandate_ledger' / 'recurrence_tribunal_disposition' / 'recurrence_tribunal_lane' / 'chronic_instability_packet', board_label=ns.board_label, emitted_at_utc=parse_utc(ns.issued_at_utc)),
                                                reopen_recurrence_policy=materialize_operator_reopen_recurrence_policy(
                                                    build_operator_reopen_recurrence_policy_request(policy_root=Path(ns.activation_root) / 'monitored_rejoin_policy' / 'chronic_exit_return_bridge' / 'chronic_exit_certification' / 'freeze_release_attestation' / 'freeze_release_gate' / 'chronic_remediation_satisfaction' / 'chronic_remediation_mandate_ledger' / 'recurrence_tribunal_disposition' / 'recurrence_tribunal_lane' / 'chronic_instability_packet' / 'reopen_recurrence_policy', board_label=ns.board_label, evaluated_at_utc=parse_utc(ns.issued_at_utc)),
                                                    reopen_lineage=materialize_operator_reopen_lineage(
                                                        build_operator_reopen_lineage_request(lineage_root=Path(ns.activation_root) / 'monitored_rejoin_policy' / 'chronic_exit_return_bridge' / 'chronic_exit_certification' / 'freeze_release_attestation' / 'freeze_release_gate' / 'chronic_remediation_satisfaction' / 'chronic_remediation_mandate_ledger' / 'recurrence_tribunal_disposition' / 'recurrence_tribunal_lane' / 'chronic_instability_packet' / 'reopen_recurrence_policy' / 'reopen_lineage', board_label=ns.board_label, analyzed_at_utc=parse_utc(ns.issued_at_utc), prior_reopen_counts=_parse_prior_reopen_counts(ns.prior_reopen_count)),
                                                        operator_queue_query_result=query,
                                                        board_label=ns.board_label,
                                                    ),
                                                    board_label=ns.board_label,
                                                ),
                                                board_label=ns.board_label,
                                            ),
                                            board_label=ns.board_label,
                                        ),
                                        board_label=ns.board_label,
                                    ),
                                    board_label=ns.board_label,
                                ),
                                board_label=ns.board_label,
                            ),
                            board_label=ns.board_label,
                        ),
                        board_label=ns.board_label,
                    ),
                    board_label=ns.board_label,
                ),
                board_label=ns.board_label,
            ),
            board_label=ns.board_label,
        ),
        board_label=ns.board_label,
    ).to_payload()
    return _emit_payload(payload, ns.output)
def cmd_oracle_operator_chronic_watch_handoff(ns: argparse.Namespace) -> int:
    queue_state = _build_queue_state(ns)
    query = run_operator_queue_query(operator_queue_snapshot=materialize_operator_queue_snapshot(governance_work_queue=queue_state))
    payload = materialize_operator_chronic_watch_handoff(
        build_operator_chronic_watch_handoff_request(handoff_root=Path(ns.handoff_root), board_label=ns.board_label, handoff_label='chronic-watch-handoff', handed_off_at_utc=parse_utc(ns.issued_at_utc) - timedelta(days=2)),
        monitored_rejoin_activation=materialize_operator_monitored_rejoin_activation(
            build_operator_monitored_rejoin_activation_request(activation_root=Path(ns.handoff_root) / 'monitored_rejoin_activation', board_label=ns.board_label, activator_label='chronic-rejoin-activator', activated_at_utc=parse_utc(ns.issued_at_utc)),
            monitored_rejoin_policy=materialize_operator_monitored_rejoin_policy(
                build_operator_monitored_rejoin_policy_request(policy_root=Path(ns.handoff_root) / 'monitored_rejoin_activation' / 'monitored_rejoin_policy', board_label=ns.board_label, evaluated_at_utc=parse_utc(ns.issued_at_utc)),
                chronic_exit_return_bridge=materialize_operator_chronic_exit_return_bridge(
                    build_operator_chronic_exit_return_bridge_request(bridge_root=Path(ns.handoff_root) / 'monitored_rejoin_activation' / 'monitored_rejoin_policy' / 'chronic_exit_return_bridge', board_label=ns.board_label, bridged_at_utc=parse_utc(ns.issued_at_utc)),
                    chronic_exit_certification=materialize_operator_chronic_exit_certification(
                        build_operator_chronic_exit_certification_request(certification_root=Path(ns.handoff_root) / 'monitored_rejoin_activation' / 'monitored_rejoin_policy' / 'chronic_exit_return_bridge' / 'chronic_exit_certification', board_label=ns.board_label, certified_at_utc=parse_utc(ns.issued_at_utc)),
                        freeze_release_attestation=materialize_operator_freeze_release_attestation(
                            build_operator_freeze_release_attestation_request(attestation_root=Path(ns.handoff_root) / 'monitored_rejoin_activation' / 'monitored_rejoin_policy' / 'chronic_exit_return_bridge' / 'chronic_exit_certification' / 'freeze_release_attestation', board_label=ns.board_label, attested_at_utc=parse_utc(ns.issued_at_utc)),
                            freeze_release_gate=materialize_operator_freeze_release_gate(
                                build_operator_freeze_release_gate_request(gate_root=Path(ns.handoff_root) / 'monitored_rejoin_activation' / 'monitored_rejoin_policy' / 'chronic_exit_return_bridge' / 'chronic_exit_certification' / 'freeze_release_attestation' / 'freeze_release_gate', board_label=ns.board_label, reviewed_at_utc=parse_utc(ns.issued_at_utc)),
                                chronic_remediation_satisfaction=materialize_operator_chronic_remediation_satisfaction(
                                    build_operator_chronic_remediation_satisfaction_request(satisfaction_root=Path(ns.handoff_root) / 'monitored_rejoin_activation' / 'monitored_rejoin_policy' / 'chronic_exit_return_bridge' / 'chronic_exit_certification' / 'freeze_release_attestation' / 'freeze_release_gate' / 'chronic_remediation_satisfaction', board_label=ns.board_label, evaluated_at_utc=parse_utc(ns.issued_at_utc)),
                                    chronic_remediation_mandate_ledger=materialize_operator_chronic_remediation_mandate_ledger(
                                        build_operator_chronic_remediation_mandate_ledger_request(ledger_root=Path(ns.handoff_root) / 'monitored_rejoin_activation' / 'monitored_rejoin_policy' / 'chronic_exit_return_bridge' / 'chronic_exit_certification' / 'freeze_release_attestation' / 'freeze_release_gate' / 'chronic_remediation_satisfaction' / 'chronic_remediation_mandate_ledger', board_label=ns.board_label, mandated_at_utc=parse_utc(ns.issued_at_utc)),
                                        recurrence_tribunal_disposition=materialize_operator_recurrence_tribunal_disposition(
                                            build_operator_recurrence_tribunal_disposition_request(disposition_root=Path(ns.handoff_root) / 'monitored_rejoin_activation' / 'monitored_rejoin_policy' / 'chronic_exit_return_bridge' / 'chronic_exit_certification' / 'freeze_release_attestation' / 'freeze_release_gate' / 'chronic_remediation_satisfaction' / 'chronic_remediation_mandate_ledger' / 'recurrence_tribunal_disposition', board_label=ns.board_label, reviewed_at_utc=parse_utc(ns.issued_at_utc)),
                                            recurrence_tribunal_lane=materialize_operator_recurrence_tribunal_lane(
                                                build_operator_recurrence_tribunal_lane_request(tribunal_root=Path(ns.handoff_root) / 'monitored_rejoin_activation' / 'monitored_rejoin_policy' / 'chronic_exit_return_bridge' / 'chronic_exit_certification' / 'freeze_release_attestation' / 'freeze_release_gate' / 'chronic_remediation_satisfaction' / 'chronic_remediation_mandate_ledger' / 'recurrence_tribunal_disposition' / 'recurrence_tribunal_lane', board_label=ns.board_label, reviewed_at_utc=parse_utc(ns.issued_at_utc)),
                                                chronic_instability_packet=materialize_operator_chronic_instability_packet(
                                                    build_operator_chronic_instability_packet_request(packet_root=Path(ns.handoff_root) / 'monitored_rejoin_activation' / 'monitored_rejoin_policy' / 'chronic_exit_return_bridge' / 'chronic_exit_certification' / 'freeze_release_attestation' / 'freeze_release_gate' / 'chronic_remediation_satisfaction' / 'chronic_remediation_mandate_ledger' / 'recurrence_tribunal_disposition' / 'recurrence_tribunal_lane' / 'chronic_instability_packet', board_label=ns.board_label, emitted_at_utc=parse_utc(ns.issued_at_utc)),
                                                    reopen_recurrence_policy=materialize_operator_reopen_recurrence_policy(
                                                        build_operator_reopen_recurrence_policy_request(policy_root=Path(ns.handoff_root) / 'monitored_rejoin_activation' / 'monitored_rejoin_policy' / 'chronic_exit_return_bridge' / 'chronic_exit_certification' / 'freeze_release_attestation' / 'freeze_release_gate' / 'chronic_remediation_satisfaction' / 'chronic_remediation_mandate_ledger' / 'recurrence_tribunal_disposition' / 'recurrence_tribunal_lane' / 'chronic_instability_packet' / 'reopen_recurrence_policy', board_label=ns.board_label, evaluated_at_utc=parse_utc(ns.issued_at_utc)),
                                                        reopen_lineage=materialize_operator_reopen_lineage(
                                                            build_operator_reopen_lineage_request(lineage_root=Path(ns.handoff_root) / 'monitored_rejoin_activation' / 'monitored_rejoin_policy' / 'chronic_exit_return_bridge' / 'chronic_exit_certification' / 'freeze_release_attestation' / 'freeze_release_gate' / 'chronic_remediation_satisfaction' / 'chronic_remediation_mandate_ledger' / 'recurrence_tribunal_disposition' / 'recurrence_tribunal_lane' / 'chronic_instability_packet' / 'reopen_recurrence_policy' / 'reopen_lineage', board_label=ns.board_label, analyzed_at_utc=parse_utc(ns.issued_at_utc), prior_reopen_counts=_parse_prior_reopen_counts(ns.prior_reopen_count)),
                                                            operator_queue_query_result=query,
                                                            board_label=ns.board_label,
                                                        ),
                                                        board_label=ns.board_label,
                                                    ),
                                                    board_label=ns.board_label,
                                                ),
                                                board_label=ns.board_label,
                                            ),
                                            board_label=ns.board_label,
                                        ),
                                        board_label=ns.board_label,
                                    ),
                                    board_label=ns.board_label,
                                ),
                                board_label=ns.board_label,
                            ),
                            board_label=ns.board_label,
                        ),
                        board_label=ns.board_label,
                    ),
                    board_label=ns.board_label,
                ),
                board_label=ns.board_label,
            ),
            board_label=ns.board_label,
        ),
        board_label=ns.board_label,
    ).to_payload()
    return _emit_payload(payload, ns.output)
def cmd_oracle_operator_control_plane_bundle(ns: argparse.Namespace) -> int:
    queue_state = _build_queue_state(ns)
    query = run_operator_queue_query(operator_queue_snapshot=materialize_operator_queue_snapshot(governance_work_queue=queue_state))
    payload = materialize_operator_control_plane_bundle(
        build_operator_control_plane_bundle_request(bundle_root=Path(ns.bundle_root), emitted_at_utc=parse_utc(ns.issued_at_utc), board_label=ns.board_label),
        operator_queue_query_result=query,
        decision_execution_request=build_operator_decision_execution_request(execution_root=Path(ns.bundle_root) / 'decision_execution', emitted_at_utc=parse_utc(ns.issued_at_utc), board_label=ns.board_label, desired_transition=ns.outcome_state, actor_label=ns.actor_label, note=ns.note),
        escalation_routing_request=build_operator_escalation_routing_request(routing_root=Path(ns.bundle_root) / 'escalation_routing', board_label=ns.board_label),
        escalation_sla_request=build_operator_escalation_sla_request(sla_root=Path(ns.bundle_root) / 'escalation_sla', board_label=ns.board_label, evaluated_at_utc=parse_utc(ns.issued_at_utc), escalation_started_at_utc=parse_utc(ns.issued_at_utc)),
        action_outcome_ledger_request=build_operator_action_outcome_ledger_request(ledger_root=Path(ns.bundle_root) / 'action_outcomes', emitted_at_utc=parse_utc(ns.issued_at_utc), board_label=ns.board_label, outcome_state=ns.outcome_state, actor_label=ns.actor_label, note=ns.note),
        reentry_acceptance_request=build_operator_reentry_acceptance_request(acceptance_root=Path(ns.bundle_root) / 'reentry_acceptance', board_label=ns.board_label, accepted_at_utc=parse_utc(ns.issued_at_utc)),
        feedback_state_request=build_operator_feedback_state_request(state_root=Path(ns.bundle_root) / 'feedback_state', emitted_at_utc=parse_utc(ns.issued_at_utc), board_label=ns.board_label),
    ).to_payload()
    return _emit_payload(payload, ns.output)
def cmd_oracle_operator_return_monitoring(ns: argparse.Namespace) -> int:
    queue_state = _build_queue_state(ns)
    query = run_operator_queue_query(operator_queue_snapshot=materialize_operator_queue_snapshot(governance_work_queue=queue_state))
    payload = materialize_operator_return_monitoring(
        build_operator_return_monitoring_request(
            monitoring_root=Path(ns.monitoring_root),
            board_label=ns.board_label,
            monitor_label=ns.monitor_label,
            evaluated_at_utc=parse_utc(ns.issued_at_utc),
            monitoring_started_at_utc=parse_utc(ns.monitoring_started_at_utc) if ns.monitoring_started_at_utc else parse_utc(ns.issued_at_utc),
        ),
        operator_queue_query_result=query,
        board_label=ns.board_label,
    ).to_payload()
    return _emit_payload(payload, ns.output)
def cmd_oracle_operator_restoration_audit(ns: argparse.Namespace) -> int:
    queue_state = _build_queue_state(ns)
    query = run_operator_queue_query(operator_queue_snapshot=materialize_operator_queue_snapshot(governance_work_queue=queue_state))
    payload = materialize_operator_restoration_audit(
        build_operator_restoration_audit_request(
            audit_root=Path(ns.audit_root),
            board_label=ns.board_label,
            auditor_label=ns.auditor_label,
            audited_at_utc=parse_utc(ns.issued_at_utc),
        ),
        operator_queue_query_result=query,
        board_label=ns.board_label,
    ).to_payload()
    return _emit_payload(payload, ns.output)
def cmd_oracle_operator_return_drift_breach(ns: argparse.Namespace) -> int:
    queue_state = _build_queue_state(ns)
    query = run_operator_queue_query(operator_queue_snapshot=materialize_operator_queue_snapshot(governance_work_queue=queue_state))
    payload = materialize_operator_return_drift_breach(
        build_operator_return_drift_breach_request(
            breach_root=Path(ns.breach_root),
            board_label=ns.board_label,
            evaluator_label=ns.evaluator_label,
            evaluated_at_utc=parse_utc(ns.issued_at_utc),
            drift_signal_mode=ns.drift_signal_mode,
        ),
        operator_queue_query_result=query,
        board_label=ns.board_label,
    ).to_payload()
    return _emit_payload(payload, ns.output)
def cmd_oracle_operator_return_reopen_loop(ns: argparse.Namespace) -> int:
    queue_state = _build_queue_state(ns)
    query = run_operator_queue_query(operator_queue_snapshot=materialize_operator_queue_snapshot(governance_work_queue=queue_state))
    payload = materialize_operator_return_reopen_loop(
        build_operator_return_reopen_loop_request(
            reopen_root=Path(ns.reopen_root),
            board_label=ns.board_label,
            reopen_label=ns.reopen_label,
            reopened_at_utc=parse_utc(ns.issued_at_utc),
            drift_signal_mode=ns.drift_signal_mode,
        ),
        operator_queue_query_result=query,
        board_label=ns.board_label,
    ).to_payload()
    return _emit_payload(payload, ns.output)
def cmd_oracle_operator_chronic_watch_outcome(ns: argparse.Namespace) -> int:
    queue_state = _build_queue_state(ns)
    query = run_operator_queue_query(operator_queue_snapshot=materialize_operator_queue_snapshot(governance_work_queue=queue_state))
    payload = materialize_operator_chronic_watch_outcome(
        build_operator_chronic_watch_outcome_request(outcome_root=Path(ns.outcome_root), board_label=ns.board_label, evaluated_at_utc=parse_utc(ns.issued_at_utc), drift_signal_mode=ns.drift_signal_mode),
        chronic_watch_handoff=materialize_operator_chronic_watch_handoff(
            build_operator_chronic_watch_handoff_request(handoff_root=Path(ns.outcome_root) / 'chronic_watch_handoff', board_label=ns.board_label, handoff_label='chronic-watch-handoff', handed_off_at_utc=parse_utc(ns.issued_at_utc) - timedelta(days=2)),
            monitored_rejoin_activation=materialize_operator_monitored_rejoin_activation(
                build_operator_monitored_rejoin_activation_request(activation_root=Path(ns.outcome_root) / 'chronic_watch_handoff' / 'monitored_rejoin_activation', board_label=ns.board_label, activated_at_utc=parse_utc(ns.issued_at_utc)),
                monitored_rejoin_policy=materialize_operator_monitored_rejoin_policy(
                    build_operator_monitored_rejoin_policy_request(policy_root=Path(ns.outcome_root) / 'chronic_watch_handoff' / 'monitored_rejoin_activation' / 'monitored_rejoin_policy', board_label=ns.board_label, evaluated_at_utc=parse_utc(ns.issued_at_utc)),
                    chronic_exit_return_bridge=materialize_operator_chronic_exit_return_bridge(
                        build_operator_chronic_exit_return_bridge_request(bridge_root=Path(ns.outcome_root) / 'chronic_watch_handoff' / 'monitored_rejoin_activation' / 'monitored_rejoin_policy' / 'chronic_exit_return_bridge', board_label=ns.board_label, bridged_at_utc=parse_utc(ns.issued_at_utc)),
                        chronic_exit_certification=materialize_operator_chronic_exit_certification(
                            build_operator_chronic_exit_certification_request(certification_root=Path(ns.outcome_root) / 'chronic_watch_handoff' / 'monitored_rejoin_activation' / 'monitored_rejoin_policy' / 'chronic_exit_return_bridge' / 'chronic_exit_certification', board_label=ns.board_label, certified_at_utc=parse_utc(ns.issued_at_utc)),
                            freeze_release_attestation=materialize_operator_freeze_release_attestation(
                                build_operator_freeze_release_attestation_request(attestation_root=Path(ns.outcome_root) / 'chronic_watch_handoff' / 'monitored_rejoin_activation' / 'monitored_rejoin_policy' / 'chronic_exit_return_bridge' / 'chronic_exit_certification' / 'freeze_release_attestation', board_label=ns.board_label, attested_at_utc=parse_utc(ns.issued_at_utc)),
                                freeze_release_gate=materialize_operator_freeze_release_gate(
                                    build_operator_freeze_release_gate_request(gate_root=Path(ns.outcome_root) / 'chronic_watch_handoff' / 'monitored_rejoin_activation' / 'monitored_rejoin_policy' / 'chronic_exit_return_bridge' / 'chronic_exit_certification' / 'freeze_release_attestation' / 'freeze_release_gate', board_label=ns.board_label, reviewed_at_utc=parse_utc(ns.issued_at_utc)),
                                    chronic_remediation_satisfaction=materialize_operator_chronic_remediation_satisfaction(
                                        build_operator_chronic_remediation_satisfaction_request(satisfaction_root=Path(ns.outcome_root) / 'chronic_watch_handoff' / 'monitored_rejoin_activation' / 'monitored_rejoin_policy' / 'chronic_exit_return_bridge' / 'chronic_exit_certification' / 'freeze_release_attestation' / 'freeze_release_gate' / 'chronic_remediation_satisfaction', board_label=ns.board_label, evaluated_at_utc=parse_utc(ns.issued_at_utc)),
                                        chronic_remediation_mandate_ledger=materialize_operator_chronic_remediation_mandate_ledger(
                                            build_operator_chronic_remediation_mandate_ledger_request(ledger_root=Path(ns.outcome_root) / 'chronic_watch_handoff' / 'monitored_rejoin_activation' / 'monitored_rejoin_policy' / 'chronic_exit_return_bridge' / 'chronic_exit_certification' / 'freeze_release_attestation' / 'freeze_release_gate' / 'chronic_remediation_satisfaction' / 'chronic_remediation_mandate_ledger', board_label=ns.board_label, mandated_at_utc=parse_utc(ns.issued_at_utc)),
                                            recurrence_tribunal_disposition=materialize_operator_recurrence_tribunal_disposition(
                                                build_operator_recurrence_tribunal_disposition_request(disposition_root=Path(ns.outcome_root) / 'chronic_watch_handoff' / 'monitored_rejoin_activation' / 'monitored_rejoin_policy' / 'chronic_exit_return_bridge' / 'chronic_exit_certification' / 'freeze_release_attestation' / 'freeze_release_gate' / 'chronic_remediation_satisfaction' / 'chronic_remediation_mandate_ledger' / 'recurrence_tribunal_disposition', board_label=ns.board_label, reviewed_at_utc=parse_utc(ns.issued_at_utc)),
                                                recurrence_tribunal_lane=materialize_operator_recurrence_tribunal_lane(
                                                    build_operator_recurrence_tribunal_lane_request(tribunal_root=Path(ns.outcome_root) / 'chronic_watch_handoff' / 'monitored_rejoin_activation' / 'monitored_rejoin_policy' / 'chronic_exit_return_bridge' / 'chronic_exit_certification' / 'freeze_release_attestation' / 'freeze_release_gate' / 'chronic_remediation_satisfaction' / 'chronic_remediation_mandate_ledger' / 'recurrence_tribunal_disposition' / 'recurrence_tribunal_lane', board_label=ns.board_label, reviewed_at_utc=parse_utc(ns.issued_at_utc)),
                                                    chronic_instability_packet=materialize_operator_chronic_instability_packet(
                                                        build_operator_chronic_instability_packet_request(packet_root=Path(ns.outcome_root) / 'chronic_watch_handoff' / 'monitored_rejoin_activation' / 'monitored_rejoin_policy' / 'chronic_exit_return_bridge' / 'chronic_exit_certification' / 'freeze_release_attestation' / 'freeze_release_gate' / 'chronic_remediation_satisfaction' / 'chronic_remediation_mandate_ledger' / 'recurrence_tribunal_disposition' / 'recurrence_tribunal_lane' / 'chronic_instability_packet', board_label=ns.board_label, emitted_at_utc=parse_utc(ns.issued_at_utc)),
                                                        reopen_recurrence_policy=materialize_operator_reopen_recurrence_policy(
                                                            build_operator_reopen_recurrence_policy_request(policy_root=Path(ns.outcome_root) / 'chronic_watch_handoff' / 'monitored_rejoin_activation' / 'monitored_rejoin_policy' / 'chronic_exit_return_bridge' / 'chronic_exit_certification' / 'freeze_release_attestation' / 'freeze_release_gate' / 'chronic_remediation_satisfaction' / 'chronic_remediation_mandate_ledger' / 'recurrence_tribunal_disposition' / 'recurrence_tribunal_lane' / 'chronic_instability_packet' / 'reopen_recurrence_policy', board_label=ns.board_label, evaluated_at_utc=parse_utc(ns.issued_at_utc)),
                                                            reopen_lineage=materialize_operator_reopen_lineage(
                                                                build_operator_reopen_lineage_request(lineage_root=Path(ns.outcome_root) / 'chronic_watch_handoff' / 'monitored_rejoin_activation' / 'monitored_rejoin_policy' / 'chronic_exit_return_bridge' / 'chronic_exit_certification' / 'freeze_release_attestation' / 'freeze_release_gate' / 'chronic_remediation_satisfaction' / 'chronic_remediation_mandate_ledger' / 'recurrence_tribunal_disposition' / 'recurrence_tribunal_lane' / 'chronic_instability_packet' / 'reopen_recurrence_policy' / 'reopen_lineage', board_label=ns.board_label, analyzed_at_utc=parse_utc(ns.issued_at_utc), prior_reopen_counts=_parse_prior_reopen_counts(ns.prior_reopen_count)),
                                                                operator_queue_query_result=query,
                                                                board_label=ns.board_label,
                                                            ),
                                                            board_label=ns.board_label,
                                                        ),
                                                        board_label=ns.board_label,
                                                    ),
                                                    board_label=ns.board_label,
                                                ),
                                                board_label=ns.board_label,
                                            ),
                                            board_label=ns.board_label,
                                        ),
                                        board_label=ns.board_label,
                                    ),
                                    board_label=ns.board_label,
                                ),
                                board_label=ns.board_label,
                            ),
                            board_label=ns.board_label,
                        ),
                        board_label=ns.board_label,
                    ),
                    board_label=ns.board_label,
                ),
                board_label=ns.board_label,
            ),
            board_label=ns.board_label,
        ),
        board_label=ns.board_label,
    ).to_payload()
    return _emit_payload(payload, ns.output)
def cmd_oracle_operator_monitored_rejoin_normalization_bridge(ns: argparse.Namespace) -> int:
    queue_state = _build_queue_state(ns)
    query = run_operator_queue_query(operator_queue_snapshot=materialize_operator_queue_snapshot(governance_work_queue=queue_state))
    payload = materialize_operator_monitored_rejoin_normalization_bridge(
        build_operator_monitored_rejoin_normalization_bridge_request(bridge_root=Path(ns.bridge_root), board_label=ns.board_label, bridged_at_utc=parse_utc(ns.issued_at_utc)),
        chronic_watch_outcome=materialize_operator_chronic_watch_outcome(
            build_operator_chronic_watch_outcome_request(outcome_root=Path(ns.bridge_root) / 'chronic_watch_outcome', board_label=ns.board_label, evaluated_at_utc=parse_utc(ns.issued_at_utc), drift_signal_mode=ns.drift_signal_mode),
            chronic_watch_handoff=materialize_operator_chronic_watch_handoff(
                build_operator_chronic_watch_handoff_request(handoff_root=Path(ns.bridge_root) / 'chronic_watch_outcome' / 'chronic_watch_handoff', board_label=ns.board_label, handoff_label='chronic-watch-handoff', handed_off_at_utc=parse_utc(ns.issued_at_utc) - timedelta(days=2)),
                monitored_rejoin_activation=materialize_operator_monitored_rejoin_activation(
                    build_operator_monitored_rejoin_activation_request(activation_root=Path(ns.bridge_root) / 'chronic_watch_outcome' / 'chronic_watch_handoff' / 'monitored_rejoin_activation', board_label=ns.board_label, activated_at_utc=parse_utc(ns.issued_at_utc)),
                    monitored_rejoin_policy=materialize_operator_monitored_rejoin_policy(
                        build_operator_monitored_rejoin_policy_request(policy_root=Path(ns.bridge_root) / 'chronic_watch_outcome' / 'chronic_watch_handoff' / 'monitored_rejoin_activation' / 'monitored_rejoin_policy', board_label=ns.board_label, evaluated_at_utc=parse_utc(ns.issued_at_utc)),
                        chronic_exit_return_bridge=materialize_operator_chronic_exit_return_bridge(
                            build_operator_chronic_exit_return_bridge_request(bridge_root=Path(ns.bridge_root) / 'chronic_watch_outcome' / 'chronic_watch_handoff' / 'monitored_rejoin_activation' / 'monitored_rejoin_policy' / 'chronic_exit_return_bridge', board_label=ns.board_label, bridged_at_utc=parse_utc(ns.issued_at_utc)),
                            chronic_exit_certification=materialize_operator_chronic_exit_certification(
                                build_operator_chronic_exit_certification_request(certification_root=Path(ns.bridge_root) / 'chronic_watch_outcome' / 'chronic_watch_handoff' / 'monitored_rejoin_activation' / 'monitored_rejoin_policy' / 'chronic_exit_return_bridge' / 'chronic_exit_certification', board_label=ns.board_label, certified_at_utc=parse_utc(ns.issued_at_utc)),
                                freeze_release_attestation=materialize_operator_freeze_release_attestation(
                                    build_operator_freeze_release_attestation_request(attestation_root=Path(ns.bridge_root) / 'chronic_watch_outcome' / 'chronic_watch_handoff' / 'monitored_rejoin_activation' / 'monitored_rejoin_policy' / 'chronic_exit_return_bridge' / 'chronic_exit_certification' / 'freeze_release_attestation', board_label=ns.board_label, attested_at_utc=parse_utc(ns.issued_at_utc)),
                                    freeze_release_gate=materialize_operator_freeze_release_gate(
                                        build_operator_freeze_release_gate_request(gate_root=Path(ns.bridge_root) / 'chronic_watch_outcome' / 'chronic_watch_handoff' / 'monitored_rejoin_activation' / 'monitored_rejoin_policy' / 'chronic_exit_return_bridge' / 'chronic_exit_certification' / 'freeze_release_attestation' / 'freeze_release_gate', board_label=ns.board_label, reviewed_at_utc=parse_utc(ns.issued_at_utc)),
                                        chronic_remediation_satisfaction=materialize_operator_chronic_remediation_satisfaction(
                                            build_operator_chronic_remediation_satisfaction_request(satisfaction_root=Path(ns.bridge_root) / 'chronic_watch_outcome' / 'chronic_watch_handoff' / 'monitored_rejoin_activation' / 'monitored_rejoin_policy' / 'chronic_exit_return_bridge' / 'chronic_exit_certification' / 'freeze_release_attestation' / 'freeze_release_gate' / 'chronic_remediation_satisfaction', board_label=ns.board_label, evaluated_at_utc=parse_utc(ns.issued_at_utc)),
                                            chronic_remediation_mandate_ledger=materialize_operator_chronic_remediation_mandate_ledger(
                                                build_operator_chronic_remediation_mandate_ledger_request(ledger_root=Path(ns.bridge_root) / 'chronic_watch_outcome' / 'chronic_watch_handoff' / 'monitored_rejoin_activation' / 'monitored_rejoin_policy' / 'chronic_exit_return_bridge' / 'chronic_exit_certification' / 'freeze_release_attestation' / 'freeze_release_gate' / 'chronic_remediation_satisfaction' / 'chronic_remediation_mandate_ledger', board_label=ns.board_label, mandated_at_utc=parse_utc(ns.issued_at_utc)),
                                                recurrence_tribunal_disposition=materialize_operator_recurrence_tribunal_disposition(
                                                    build_operator_recurrence_tribunal_disposition_request(disposition_root=Path(ns.bridge_root) / 'chronic_watch_outcome' / 'chronic_watch_handoff' / 'monitored_rejoin_activation' / 'monitored_rejoin_policy' / 'chronic_exit_return_bridge' / 'chronic_exit_certification' / 'freeze_release_attestation' / 'freeze_release_gate' / 'chronic_remediation_satisfaction' / 'chronic_remediation_mandate_ledger' / 'recurrence_tribunal_disposition', board_label=ns.board_label, reviewed_at_utc=parse_utc(ns.issued_at_utc)),
                                                    recurrence_tribunal_lane=materialize_operator_recurrence_tribunal_lane(
                                                        build_operator_recurrence_tribunal_lane_request(tribunal_root=Path(ns.bridge_root) / 'chronic_watch_outcome' / 'chronic_watch_handoff' / 'monitored_rejoin_activation' / 'monitored_rejoin_policy' / 'chronic_exit_return_bridge' / 'chronic_exit_certification' / 'freeze_release_attestation' / 'freeze_release_gate' / 'chronic_remediation_satisfaction' / 'chronic_remediation_mandate_ledger' / 'recurrence_tribunal_disposition' / 'recurrence_tribunal_lane', board_label=ns.board_label, reviewed_at_utc=parse_utc(ns.issued_at_utc)),
                                                        chronic_instability_packet=materialize_operator_chronic_instability_packet(
                                                            build_operator_chronic_instability_packet_request(packet_root=Path(ns.bridge_root) / 'chronic_watch_outcome' / 'chronic_watch_handoff' / 'monitored_rejoin_activation' / 'monitored_rejoin_policy' / 'chronic_exit_return_bridge' / 'chronic_exit_certification' / 'freeze_release_attestation' / 'freeze_release_gate' / 'chronic_remediation_satisfaction' / 'chronic_remediation_mandate_ledger' / 'recurrence_tribunal_disposition' / 'recurrence_tribunal_lane' / 'chronic_instability_packet', board_label=ns.board_label, emitted_at_utc=parse_utc(ns.issued_at_utc)),
                                                            reopen_recurrence_policy=materialize_operator_reopen_recurrence_policy(
                                                                build_operator_reopen_recurrence_policy_request(policy_root=Path(ns.bridge_root) / 'chronic_watch_outcome' / 'chronic_watch_handoff' / 'monitored_rejoin_activation' / 'monitored_rejoin_policy' / 'chronic_exit_return_bridge' / 'chronic_exit_certification' / 'freeze_release_attestation' / 'freeze_release_gate' / 'chronic_remediation_satisfaction' / 'chronic_remediation_mandate_ledger' / 'recurrence_tribunal_disposition' / 'recurrence_tribunal_lane' / 'chronic_instability_packet' / 'reopen_recurrence_policy', board_label=ns.board_label, evaluated_at_utc=parse_utc(ns.issued_at_utc)),
                                                                reopen_lineage=materialize_operator_reopen_lineage(
                                                                    build_operator_reopen_lineage_request(lineage_root=Path(ns.bridge_root) / 'chronic_watch_outcome' / 'chronic_watch_handoff' / 'monitored_rejoin_activation' / 'monitored_rejoin_policy' / 'chronic_exit_return_bridge' / 'chronic_exit_certification' / 'freeze_release_attestation' / 'freeze_release_gate' / 'chronic_remediation_satisfaction' / 'chronic_remediation_mandate_ledger' / 'recurrence_tribunal_disposition' / 'recurrence_tribunal_lane' / 'chronic_instability_packet' / 'reopen_recurrence_policy' / 'reopen_lineage', board_label=ns.board_label, analyzed_at_utc=parse_utc(ns.issued_at_utc), prior_reopen_counts=_parse_prior_reopen_counts(ns.prior_reopen_count)),
                                                                    operator_queue_query_result=query,
                                                                    board_label=ns.board_label,
                                                                ),
                                                                board_label=ns.board_label,
                                                            ),
                                                            board_label=ns.board_label,
                                                        ),
                                                        board_label=ns.board_label,
                                                    ),
                                                    board_label=ns.board_label,
                                                ),
                                                board_label=ns.board_label,
                                            ),
                                            board_label=ns.board_label,
                                        ),
                                        board_label=ns.board_label,
                                    ),
                                    board_label=ns.board_label,
                                ),
                                board_label=ns.board_label,
                            ),
                            board_label=ns.board_label,
                        ),
                        board_label=ns.board_label,
                    ),
                    board_label=ns.board_label,
                ),
                board_label=ns.board_label,
            ),
            board_label=ns.board_label,
        ),
        board_label=ns.board_label,
    ).to_payload()
    return _emit_payload(payload, ns.output)
def cmd_oracle_operator_normalization_bridge_activation(ns: argparse.Namespace) -> int:
    queue_state = _build_queue_state(ns)
    query = run_operator_queue_query(operator_queue_snapshot=materialize_operator_queue_snapshot(governance_work_queue=queue_state))
    payload = materialize_operator_normalization_bridge_activation(
        build_operator_normalization_bridge_activation_request(
            activation_root=Path(ns.activation_root),
            board_label=ns.board_label,
            activator_label=ns.activator_label,
            activated_at_utc=parse_utc(ns.issued_at_utc),
            monitoring_started_at_utc=parse_utc(ns.monitoring_started_at_utc) if ns.monitoring_started_at_utc else parse_utc(ns.issued_at_utc),
        ),
        monitored_rejoin_normalization_bridge=materialize_operator_monitored_rejoin_normalization_bridge(
            build_operator_monitored_rejoin_normalization_bridge_request(
                bridge_root=Path(ns.activation_root) / 'monitored_rejoin_normalization_bridge',
                board_label=ns.board_label,
                bridged_at_utc=parse_utc(ns.issued_at_utc),
            ),
            operator_queue_query_result=query,
            board_label=ns.board_label,
        ),
        board_label=ns.board_label,
    ).to_payload()
    return _emit_payload(payload, ns.output)
def cmd_oracle_operator_chronic_watch_audit_convergence(ns: argparse.Namespace) -> int:
    queue_state = _build_queue_state(ns)
    query = run_operator_queue_query(operator_queue_snapshot=materialize_operator_queue_snapshot(governance_work_queue=queue_state))
    bridge_activation = materialize_operator_normalization_bridge_activation(
        build_operator_normalization_bridge_activation_request(
            activation_root=Path(ns.convergence_root) / 'normalization_bridge_activation',
            board_label=ns.board_label,
            activator_label=ns.converger_label,
            activated_at_utc=parse_utc(ns.issued_at_utc),
            monitoring_started_at_utc=parse_utc(ns.monitoring_started_at_utc) if ns.monitoring_started_at_utc else parse_utc(ns.issued_at_utc) - timedelta(hours=2),
        ),
        monitored_rejoin_normalization_bridge=materialize_operator_monitored_rejoin_normalization_bridge(
            build_operator_monitored_rejoin_normalization_bridge_request(
                bridge_root=Path(ns.convergence_root) / 'normalization_bridge_activation' / 'monitored_rejoin_normalization_bridge',
                board_label=ns.board_label,
                bridged_at_utc=parse_utc(ns.issued_at_utc),
            ),
            operator_queue_query_result=query,
            board_label=ns.board_label,
        ),
        board_label=ns.board_label,
    )
    payload = materialize_operator_chronic_watch_audit_convergence(
        build_operator_chronic_watch_audit_convergence_request(
            convergence_root=Path(ns.convergence_root),
            board_label=ns.board_label,
            converger_label=ns.converger_label,
            converged_at_utc=parse_utc(ns.issued_at_utc),
            normalization_window_minutes=ns.normalization_window_minutes,
        ),
        normalization_bridge_activation=bridge_activation,
        board_label=ns.board_label,
    ).to_payload()
    return _emit_payload(payload, ns.output)
def cmd_oracle_operator_converged_normalization_attestation(ns: argparse.Namespace) -> int:
    queue_state = _build_queue_state(ns)
    query = run_operator_queue_query(operator_queue_snapshot=materialize_operator_queue_snapshot(governance_work_queue=queue_state))
    convergence = materialize_operator_chronic_watch_audit_convergence(
        build_operator_chronic_watch_audit_convergence_request(
            convergence_root=Path(ns.attestation_root) / 'chronic_watch_audit_convergence',
            board_label=ns.board_label,
            converger_label=ns.attestor_label,
            converged_at_utc=parse_utc(ns.issued_at_utc),
            normalization_window_minutes=ns.normalization_window_minutes,
        ),
        normalization_bridge_activation=materialize_operator_normalization_bridge_activation(
            build_operator_normalization_bridge_activation_request(
                activation_root=Path(ns.attestation_root) / 'chronic_watch_audit_convergence' / 'normalization_bridge_activation',
                board_label=ns.board_label,
                activator_label=ns.attestor_label,
                activated_at_utc=parse_utc(ns.issued_at_utc),
                monitoring_started_at_utc=parse_utc(ns.monitoring_started_at_utc) if ns.monitoring_started_at_utc else parse_utc(ns.issued_at_utc) - timedelta(hours=2),
            ),
            monitored_rejoin_normalization_bridge=materialize_operator_monitored_rejoin_normalization_bridge(
                build_operator_monitored_rejoin_normalization_bridge_request(
                    bridge_root=Path(ns.attestation_root) / 'chronic_watch_audit_convergence' / 'normalization_bridge_activation' / 'monitored_rejoin_normalization_bridge',
                    board_label=ns.board_label,
                    bridged_at_utc=parse_utc(ns.issued_at_utc),
                ),
                operator_queue_query_result=query,
                board_label=ns.board_label,
            ),
            board_label=ns.board_label,
        ),
        board_label=ns.board_label,
    )
    payload = materialize_operator_converged_normalization_attestation(
        build_operator_converged_normalization_attestation_request(
            attestation_root=Path(ns.attestation_root),
            board_label=ns.board_label,
            attestor_label=ns.attestor_label,
            attested_at_utc=parse_utc(ns.issued_at_utc),
        ),
        chronic_watch_audit_convergence=convergence,
        board_label=ns.board_label,
    ).to_payload()
    return _emit_payload(payload, ns.output)
def cmd_oracle_operator_chronic_origin_restoration_provenance(ns: argparse.Namespace) -> int:
    queue_state = _build_queue_state(ns)
    query = run_operator_queue_query(operator_queue_snapshot=materialize_operator_queue_snapshot(governance_work_queue=queue_state))
    attestation = materialize_operator_converged_normalization_attestation(
        build_operator_converged_normalization_attestation_request(
            attestation_root=Path(ns.provenance_root) / 'converged_normalization_attestation',
            board_label=ns.board_label,
            attestor_label=ns.provenance_label,
            attested_at_utc=parse_utc(ns.issued_at_utc),
        ),
        chronic_watch_audit_convergence=materialize_operator_chronic_watch_audit_convergence(
            build_operator_chronic_watch_audit_convergence_request(
                convergence_root=Path(ns.provenance_root) / 'converged_normalization_attestation' / 'chronic_watch_audit_convergence',
                board_label=ns.board_label,
                converger_label=ns.provenance_label,
                converged_at_utc=parse_utc(ns.issued_at_utc),
                normalization_window_minutes=ns.normalization_window_minutes,
            ),
            normalization_bridge_activation=materialize_operator_normalization_bridge_activation(
                build_operator_normalization_bridge_activation_request(
                    activation_root=Path(ns.provenance_root) / 'converged_normalization_attestation' / 'chronic_watch_audit_convergence' / 'normalization_bridge_activation',
                    board_label=ns.board_label,
                    activator_label=ns.provenance_label,
                    activated_at_utc=parse_utc(ns.issued_at_utc),
                    monitoring_started_at_utc=parse_utc(ns.monitoring_started_at_utc) if ns.monitoring_started_at_utc else parse_utc(ns.issued_at_utc) - timedelta(hours=2),
                ),
                monitored_rejoin_normalization_bridge=materialize_operator_monitored_rejoin_normalization_bridge(
                    build_operator_monitored_rejoin_normalization_bridge_request(
                        bridge_root=Path(ns.provenance_root) / 'converged_normalization_attestation' / 'chronic_watch_audit_convergence' / 'normalization_bridge_activation' / 'monitored_rejoin_normalization_bridge',
                        board_label=ns.board_label,
                        bridged_at_utc=parse_utc(ns.issued_at_utc),
                    ),
                    operator_queue_query_result=query,
                    board_label=ns.board_label,
                ),
                board_label=ns.board_label,
            ),
            board_label=ns.board_label,
        ),
        board_label=ns.board_label,
    )
    payload = materialize_operator_chronic_origin_restoration_provenance(
        build_operator_chronic_origin_restoration_provenance_request(
            provenance_root=Path(ns.provenance_root),
            board_label=ns.board_label,
            provenance_label=ns.provenance_label,
            recorded_at_utc=parse_utc(ns.issued_at_utc),
        ),
        converged_normalization_attestation=attestation,
        board_label=ns.board_label,
    ).to_payload()
    return _emit_payload(payload, ns.output)
def cmd_oracle_operator_chronic_origin_restoration_audit_overlay(ns: argparse.Namespace) -> int:
    queue_state = _build_queue_state(ns)
    query = run_operator_queue_query(operator_queue_snapshot=materialize_operator_queue_snapshot(governance_work_queue=queue_state))
    provenance = materialize_operator_chronic_origin_restoration_provenance(
        build_operator_chronic_origin_restoration_provenance_request(
            provenance_root=Path(ns.overlay_root) / 'chronic_origin_restoration_provenance',
            board_label=ns.board_label,
            provenance_label=ns.overlay_label,
            recorded_at_utc=parse_utc(ns.issued_at_utc),
        ),
        operator_queue_query_result=query,
        board_label=ns.board_label,
    )
    restoration = materialize_operator_restoration_audit(
        build_operator_restoration_audit_request(
            audit_root=Path(ns.overlay_root) / 'restoration_audit',
            board_label=ns.board_label,
            auditor_label=ns.overlay_label,
            audited_at_utc=parse_utc(ns.issued_at_utc),
        ),
        operator_queue_query_result=query,
        board_label=ns.board_label,
    )
    payload = materialize_operator_chronic_origin_restoration_audit_overlay(
        build_operator_chronic_origin_restoration_audit_overlay_request(
            overlay_root=Path(ns.overlay_root),
            board_label=ns.board_label,
            overlay_label=ns.overlay_label,
            overlaid_at_utc=parse_utc(ns.issued_at_utc),
        ),
        chronic_origin_restoration_provenance=provenance,
        restoration_audit=restoration,
        board_label=ns.board_label,
    ).to_payload()
    return _emit_payload(payload, ns.output)
def cmd_oracle_operator_provenance_aware_drift_policy(ns: argparse.Namespace) -> int:
    queue_state = _build_queue_state(ns)
    query = run_operator_queue_query(operator_queue_snapshot=materialize_operator_queue_snapshot(governance_work_queue=queue_state))
    overlay = materialize_operator_chronic_origin_restoration_audit_overlay(
        build_operator_chronic_origin_restoration_audit_overlay_request(
            overlay_root=Path(ns.policy_root) / 'chronic_origin_restoration_audit_overlay',
            board_label=ns.board_label,
            overlay_label=ns.policy_label,
            overlaid_at_utc=parse_utc(ns.issued_at_utc),
        ),
        operator_queue_query_result=query,
        board_label=ns.board_label,
    )
    payload = materialize_operator_provenance_aware_drift_policy(
        build_operator_provenance_aware_drift_policy_request(
            policy_root=Path(ns.policy_root),
            board_label=ns.board_label,
            policy_label=ns.policy_label,
            evaluated_at_utc=parse_utc(ns.issued_at_utc),
        ),
        chronic_origin_restoration_audit_overlay=overlay,
        board_label=ns.board_label,
    ).to_payload()
    return _emit_payload(payload, ns.output)

__all__ = ['cmd_oracle_operator_chronic_exit_return_bridge', 'cmd_oracle_operator_monitored_rejoin_policy', 'cmd_oracle_operator_monitored_rejoin_activation', 'cmd_oracle_operator_chronic_watch_handoff', 'cmd_oracle_operator_control_plane_bundle', 'cmd_oracle_operator_return_monitoring', 'cmd_oracle_operator_restoration_audit', 'cmd_oracle_operator_return_drift_breach', 'cmd_oracle_operator_return_reopen_loop', 'cmd_oracle_operator_chronic_watch_outcome', 'cmd_oracle_operator_monitored_rejoin_normalization_bridge', 'cmd_oracle_operator_normalization_bridge_activation', 'cmd_oracle_operator_chronic_watch_audit_convergence', 'cmd_oracle_operator_converged_normalization_attestation', 'cmd_oracle_operator_chronic_origin_restoration_provenance', 'cmd_oracle_operator_chronic_origin_restoration_audit_overlay', 'cmd_oracle_operator_provenance_aware_drift_policy']
