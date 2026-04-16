from __future__ import annotations

import argparse
import json
from pathlib import Path
from datetime import timedelta

from strategy_validator.application.governance_surface import (
    build_governance_queue_state,
    build_workboard_action_contract_payload,
)
from strategy_validator.application.operator_queue_commands import (
    build_queue_query_payload,
    build_transition_policy_payload,
    build_workboard_payload,
)
from strategy_validator.cli.oracle_cli_common import parse_utc
from strategy_validator.control_plane import (
    assess_governance_plane,
    build_operator_action_outcome_ledger_request,
    build_operator_control_plane_bundle_request,
    build_operator_decision_execution_request,
    build_operator_decision_journal_request,
    build_operator_feedback_state_request,
    build_operator_reentry_queue_state_request,
    build_operator_reentry_assignment_request,
    build_operator_reentry_acceptance_request,
    build_operator_reentry_acknowledgement_timeout_request,
    build_operator_reentry_reassignment_request,
    build_operator_reentry_completion_request,
    build_operator_reentry_completion_attestation_request,
    build_operator_reentry_post_review_gate_request,
    build_operator_post_review_disposition_request,
    build_operator_return_authorization_ledger_request,
    build_operator_return_activation_request,
    build_operator_return_monitoring_request,
    build_operator_restoration_audit_request,
    build_operator_return_drift_breach_request,
    build_operator_return_reopen_loop_request,
    build_operator_reopen_lineage_request,
    build_operator_reopen_recurrence_policy_request,
    build_operator_chronic_instability_packet_request,
    build_operator_recurrence_tribunal_lane_request,
    build_operator_recurrence_tribunal_disposition_request,
    build_operator_chronic_remediation_mandate_ledger_request,
    build_operator_chronic_remediation_satisfaction_request,
    build_operator_freeze_release_gate_request,
    build_operator_freeze_release_attestation_request,
    build_operator_chronic_exit_certification_request,
    build_operator_chronic_exit_return_bridge_request,
    build_operator_monitored_rejoin_policy_request,
    build_operator_monitored_rejoin_activation_request,
    build_operator_chronic_watch_handoff_request,
    build_operator_chronic_watch_outcome_request,
    build_operator_monitored_rejoin_normalization_bridge_request,
    build_operator_normalization_bridge_activation_request,
    build_operator_chronic_watch_audit_convergence_request,
    build_operator_converged_normalization_attestation_request,
    build_operator_chronic_origin_restoration_provenance_request,
    build_operator_provenance_aware_drift_policy_request,
    build_operator_chronic_origin_restoration_audit_overlay_request,
    build_operator_escalation_routing_request,
    build_operator_escalation_packet_request,
    build_operator_escalation_sla_request,
    build_operator_supervisor_review_request,
    build_operator_escalation_closure_request,
    build_operator_transition_policy_request,
    materialize_governance_work_queue_state,
    materialize_operator_action_outcome_ledger,
    materialize_operator_control_plane_bundle,
    materialize_operator_decision_execution,
    materialize_operator_decision_journal,
    materialize_operator_feedback_state,
    materialize_operator_reentry_queue_state,
    materialize_operator_reentry_assignment,
    materialize_operator_reentry_acceptance,
    materialize_operator_reentry_acknowledgement_timeout,
    materialize_operator_reentry_reassignment,
    materialize_operator_reentry_completion,
    materialize_operator_reentry_completion_attestation,
    materialize_operator_reentry_post_review_gate,
    materialize_operator_post_review_disposition,
    materialize_operator_return_authorization_ledger,
    materialize_operator_return_activation,
    materialize_operator_return_monitoring,
    materialize_operator_restoration_audit,
    materialize_operator_return_drift_breach,
    materialize_operator_return_reopen_loop,
    materialize_operator_reopen_lineage,
    materialize_operator_reopen_recurrence_policy,
    materialize_operator_chronic_instability_packet,
    materialize_operator_recurrence_tribunal_lane,
    materialize_operator_recurrence_tribunal_disposition,
    materialize_operator_chronic_remediation_mandate_ledger,
    materialize_operator_chronic_remediation_satisfaction,
    materialize_operator_freeze_release_gate,
    materialize_operator_freeze_release_attestation,
    materialize_operator_chronic_exit_certification,
    materialize_operator_chronic_exit_return_bridge,
    materialize_operator_monitored_rejoin_policy,
    materialize_operator_monitored_rejoin_activation,
    materialize_operator_chronic_watch_handoff,
    materialize_operator_chronic_watch_outcome,
    materialize_operator_monitored_rejoin_normalization_bridge,
    materialize_operator_normalization_bridge_activation,
    materialize_operator_chronic_watch_audit_convergence,
    materialize_operator_converged_normalization_attestation,
    materialize_operator_chronic_origin_restoration_provenance,
    materialize_operator_provenance_aware_drift_policy,
    materialize_operator_chronic_origin_restoration_audit_overlay,
    materialize_operator_escalation_routing,
    materialize_operator_escalation_packet,
    materialize_operator_escalation_sla,
    materialize_operator_supervisor_review,
    materialize_operator_escalation_closure,
    materialize_operator_transition_policy,
    materialize_operator_queue_snapshot,
    materialize_operator_workboard,
    materialize_operator_workboard_action_contract,
    run_operator_queue_query,
)


def _build_queue_state(ns: argparse.Namespace):
    return build_governance_queue_state(
        issued_at_utc=parse_utc(ns.issued_at_utc),
        evidence_freshness_status=ns.evidence_freshness_status,
        evidence_integrity_status=ns.evidence_integrity_status,
        evidence_coverage_status=ns.evidence_coverage_status,
        support_verification_status=ns.support_verification_status,
        support_chain_trust_status=ns.support_chain_trust_status,
        support_chain_remediation_status=ns.support_chain_remediation_status,
        support_chain_remediation_actions=[item.strip() for item in getattr(ns, 'support_chain_remediation_action', []) if item.strip()],
        operator_readiness=ns.operator_readiness,
        surface_label=ns.surface_label,
    )


def _emit_payload(payload: dict, output: str) -> int:
    text = json.dumps(payload, indent=2, sort_keys=True)
    if output == '-':
        print(text)
    else:
        Path(output).write_text(text + '\n', encoding='utf-8')
    return 0


def _parse_prior_reopen_counts(values: list[str]) -> dict[str, int]:
    parsed: dict[str, int] = {}
    for item in values:
        key, raw = item.split('=', 1)
        parsed[key] = int(raw)
    return parsed


def _build_queue_kwargs(ns: argparse.Namespace) -> dict:
    return {
        'issued_at_utc': parse_utc(ns.issued_at_utc),
        'surface_label': ns.surface_label,
        'evidence_freshness_status': ns.evidence_freshness_status,
        'evidence_integrity_status': ns.evidence_integrity_status,
        'evidence_coverage_status': ns.evidence_coverage_status,
        'support_verification_status': ns.support_verification_status,
        'support_chain_trust_status': ns.support_chain_trust_status,
        'support_chain_remediation_status': ns.support_chain_remediation_status,
        'support_chain_remediation_actions': [
            item.strip()
            for item in getattr(ns, 'support_chain_remediation_action', [])
            if item.strip()
        ],
        'operator_readiness': ns.operator_readiness,
    }


