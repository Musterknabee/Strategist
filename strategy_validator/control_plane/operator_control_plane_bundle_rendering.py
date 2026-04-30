from __future__ import annotations

from strategy_validator.contracts.operator_control_plane_bundle import OracleOperatorControlPlaneBundle


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



__all__ = [
    "render_operator_control_plane_bundle_markdown_lines",
]
