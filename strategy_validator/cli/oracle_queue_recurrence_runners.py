from __future__ import annotations

from strategy_validator.cli.oracle_queue_runner_common import *
from strategy_validator.cli.oracle_queue_runner_common import _build_queue_state, _emit_payload, _parse_prior_reopen_counts

def cmd_oracle_operator_reopen_lineage(ns: argparse.Namespace) -> int:
    queue_state = _build_queue_state(ns)
    query = run_operator_queue_query(operator_queue_snapshot=materialize_operator_queue_snapshot(governance_work_queue=queue_state))
    payload = materialize_operator_reopen_lineage(
        build_operator_reopen_lineage_request(
            lineage_root=Path(ns.lineage_root),
            board_label=ns.board_label,
            lineage_label=ns.lineage_label,
            analyzed_at_utc=parse_utc(ns.issued_at_utc),
            prior_reopen_counts=_parse_prior_reopen_counts(ns.prior_reopen_count),
            drift_signal_mode=ns.drift_signal_mode,
        ),
        operator_queue_query_result=query,
        board_label=ns.board_label,
    ).to_payload()
    return _emit_payload(payload, ns.output)
def cmd_oracle_operator_reopen_recurrence_policy(ns: argparse.Namespace) -> int:
    queue_state = _build_queue_state(ns)
    query = run_operator_queue_query(operator_queue_snapshot=materialize_operator_queue_snapshot(governance_work_queue=queue_state))
    reopen_lineage = materialize_operator_reopen_lineage(
        build_operator_reopen_lineage_request(
            lineage_root=Path(ns.policy_root) / 'reopen_lineage',
            board_label=ns.board_label,
            lineage_label=ns.evaluator_label,
            analyzed_at_utc=parse_utc(ns.issued_at_utc),
            prior_reopen_counts=_parse_prior_reopen_counts(ns.prior_reopen_count),
            drift_signal_mode=ns.drift_signal_mode,
        ),
        operator_queue_query_result=query,
        board_label=ns.board_label,
    )
    payload = materialize_operator_reopen_recurrence_policy(
        build_operator_reopen_recurrence_policy_request(
            policy_root=Path(ns.policy_root),
            board_label=ns.board_label,
            evaluator_label=ns.evaluator_label,
            evaluated_at_utc=parse_utc(ns.issued_at_utc),
            escalation_after_reopen_count=ns.escalation_after_reopen_count,
            chronic_after_reopen_count=ns.chronic_after_reopen_count,
            drift_signal_mode=ns.drift_signal_mode,
        ),
        reopen_lineage=reopen_lineage,
        board_label=ns.board_label,
    ).to_payload()
    return _emit_payload(payload, ns.output)
def cmd_oracle_operator_chronic_instability_packet(ns: argparse.Namespace) -> int:
    queue_state = _build_queue_state(ns)
    query = run_operator_queue_query(operator_queue_snapshot=materialize_operator_queue_snapshot(governance_work_queue=queue_state))
    reopen_lineage = materialize_operator_reopen_lineage(
        build_operator_reopen_lineage_request(
            lineage_root=Path(ns.packet_root) / 'reopen_lineage',
            board_label=ns.board_label,
            lineage_label=ns.evaluator_label,
            analyzed_at_utc=parse_utc(ns.issued_at_utc),
            prior_reopen_counts=_parse_prior_reopen_counts(ns.prior_reopen_count),
            drift_signal_mode=ns.drift_signal_mode,
        ),
        operator_queue_query_result=query,
        board_label=ns.board_label,
    )
    recurrence_policy = materialize_operator_reopen_recurrence_policy(
        build_operator_reopen_recurrence_policy_request(
            policy_root=Path(ns.packet_root) / 'reopen_recurrence_policy',
            board_label=ns.board_label,
            evaluator_label=ns.evaluator_label,
            evaluated_at_utc=parse_utc(ns.issued_at_utc),
            escalation_after_reopen_count=ns.escalation_after_reopen_count,
            chronic_after_reopen_count=ns.chronic_after_reopen_count,
            drift_signal_mode=ns.drift_signal_mode,
        ),
        reopen_lineage=reopen_lineage,
        board_label=ns.board_label,
    )
    payload = materialize_operator_chronic_instability_packet(
        build_operator_chronic_instability_packet_request(
            packet_root=Path(ns.packet_root),
            board_label=ns.board_label,
            evaluator_label=ns.evaluator_label,
            emitted_at_utc=parse_utc(ns.issued_at_utc),
        ),
        reopen_recurrence_policy=recurrence_policy,
        board_label=ns.board_label,
    ).to_payload()
    return _emit_payload(payload, ns.output)
def cmd_oracle_operator_recurrence_tribunal_lane(ns: argparse.Namespace) -> int:
    queue_state = _build_queue_state(ns)
    query = run_operator_queue_query(operator_queue_snapshot=materialize_operator_queue_snapshot(governance_work_queue=queue_state))
    reopen_lineage = materialize_operator_reopen_lineage(
        build_operator_reopen_lineage_request(
            lineage_root=Path(ns.tribunal_root) / 'reopen_lineage',
            board_label=ns.board_label,
            lineage_label=ns.reviewer_label,
            analyzed_at_utc=parse_utc(ns.issued_at_utc),
            prior_reopen_counts=_parse_prior_reopen_counts(ns.prior_reopen_count),
            drift_signal_mode=ns.drift_signal_mode,
        ),
        operator_queue_query_result=query,
        board_label=ns.board_label,
    )
    recurrence_policy = materialize_operator_reopen_recurrence_policy(
        build_operator_reopen_recurrence_policy_request(
            policy_root=Path(ns.tribunal_root) / 'reopen_recurrence_policy',
            board_label=ns.board_label,
            evaluator_label=ns.reviewer_label,
            evaluated_at_utc=parse_utc(ns.issued_at_utc),
            escalation_after_reopen_count=ns.escalation_after_reopen_count,
            chronic_after_reopen_count=ns.chronic_after_reopen_count,
            drift_signal_mode=ns.drift_signal_mode,
        ),
        reopen_lineage=reopen_lineage,
        board_label=ns.board_label,
    )
    packet = materialize_operator_chronic_instability_packet(
        build_operator_chronic_instability_packet_request(
            packet_root=Path(ns.tribunal_root) / 'chronic_instability_packet',
            board_label=ns.board_label,
            evaluator_label=ns.reviewer_label,
            emitted_at_utc=parse_utc(ns.issued_at_utc),
        ),
        reopen_recurrence_policy=recurrence_policy,
        board_label=ns.board_label,
    )
    payload = materialize_operator_recurrence_tribunal_lane(
        build_operator_recurrence_tribunal_lane_request(
            tribunal_root=Path(ns.tribunal_root),
            board_label=ns.board_label,
            reviewer_label=ns.reviewer_label,
            reviewed_at_utc=parse_utc(ns.issued_at_utc),
        ),
        chronic_instability_packet=packet,
        board_label=ns.board_label,
    ).to_payload()
    return _emit_payload(payload, ns.output)
def cmd_oracle_operator_recurrence_tribunal_disposition(ns: argparse.Namespace) -> int:
    queue_state = _build_queue_state(ns)
    query = run_operator_queue_query(operator_queue_snapshot=materialize_operator_queue_snapshot(governance_work_queue=queue_state))
    payload = materialize_operator_recurrence_tribunal_disposition(
        build_operator_recurrence_tribunal_disposition_request(
            disposition_root=Path(ns.disposition_root),
            board_label=ns.board_label,
            reviewed_at_utc=parse_utc(ns.issued_at_utc),
        ),
        recurrence_tribunal_lane=materialize_operator_recurrence_tribunal_lane(
            build_operator_recurrence_tribunal_lane_request(
                tribunal_root=Path(ns.disposition_root) / 'recurrence_tribunal_lane',
                board_label=ns.board_label,
                reviewed_at_utc=parse_utc(ns.issued_at_utc),
            ),
            chronic_instability_packet=materialize_operator_chronic_instability_packet(
                build_operator_chronic_instability_packet_request(
                    packet_root=Path(ns.disposition_root) / 'recurrence_tribunal_lane' / 'chronic_instability_packet',
                    board_label=ns.board_label,
                    emitted_at_utc=parse_utc(ns.issued_at_utc),
                ),
                reopen_recurrence_policy=materialize_operator_reopen_recurrence_policy(
                    build_operator_reopen_recurrence_policy_request(
                        policy_root=Path(ns.disposition_root) / 'recurrence_tribunal_lane' / 'chronic_instability_packet' / 'reopen_recurrence_policy',
                        board_label=ns.board_label,
                        evaluated_at_utc=parse_utc(ns.issued_at_utc),
                    ),
                    reopen_lineage=materialize_operator_reopen_lineage(
                        build_operator_reopen_lineage_request(
                            lineage_root=Path(ns.disposition_root) / 'recurrence_tribunal_lane' / 'chronic_instability_packet' / 'reopen_recurrence_policy' / 'reopen_lineage',
                            board_label=ns.board_label,
                            analyzed_at_utc=parse_utc(ns.issued_at_utc),
                            prior_reopen_counts=_parse_prior_reopen_counts(ns.prior_reopen_count),
                        ),
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
    ).to_payload()
    return _emit_payload(payload, ns.output)
def cmd_oracle_operator_chronic_remediation_mandate_ledger(ns: argparse.Namespace) -> int:
    queue_state = _build_queue_state(ns)
    query = run_operator_queue_query(operator_queue_snapshot=materialize_operator_queue_snapshot(governance_work_queue=queue_state))
    payload = materialize_operator_chronic_remediation_mandate_ledger(
        build_operator_chronic_remediation_mandate_ledger_request(
            ledger_root=Path(ns.ledger_root),
            board_label=ns.board_label,
            mandated_at_utc=parse_utc(ns.issued_at_utc),
        ),
        recurrence_tribunal_disposition=materialize_operator_recurrence_tribunal_disposition(
            build_operator_recurrence_tribunal_disposition_request(
                disposition_root=Path(ns.ledger_root) / 'recurrence_tribunal_disposition',
                board_label=ns.board_label,
                reviewed_at_utc=parse_utc(ns.issued_at_utc),
            ),
            recurrence_tribunal_lane=materialize_operator_recurrence_tribunal_lane(
                build_operator_recurrence_tribunal_lane_request(
                    tribunal_root=Path(ns.ledger_root) / 'recurrence_tribunal_disposition' / 'recurrence_tribunal_lane',
                    board_label=ns.board_label,
                    reviewed_at_utc=parse_utc(ns.issued_at_utc),
                ),
                chronic_instability_packet=materialize_operator_chronic_instability_packet(
                    build_operator_chronic_instability_packet_request(
                        packet_root=Path(ns.ledger_root) / 'recurrence_tribunal_disposition' / 'recurrence_tribunal_lane' / 'chronic_instability_packet',
                        board_label=ns.board_label,
                        emitted_at_utc=parse_utc(ns.issued_at_utc),
                    ),
                    reopen_recurrence_policy=materialize_operator_reopen_recurrence_policy(
                        build_operator_reopen_recurrence_policy_request(
                            policy_root=Path(ns.ledger_root) / 'recurrence_tribunal_disposition' / 'recurrence_tribunal_lane' / 'chronic_instability_packet' / 'reopen_recurrence_policy',
                            board_label=ns.board_label,
                            evaluated_at_utc=parse_utc(ns.issued_at_utc),
                        ),
                        reopen_lineage=materialize_operator_reopen_lineage(
                            build_operator_reopen_lineage_request(
                                lineage_root=Path(ns.ledger_root) / 'recurrence_tribunal_disposition' / 'recurrence_tribunal_lane' / 'chronic_instability_packet' / 'reopen_recurrence_policy' / 'reopen_lineage',
                                board_label=ns.board_label,
                                analyzed_at_utc=parse_utc(ns.issued_at_utc),
                                prior_reopen_counts=_parse_prior_reopen_counts(ns.prior_reopen_count),
                            ),
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
    ).to_payload()
    return _emit_payload(payload, ns.output)
def cmd_oracle_operator_chronic_remediation_satisfaction(ns: argparse.Namespace) -> int:
    queue_state = _build_queue_state(ns)
    query = run_operator_queue_query(operator_queue_snapshot=materialize_operator_queue_snapshot(governance_work_queue=queue_state))
    payload = materialize_operator_chronic_remediation_satisfaction(
        build_operator_chronic_remediation_satisfaction_request(
            satisfaction_root=Path(ns.satisfaction_root),
            board_label=ns.board_label,
            evaluated_at_utc=parse_utc(ns.issued_at_utc),
        ),
        chronic_remediation_mandate_ledger=materialize_operator_chronic_remediation_mandate_ledger(
            build_operator_chronic_remediation_mandate_ledger_request(
                ledger_root=Path(ns.satisfaction_root) / 'chronic_remediation_mandate_ledger',
                board_label=ns.board_label,
                mandated_at_utc=parse_utc(ns.issued_at_utc),
            ),
            recurrence_tribunal_disposition=materialize_operator_recurrence_tribunal_disposition(
                build_operator_recurrence_tribunal_disposition_request(
                    disposition_root=Path(ns.satisfaction_root) / 'chronic_remediation_mandate_ledger' / 'recurrence_tribunal_disposition',
                    board_label=ns.board_label,
                    reviewed_at_utc=parse_utc(ns.issued_at_utc),
                ),
                recurrence_tribunal_lane=materialize_operator_recurrence_tribunal_lane(
                    build_operator_recurrence_tribunal_lane_request(
                        tribunal_root=Path(ns.satisfaction_root) / 'chronic_remediation_mandate_ledger' / 'recurrence_tribunal_disposition' / 'recurrence_tribunal_lane',
                        board_label=ns.board_label,
                        reviewed_at_utc=parse_utc(ns.issued_at_utc),
                    ),
                    chronic_instability_packet=materialize_operator_chronic_instability_packet(
                        build_operator_chronic_instability_packet_request(
                            packet_root=Path(ns.satisfaction_root) / 'chronic_remediation_mandate_ledger' / 'recurrence_tribunal_disposition' / 'recurrence_tribunal_lane' / 'chronic_instability_packet',
                            board_label=ns.board_label,
                            emitted_at_utc=parse_utc(ns.issued_at_utc),
                        ),
                        reopen_recurrence_policy=materialize_operator_reopen_recurrence_policy(
                            build_operator_reopen_recurrence_policy_request(
                                policy_root=Path(ns.satisfaction_root) / 'chronic_remediation_mandate_ledger' / 'recurrence_tribunal_disposition' / 'recurrence_tribunal_lane' / 'chronic_instability_packet' / 'reopen_recurrence_policy',
                                board_label=ns.board_label,
                                evaluated_at_utc=parse_utc(ns.issued_at_utc),
                            ),
                            reopen_lineage=materialize_operator_reopen_lineage(
                                build_operator_reopen_lineage_request(
                                    lineage_root=Path(ns.satisfaction_root) / 'chronic_remediation_mandate_ledger' / 'recurrence_tribunal_disposition' / 'recurrence_tribunal_lane' / 'chronic_instability_packet' / 'reopen_recurrence_policy' / 'reopen_lineage',
                                    board_label=ns.board_label,
                                    analyzed_at_utc=parse_utc(ns.issued_at_utc),
                                    prior_reopen_counts=_parse_prior_reopen_counts(ns.prior_reopen_count),
                                ),
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
    ).to_payload()
    return _emit_payload(payload, ns.output)
def cmd_oracle_operator_freeze_release_gate(ns: argparse.Namespace) -> int:
    queue_state = _build_queue_state(ns)
    query = run_operator_queue_query(operator_queue_snapshot=materialize_operator_queue_snapshot(governance_work_queue=queue_state))
    payload = materialize_operator_freeze_release_gate(
        build_operator_freeze_release_gate_request(
            gate_root=Path(ns.gate_root),
            board_label=ns.board_label,
            reviewed_at_utc=parse_utc(ns.issued_at_utc),
        ),
        chronic_remediation_satisfaction=materialize_operator_chronic_remediation_satisfaction(
            build_operator_chronic_remediation_satisfaction_request(
                satisfaction_root=Path(ns.gate_root) / 'chronic_remediation_satisfaction',
                board_label=ns.board_label,
                evaluated_at_utc=parse_utc(ns.issued_at_utc),
            ),
            chronic_remediation_mandate_ledger=materialize_operator_chronic_remediation_mandate_ledger(
                build_operator_chronic_remediation_mandate_ledger_request(
                    ledger_root=Path(ns.gate_root) / 'chronic_remediation_satisfaction' / 'chronic_remediation_mandate_ledger',
                    board_label=ns.board_label,
                    mandated_at_utc=parse_utc(ns.issued_at_utc),
                ),
                recurrence_tribunal_disposition=materialize_operator_recurrence_tribunal_disposition(
                    build_operator_recurrence_tribunal_disposition_request(
                        disposition_root=Path(ns.gate_root) / 'chronic_remediation_satisfaction' / 'chronic_remediation_mandate_ledger' / 'recurrence_tribunal_disposition',
                        board_label=ns.board_label,
                        reviewed_at_utc=parse_utc(ns.issued_at_utc),
                    ),
                    recurrence_tribunal_lane=materialize_operator_recurrence_tribunal_lane(
                        build_operator_recurrence_tribunal_lane_request(
                            tribunal_root=Path(ns.gate_root) / 'chronic_remediation_satisfaction' / 'chronic_remediation_mandate_ledger' / 'recurrence_tribunal_disposition' / 'recurrence_tribunal_lane',
                            board_label=ns.board_label,
                            reviewed_at_utc=parse_utc(ns.issued_at_utc),
                        ),
                        chronic_instability_packet=materialize_operator_chronic_instability_packet(
                            build_operator_chronic_instability_packet_request(
                                packet_root=Path(ns.gate_root) / 'chronic_remediation_satisfaction' / 'chronic_remediation_mandate_ledger' / 'recurrence_tribunal_disposition' / 'recurrence_tribunal_lane' / 'chronic_instability_packet',
                                board_label=ns.board_label,
                                emitted_at_utc=parse_utc(ns.issued_at_utc),
                            ),
                            reopen_recurrence_policy=materialize_operator_reopen_recurrence_policy(
                                build_operator_reopen_recurrence_policy_request(
                                    policy_root=Path(ns.gate_root) / 'chronic_remediation_satisfaction' / 'chronic_remediation_mandate_ledger' / 'recurrence_tribunal_disposition' / 'recurrence_tribunal_lane' / 'chronic_instability_packet' / 'reopen_recurrence_policy',
                                    board_label=ns.board_label,
                                    evaluated_at_utc=parse_utc(ns.issued_at_utc),
                                ),
                                reopen_lineage=materialize_operator_reopen_lineage(
                                    build_operator_reopen_lineage_request(
                                        lineage_root=Path(ns.gate_root) / 'chronic_remediation_satisfaction' / 'chronic_remediation_mandate_ledger' / 'recurrence_tribunal_disposition' / 'recurrence_tribunal_lane' / 'chronic_instability_packet' / 'reopen_recurrence_policy' / 'reopen_lineage',
                                        board_label=ns.board_label,
                                        analyzed_at_utc=parse_utc(ns.issued_at_utc),
                                        prior_reopen_counts=_parse_prior_reopen_counts(ns.prior_reopen_count),
                                    ),
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
    ).to_payload()
    return _emit_payload(payload, ns.output)
def cmd_oracle_operator_freeze_release_attestation(ns: argparse.Namespace) -> int:
    queue_state = _build_queue_state(ns)
    query = run_operator_queue_query(operator_queue_snapshot=materialize_operator_queue_snapshot(governance_work_queue=queue_state))
    payload = materialize_operator_freeze_release_attestation(
        build_operator_freeze_release_attestation_request(attestation_root=Path(ns.attestation_root), board_label=ns.board_label, attested_at_utc=parse_utc(ns.issued_at_utc)),
        freeze_release_gate=materialize_operator_freeze_release_gate(
            build_operator_freeze_release_gate_request(gate_root=Path(ns.attestation_root) / 'freeze_release_gate', board_label=ns.board_label, reviewed_at_utc=parse_utc(ns.issued_at_utc)),
            chronic_remediation_satisfaction=materialize_operator_chronic_remediation_satisfaction(
                build_operator_chronic_remediation_satisfaction_request(satisfaction_root=Path(ns.attestation_root) / 'freeze_release_gate' / 'chronic_remediation_satisfaction', board_label=ns.board_label, evaluated_at_utc=parse_utc(ns.issued_at_utc)),
                chronic_remediation_mandate_ledger=materialize_operator_chronic_remediation_mandate_ledger(
                    build_operator_chronic_remediation_mandate_ledger_request(ledger_root=Path(ns.attestation_root) / 'freeze_release_gate' / 'chronic_remediation_satisfaction' / 'chronic_remediation_mandate_ledger', board_label=ns.board_label, mandated_at_utc=parse_utc(ns.issued_at_utc)),
                    recurrence_tribunal_disposition=materialize_operator_recurrence_tribunal_disposition(
                        build_operator_recurrence_tribunal_disposition_request(disposition_root=Path(ns.attestation_root) / 'freeze_release_gate' / 'chronic_remediation_satisfaction' / 'chronic_remediation_mandate_ledger' / 'recurrence_tribunal_disposition', board_label=ns.board_label, reviewed_at_utc=parse_utc(ns.issued_at_utc)),
                        recurrence_tribunal_lane=materialize_operator_recurrence_tribunal_lane(
                            build_operator_recurrence_tribunal_lane_request(tribunal_root=Path(ns.attestation_root) / 'freeze_release_gate' / 'chronic_remediation_satisfaction' / 'chronic_remediation_mandate_ledger' / 'recurrence_tribunal_disposition' / 'recurrence_tribunal_lane', board_label=ns.board_label, reviewed_at_utc=parse_utc(ns.issued_at_utc)),
                            chronic_instability_packet=materialize_operator_chronic_instability_packet(
                                build_operator_chronic_instability_packet_request(packet_root=Path(ns.attestation_root) / 'freeze_release_gate' / 'chronic_remediation_satisfaction' / 'chronic_remediation_mandate_ledger' / 'recurrence_tribunal_disposition' / 'recurrence_tribunal_lane' / 'chronic_instability_packet', board_label=ns.board_label, emitted_at_utc=parse_utc(ns.issued_at_utc)),
                                reopen_recurrence_policy=materialize_operator_reopen_recurrence_policy(
                                    build_operator_reopen_recurrence_policy_request(policy_root=Path(ns.attestation_root) / 'freeze_release_gate' / 'chronic_remediation_satisfaction' / 'chronic_remediation_mandate_ledger' / 'recurrence_tribunal_disposition' / 'recurrence_tribunal_lane' / 'chronic_instability_packet' / 'reopen_recurrence_policy', board_label=ns.board_label, evaluated_at_utc=parse_utc(ns.issued_at_utc)),
                                    reopen_lineage=materialize_operator_reopen_lineage(
                                        build_operator_reopen_lineage_request(lineage_root=Path(ns.attestation_root) / 'freeze_release_gate' / 'chronic_remediation_satisfaction' / 'chronic_remediation_mandate_ledger' / 'recurrence_tribunal_disposition' / 'recurrence_tribunal_lane' / 'chronic_instability_packet' / 'reopen_recurrence_policy' / 'reopen_lineage', board_label=ns.board_label, analyzed_at_utc=parse_utc(ns.issued_at_utc), prior_reopen_counts=_parse_prior_reopen_counts(ns.prior_reopen_count)),
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
    ).to_payload()
    return _emit_payload(payload, ns.output)
def cmd_oracle_operator_chronic_exit_certification(ns: argparse.Namespace) -> int:
    queue_state = _build_queue_state(ns)
    query = run_operator_queue_query(operator_queue_snapshot=materialize_operator_queue_snapshot(governance_work_queue=queue_state))
    payload = materialize_operator_chronic_exit_certification(
        build_operator_chronic_exit_certification_request(certification_root=Path(ns.certification_root), board_label=ns.board_label, certified_at_utc=parse_utc(ns.issued_at_utc)),
        freeze_release_attestation=materialize_operator_freeze_release_attestation(
            build_operator_freeze_release_attestation_request(attestation_root=Path(ns.certification_root) / 'freeze_release_attestation', board_label=ns.board_label, attested_at_utc=parse_utc(ns.issued_at_utc)),
            freeze_release_gate=materialize_operator_freeze_release_gate(
                build_operator_freeze_release_gate_request(gate_root=Path(ns.certification_root) / 'freeze_release_attestation' / 'freeze_release_gate', board_label=ns.board_label, reviewed_at_utc=parse_utc(ns.issued_at_utc)),
                chronic_remediation_satisfaction=materialize_operator_chronic_remediation_satisfaction(
                    build_operator_chronic_remediation_satisfaction_request(satisfaction_root=Path(ns.certification_root) / 'freeze_release_attestation' / 'freeze_release_gate' / 'chronic_remediation_satisfaction', board_label=ns.board_label, evaluated_at_utc=parse_utc(ns.issued_at_utc)),
                    chronic_remediation_mandate_ledger=materialize_operator_chronic_remediation_mandate_ledger(
                        build_operator_chronic_remediation_mandate_ledger_request(ledger_root=Path(ns.certification_root) / 'freeze_release_attestation' / 'freeze_release_gate' / 'chronic_remediation_satisfaction' / 'chronic_remediation_mandate_ledger', board_label=ns.board_label, mandated_at_utc=parse_utc(ns.issued_at_utc)),
                        recurrence_tribunal_disposition=materialize_operator_recurrence_tribunal_disposition(
                            build_operator_recurrence_tribunal_disposition_request(disposition_root=Path(ns.certification_root) / 'freeze_release_attestation' / 'freeze_release_gate' / 'chronic_remediation_satisfaction' / 'chronic_remediation_mandate_ledger' / 'recurrence_tribunal_disposition', board_label=ns.board_label, reviewed_at_utc=parse_utc(ns.issued_at_utc)),
                            recurrence_tribunal_lane=materialize_operator_recurrence_tribunal_lane(
                                build_operator_recurrence_tribunal_lane_request(tribunal_root=Path(ns.certification_root) / 'freeze_release_attestation' / 'freeze_release_gate' / 'chronic_remediation_satisfaction' / 'chronic_remediation_mandate_ledger' / 'recurrence_tribunal_disposition' / 'recurrence_tribunal_lane', board_label=ns.board_label, reviewed_at_utc=parse_utc(ns.issued_at_utc)),
                                chronic_instability_packet=materialize_operator_chronic_instability_packet(
                                    build_operator_chronic_instability_packet_request(packet_root=Path(ns.certification_root) / 'freeze_release_attestation' / 'freeze_release_gate' / 'chronic_remediation_satisfaction' / 'chronic_remediation_mandate_ledger' / 'recurrence_tribunal_disposition' / 'recurrence_tribunal_lane' / 'chronic_instability_packet', board_label=ns.board_label, emitted_at_utc=parse_utc(ns.issued_at_utc)),
                                    reopen_recurrence_policy=materialize_operator_reopen_recurrence_policy(
                                        build_operator_reopen_recurrence_policy_request(policy_root=Path(ns.certification_root) / 'freeze_release_attestation' / 'freeze_release_gate' / 'chronic_remediation_satisfaction' / 'chronic_remediation_mandate_ledger' / 'recurrence_tribunal_disposition' / 'recurrence_tribunal_lane' / 'chronic_instability_packet' / 'reopen_recurrence_policy', board_label=ns.board_label, evaluated_at_utc=parse_utc(ns.issued_at_utc)),
                                        reopen_lineage=materialize_operator_reopen_lineage(
                                            build_operator_reopen_lineage_request(lineage_root=Path(ns.certification_root) / 'freeze_release_attestation' / 'freeze_release_gate' / 'chronic_remediation_satisfaction' / 'chronic_remediation_mandate_ledger' / 'recurrence_tribunal_disposition' / 'recurrence_tribunal_lane' / 'chronic_instability_packet' / 'reopen_recurrence_policy' / 'reopen_lineage', board_label=ns.board_label, analyzed_at_utc=parse_utc(ns.issued_at_utc), prior_reopen_counts=_parse_prior_reopen_counts(ns.prior_reopen_count)),
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
    ).to_payload()
    return _emit_payload(payload, ns.output)


__all__ = ['cmd_oracle_operator_reopen_lineage', 'cmd_oracle_operator_reopen_recurrence_policy', 'cmd_oracle_operator_chronic_instability_packet', 'cmd_oracle_operator_recurrence_tribunal_lane', 'cmd_oracle_operator_recurrence_tribunal_disposition', 'cmd_oracle_operator_chronic_remediation_mandate_ledger', 'cmd_oracle_operator_chronic_remediation_satisfaction', 'cmd_oracle_operator_freeze_release_gate', 'cmd_oracle_operator_freeze_release_attestation', 'cmd_oracle_operator_chronic_exit_certification']
