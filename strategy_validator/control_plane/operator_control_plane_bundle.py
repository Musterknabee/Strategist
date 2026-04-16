from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from strategy_validator.control_plane.operator_control_plane_bundle_contracts import (
    OracleOperatorControlPlaneBundle,
    OracleOperatorControlPlaneBundleRequest,
)
from strategy_validator.control_plane.operator_action_outcome_ledger import (
    OracleOperatorActionOutcomeLedgerRequest,
    build_operator_action_outcome_ledger_request,
    materialize_operator_action_outcome_ledger,
)
from strategy_validator.control_plane.operator_decision_execution import (
    OracleOperatorDecisionExecutionRequest,
    build_operator_decision_execution_request,
    materialize_operator_decision_execution,
)
from strategy_validator.control_plane.operator_decision_journal import (
    OracleOperatorDecisionJournalRequest,
    build_operator_decision_journal_request,
    materialize_operator_decision_journal,
)
from strategy_validator.control_plane.operator_escalation_routing import (
    OracleOperatorEscalationRoutingRequest,
    build_operator_escalation_routing_request,
    materialize_operator_escalation_routing,
)
from strategy_validator.control_plane.operator_escalation_packet import (
    OracleOperatorEscalationPacketRequest,
    build_operator_escalation_packet_request,
    materialize_operator_escalation_packet,
)
from strategy_validator.control_plane.operator_escalation_sla import (
    OracleOperatorEscalationSLARequest,
    build_operator_escalation_sla_request,
    materialize_operator_escalation_sla,
)
from strategy_validator.control_plane.operator_supervisor_review import (
    OracleOperatorSupervisorReviewRequest,
    build_operator_supervisor_review_request,
    materialize_operator_supervisor_review,
)
from strategy_validator.control_plane.operator_escalation_closure import (
    OracleOperatorEscalationClosureRequest,
    build_operator_escalation_closure_request,
    materialize_operator_escalation_closure,
)
from strategy_validator.control_plane.operator_feedback_state import (
    OracleOperatorFeedbackStateRequest,
    build_operator_feedback_state_request,
    materialize_operator_feedback_state,
)
from strategy_validator.control_plane.operator_reentry_queue_state import (
    OracleOperatorReentryQueueStateRequest,
    build_operator_reentry_queue_state_request,
    materialize_operator_reentry_queue_state,
)
from strategy_validator.control_plane.operator_reentry_assignment import (
    OracleOperatorReentryAssignmentRequest,
    build_operator_reentry_assignment_request,
    materialize_operator_reentry_assignment,
)
from strategy_validator.control_plane.operator_reentry_acceptance import (
    OracleOperatorReentryAcceptanceRequest,
    build_operator_reentry_acceptance_request,
    materialize_operator_reentry_acceptance,
)
from strategy_validator.control_plane.operator_reentry_acknowledgement_timeout import (
    OracleOperatorReentryAcknowledgementTimeoutRequest,
    build_operator_reentry_acknowledgement_timeout_request,
    materialize_operator_reentry_acknowledgement_timeout,
)
from strategy_validator.control_plane.operator_reentry_reassignment import (
    OracleOperatorReentryReassignmentRequest,
    build_operator_reentry_reassignment_request,
    materialize_operator_reentry_reassignment,
)
from strategy_validator.control_plane.operator_reentry_completion import (
    OracleOperatorReentryCompletionRequest,
    build_operator_reentry_completion_request,
    materialize_operator_reentry_completion,
)
from strategy_validator.control_plane.operator_reentry_completion_attestation import (
    OracleOperatorReentryCompletionAttestationRequest,
    build_operator_reentry_completion_attestation_request,
    materialize_operator_reentry_completion_attestation,
)
from strategy_validator.control_plane.operator_reentry_post_review_gate import (
    OracleOperatorReentryPostReviewGateRequest,
    build_operator_reentry_post_review_gate_request,
    materialize_operator_reentry_post_review_gate,
)
from strategy_validator.control_plane.operator_return_authorization_ledger import (
    OracleOperatorReturnAuthorizationLedgerRequest,
    build_operator_return_authorization_ledger_request,
    materialize_operator_return_authorization_ledger,
)
from strategy_validator.control_plane.operator_return_activation import (
    OracleOperatorReturnActivationRequest,
    build_operator_return_activation_request,
    materialize_operator_return_activation,
)
from strategy_validator.control_plane.operator_return_monitoring import (
    OracleOperatorReturnMonitoringRequest,
    build_operator_return_monitoring_request,
    materialize_operator_return_monitoring,
)
from strategy_validator.control_plane.operator_restoration_audit import (
    OracleOperatorRestorationAuditRequest,
    build_operator_restoration_audit_request,
    materialize_operator_restoration_audit,
)
from strategy_validator.control_plane.operator_return_drift_breach import (
    OracleOperatorReturnDriftBreachRequest,
    build_operator_return_drift_breach_request,
    materialize_operator_return_drift_breach,
)
from strategy_validator.control_plane.operator_return_reopen_loop import (
    OracleOperatorReturnReopenLoopRequest,
    build_operator_return_reopen_loop_request,
    materialize_operator_return_reopen_loop,
)
from strategy_validator.control_plane.operator_reopen_lineage import (
    OracleOperatorReopenLineageRequest,
    build_operator_reopen_lineage_request,
    materialize_operator_reopen_lineage,
)
from strategy_validator.control_plane.operator_reopen_recurrence_policy import (
    OracleOperatorReopenRecurrencePolicyRequest,
    build_operator_reopen_recurrence_policy_request,
    materialize_operator_reopen_recurrence_policy,
)
from strategy_validator.control_plane.operator_chronic_instability_packet import (
    OracleOperatorChronicInstabilityPacketRequest,
    build_operator_chronic_instability_packet_request,
    materialize_operator_chronic_instability_packet,
)
from strategy_validator.control_plane.operator_recurrence_tribunal_lane import (
    OracleOperatorRecurrenceTribunalLaneRequest,
    build_operator_recurrence_tribunal_lane_request,
    materialize_operator_recurrence_tribunal_lane,
)

from strategy_validator.control_plane.operator_recurrence_tribunal_disposition import (
    OracleOperatorRecurrenceTribunalDispositionRequest,
    build_operator_recurrence_tribunal_disposition_request,
    materialize_operator_recurrence_tribunal_disposition,
)
from strategy_validator.control_plane.operator_chronic_remediation_mandate_ledger import (
    OracleOperatorChronicRemediationMandateLedgerRequest,
    build_operator_chronic_remediation_mandate_ledger_request,
    materialize_operator_chronic_remediation_mandate_ledger,
)

from strategy_validator.control_plane.operator_chronic_remediation_satisfaction import (
    OracleOperatorChronicRemediationSatisfactionRequest,
    build_operator_chronic_remediation_satisfaction_request,
    materialize_operator_chronic_remediation_satisfaction,
)
from strategy_validator.control_plane.operator_freeze_release_gate import (
    OracleOperatorFreezeReleaseGateRequest,
    build_operator_freeze_release_gate_request,
    materialize_operator_freeze_release_gate,
)
from strategy_validator.control_plane.operator_freeze_release_attestation import (
    OracleOperatorFreezeReleaseAttestationRequest,
    build_operator_freeze_release_attestation_request,
    materialize_operator_freeze_release_attestation,
)
from strategy_validator.control_plane.operator_chronic_exit_certification import (
    OracleOperatorChronicExitCertificationRequest,
    build_operator_chronic_exit_certification_request,
    materialize_operator_chronic_exit_certification,
)
from strategy_validator.control_plane.operator_chronic_exit_return_bridge import (
    OracleOperatorChronicExitReturnBridgeRequest,
    build_operator_chronic_exit_return_bridge_request,
    materialize_operator_chronic_exit_return_bridge,
)
from strategy_validator.control_plane.operator_monitored_rejoin_policy import (
    OracleOperatorMonitoredRejoinPolicyRequest,
    build_operator_monitored_rejoin_policy_request,
    materialize_operator_monitored_rejoin_policy,
)

from strategy_validator.control_plane.operator_monitored_rejoin_activation import (
    OracleOperatorMonitoredRejoinActivationRequest,
    build_operator_monitored_rejoin_activation_request,
    materialize_operator_monitored_rejoin_activation,
)
from strategy_validator.control_plane.operator_chronic_watch_handoff import (
    OracleOperatorChronicWatchHandoffRequest,
    build_operator_chronic_watch_handoff_request,
    materialize_operator_chronic_watch_handoff,
)

from strategy_validator.control_plane.operator_chronic_watch_outcome import (
    OracleOperatorChronicWatchOutcomeRequest,
    build_operator_chronic_watch_outcome_request,
    materialize_operator_chronic_watch_outcome,
)
from strategy_validator.control_plane.operator_monitored_rejoin_normalization_bridge import (
    OracleOperatorMonitoredRejoinNormalizationBridgeRequest,
    build_operator_monitored_rejoin_normalization_bridge_request,
    materialize_operator_monitored_rejoin_normalization_bridge,
)
from strategy_validator.control_plane.operator_normalization_bridge_activation import (
    OracleOperatorNormalizationBridgeActivationRequest,
    build_operator_normalization_bridge_activation_request,
    materialize_operator_normalization_bridge_activation,
)
from strategy_validator.control_plane.operator_chronic_watch_audit_convergence import (
    OracleOperatorChronicWatchAuditConvergenceRequest,
    build_operator_chronic_watch_audit_convergence_request,
    materialize_operator_chronic_watch_audit_convergence,
)
from strategy_validator.control_plane.operator_converged_normalization_attestation import (
    OracleOperatorConvergedNormalizationAttestationRequest,
    build_operator_converged_normalization_attestation_request,
    materialize_operator_converged_normalization_attestation,
)
from strategy_validator.control_plane.operator_chronic_origin_restoration_provenance import (
    OracleOperatorChronicOriginRestorationProvenanceRequest,
    build_operator_chronic_origin_restoration_provenance_request,
    materialize_operator_chronic_origin_restoration_provenance,
)
from strategy_validator.control_plane.operator_chronic_origin_restoration_audit_overlay import (
    OracleOperatorChronicOriginRestorationAuditOverlayRequest,
    build_operator_chronic_origin_restoration_audit_overlay_request,
    materialize_operator_chronic_origin_restoration_audit_overlay,
)
from strategy_validator.control_plane.operator_provenance_aware_drift_policy import (
    OracleOperatorProvenanceAwareDriftPolicyRequest,
    build_operator_provenance_aware_drift_policy_request,
    materialize_operator_provenance_aware_drift_policy,
)
from strategy_validator.control_plane.operator_post_review_disposition import (
    OracleOperatorPostReviewDispositionRequest,
    build_operator_post_review_disposition_request,
    materialize_operator_post_review_disposition,
)
from strategy_validator.control_plane.operator_queue_query import (
    OracleOperatorQueueQueryRequest,
    OracleOperatorQueueQueryResult,
    run_operator_queue_query,
)
from strategy_validator.control_plane.operator_transition_policy import (
    build_operator_transition_policy_request,
    materialize_operator_transition_policy,
)
from strategy_validator.control_plane.operator_workboard import materialize_operator_workboard
from strategy_validator.control_plane.operator_workboard_actions import materialize_operator_workboard_action_contract

def build_operator_control_plane_bundle_request(**kwargs: Any) -> OracleOperatorControlPlaneBundleRequest:
    kwargs['bundle_root'] = Path(kwargs['bundle_root']).resolve()
    return OracleOperatorControlPlaneBundleRequest(**kwargs)


def render_operator_control_plane_bundle_markdown_lines(bundle: OracleOperatorControlPlaneBundle) -> list[str]:
    return [
        '## Operator Control Plane Bundle',
        f"- Board label: `{bundle.board_label}`",
        f"- Queue key: `{bundle.queue_key}`",
        f"- Review target: `{bundle.review_target}`",
        f"- Priority band: `{bundle.priority_band}`",
        f"- Sections: {', '.join(bundle.bundle_sections)}",
        f"- Work items: `{bundle.queue_query['work_item_count']}`",
        f"- Action contracts: `{bundle.action_contract['contract_count']}`",
        f"- Transition policies: `{bundle.transition_policy['policy_count']}`",
        f"- Journal events: `{bundle.decision_journal['event_count']}`",
        f"- Decision executions: `{bundle.decision_execution['execution_count']}`",
        f"- Escalation routes: `{bundle.escalation_routing['escalation_route_count']}`",
        f"- Escalation packets: `{bundle.escalation_packet['escalated_packet_count']}`",
        f"- Escalation SLA urgent items: `{bundle.escalation_sla['urgent_item_count']}`",
        f"- Supervisor reviews: `{bundle.supervisor_review['total_review_count']}`",
        f"- Escalation closures: `{bundle.escalation_closure['total_item_count']}`",
        f"- Reentry queue items: `{bundle.reentry_queue_state['reentry_item_count']}`",
        f"- Reentry assignments: `{bundle.reentry_assignment['assignment_count']}`",
        f"- Reentry acceptances: `{bundle.reentry_acceptance['acceptance_count']}`",
        f"- Reentry ack timeouts: `{bundle.reentry_acknowledgement_timeout['timed_out_count']}` timed out / `{bundle.reentry_acknowledgement_timeout['pending_item_count']}` pending",
        f"- Reentry reassignments: `{bundle.reentry_reassignment['reassignment_required_count']}` required",
        f"- Reentry completions: `{bundle.reentry_completion['completed_count']}` completed / `{bundle.reentry_completion['reassigned_cycle_count']}` reassigned",
        f"- Completion attestations: `{bundle.reentry_completion_attestation['attestation_count']}` / review required `{bundle.reentry_completion_attestation['review_required_count']}`",
        f"- Post-review gate: `{bundle.reentry_post_review_gate['return_authorized_count']}` authorized / `{bundle.reentry_post_review_gate['review_pending_count']}` pending review",
        f"- Review dispositions: `{bundle.post_review_disposition['approved_count']}` approved / `{bundle.post_review_disposition['rework_count']}` rework",
        f"- Return authorizations: `{bundle.return_authorization_ledger['authorized_count']}` authorized / `{bundle.return_authorization_ledger['denied_count']}` denied",
        f"- Return activations: `{bundle.return_activation['activated_count']}` activated / monitor `{bundle.return_activation['monitoring_required_count']}`",
        f"- Return drift breaches: `{bundle.return_drift_breach['breach_count']}` breaches / `{bundle.return_drift_breach['watch_count']}` watch",
        f"- Return reopen loop: `{bundle.return_reopen_loop['reopened_count']}` reopened / `{bundle.return_reopen_loop['stable_count']}` stable",
        f"- Chronic instability packets: `{bundle.chronic_instability_packet['packet_count']}` / chronic `{bundle.chronic_instability_packet['chronic_packet_count']}`",
        f"- Recurrence tribunal lane: `{bundle.recurrence_tribunal_lane['tribunal_review_required_count']}` required / tribunal `{bundle.recurrence_tribunal_lane['chronic_lane_count']}`",
        f"- Tribunal dispositions: `{bundle.recurrence_tribunal_disposition['mandate_required_count']}` mandates / freeze `{bundle.recurrence_tribunal_disposition['freeze_return_count']}`",
        f"- Chronic remediation ledger: `{bundle.chronic_remediation_mandate_ledger['mandate_required_count']}` mandates / chronic `{bundle.chronic_remediation_mandate_ledger['chronic_mandate_count']}`",
        f"- Chronic satisfaction: `{bundle.chronic_remediation_satisfaction['satisfied_count']}` satisfied / release eligible `{bundle.chronic_remediation_satisfaction['release_eligible_count']}`",
        f"- Freeze release gate: `{bundle.freeze_release_gate['release_authorized_count']}` authorized / hold `{bundle.freeze_release_gate['hold_count']}`",
        f"- Freeze release attestation: `{bundle.freeze_release_attestation['return_ready_count']}` return-ready / supervisor monitoring `{bundle.freeze_release_attestation['supervisor_monitoring_count']}`",
        f"- Chronic exit certification: `{bundle.chronic_exit_certification['certified_count']}` certified / monitoring `{bundle.chronic_exit_certification['monitoring_certified_count']}` / hold `{bundle.chronic_exit_certification['held_count']}`",
        f"- Chronic exit return bridge: `{bundle.chronic_exit_return_bridge['authorized_bridge_count']}` authorized / monitored `{bundle.chronic_exit_return_bridge['monitored_bridge_count']}` / held `{bundle.chronic_exit_return_bridge['held_bridge_count']}`",
        f"- Monitored rejoin policy: `{bundle.monitored_rejoin_policy['monitored_rejoin_count']}` monitored / standard `{bundle.monitored_rejoin_policy['standard_rejoin_count']}` / blocked `{bundle.monitored_rejoin_policy['blocked_rejoin_count']}`",
        f"- Monitored rejoin activation: `{bundle.monitored_rejoin_activation['activated_count']}` activated / monitored `{bundle.monitored_rejoin_activation['monitored_activation_count']}` / blocked `{bundle.monitored_rejoin_activation['blocked_activation_count']}`",
        f"- Chronic watch handoff: `{bundle.chronic_watch_handoff['monitoring_handoff_count']}` handoffs / supervisor `{bundle.chronic_watch_handoff['supervisor_handoff_count']}` / blocked `{bundle.chronic_watch_handoff['blocked_handoff_count']}`",
        f"- Chronic watch outcome: stable `{bundle.chronic_watch_outcome['stable_count']}` / active `{bundle.chronic_watch_outcome['active_watch_count']}` / breached `{bundle.chronic_watch_outcome['breached_count']}`",
        f"- Monitored rejoin normalization bridge: normalization `{bundle.monitored_rejoin_normalization_bridge['normalization_bridge_count']}` / watch `{bundle.monitored_rejoin_normalization_bridge['watch_continuation_count']}` / reopen `{bundle.monitored_rejoin_normalization_bridge['reopen_bridge_count']}`",
        f"- Normalization bridge activation: activated `{bundle.normalization_bridge_activation['normalization_activation_count']}` / watch `{bundle.normalization_bridge_activation['watch_continuation_count']}` / reopen `{bundle.normalization_bridge_activation['reopen_activation_count']}`",
        f"- Chronic watch audit convergence: monitoring `{bundle.chronic_watch_audit_convergence['return_monitoring_converged_count']}` / audit `{bundle.chronic_watch_audit_convergence['restoration_audit_converged_count']}` / confirmed `{bundle.chronic_watch_audit_convergence['normalization_confirmed_count']}`",
        f"- Chronic-origin audit overlay: heightened `{bundle.chronic_origin_restoration_audit_overlay['heightened_count']}` / standard `{bundle.chronic_origin_restoration_audit_overlay['standard_count']}` / held `{bundle.chronic_origin_restoration_audit_overlay['held_count']}`",
        f"- Provenance-aware drift policy: heightened `{bundle.provenance_aware_drift_policy['heightened_policy_count']}` / guarded `{bundle.provenance_aware_drift_policy['guarded_policy_count']}` / blocked `{bundle.provenance_aware_drift_policy['blocked_policy_count']}`",
        f"- Outcome entries: `{bundle.action_outcome_ledger['outcome_count']}`",
        f"- Feedback states: `{bundle.feedback_state['work_item_count']}`",
        '',
    ]


def materialize_operator_control_plane_bundle(
    request: OracleOperatorControlPlaneBundleRequest,
    *,
    operator_queue_query_result: OracleOperatorQueueQueryResult | None = None,
    operator_queue_query_request: OracleOperatorQueueQueryRequest | None = None,
    decision_journal_request: OracleOperatorDecisionJournalRequest | None = None,
    decision_execution_request: OracleOperatorDecisionExecutionRequest | None = None,
    escalation_routing_request: OracleOperatorEscalationRoutingRequest | None = None,
    escalation_packet_request: OracleOperatorEscalationPacketRequest | None = None,
    escalation_sla_request: OracleOperatorEscalationSLARequest | None = None,
    supervisor_review_request: OracleOperatorSupervisorReviewRequest | None = None,
    escalation_closure_request: OracleOperatorEscalationClosureRequest | None = None,
    action_outcome_ledger_request: OracleOperatorActionOutcomeLedgerRequest | None = None,
    feedback_state_request: OracleOperatorFeedbackStateRequest | None = None,
    reentry_queue_state_request: OracleOperatorReentryQueueStateRequest | None = None,
    reentry_assignment_request: OracleOperatorReentryAssignmentRequest | None = None,
    reentry_acceptance_request: OracleOperatorReentryAcceptanceRequest | None = None,
    reentry_acknowledgement_timeout_request: OracleOperatorReentryAcknowledgementTimeoutRequest | None = None,
    reentry_reassignment_request: OracleOperatorReentryReassignmentRequest | None = None,
    reentry_completion_request: OracleOperatorReentryCompletionRequest | None = None,
    reentry_completion_attestation_request: OracleOperatorReentryCompletionAttestationRequest | None = None,
    reentry_post_review_gate_request: OracleOperatorReentryPostReviewGateRequest | None = None,
    post_review_disposition_request: OracleOperatorPostReviewDispositionRequest | None = None,
    return_authorization_ledger_request: OracleOperatorReturnAuthorizationLedgerRequest | None = None,
    return_activation_request: OracleOperatorReturnActivationRequest | None = None,
    return_monitoring_request: OracleOperatorReturnMonitoringRequest | None = None,
    restoration_audit_request: OracleOperatorRestorationAuditRequest | None = None,
    return_drift_breach_request: OracleOperatorReturnDriftBreachRequest | None = None,
    return_reopen_loop_request: OracleOperatorReturnReopenLoopRequest | None = None,
    reopen_lineage_request: OracleOperatorReopenLineageRequest | None = None,
    reopen_recurrence_policy_request: OracleOperatorReopenRecurrencePolicyRequest | None = None,
    chronic_instability_packet_request: OracleOperatorChronicInstabilityPacketRequest | None = None,
    recurrence_tribunal_lane_request: OracleOperatorRecurrenceTribunalLaneRequest | None = None,
    recurrence_tribunal_disposition_request: OracleOperatorRecurrenceTribunalDispositionRequest | None = None,
    chronic_remediation_mandate_ledger_request: OracleOperatorChronicRemediationMandateLedgerRequest | None = None,
    chronic_remediation_satisfaction_request: OracleOperatorChronicRemediationSatisfactionRequest | None = None,
    freeze_release_gate_request: OracleOperatorFreezeReleaseGateRequest | None = None,
    freeze_release_attestation_request: OracleOperatorFreezeReleaseAttestationRequest | None = None,
    chronic_exit_certification_request: OracleOperatorChronicExitCertificationRequest | None = None,
    chronic_exit_return_bridge_request: OracleOperatorChronicExitReturnBridgeRequest | None = None,
    monitored_rejoin_policy_request: OracleOperatorMonitoredRejoinPolicyRequest | None = None,
    monitored_rejoin_activation_request: OracleOperatorMonitoredRejoinActivationRequest | None = None,
    chronic_watch_handoff_request: OracleOperatorChronicWatchHandoffRequest | None = None,
    chronic_watch_outcome_request: OracleOperatorChronicWatchOutcomeRequest | None = None,
    monitored_rejoin_normalization_bridge_request: OracleOperatorMonitoredRejoinNormalizationBridgeRequest | None = None,
    normalization_bridge_activation_request: OracleOperatorNormalizationBridgeActivationRequest | None = None,
    chronic_watch_audit_convergence_request: OracleOperatorChronicWatchAuditConvergenceRequest | None = None,
    converged_normalization_attestation_request: OracleOperatorConvergedNormalizationAttestationRequest | None = None,
    chronic_origin_restoration_provenance_request: OracleOperatorChronicOriginRestorationProvenanceRequest | None = None,
    chronic_origin_restoration_audit_overlay_request: OracleOperatorChronicOriginRestorationAuditOverlayRequest | None = None,
    provenance_aware_drift_policy_request: OracleOperatorProvenanceAwareDriftPolicyRequest | None = None,
    **kwargs: Any,
) -> OracleOperatorControlPlaneBundle:
    emitted_at_utc = request.emitted_at_utc or datetime.now(tz=UTC).replace(microsecond=0)
    if emitted_at_utc.tzinfo is None:
        emitted_at_utc = emitted_at_utc.replace(tzinfo=UTC)
    if operator_queue_query_result is None:
        operator_queue_query_result = run_operator_queue_query(request=operator_queue_query_request, **kwargs)

    request.bundle_root.mkdir(parents=True, exist_ok=True)
    workboard = materialize_operator_workboard(operator_queue_query_result=operator_queue_query_result, board_label=request.board_label)
    action_contract = materialize_operator_workboard_action_contract(operator_queue_query_result=operator_queue_query_result, board_label=request.board_label)
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
    chronic_instability_packet = materialize_operator_chronic_instability_packet(
        chronic_instability_packet_request or build_operator_chronic_instability_packet_request(
            packet_root=request.bundle_root / 'chronic_instability_packet',
            board_label=request.board_label,
            emitted_at_utc=emitted_at_utc,
        ),
        reopen_recurrence_policy=reopen_recurrence_policy,
        board_label=request.board_label,
    )
    recurrence_tribunal_lane = materialize_operator_recurrence_tribunal_lane(
        recurrence_tribunal_lane_request or build_operator_recurrence_tribunal_lane_request(
            tribunal_root=request.bundle_root / 'recurrence_tribunal_lane',
            board_label=request.board_label,
            reviewed_at_utc=emitted_at_utc,
        ),
        chronic_instability_packet=chronic_instability_packet,
        board_label=request.board_label,
    )
    recurrence_tribunal_disposition = materialize_operator_recurrence_tribunal_disposition(
        recurrence_tribunal_disposition_request or build_operator_recurrence_tribunal_disposition_request(
            disposition_root=request.bundle_root / 'recurrence_tribunal_disposition',
            board_label=request.board_label,
            reviewed_at_utc=emitted_at_utc,
        ),
        recurrence_tribunal_lane=recurrence_tribunal_lane,
        board_label=request.board_label,
    )
    chronic_remediation_mandate_ledger = materialize_operator_chronic_remediation_mandate_ledger(
        chronic_remediation_mandate_ledger_request or build_operator_chronic_remediation_mandate_ledger_request(
            ledger_root=request.bundle_root / 'chronic_remediation_mandate_ledger',
            board_label=request.board_label,
            mandated_at_utc=emitted_at_utc,
        ),
        recurrence_tribunal_disposition=recurrence_tribunal_disposition,
        board_label=request.board_label,
    )
    chronic_remediation_satisfaction = materialize_operator_chronic_remediation_satisfaction(
        chronic_remediation_satisfaction_request or build_operator_chronic_remediation_satisfaction_request(
            satisfaction_root=request.bundle_root / 'chronic_remediation_satisfaction',
            board_label=request.board_label,
            evaluated_at_utc=emitted_at_utc,
        ),
        chronic_remediation_mandate_ledger=chronic_remediation_mandate_ledger,
        board_label=request.board_label,
    )
    freeze_release_gate = materialize_operator_freeze_release_gate(
        freeze_release_gate_request or build_operator_freeze_release_gate_request(
            gate_root=request.bundle_root / 'freeze_release_gate',
            board_label=request.board_label,
            reviewed_at_utc=emitted_at_utc,
        ),
        chronic_remediation_satisfaction=chronic_remediation_satisfaction,
        board_label=request.board_label,
    )
    freeze_release_attestation = materialize_operator_freeze_release_attestation(
        freeze_release_attestation_request or build_operator_freeze_release_attestation_request(
            attestation_root=request.bundle_root / 'freeze_release_attestation',
            board_label=request.board_label,
            attested_at_utc=emitted_at_utc,
        ),
        freeze_release_gate=freeze_release_gate,
        board_label=request.board_label,
    )
    chronic_exit_certification = materialize_operator_chronic_exit_certification(
        chronic_exit_certification_request or build_operator_chronic_exit_certification_request(
            certification_root=request.bundle_root / 'chronic_exit_certification',
            board_label=request.board_label,
            certified_at_utc=emitted_at_utc,
        ),
        freeze_release_attestation=freeze_release_attestation,
        board_label=request.board_label,
    )
    chronic_exit_return_bridge = materialize_operator_chronic_exit_return_bridge(
        chronic_exit_return_bridge_request or build_operator_chronic_exit_return_bridge_request(
            bridge_root=request.bundle_root / 'chronic_exit_return_bridge',
            board_label=request.board_label,
            bridged_at_utc=emitted_at_utc,
        ),
        chronic_exit_certification=chronic_exit_certification,
        board_label=request.board_label,
    )
    monitored_rejoin_policy = materialize_operator_monitored_rejoin_policy(
        monitored_rejoin_policy_request or build_operator_monitored_rejoin_policy_request(
            policy_root=request.bundle_root / 'monitored_rejoin_policy',
            board_label=request.board_label,
            evaluated_at_utc=emitted_at_utc,
        ),
        chronic_exit_return_bridge=chronic_exit_return_bridge,
        board_label=request.board_label,
    )
    monitored_rejoin_activation = materialize_operator_monitored_rejoin_activation(
        monitored_rejoin_activation_request or build_operator_monitored_rejoin_activation_request(
            activation_root=request.bundle_root / 'monitored_rejoin_activation',
            board_label=request.board_label,
            activator_label='chronic-rejoin-activator',
            activated_at_utc=emitted_at_utc,
        ),
        monitored_rejoin_policy=monitored_rejoin_policy,
        board_label=request.board_label,
    )
    chronic_watch_handoff = materialize_operator_chronic_watch_handoff(
        chronic_watch_handoff_request or build_operator_chronic_watch_handoff_request(
            handoff_root=request.bundle_root / 'chronic_watch_handoff',
            board_label=request.board_label,
            handoff_label='chronic-watch-handoff',
            handed_off_at_utc=emitted_at_utc - timedelta(days=2),
        ),
        monitored_rejoin_activation=monitored_rejoin_activation,
        board_label=request.board_label,
    )
    chronic_watch_outcome = materialize_operator_chronic_watch_outcome(
        chronic_watch_outcome_request or build_operator_chronic_watch_outcome_request(
            outcome_root=request.bundle_root / 'chronic_watch_outcome',
            board_label=request.board_label,
            evaluated_at_utc=emitted_at_utc,
        ),
        chronic_watch_handoff=chronic_watch_handoff,
        board_label=request.board_label,
    )
    monitored_rejoin_normalization_bridge = materialize_operator_monitored_rejoin_normalization_bridge(
        monitored_rejoin_normalization_bridge_request or build_operator_monitored_rejoin_normalization_bridge_request(
            bridge_root=request.bundle_root / 'monitored_rejoin_normalization_bridge',
            board_label=request.board_label,
            bridged_at_utc=emitted_at_utc,
        ),
        chronic_watch_outcome=chronic_watch_outcome,
        board_label=request.board_label,
    )
    normalization_bridge_activation = materialize_operator_normalization_bridge_activation(
        normalization_bridge_activation_request or build_operator_normalization_bridge_activation_request(
            activation_root=request.bundle_root / 'normalization_bridge_activation',
            board_label=request.board_label,
            activated_at_utc=emitted_at_utc,
            monitoring_started_at_utc=emitted_at_utc - timedelta(hours=2),
        ),
        monitored_rejoin_normalization_bridge=monitored_rejoin_normalization_bridge,
        board_label=request.board_label,
    )
    chronic_watch_audit_convergence = materialize_operator_chronic_watch_audit_convergence(
        chronic_watch_audit_convergence_request or build_operator_chronic_watch_audit_convergence_request(
            convergence_root=request.bundle_root / 'chronic_watch_audit_convergence',
            board_label=request.board_label,
            converged_at_utc=emitted_at_utc,
        ),
        normalization_bridge_activation=normalization_bridge_activation,
        board_label=request.board_label,
    )
    converged_normalization_attestation = materialize_operator_converged_normalization_attestation(
        converged_normalization_attestation_request or build_operator_converged_normalization_attestation_request(
            attestation_root=request.bundle_root / 'converged_normalization_attestation',
            board_label=request.board_label,
            attested_at_utc=emitted_at_utc,
        ),
        chronic_watch_audit_convergence=chronic_watch_audit_convergence,
        board_label=request.board_label,
    )
    chronic_origin_restoration_provenance = materialize_operator_chronic_origin_restoration_provenance(
        chronic_origin_restoration_provenance_request or build_operator_chronic_origin_restoration_provenance_request(
            provenance_root=request.bundle_root / 'chronic_origin_restoration_provenance',
            board_label=request.board_label,
            recorded_at_utc=emitted_at_utc,
        ),
        converged_normalization_attestation=converged_normalization_attestation,
        board_label=request.board_label,
    )

    chronic_origin_restoration_audit_overlay = materialize_operator_chronic_origin_restoration_audit_overlay(
        chronic_origin_restoration_audit_overlay_request or build_operator_chronic_origin_restoration_audit_overlay_request(
            overlay_root=request.bundle_root / 'chronic_origin_restoration_audit_overlay',
            board_label=request.board_label,
            overlaid_at_utc=emitted_at_utc,
        ),
        chronic_origin_restoration_provenance=chronic_origin_restoration_provenance,
        restoration_audit=restoration_audit,
        board_label=request.board_label,
    )
    provenance_aware_drift_policy = materialize_operator_provenance_aware_drift_policy(
        provenance_aware_drift_policy_request or build_operator_provenance_aware_drift_policy_request(
            policy_root=request.bundle_root / 'provenance_aware_drift_policy',
            board_label=request.board_label,
            evaluated_at_utc=emitted_at_utc,
        ),
        chronic_origin_restoration_audit_overlay=chronic_origin_restoration_audit_overlay,
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

    bundle = OracleOperatorControlPlaneBundle(
        schema_version='oracle_operator_control_plane_bundle/v1',
        bundle_root=str(request.bundle_root),
        board_label=request.board_label,
        queue_key=operator_queue_query_result.queue_key,
        review_target=operator_queue_query_result.review_target,
        priority_band=operator_queue_query_result.priority_band,
        emitted_at_utc=emitted_at_utc.isoformat(),
        bundle_sections=('queue_query', 'workboard', 'action_contract', 'transition_policy', 'decision_journal', 'decision_execution', 'escalation_routing', 'escalation_packet', 'escalation_sla', 'supervisor_review', 'escalation_closure', 'reentry_queue_state', 'reentry_assignment', 'reentry_acceptance', 'reentry_acknowledgement_timeout', 'reentry_reassignment', 'reentry_completion', 'reentry_completion_attestation', 'reentry_post_review_gate', 'post_review_disposition', 'return_authorization_ledger', 'return_activation', 'return_monitoring', 'restoration_audit', 'return_drift_breach', 'return_reopen_loop', 'reopen_lineage', 'reopen_recurrence_policy', 'chronic_instability_packet', 'recurrence_tribunal_lane', 'recurrence_tribunal_disposition', 'chronic_remediation_mandate_ledger', 'chronic_remediation_satisfaction', 'freeze_release_gate', 'freeze_release_attestation', 'chronic_exit_certification', 'chronic_exit_return_bridge', 'monitored_rejoin_policy', 'monitored_rejoin_activation', 'chronic_watch_handoff', 'chronic_watch_outcome', 'monitored_rejoin_normalization_bridge', 'normalization_bridge_activation', 'chronic_watch_audit_convergence', 'converged_normalization_attestation', 'chronic_origin_restoration_provenance', 'chronic_origin_restoration_audit_overlay', 'provenance_aware_drift_policy', 'action_outcome_ledger', 'feedback_state'),
        summary_output_path=str(request.bundle_root / 'ORACLE_OPERATOR_CONTROL_PLANE_BUNDLE.json'),
        markdown_output_path=str(request.bundle_root / 'ORACLE_OPERATOR_CONTROL_PLANE_BUNDLE.md'),
        queue_query=operator_queue_query_result.to_payload(),
        workboard=workboard.to_payload(),
        action_contract=action_contract.to_payload(),
        transition_policy=transition_policy.to_payload(),
        decision_journal=decision_journal.to_payload(),
        decision_execution=decision_execution.to_payload(),
        escalation_routing=escalation_routing.to_payload(),
        escalation_packet=escalation_packet.to_payload(),
        escalation_sla=escalation_sla.to_payload(),
        supervisor_review=supervisor_review.to_payload(),
        escalation_closure=escalation_closure.to_payload(),
        reentry_queue_state=reentry_queue_state.to_payload(),
        reentry_assignment=reentry_assignment.to_payload(),
        reentry_acceptance=reentry_acceptance.to_payload(),
        reentry_acknowledgement_timeout=reentry_acknowledgement_timeout.to_payload(),
        reentry_reassignment=reentry_reassignment.to_payload(),
        reentry_completion=reentry_completion.to_payload(),
        reentry_completion_attestation=reentry_completion_attestation.to_payload(),
        reentry_post_review_gate=reentry_post_review_gate.to_payload(),
        post_review_disposition=post_review_disposition.to_payload(),
        return_authorization_ledger=return_authorization_ledger.to_payload(),
        return_activation=return_activation.to_payload(),
        return_monitoring=return_monitoring.to_payload(),
        restoration_audit=restoration_audit.to_payload(),
        return_drift_breach=return_drift_breach.to_payload(),
        return_reopen_loop=return_reopen_loop.to_payload(),
        reopen_lineage=reopen_lineage.to_payload(),
        reopen_recurrence_policy=reopen_recurrence_policy.to_payload(),
        chronic_instability_packet=chronic_instability_packet.to_payload(),
        recurrence_tribunal_lane=recurrence_tribunal_lane.to_payload(),
        recurrence_tribunal_disposition=recurrence_tribunal_disposition.to_payload(),
        chronic_remediation_mandate_ledger=chronic_remediation_mandate_ledger.to_payload(),
        chronic_remediation_satisfaction=chronic_remediation_satisfaction.to_payload(),
        freeze_release_gate=freeze_release_gate.to_payload(),
        freeze_release_attestation=freeze_release_attestation.to_payload(),
        chronic_exit_certification=chronic_exit_certification.to_payload(),
        chronic_exit_return_bridge=chronic_exit_return_bridge.to_payload(),
        monitored_rejoin_policy=monitored_rejoin_policy.to_payload(),
        monitored_rejoin_activation=monitored_rejoin_activation.to_payload(),
        chronic_watch_handoff=chronic_watch_handoff.to_payload(),
        chronic_watch_outcome=chronic_watch_outcome.to_payload(),
        monitored_rejoin_normalization_bridge=monitored_rejoin_normalization_bridge.to_payload(),
        normalization_bridge_activation=normalization_bridge_activation.to_payload(),
        chronic_watch_audit_convergence=chronic_watch_audit_convergence.to_payload(),
        converged_normalization_attestation=converged_normalization_attestation.to_payload(),
        chronic_origin_restoration_provenance=chronic_origin_restoration_provenance.to_payload(),
        chronic_origin_restoration_audit_overlay=chronic_origin_restoration_audit_overlay.to_payload(),
        provenance_aware_drift_policy=provenance_aware_drift_policy.to_payload(),
        action_outcome_ledger=action_outcome_ledger.to_payload(),
        feedback_state=feedback_state.to_payload(),
    )
    Path(bundle.summary_output_path).write_text(json.dumps(bundle.to_payload(), indent=2) + '\n', encoding='utf-8')
    Path(bundle.markdown_output_path).write_text('\n'.join(render_operator_control_plane_bundle_markdown_lines(bundle)), encoding='utf-8')
    return bundle


__all__ = [
    'OracleOperatorControlPlaneBundle',
    'OracleOperatorControlPlaneBundleRequest',
    'build_operator_control_plane_bundle_request',
    'materialize_operator_control_plane_bundle',
    'render_operator_control_plane_bundle_markdown_lines',
]
