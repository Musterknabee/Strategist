from __future__ import annotations

from strategy_validator.cli.oracle_queue_runner_common import *
from strategy_validator.cli.oracle_queue_runner_common import _build_queue_state, _emit_payload

def cmd_oracle_operator_reentry_queue_state(ns: argparse.Namespace) -> int:
    queue_state = _build_queue_state(ns)
    query = run_operator_queue_query(operator_queue_snapshot=materialize_operator_queue_snapshot(governance_work_queue=queue_state))
    decision_execution = materialize_operator_decision_execution(
        build_operator_decision_execution_request(execution_root=Path(ns.reentry_root) / 'decision_execution', emitted_at_utc=parse_utc(ns.issued_at_utc), board_label=ns.board_label, desired_transition=ns.desired_transition, actor_label=ns.actor_label, note=ns.note),
        operator_queue_query_result=query,
        board_label=ns.board_label,
    )
    escalation_routing = materialize_operator_escalation_routing(
        build_operator_escalation_routing_request(routing_root=Path(ns.reentry_root) / 'routing', board_label=ns.board_label),
        decision_execution=decision_execution,
        operator_queue_query_result=query,
        board_label=ns.board_label,
    )
    escalation_packet = materialize_operator_escalation_packet(
        build_operator_escalation_packet_request(packet_root=Path(ns.reentry_root) / 'packet', board_label=ns.board_label),
        escalation_routing=escalation_routing,
        decision_execution=decision_execution,
        operator_queue_query_result=query,
        board_label=ns.board_label,
    )
    escalation_started_at_utc = parse_utc(ns.escalation_started_at_utc) if ns.escalation_started_at_utc else parse_utc(ns.issued_at_utc)
    escalation_sla = materialize_operator_escalation_sla(
        build_operator_escalation_sla_request(sla_root=Path(ns.reentry_root) / 'sla', board_label=ns.board_label, evaluated_at_utc=parse_utc(ns.issued_at_utc), escalation_started_at_utc=escalation_started_at_utc),
        escalation_packet=escalation_packet,
        board_label=ns.board_label,
    )
    supervisor_review = materialize_operator_supervisor_review(
        build_operator_supervisor_review_request(review_root=Path(ns.reentry_root) / 'review', board_label=ns.board_label, supervisor_actor_label=ns.supervisor_actor_label, note=ns.supervisor_note, reviewed_at_utc=parse_utc(ns.issued_at_utc)),
        escalation_packet=escalation_packet,
        escalation_sla=escalation_sla,
        board_label=ns.board_label,
    )
    escalation_closure = materialize_operator_escalation_closure(
        build_operator_escalation_closure_request(closure_root=Path(ns.reentry_root) / 'closure', board_label=ns.board_label, closed_at_utc=parse_utc(ns.issued_at_utc)),
        supervisor_review=supervisor_review,
        board_label=ns.board_label,
    )
    action_contract = materialize_operator_workboard_action_contract(
        operator_queue_query_result=query,
        board_label=ns.board_label,
    )
    payload = materialize_operator_reentry_queue_state(
        build_operator_reentry_queue_state_request(reentry_root=Path(ns.reentry_root), board_label=ns.board_label, reopened_at_utc=parse_utc(ns.issued_at_utc)),
        escalation_closure=escalation_closure,
        action_contract=action_contract,
        board_label=ns.board_label,
    ).to_payload()
    return _emit_payload(payload, ns.output)

def cmd_oracle_operator_reentry_assignment(ns: argparse.Namespace) -> int:
    queue_state = _build_queue_state(ns)
    query = run_operator_queue_query(operator_queue_snapshot=materialize_operator_queue_snapshot(governance_work_queue=queue_state))
    payload = materialize_operator_reentry_assignment(
        build_operator_reentry_assignment_request(
            assignment_root=Path(ns.assignment_root),
            board_label=ns.board_label,
            ownership_mode=ns.ownership_mode,
            default_assignee_label=ns.default_assignee_label,
            fallback_assignee_label=ns.fallback_assignee_label,
            assigned_at_utc=parse_utc(ns.issued_at_utc),
        ),
        operator_queue_query_result=query,
        board_label=ns.board_label,
    ).to_payload()
    return _emit_payload(payload, ns.output)

def cmd_oracle_operator_reentry_acceptance(ns: argparse.Namespace) -> int:
    queue_state = _build_queue_state(ns)
    query = run_operator_queue_query(operator_queue_snapshot=materialize_operator_queue_snapshot(governance_work_queue=queue_state))
    payload = materialize_operator_reentry_acceptance(
        build_operator_reentry_acceptance_request(
            acceptance_root=Path(ns.acceptance_root),
            board_label=ns.board_label,
            accepted_at_utc=parse_utc(ns.issued_at_utc),
        ),
        reentry_assignment=materialize_operator_reentry_assignment(
            build_operator_reentry_assignment_request(
                assignment_root=Path(ns.acceptance_root) / 'reentry_assignment',
                board_label=ns.board_label,
                ownership_mode=ns.ownership_mode,
                default_assignee_label=ns.default_assignee_label,
                fallback_assignee_label=ns.fallback_assignee_label,
                assigned_at_utc=parse_utc(ns.issued_at_utc),
            ),
            operator_queue_query_result=query,
            board_label=ns.board_label,
        ),
        board_label=ns.board_label,
    ).to_payload()
    return _emit_payload(payload, ns.output)

def cmd_oracle_operator_reentry_acknowledgement_timeout(ns: argparse.Namespace) -> int:
    queue_state = _build_queue_state(ns)
    accepted_at = parse_utc(ns.accepted_at_utc) if ns.accepted_at_utc else parse_utc(ns.issued_at_utc)
    evaluated_at = parse_utc(ns.evaluated_at_utc) if ns.evaluated_at_utc else parse_utc(ns.issued_at_utc)
    payload = materialize_operator_reentry_acknowledgement_timeout(
        build_operator_reentry_acknowledgement_timeout_request(
            timeout_root=Path(ns.timeout_root),
            board_label=ns.board_label,
            evaluated_at_utc=evaluated_at,
        ),
        reentry_acceptance=materialize_operator_reentry_acceptance(
            build_operator_reentry_acceptance_request(
                acceptance_root=Path(ns.timeout_root) / 'reentry_acceptance',
                board_label=ns.board_label,
                accepted_at_utc=accepted_at,
            ),
            reentry_assignment=materialize_operator_reentry_assignment(
                build_operator_reentry_assignment_request(
                    assignment_root=Path(ns.timeout_root) / 'reentry_assignment',
                    board_label=ns.board_label,
                    assigned_at_utc=accepted_at,
                ),
                reentry_queue_state=materialize_operator_reentry_queue_state(
                    build_operator_reentry_queue_state_request(
                        reentry_root=Path(ns.timeout_root) / 'reentry_queue_state',
                        board_label=ns.board_label,
                        reopened_at_utc=accepted_at,
                    ),
                    operator_queue_query_result=run_operator_queue_query(operator_queue_snapshot=materialize_operator_queue_snapshot(governance_work_queue=queue_state)),
                    board_label=ns.board_label,
                ),
                board_label=ns.board_label,
            ),
            board_label=ns.board_label,
        ),
        board_label=ns.board_label,
    ).to_payload()
    return _emit_payload(payload, ns.output)

def cmd_oracle_operator_reentry_completion_attestation(ns: argparse.Namespace) -> int:
    queue_state = _build_queue_state(ns)
    query = run_operator_queue_query(operator_queue_snapshot=materialize_operator_queue_snapshot(governance_work_queue=queue_state))
    payload = materialize_operator_reentry_completion_attestation(
        build_operator_reentry_completion_attestation_request(attestation_root=Path(ns.attestation_root), board_label=ns.board_label, attestor_label=ns.attestor_label, attested_at_utc=parse_utc(ns.issued_at_utc)),
        operator_queue_query_result=query,
        board_label=ns.board_label,
    ).to_payload()
    return _emit_payload(payload, ns.output)

def cmd_oracle_operator_reentry_post_review_gate(ns: argparse.Namespace) -> int:
    queue_state = _build_queue_state(ns)
    query = run_operator_queue_query(operator_queue_snapshot=materialize_operator_queue_snapshot(governance_work_queue=queue_state))
    payload = materialize_operator_reentry_post_review_gate(
        build_operator_reentry_post_review_gate_request(review_root=Path(ns.review_root), board_label=ns.board_label, reviewer_label=ns.reviewer_label, reviewed_at_utc=parse_utc(ns.issued_at_utc)),
        operator_queue_query_result=query,
        board_label=ns.board_label,
    ).to_payload()
    return _emit_payload(payload, ns.output)

def cmd_oracle_operator_post_review_disposition(ns: argparse.Namespace) -> int:
    queue_state = _build_queue_state(ns)
    query = run_operator_queue_query(operator_queue_snapshot=materialize_operator_queue_snapshot(governance_work_queue=queue_state))
    payload = materialize_operator_post_review_disposition(
        build_operator_post_review_disposition_request(
            disposition_root=Path(ns.disposition_root),
            board_label=ns.board_label,
            reviewer_label=ns.reviewer_label,
            reviewed_at_utc=parse_utc(ns.issued_at_utc),
        ),
        operator_queue_query_result=query,
        board_label=ns.board_label,
    ).to_payload()
    return _emit_payload(payload, ns.output)

def cmd_oracle_operator_return_authorization_ledger(ns: argparse.Namespace) -> int:
    queue_state = _build_queue_state(ns)
    query = run_operator_queue_query(operator_queue_snapshot=materialize_operator_queue_snapshot(governance_work_queue=queue_state))
    payload = materialize_operator_return_authorization_ledger(
        build_operator_return_authorization_ledger_request(
            ledger_root=Path(ns.ledger_root),
            board_label=ns.board_label,
            reviewer_label=ns.reviewer_label,
            authorized_at_utc=parse_utc(ns.issued_at_utc),
        ),
        operator_queue_query_result=query,
        board_label=ns.board_label,
    ).to_payload()
    return _emit_payload(payload, ns.output)

def cmd_oracle_operator_return_activation(ns: argparse.Namespace) -> int:
    queue_state = _build_queue_state(ns)
    query = run_operator_queue_query(operator_queue_snapshot=materialize_operator_queue_snapshot(governance_work_queue=queue_state))
    payload = materialize_operator_return_activation(
        build_operator_return_activation_request(
            activation_root=Path(ns.activation_root),
            board_label=ns.board_label,
            activator_label=ns.activator_label,
            activated_at_utc=parse_utc(ns.issued_at_utc),
        ),
        operator_queue_query_result=query,
        board_label=ns.board_label,
    ).to_payload()
    return _emit_payload(payload, ns.output)

def cmd_oracle_operator_action_outcome_ledger(ns: argparse.Namespace) -> int:
    queue_state = _build_queue_state(ns)
    query = run_operator_queue_query(operator_queue_snapshot=materialize_operator_queue_snapshot(governance_work_queue=queue_state))
    payload = materialize_operator_action_outcome_ledger(
        build_operator_action_outcome_ledger_request(ledger_root=Path(ns.ledger_root), emitted_at_utc=parse_utc(ns.issued_at_utc), board_label=ns.board_label, outcome_state=ns.outcome_state, actor_label=ns.actor_label, note=ns.note),
        operator_queue_query_result=query,
        board_label=ns.board_label,
    ).to_payload()
    return _emit_payload(payload, ns.output)

def cmd_oracle_operator_feedback_state(ns: argparse.Namespace) -> int:
    queue_state = _build_queue_state(ns)
    query = run_operator_queue_query(operator_queue_snapshot=materialize_operator_queue_snapshot(governance_work_queue=queue_state))
    ledger = materialize_operator_action_outcome_ledger(
        build_operator_action_outcome_ledger_request(ledger_root=Path(ns.state_root) / 'outcomes', emitted_at_utc=parse_utc(ns.issued_at_utc), board_label=ns.board_label, outcome_state=ns.outcome_state, actor_label=ns.actor_label, note=ns.note),
        operator_queue_query_result=query,
        board_label=ns.board_label,
    )
    payload = materialize_operator_feedback_state(
        build_operator_feedback_state_request(state_root=Path(ns.state_root), emitted_at_utc=parse_utc(ns.issued_at_utc), board_label=ns.board_label),
        operator_queue_query_result=query,
        action_outcome_ledger=ledger,
        board_label=ns.board_label,
    ).to_payload()
    return _emit_payload(payload, ns.output)

def cmd_oracle_operator_reentry_reassignment(ns: argparse.Namespace) -> int:
    queue_state = _build_queue_state(ns)
    accepted_at = parse_utc(ns.accepted_at_utc) if ns.accepted_at_utc else parse_utc(ns.issued_at_utc)
    evaluated_at = parse_utc(ns.evaluated_at_utc) if ns.evaluated_at_utc else parse_utc(ns.issued_at_utc)
    payload = materialize_operator_reentry_reassignment(
        build_operator_reentry_reassignment_request(
            reassignment_root=Path(ns.reassignment_root),
            board_label=ns.board_label,
            backup_assignee_label=ns.backup_assignee_label,
            supervisor_assignee_label=ns.supervisor_assignee_label,
            evaluated_at_utc=evaluated_at,
        ),
        reentry_acknowledgement_timeout=materialize_operator_reentry_acknowledgement_timeout(
            build_operator_reentry_acknowledgement_timeout_request(
                timeout_root=Path(ns.reassignment_root) / 'reentry_acknowledgement_timeout',
                board_label=ns.board_label,
                evaluated_at_utc=evaluated_at,
            ),
            reentry_acceptance=materialize_operator_reentry_acceptance(
                build_operator_reentry_acceptance_request(
                    acceptance_root=Path(ns.reassignment_root) / 'reentry_acceptance',
                    board_label=ns.board_label,
                    accepted_at_utc=accepted_at,
                ),
                reentry_assignment=materialize_operator_reentry_assignment(
                    build_operator_reentry_assignment_request(
                        assignment_root=Path(ns.reassignment_root) / 'reentry_assignment',
                        board_label=ns.board_label,
                        assigned_at_utc=accepted_at,
                    ),
                    reentry_queue_state=materialize_operator_reentry_queue_state(
                        build_operator_reentry_queue_state_request(
                            reentry_root=Path(ns.reassignment_root) / 'reentry_queue_state',
                            board_label=ns.board_label,
                            reopened_at_utc=accepted_at,
                        ),
                        operator_queue_query_result=run_operator_queue_query(operator_queue_snapshot=materialize_operator_queue_snapshot(governance_work_queue=queue_state)),
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

def cmd_oracle_operator_reentry_completion(ns: argparse.Namespace) -> int:
    queue_state = _build_queue_state(ns)
    accepted_at = parse_utc(ns.accepted_at_utc) if ns.accepted_at_utc else parse_utc(ns.issued_at_utc)
    evaluated_at = parse_utc(ns.evaluated_at_utc) if ns.evaluated_at_utc else parse_utc(ns.issued_at_utc)
    completed_at = parse_utc(ns.completed_at_utc) if ns.completed_at_utc else evaluated_at
    query = run_operator_queue_query(operator_queue_snapshot=materialize_operator_queue_snapshot(governance_work_queue=queue_state))
    reentry_acceptance = materialize_operator_reentry_acceptance(
        build_operator_reentry_acceptance_request(
            acceptance_root=Path(ns.completion_root) / 'reentry_acceptance',
            board_label=ns.board_label,
            accepted_at_utc=accepted_at,
        ),
        reentry_assignment=materialize_operator_reentry_assignment(
            build_operator_reentry_assignment_request(
                assignment_root=Path(ns.completion_root) / 'reentry_assignment',
                board_label=ns.board_label,
                assigned_at_utc=accepted_at,
            ),
            reentry_queue_state=materialize_operator_reentry_queue_state(
                build_operator_reentry_queue_state_request(
                    reentry_root=Path(ns.completion_root) / 'reentry_queue_state',
                    board_label=ns.board_label,
                    reopened_at_utc=accepted_at,
                ),
                operator_queue_query_result=query,
                board_label=ns.board_label,
            ),
            board_label=ns.board_label,
        ),
        board_label=ns.board_label,
    )
    reentry_reassignment = materialize_operator_reentry_reassignment(
        build_operator_reentry_reassignment_request(
            reassignment_root=Path(ns.completion_root) / 'reentry_reassignment',
            board_label=ns.board_label,
            evaluated_at_utc=evaluated_at,
        ),
        reentry_acknowledgement_timeout=materialize_operator_reentry_acknowledgement_timeout(
            build_operator_reentry_acknowledgement_timeout_request(
                timeout_root=Path(ns.completion_root) / 'reentry_acknowledgement_timeout',
                board_label=ns.board_label,
                evaluated_at_utc=evaluated_at,
            ),
            reentry_acceptance=reentry_acceptance,
            board_label=ns.board_label,
        ),
        board_label=ns.board_label,
    )
    payload = materialize_operator_reentry_completion(
        build_operator_reentry_completion_request(
            completion_root=Path(ns.completion_root),
            board_label=ns.board_label,
            completed_at_utc=completed_at,
        ),
        reentry_reassignment=reentry_reassignment,
        reentry_acceptance=reentry_acceptance,
        board_label=ns.board_label,
    ).to_payload()
    return _emit_payload(payload, ns.output)


__all__ = [
    'cmd_oracle_operator_reentry_queue_state',
    'cmd_oracle_operator_reentry_assignment',
    'cmd_oracle_operator_reentry_acceptance',
    'cmd_oracle_operator_reentry_acknowledgement_timeout',
    'cmd_oracle_operator_reentry_completion_attestation',
    'cmd_oracle_operator_reentry_post_review_gate',
    'cmd_oracle_operator_post_review_disposition',
    'cmd_oracle_operator_return_authorization_ledger',
    'cmd_oracle_operator_return_activation',
    'cmd_oracle_operator_action_outcome_ledger',
    'cmd_oracle_operator_feedback_state',
    'cmd_oracle_operator_reentry_reassignment',
    'cmd_oracle_operator_reentry_completion',
]
