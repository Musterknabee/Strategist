from __future__ import annotations

from datetime import datetime

from strategy_validator.control_plane.operator_control_plane_bundle_stage_reentry_surfaces import (
    build_operator_post_review_disposition_request,
    build_operator_reentry_acceptance_request,
    build_operator_reentry_acknowledgement_timeout_request,
    build_operator_reentry_assignment_request,
    build_operator_reentry_completion_attestation_request,
    build_operator_reentry_completion_request,
    build_operator_reentry_post_review_gate_request,
    build_operator_reentry_queue_state_request,
    build_operator_reentry_reassignment_request,
    build_operator_reopen_lineage_request,
    build_operator_reopen_recurrence_policy_request,
    build_operator_restoration_audit_request,
    build_operator_return_activation_request,
    build_operator_return_authorization_ledger_request,
    build_operator_return_drift_breach_request,
    build_operator_return_monitoring_request,
    build_operator_return_reopen_loop_request,
    materialize_operator_post_review_disposition,
    materialize_operator_reentry_acceptance,
    materialize_operator_reentry_acknowledgement_timeout,
    materialize_operator_reentry_assignment,
    materialize_operator_reentry_completion_attestation,
    materialize_operator_reentry_completion,
    materialize_operator_reentry_post_review_gate,
    materialize_operator_reentry_queue_state,
    materialize_operator_reentry_reassignment,
    materialize_operator_reopen_lineage,
    materialize_operator_reopen_recurrence_policy,
    materialize_operator_restoration_audit,
    materialize_operator_return_activation,
    materialize_operator_return_authorization_ledger,
    materialize_operator_return_drift_breach,
    materialize_operator_return_monitoring,
    materialize_operator_return_reopen_loop,
)

def materialize_operator_control_plane_bundle_reentry_stage(request, *, emitted_at_utc: datetime, operator_queue_query_result, action_contract, escalation_closure, reentry_queue_state_request=None, reentry_assignment_request=None, reentry_acceptance_request=None, reentry_acknowledgement_timeout_request=None, reentry_reassignment_request=None, reentry_completion_request=None, reentry_completion_attestation_request=None, reentry_post_review_gate_request=None, post_review_disposition_request=None, return_authorization_ledger_request=None, return_activation_request=None, return_monitoring_request=None, restoration_audit_request=None, return_drift_breach_request=None, return_reopen_loop_request=None, reopen_lineage_request=None, reopen_recurrence_policy_request=None):
    reentry_queue_state = materialize_operator_reentry_queue_state(
        reentry_queue_state_request or build_operator_reentry_queue_state_request(
            reentry_root=request.bundle_root / 'reentry_queue_state',
            board_label=request.board_label,
            reopened_at_utc=emitted_at_utc,
        ),
        escalation_closure=escalation_closure,
        action_contract=action_contract,
        board_label=request.board_label,
    )
    reentry_assignment = materialize_operator_reentry_assignment(
        reentry_assignment_request or build_operator_reentry_assignment_request(
            assignment_root=request.bundle_root / 'reentry_assignment',
            board_label=request.board_label,
            assigned_at_utc=emitted_at_utc,
        ),
        reentry_queue_state=reentry_queue_state,
        board_label=request.board_label,
    )
    reentry_acceptance = materialize_operator_reentry_acceptance(
        reentry_acceptance_request or build_operator_reentry_acceptance_request(
            acceptance_root=request.bundle_root / 'reentry_acceptance',
            board_label=request.board_label,
            accepted_at_utc=emitted_at_utc,
        ),
        reentry_assignment=reentry_assignment,
        board_label=request.board_label,
    )
    reentry_acknowledgement_timeout = materialize_operator_reentry_acknowledgement_timeout(
        reentry_acknowledgement_timeout_request or build_operator_reentry_acknowledgement_timeout_request(
            timeout_root=request.bundle_root / 'reentry_acknowledgement_timeout',
            board_label=request.board_label,
            evaluated_at_utc=emitted_at_utc,
        ),
        reentry_acceptance=reentry_acceptance,
        board_label=request.board_label,
    )
    reentry_reassignment = materialize_operator_reentry_reassignment(
        reentry_reassignment_request or build_operator_reentry_reassignment_request(
            reassignment_root=request.bundle_root / 'reentry_reassignment',
            board_label=request.board_label,
            evaluated_at_utc=emitted_at_utc,
        ),
        reentry_acknowledgement_timeout=reentry_acknowledgement_timeout,
        board_label=request.board_label,
    )
    reentry_completion = materialize_operator_reentry_completion(
        reentry_completion_request or build_operator_reentry_completion_request(
            completion_root=request.bundle_root / 'reentry_completion',
            board_label=request.board_label,
            completed_at_utc=emitted_at_utc,
        ),
        reentry_reassignment=reentry_reassignment,
        reentry_acceptance=reentry_acceptance,
        board_label=request.board_label,
    )
    reentry_completion_attestation = materialize_operator_reentry_completion_attestation(
        reentry_completion_attestation_request or build_operator_reentry_completion_attestation_request(
            attestation_root=request.bundle_root / 'reentry_completion_attestation',
            board_label=request.board_label,
            attested_at_utc=emitted_at_utc,
        ),
        reentry_completion=reentry_completion,
        board_label=request.board_label,
    )
    reentry_post_review_gate = materialize_operator_reentry_post_review_gate(
        reentry_post_review_gate_request or build_operator_reentry_post_review_gate_request(
            review_root=request.bundle_root / 'reentry_post_review_gate',
            board_label=request.board_label,
            reviewed_at_utc=emitted_at_utc,
        ),
        reentry_completion_attestation=reentry_completion_attestation,
        board_label=request.board_label,
    )
    post_review_disposition = materialize_operator_post_review_disposition(
        post_review_disposition_request or build_operator_post_review_disposition_request(
            disposition_root=request.bundle_root / 'post_review_disposition',
            board_label=request.board_label,
            reviewed_at_utc=emitted_at_utc,
        ),
        reentry_post_review_gate=reentry_post_review_gate,
        board_label=request.board_label,
    )
    return_authorization_ledger = materialize_operator_return_authorization_ledger(
        return_authorization_ledger_request or build_operator_return_authorization_ledger_request(
            ledger_root=request.bundle_root / 'return_authorization_ledger',
            board_label=request.board_label,
            authorized_at_utc=emitted_at_utc,
        ),
        post_review_disposition=post_review_disposition,
        board_label=request.board_label,
    )
    return_activation = materialize_operator_return_activation(
        return_activation_request or build_operator_return_activation_request(
            activation_root=request.bundle_root / 'return_activation',
            board_label=request.board_label,
            activated_at_utc=emitted_at_utc,
        ),
        return_authorization_ledger=return_authorization_ledger,
        board_label=request.board_label,
    )
    return_monitoring = materialize_operator_return_monitoring(
        return_monitoring_request or build_operator_return_monitoring_request(
            monitoring_root=request.bundle_root / 'return_monitoring',
            board_label=request.board_label,
            evaluated_at_utc=emitted_at_utc,
            monitoring_started_at_utc=emitted_at_utc,
        ),
        return_activation=return_activation,
        board_label=request.board_label,
    )
    restoration_audit = materialize_operator_restoration_audit(
        restoration_audit_request or build_operator_restoration_audit_request(
            audit_root=request.bundle_root / 'restoration_audit',
            board_label=request.board_label,
            audited_at_utc=emitted_at_utc,
        ),
        return_monitoring=return_monitoring,
        board_label=request.board_label,
    )
    return_drift_breach = materialize_operator_return_drift_breach(
        return_drift_breach_request or build_operator_return_drift_breach_request(
            breach_root=request.bundle_root / 'return_drift_breach',
            board_label=request.board_label,
            evaluated_at_utc=emitted_at_utc,
        ),
        restoration_audit=restoration_audit,
        board_label=request.board_label,
    )
    return_reopen_loop = materialize_operator_return_reopen_loop(
        return_reopen_loop_request or build_operator_return_reopen_loop_request(
            reopen_root=request.bundle_root / 'return_reopen_loop',
            board_label=request.board_label,
            reopened_at_utc=emitted_at_utc,
        ),
        return_drift_breach=return_drift_breach,
        board_label=request.board_label,
    )
    reopen_lineage = materialize_operator_reopen_lineage(
        reopen_lineage_request or build_operator_reopen_lineage_request(
            lineage_root=request.bundle_root / 'reopen_lineage',
            board_label=request.board_label,
            analyzed_at_utc=emitted_at_utc,
        ),
        return_reopen_loop=return_reopen_loop,
        operator_queue_query_result=operator_queue_query_result,
        board_label=request.board_label,
    )
    reopen_recurrence_policy = materialize_operator_reopen_recurrence_policy(
        reopen_recurrence_policy_request or build_operator_reopen_recurrence_policy_request(
            policy_root=request.bundle_root / 'reopen_recurrence_policy',
            board_label=request.board_label,
            evaluated_at_utc=emitted_at_utc,
        ),
        reopen_lineage=reopen_lineage,
        board_label=request.board_label,
    )
    return {
        'reentry_queue_state': reentry_queue_state,
        'reentry_assignment': reentry_assignment,
        'reentry_acceptance': reentry_acceptance,
        'reentry_acknowledgement_timeout': reentry_acknowledgement_timeout,
        'reentry_reassignment': reentry_reassignment,
        'reentry_completion': reentry_completion,
        'reentry_completion_attestation': reentry_completion_attestation,
        'reentry_post_review_gate': reentry_post_review_gate,
        'post_review_disposition': post_review_disposition,
        'return_authorization_ledger': return_authorization_ledger,
        'return_activation': return_activation,
        'return_monitoring': return_monitoring,
        'restoration_audit': restoration_audit,
        'return_drift_breach': return_drift_breach,
        'return_reopen_loop': return_reopen_loop,
        'reopen_lineage': reopen_lineage,
        'reopen_recurrence_policy': reopen_recurrence_policy,
    }


__all__ = ['materialize_operator_control_plane_bundle_reentry_stage']
