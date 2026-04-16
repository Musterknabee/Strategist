from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class OracleOperatorControlPlaneBundleRequest:
    bundle_root: Path
    board_label: str = "default"
    emitted_at_utc: datetime | None = None


@dataclass(frozen=True)
class OracleOperatorControlPlaneBundle:
    schema_version: str
    bundle_root: str
    board_label: str
    queue_key: str
    review_target: str
    priority_band: str
    emitted_at_utc: str
    bundle_sections: tuple[str, ...]
    summary_output_path: str
    markdown_output_path: str
    queue_query: dict[str, Any]
    workboard: dict[str, Any]
    action_contract: dict[str, Any]
    transition_policy: dict[str, Any]
    decision_journal: dict[str, Any]
    decision_execution: dict[str, Any]
    escalation_routing: dict[str, Any]
    escalation_packet: dict[str, Any]
    escalation_sla: dict[str, Any]
    supervisor_review: dict[str, Any]
    escalation_closure: dict[str, Any]
    reentry_queue_state: dict[str, Any]
    reentry_assignment: dict[str, Any]
    reentry_acceptance: dict[str, Any]
    reentry_acknowledgement_timeout: dict[str, Any]
    reentry_reassignment: dict[str, Any]
    reentry_completion: dict[str, Any]
    reentry_completion_attestation: dict[str, Any]
    reentry_post_review_gate: dict[str, Any]
    post_review_disposition: dict[str, Any]
    return_authorization_ledger: dict[str, Any]
    return_activation: dict[str, Any]
    return_monitoring: dict[str, Any]
    restoration_audit: dict[str, Any]
    return_drift_breach: dict[str, Any]
    return_reopen_loop: dict[str, Any]
    reopen_lineage: dict[str, Any]
    reopen_recurrence_policy: dict[str, Any]
    chronic_instability_packet: dict[str, Any]
    recurrence_tribunal_lane: dict[str, Any]
    recurrence_tribunal_disposition: dict[str, Any]
    chronic_remediation_mandate_ledger: dict[str, Any]
    chronic_remediation_satisfaction: dict[str, Any]
    freeze_release_gate: dict[str, Any]
    freeze_release_attestation: dict[str, Any]
    chronic_exit_certification: dict[str, Any]
    chronic_exit_return_bridge: dict[str, Any]
    monitored_rejoin_policy: dict[str, Any]
    monitored_rejoin_activation: dict[str, Any]
    chronic_watch_handoff: dict[str, Any]
    chronic_watch_outcome: dict[str, Any]
    monitored_rejoin_normalization_bridge: dict[str, Any]
    normalization_bridge_activation: dict[str, Any]
    chronic_watch_audit_convergence: dict[str, Any]
    converged_normalization_attestation: dict[str, Any]
    chronic_origin_restoration_provenance: dict[str, Any]
    chronic_origin_restoration_audit_overlay: dict[str, Any]
    provenance_aware_drift_policy: dict[str, Any]
    action_outcome_ledger: dict[str, Any]
    feedback_state: dict[str, Any]

    def to_payload(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "bundle_root": self.bundle_root,
            "board_label": self.board_label,
            "queue_key": self.queue_key,
            "review_target": self.review_target,
            "priority_band": self.priority_band,
            "emitted_at_utc": self.emitted_at_utc,
            "bundle_sections": list(self.bundle_sections),
            "summary_output_path": self.summary_output_path,
            "markdown_output_path": self.markdown_output_path,
            "queue_query": self.queue_query,
            "workboard": self.workboard,
            "action_contract": self.action_contract,
            "transition_policy": self.transition_policy,
            "decision_journal": self.decision_journal,
            "decision_execution": self.decision_execution,
            "escalation_routing": self.escalation_routing,
            "escalation_packet": self.escalation_packet,
            "escalation_sla": self.escalation_sla,
            "supervisor_review": self.supervisor_review,
            "escalation_closure": self.escalation_closure,
            "reentry_queue_state": self.reentry_queue_state,
            "reentry_assignment": self.reentry_assignment,
            "reentry_acceptance": self.reentry_acceptance,
            "reentry_acknowledgement_timeout": self.reentry_acknowledgement_timeout,
            "reentry_reassignment": self.reentry_reassignment,
            "reentry_completion": self.reentry_completion,
            "reentry_completion_attestation": self.reentry_completion_attestation,
            "reentry_post_review_gate": self.reentry_post_review_gate,
            "post_review_disposition": self.post_review_disposition,
            "return_authorization_ledger": self.return_authorization_ledger,
            "return_activation": self.return_activation,
            "return_monitoring": self.return_monitoring,
            "restoration_audit": self.restoration_audit,
            "return_drift_breach": self.return_drift_breach,
            "return_reopen_loop": self.return_reopen_loop,
            "reopen_lineage": self.reopen_lineage,
            "reopen_recurrence_policy": self.reopen_recurrence_policy,
            "chronic_instability_packet": self.chronic_instability_packet,
            "recurrence_tribunal_lane": self.recurrence_tribunal_lane,
            "recurrence_tribunal_disposition": self.recurrence_tribunal_disposition,
            "chronic_remediation_mandate_ledger": self.chronic_remediation_mandate_ledger,
            "chronic_remediation_satisfaction": self.chronic_remediation_satisfaction,
            "freeze_release_gate": self.freeze_release_gate,
            "freeze_release_attestation": self.freeze_release_attestation,
            "chronic_exit_certification": self.chronic_exit_certification,
            "chronic_exit_return_bridge": self.chronic_exit_return_bridge,
            "monitored_rejoin_policy": self.monitored_rejoin_policy,
            "monitored_rejoin_activation": self.monitored_rejoin_activation,
            "chronic_watch_handoff": self.chronic_watch_handoff,
            "chronic_watch_outcome": self.chronic_watch_outcome,
            "monitored_rejoin_normalization_bridge": self.monitored_rejoin_normalization_bridge,
            "normalization_bridge_activation": self.normalization_bridge_activation,
            "chronic_watch_audit_convergence": self.chronic_watch_audit_convergence,
            "converged_normalization_attestation": self.converged_normalization_attestation,
            "chronic_origin_restoration_provenance": self.chronic_origin_restoration_provenance,
            "chronic_origin_restoration_audit_overlay": self.chronic_origin_restoration_audit_overlay,
            "provenance_aware_drift_policy": self.provenance_aware_drift_policy,
            "action_outcome_ledger": self.action_outcome_ledger,
            "feedback_state": self.feedback_state,
        }

