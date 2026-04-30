from __future__ import annotations

from strategy_validator.cli.oracle_queue_runner_common import *
from strategy_validator.cli.oracle_queue_runner_common import _build_queue_kwargs, _build_queue_state, _emit_payload

def cmd_oracle_operator_decision_execution(ns: argparse.Namespace) -> int:
    queue_state = _build_queue_state(ns)
    query = run_operator_queue_query(operator_queue_snapshot=materialize_operator_queue_snapshot(governance_work_queue=queue_state))
    payload = materialize_operator_decision_execution(
        build_operator_decision_execution_request(execution_root=Path(ns.execution_root), emitted_at_utc=parse_utc(ns.issued_at_utc), board_label=ns.board_label, desired_transition=ns.desired_transition, actor_label=ns.actor_label, note=ns.note),
        operator_queue_query_result=query,
        board_label=ns.board_label,
    ).to_payload()
    return _emit_payload(payload, ns.output)

def cmd_oracle_operator_escalation_routing(ns: argparse.Namespace) -> int:
    queue_state = _build_queue_state(ns)
    query = run_operator_queue_query(operator_queue_snapshot=materialize_operator_queue_snapshot(governance_work_queue=queue_state))
    decision_execution = materialize_operator_decision_execution(
        build_operator_decision_execution_request(execution_root=Path(ns.routing_root) / 'decision_execution', emitted_at_utc=parse_utc(ns.issued_at_utc), board_label=ns.board_label, desired_transition=ns.desired_transition, actor_label=ns.actor_label, note=ns.note),
        operator_queue_query_result=query,
        board_label=ns.board_label,
    )
    payload = materialize_operator_escalation_routing(
        build_operator_escalation_routing_request(routing_root=Path(ns.routing_root), board_label=ns.board_label),
        decision_execution=decision_execution,
        operator_queue_query_result=query,
        board_label=ns.board_label,
    ).to_payload()
    return _emit_payload(payload, ns.output)

def cmd_oracle_operator_escalation_packet(ns: argparse.Namespace) -> int:
    queue_state = _build_queue_state(ns)
    query = run_operator_queue_query(operator_queue_snapshot=materialize_operator_queue_snapshot(governance_work_queue=queue_state))
    decision_execution = materialize_operator_decision_execution(
        build_operator_decision_execution_request(execution_root=Path(ns.packet_root) / 'decision_execution', emitted_at_utc=parse_utc(ns.issued_at_utc), board_label=ns.board_label, desired_transition=ns.desired_transition, actor_label=ns.actor_label, note=ns.note),
        operator_queue_query_result=query,
        board_label=ns.board_label,
    )
    escalation_routing = materialize_operator_escalation_routing(
        build_operator_escalation_routing_request(routing_root=Path(ns.packet_root) / 'routing', board_label=ns.board_label),
        decision_execution=decision_execution,
        operator_queue_query_result=query,
        board_label=ns.board_label,
    )
    payload = materialize_operator_escalation_packet(
        build_operator_escalation_packet_request(packet_root=Path(ns.packet_root), board_label=ns.board_label),
        escalation_routing=escalation_routing,
        decision_execution=decision_execution,
        operator_queue_query_result=query,
        board_label=ns.board_label,
    ).to_payload()
    return _emit_payload(payload, ns.output)

def cmd_oracle_operator_escalation_sla(ns: argparse.Namespace) -> int:
    queue_state = _build_queue_state(ns)
    query = run_operator_queue_query(operator_queue_snapshot=materialize_operator_queue_snapshot(governance_work_queue=queue_state))
    decision_execution = materialize_operator_decision_execution(
        build_operator_decision_execution_request(execution_root=Path(ns.sla_root) / 'decision_execution', emitted_at_utc=parse_utc(ns.issued_at_utc), board_label=ns.board_label, desired_transition=ns.desired_transition, actor_label=ns.actor_label, note=ns.note),
        operator_queue_query_result=query,
        board_label=ns.board_label,
    )
    escalation_routing = materialize_operator_escalation_routing(
        build_operator_escalation_routing_request(routing_root=Path(ns.sla_root) / 'routing', board_label=ns.board_label),
        decision_execution=decision_execution,
        operator_queue_query_result=query,
        board_label=ns.board_label,
    )
    escalation_packet = materialize_operator_escalation_packet(
        build_operator_escalation_packet_request(packet_root=Path(ns.sla_root) / 'packet', board_label=ns.board_label),
        escalation_routing=escalation_routing,
        decision_execution=decision_execution,
        operator_queue_query_result=query,
        board_label=ns.board_label,
    )
    payload = materialize_operator_escalation_sla(
        build_operator_escalation_sla_request(sla_root=Path(ns.sla_root), board_label=ns.board_label, evaluated_at_utc=parse_utc(ns.issued_at_utc), escalation_started_at_utc=parse_utc(ns.escalation_started_at_utc) if ns.escalation_started_at_utc else parse_utc(ns.issued_at_utc)),
        escalation_packet=escalation_packet,
        board_label=ns.board_label,
    ).to_payload()
    return _emit_payload(payload, ns.output)

def cmd_oracle_operator_decision_journal(ns: argparse.Namespace) -> int:
    queue_state = _build_queue_state(ns)
    query = run_operator_queue_query(operator_queue_snapshot=materialize_operator_queue_snapshot(governance_work_queue=queue_state))
    payload = materialize_operator_decision_journal(
        build_operator_decision_journal_request(journal_root=Path(ns.journal_root), emitted_at_utc=parse_utc(ns.issued_at_utc), board_label=ns.board_label),
        operator_queue_query_result=query,
        board_label=ns.board_label,
    ).to_payload()
    return _emit_payload(payload, ns.output)

def cmd_oracle_operator_supervisor_review(ns: argparse.Namespace) -> int:
    queue_state = _build_queue_state(ns)
    query = run_operator_queue_query(operator_queue_snapshot=materialize_operator_queue_snapshot(governance_work_queue=queue_state))
    payload = materialize_operator_supervisor_review(
        build_operator_supervisor_review_request(
            review_root=Path(ns.review_root),
            board_label=ns.board_label,
            supervisor_actor_label=ns.supervisor_actor_label,
            note=ns.note,
            reviewed_at_utc=parse_utc(ns.issued_at_utc),
        ),
        operator_queue_query_result=query,
        board_label=ns.board_label,
    ).to_payload()
    return _emit_payload(payload, ns.output)

def cmd_oracle_operator_escalation_closure(ns: argparse.Namespace) -> int:
    queue_state = _build_queue_state(ns)
    query = run_operator_queue_query(operator_queue_snapshot=materialize_operator_queue_snapshot(governance_work_queue=queue_state))
    payload = materialize_operator_escalation_closure(
        build_operator_escalation_closure_request(
            closure_root=Path(ns.closure_root),
            board_label=ns.board_label,
            closed_at_utc=parse_utc(ns.issued_at_utc),
        ),
        operator_queue_query_result=query,
        board_label=ns.board_label,
    ).to_payload()
    return _emit_payload(payload, ns.output)


__all__ = [
    'cmd_oracle_operator_decision_execution',
    'cmd_oracle_operator_escalation_routing',
    'cmd_oracle_operator_escalation_packet',
    'cmd_oracle_operator_escalation_sla',
    'cmd_oracle_operator_decision_journal',
    'cmd_oracle_operator_supervisor_review',
    'cmd_oracle_operator_escalation_closure',
]
