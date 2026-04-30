from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from strategy_validator.contracts.operator_control_plane_bundle import (
    OracleOperatorControlPlaneBundle,
    OracleOperatorControlPlaneBundleRequest,
)
from strategy_validator.control_plane.operator_control_plane_bundle_stage_core import (
    materialize_operator_control_plane_bundle_core_stage,
)
from strategy_validator.control_plane.operator_control_plane_bundle_stage_recurrence import (
    materialize_operator_control_plane_bundle_recurrence_stage,
)
from strategy_validator.control_plane.operator_control_plane_bundle_stage_reentry import (
    materialize_operator_control_plane_bundle_reentry_stage,
)
from strategy_validator.control_plane.operator_queue_query import (
    OracleOperatorQueueQueryRequest,
    OracleOperatorQueueQueryResult,
    run_operator_queue_query,
)


def materialize_operator_control_plane_bundle_sections(
    request: OracleOperatorControlPlaneBundleRequest,
    *,
    operator_queue_query_result: OracleOperatorQueueQueryResult | None = None,
    operator_queue_query_request: OracleOperatorQueueQueryRequest | None = None,
    **kwargs: Any,
) -> OracleOperatorControlPlaneBundle:
    emitted_at_utc = request.emitted_at_utc or datetime.now(tz=UTC).replace(microsecond=0)
    if emitted_at_utc.tzinfo is None:
        emitted_at_utc = emitted_at_utc.replace(tzinfo=UTC)
    if operator_queue_query_result is None:
        operator_queue_query_result = run_operator_queue_query(request=operator_queue_query_request, **kwargs)

    request.bundle_root.mkdir(parents=True, exist_ok=True)

    core = materialize_operator_control_plane_bundle_core_stage(
        request,
        emitted_at_utc=emitted_at_utc,
        operator_queue_query_result=operator_queue_query_result,
        decision_journal_request=kwargs.get('decision_journal_request'),
        decision_execution_request=kwargs.get('decision_execution_request'),
        escalation_routing_request=kwargs.get('escalation_routing_request'),
        escalation_packet_request=kwargs.get('escalation_packet_request'),
        escalation_sla_request=kwargs.get('escalation_sla_request'),
        supervisor_review_request=kwargs.get('supervisor_review_request'),
        escalation_closure_request=kwargs.get('escalation_closure_request'),
        action_outcome_ledger_request=kwargs.get('action_outcome_ledger_request'),
        feedback_state_request=kwargs.get('feedback_state_request'),
    )
    reentry = materialize_operator_control_plane_bundle_reentry_stage(
        request,
        emitted_at_utc=emitted_at_utc,
        operator_queue_query_result=operator_queue_query_result,
        action_contract=core['action_contract'],
        escalation_closure=core['escalation_closure'],
        reentry_queue_state_request=kwargs.get('reentry_queue_state_request'),
        reentry_assignment_request=kwargs.get('reentry_assignment_request'),
        reentry_acceptance_request=kwargs.get('reentry_acceptance_request'),
        reentry_acknowledgement_timeout_request=kwargs.get('reentry_acknowledgement_timeout_request'),
        reentry_reassignment_request=kwargs.get('reentry_reassignment_request'),
        reentry_completion_request=kwargs.get('reentry_completion_request'),
        reentry_completion_attestation_request=kwargs.get('reentry_completion_attestation_request'),
        reentry_post_review_gate_request=kwargs.get('reentry_post_review_gate_request'),
        post_review_disposition_request=kwargs.get('post_review_disposition_request'),
        return_authorization_ledger_request=kwargs.get('return_authorization_ledger_request'),
        return_activation_request=kwargs.get('return_activation_request'),
        return_monitoring_request=kwargs.get('return_monitoring_request'),
        restoration_audit_request=kwargs.get('restoration_audit_request'),
        return_drift_breach_request=kwargs.get('return_drift_breach_request'),
        return_reopen_loop_request=kwargs.get('return_reopen_loop_request'),
        reopen_lineage_request=kwargs.get('reopen_lineage_request'),
        reopen_recurrence_policy_request=kwargs.get('reopen_recurrence_policy_request'),
    )
    recurrence = materialize_operator_control_plane_bundle_recurrence_stage(
        request,
        emitted_at_utc=emitted_at_utc,
        reopen_recurrence_policy=reentry['reopen_recurrence_policy'],
        restoration_audit=reentry['restoration_audit'],
        chronic_instability_packet_request=kwargs.get('chronic_instability_packet_request'),
        recurrence_tribunal_lane_request=kwargs.get('recurrence_tribunal_lane_request'),
        recurrence_tribunal_disposition_request=kwargs.get('recurrence_tribunal_disposition_request'),
        chronic_remediation_mandate_ledger_request=kwargs.get('chronic_remediation_mandate_ledger_request'),
        chronic_remediation_satisfaction_request=kwargs.get('chronic_remediation_satisfaction_request'),
        freeze_release_gate_request=kwargs.get('freeze_release_gate_request'),
        freeze_release_attestation_request=kwargs.get('freeze_release_attestation_request'),
        chronic_exit_certification_request=kwargs.get('chronic_exit_certification_request'),
        chronic_exit_return_bridge_request=kwargs.get('chronic_exit_return_bridge_request'),
        monitored_rejoin_policy_request=kwargs.get('monitored_rejoin_policy_request'),
        monitored_rejoin_activation_request=kwargs.get('monitored_rejoin_activation_request'),
        chronic_watch_handoff_request=kwargs.get('chronic_watch_handoff_request'),
        chronic_watch_outcome_request=kwargs.get('chronic_watch_outcome_request'),
        monitored_rejoin_normalization_bridge_request=kwargs.get('monitored_rejoin_normalization_bridge_request'),
        normalization_bridge_activation_request=kwargs.get('normalization_bridge_activation_request'),
        chronic_watch_audit_convergence_request=kwargs.get('chronic_watch_audit_convergence_request'),
        converged_normalization_attestation_request=kwargs.get('converged_normalization_attestation_request'),
        chronic_origin_restoration_provenance_request=kwargs.get('chronic_origin_restoration_provenance_request'),
        chronic_origin_restoration_audit_overlay_request=kwargs.get('chronic_origin_restoration_audit_overlay_request'),
        provenance_aware_drift_policy_request=kwargs.get('provenance_aware_drift_policy_request'),
    )

    parts = {**core, **reentry, **recurrence}
    bundle = OracleOperatorControlPlaneBundle(
        schema_version='oracle_operator_control_plane_bundle/v1',
        bundle_root=str(request.bundle_root),
        board_label=request.board_label,
        queue_key=operator_queue_query_result.queue_key,
        review_target=operator_queue_query_result.review_target,
        priority_band=operator_queue_query_result.priority_band,
        emitted_at_utc=emitted_at_utc.isoformat(),
        bundle_sections=(
            'queue_query', 'workboard', 'action_contract', 'transition_policy', 'decision_journal', 'decision_execution',
            'escalation_routing', 'escalation_packet', 'escalation_sla', 'supervisor_review', 'escalation_closure',
            'reentry_queue_state', 'reentry_assignment', 'reentry_acceptance', 'reentry_acknowledgement_timeout',
            'reentry_reassignment', 'reentry_completion', 'reentry_completion_attestation', 'reentry_post_review_gate',
            'post_review_disposition', 'return_authorization_ledger', 'return_activation', 'return_monitoring',
            'restoration_audit', 'return_drift_breach', 'return_reopen_loop', 'reopen_lineage', 'reopen_recurrence_policy',
            'chronic_instability_packet', 'recurrence_tribunal_lane', 'recurrence_tribunal_disposition',
            'chronic_remediation_mandate_ledger', 'chronic_remediation_satisfaction', 'freeze_release_gate',
            'freeze_release_attestation', 'chronic_exit_certification', 'chronic_exit_return_bridge',
            'monitored_rejoin_policy', 'monitored_rejoin_activation', 'chronic_watch_handoff', 'chronic_watch_outcome',
            'monitored_rejoin_normalization_bridge', 'normalization_bridge_activation', 'chronic_watch_audit_convergence',
            'converged_normalization_attestation', 'chronic_origin_restoration_provenance',
            'chronic_origin_restoration_audit_overlay', 'provenance_aware_drift_policy', 'action_outcome_ledger', 'feedback_state',
        ),
        summary_output_path=str(request.bundle_root / 'ORACLE_OPERATOR_CONTROL_PLANE_BUNDLE.json'),
        markdown_output_path=str(request.bundle_root / 'ORACLE_OPERATOR_CONTROL_PLANE_BUNDLE.md'),
        queue_query=operator_queue_query_result.to_payload(),
        **{key: value.to_payload() for key, value in parts.items()},
    )
    return bundle


__all__ = ['materialize_operator_control_plane_bundle_sections']
