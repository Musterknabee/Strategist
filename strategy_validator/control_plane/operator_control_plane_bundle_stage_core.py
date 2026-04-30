from __future__ import annotations

from datetime import datetime

from strategy_validator.control_plane.operator_control_plane_bundle_stage_core_surfaces import (
    build_operator_action_outcome_ledger_request,
    build_operator_decision_execution_request,
    build_operator_decision_journal_request,
    build_operator_escalation_closure_request,
    build_operator_escalation_packet_request,
    build_operator_escalation_routing_request,
    build_operator_escalation_sla_request,
    build_operator_feedback_state_request,
    build_operator_supervisor_review_request,
    build_operator_transition_policy_request,
    materialize_operator_action_outcome_ledger,
    materialize_operator_decision_execution,
    materialize_operator_decision_journal,
    materialize_operator_escalation_closure,
    materialize_operator_escalation_packet,
    materialize_operator_escalation_routing,
    materialize_operator_escalation_sla,
    materialize_operator_feedback_state,
    materialize_operator_supervisor_review,
    materialize_operator_transition_policy,
    materialize_operator_workboard,
    materialize_operator_workboard_action_contract,
)

def materialize_operator_control_plane_bundle_core_stage(request, *, emitted_at_utc: datetime, operator_queue_query_result, decision_journal_request=None, decision_execution_request=None, escalation_routing_request=None, escalation_packet_request=None, escalation_sla_request=None, supervisor_review_request=None, escalation_closure_request=None, action_outcome_ledger_request=None, feedback_state_request=None):
    workboard = materialize_operator_workboard(operator_queue_query_result=operator_queue_query_result, board_label=request.board_label)
    action_contract = materialize_operator_workboard_action_contract(
        operator_queue_query_result=operator_queue_query_result,
        board_label=request.board_label,
    )
    transition_policy = materialize_operator_transition_policy(
        build_operator_transition_policy_request(board_label=request.board_label),
        action_contract=action_contract,
    )
    decision_journal = materialize_operator_decision_journal(
        decision_journal_request or build_operator_decision_journal_request(
            journal_root=request.bundle_root / 'decision_journal',
            board_label=request.board_label,
            emitted_at_utc=emitted_at_utc,
        ),
        action_contract=action_contract,
    )
    decision_execution = materialize_operator_decision_execution(
        decision_execution_request or build_operator_decision_execution_request(
            execution_root=request.bundle_root / 'decision_execution',
            board_label=request.board_label,
            actor_label='operator',
            emitted_at_utc=emitted_at_utc,
        ),
        transition_policy=transition_policy,
        action_contract=action_contract,
    )
    escalation_routing = materialize_operator_escalation_routing(
        escalation_routing_request or build_operator_escalation_routing_request(
            routing_root=request.bundle_root / 'escalation_routing',
            board_label=request.board_label,
        ),
        decision_execution=decision_execution,
        action_contract=action_contract,
    )
    escalation_packet = materialize_operator_escalation_packet(
        escalation_packet_request or build_operator_escalation_packet_request(
            packet_root=request.bundle_root / 'escalation_packet',
            board_label=request.board_label,
        ),
        escalation_routing=escalation_routing,
        decision_execution=decision_execution,
        action_contract=action_contract,
    )
    escalation_sla = materialize_operator_escalation_sla(
        escalation_sla_request or build_operator_escalation_sla_request(
            sla_root=request.bundle_root / 'escalation_sla',
            board_label=request.board_label,
            evaluated_at_utc=emitted_at_utc,
            escalation_started_at_utc=emitted_at_utc,
        ),
        escalation_packet=escalation_packet,
        board_label=request.board_label,
    )
    supervisor_review = materialize_operator_supervisor_review(
        supervisor_review_request or build_operator_supervisor_review_request(
            review_root=request.bundle_root / 'supervisor_review',
            board_label=request.board_label,
            reviewed_at_utc=emitted_at_utc,
        ),
        escalation_packet=escalation_packet,
        escalation_sla=escalation_sla,
        board_label=request.board_label,
    )
    escalation_closure = materialize_operator_escalation_closure(
        escalation_closure_request or build_operator_escalation_closure_request(
            closure_root=request.bundle_root / 'escalation_closure',
            board_label=request.board_label,
            closed_at_utc=emitted_at_utc,
        ),
        supervisor_review=supervisor_review,
        board_label=request.board_label,
    )
    action_outcome_ledger = materialize_operator_action_outcome_ledger(
        action_outcome_ledger_request or build_operator_action_outcome_ledger_request(
            ledger_root=request.bundle_root / 'action_outcomes',
            board_label=request.board_label,
            emitted_at_utc=emitted_at_utc,
        ),
        action_contract=action_contract,
        decision_execution=decision_execution,
    )
    feedback_state = materialize_operator_feedback_state(
        feedback_state_request or build_operator_feedback_state_request(
            state_root=request.bundle_root / 'feedback_state',
            board_label=request.board_label,
            emitted_at_utc=emitted_at_utc,
        ),
        action_contract=action_contract,
        action_outcome_ledger=action_outcome_ledger,
    )
    return {
        'workboard': workboard,
        'action_contract': action_contract,
        'transition_policy': transition_policy,
        'decision_journal': decision_journal,
        'decision_execution': decision_execution,
        'escalation_routing': escalation_routing,
        'escalation_packet': escalation_packet,
        'escalation_sla': escalation_sla,
        'supervisor_review': supervisor_review,
        'escalation_closure': escalation_closure,
        'action_outcome_ledger': action_outcome_ledger,
        'feedback_state': feedback_state,
    }


__all__ = ['materialize_operator_control_plane_bundle_core_stage']
