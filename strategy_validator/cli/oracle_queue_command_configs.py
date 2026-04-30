from __future__ import annotations

import argparse

def _configure_governance_surface_inputs(parser: argparse.ArgumentParser) -> None:
    parser.add_argument('--issued-at-utc', required=True, help='UTC timestamp used to materialize queue and review deadlines')
    parser.add_argument('--surface-label', required=True, help='Human-readable governance surface label')
    parser.add_argument('--evidence-freshness-status', default='EVIDENCE_CURRENT')
    parser.add_argument('--evidence-integrity-status', default='INTEGRITY_VERIFIED')
    parser.add_argument('--evidence-coverage-status', default='COVERAGE_COMPLETE')
    parser.add_argument('--support-verification-status', default='SUPPORT_VERIFIED')
    parser.add_argument('--support-chain-trust-status', default='TRUSTED')
    parser.add_argument('--support-chain-remediation-status', default='REMEDIATION_NONE')
    parser.add_argument('--support-chain-remediation-action', action='append', default=[], help='Optional remediation action; may be passed multiple times')
    parser.add_argument('--operator-readiness', default='READY_FOR_REVIEW')
    parser.add_argument('--output', default='', help='Optional output path for the emitted report')


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
    if output:
        output_path = Path(output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(payload, indent=2) + '\n', encoding='utf-8')
    else:
        print(json.dumps(payload, indent=2))
    return 0


def _configure_oracle_operator_queue_query(parser: argparse.ArgumentParser) -> None:
    _configure_governance_surface_inputs(parser)


def _configure_oracle_operator_workboard_query(parser: argparse.ArgumentParser) -> None:
    _configure_governance_surface_inputs(parser)
    parser.add_argument('--board-label', default='default', help='Logical label for the emitted operator workboard')


def _configure_oracle_operator_workboard_action_contract(parser: argparse.ArgumentParser) -> None:
    _configure_governance_surface_inputs(parser)
    parser.add_argument('--board-label', default='default', help='Logical label for the emitted operator workboard action contract')


def _configure_oracle_operator_transition_policy(parser: argparse.ArgumentParser) -> None:
    _configure_governance_surface_inputs(parser)
    parser.add_argument('--board-label', default='default')


def _configure_oracle_operator_decision_execution(parser: argparse.ArgumentParser) -> None:
    _configure_governance_surface_inputs(parser)
    parser.add_argument('--board-label', default='default')
    parser.add_argument('--execution-root', required=True)
    parser.add_argument('--desired-transition', default='EXECUTED')
    parser.add_argument('--actor-label', default='operator')
    parser.add_argument('--note', default='')


def _configure_oracle_operator_escalation_routing(parser: argparse.ArgumentParser) -> None:
    _configure_governance_surface_inputs(parser)
    parser.add_argument('--board-label', default='default')
    parser.add_argument('--routing-root', required=True)
    parser.add_argument('--desired-transition', default='EXECUTED')
    parser.add_argument('--actor-label', default='operator')
    parser.add_argument('--note', default='')


def _configure_oracle_operator_escalation_packet(parser: argparse.ArgumentParser) -> None:
    _configure_governance_surface_inputs(parser)
    parser.add_argument('--board-label', default='default')
    parser.add_argument('--packet-root', required=True)
    parser.add_argument('--desired-transition', default='EXECUTED')
    parser.add_argument('--actor-label', default='operator')
    parser.add_argument('--note', default='')


def _configure_oracle_operator_escalation_sla(parser: argparse.ArgumentParser) -> None:
    _configure_governance_surface_inputs(parser)
    parser.add_argument('--board-label', default='default')
    parser.add_argument('--sla-root', required=True)
    parser.add_argument('--desired-transition', default='EXECUTED')
    parser.add_argument('--actor-label', default='operator')
    parser.add_argument('--note', default='')
    parser.add_argument('--escalation-started-at-utc', default='')


def _configure_oracle_operator_decision_journal(parser: argparse.ArgumentParser) -> None:
    _configure_governance_surface_inputs(parser)
    parser.add_argument('--board-label', default='default')
    parser.add_argument('--journal-root', required=True)


def _configure_oracle_operator_supervisor_review(parser: argparse.ArgumentParser) -> None:
    _configure_governance_surface_inputs(parser)
    parser.add_argument('--board-label', default='default')
    parser.add_argument('--review-root', required=True)
    parser.add_argument('--supervisor-actor-label', default='supervisor')
    parser.add_argument('--note', default='')


def _configure_oracle_operator_escalation_closure(parser: argparse.ArgumentParser) -> None:
    _configure_governance_surface_inputs(parser)
    parser.add_argument('--board-label', default='default')
    parser.add_argument('--closure-root', required=True)


def _configure_oracle_operator_reentry_queue_state(parser: argparse.ArgumentParser) -> None:
    _configure_governance_surface_inputs(parser)
    parser.add_argument('--board-label', default='default')
    parser.add_argument('--reentry-root', required=True)
    parser.add_argument('--desired-transition', default='EXECUTED')
    parser.add_argument('--actor-label', default='operator')
    parser.add_argument('--note', default='')
    parser.add_argument('--escalation-started-at-utc', default='')
    parser.add_argument('--supervisor-actor-label', default='supervisor')
    parser.add_argument('--supervisor-note', default='')


def _configure_oracle_operator_reentry_assignment(parser: argparse.ArgumentParser) -> None:
    _configure_governance_surface_inputs(parser)
    parser.add_argument('--board-label', default='default')
    parser.add_argument('--assignment-root', required=True)
    parser.add_argument('--ownership-mode', default='CLASS_ROUTED')
    parser.add_argument('--default-assignee-label', default='operator-primary')
    parser.add_argument('--fallback-assignee-label', default='operator-backup')


def _configure_oracle_operator_reentry_acceptance(parser: argparse.ArgumentParser) -> None:
    _configure_governance_surface_inputs(parser)
    parser.add_argument('--board-label', default='default')
    parser.add_argument('--acceptance-root', required=True)
    parser.add_argument('--ownership-mode', default='CLASS_ROUTED')
    parser.add_argument('--default-assignee-label', default='operator-primary')
    parser.add_argument('--fallback-assignee-label', default='operator-backup')


def _configure_oracle_operator_reentry_acknowledgement_timeout(parser: argparse.ArgumentParser) -> None:
    _configure_governance_surface_inputs(parser)
    parser.add_argument('--board-label', default='default')
    parser.add_argument('--timeout-root', required=True)
    parser.add_argument('--accepted-at-utc', default='')
    parser.add_argument('--evaluated-at-utc', default='')


def _configure_oracle_operator_reentry_completion_attestation(parser: argparse.ArgumentParser) -> None:
    _configure_governance_surface_inputs(parser)
    parser.add_argument('--board-label', default='default')
    parser.add_argument('--attestation-root', required=True)
    parser.add_argument('--attestor-label', default='post-remediation-attestor')


def _configure_oracle_operator_reentry_post_review_gate(parser: argparse.ArgumentParser) -> None:
    _configure_governance_surface_inputs(parser)
    parser.add_argument('--board-label', default='default')
    parser.add_argument('--review-root', required=True)
    parser.add_argument('--reviewer-label', default='post-remediation-gate')


def _configure_oracle_operator_post_review_disposition(parser: argparse.ArgumentParser) -> None:
    _configure_governance_surface_inputs(parser)
    parser.add_argument('--board-label', default='default')
    parser.add_argument('--disposition-root', required=True)
    parser.add_argument('--reviewer-label', default='post-remediation-reviewer')


def _configure_oracle_operator_return_authorization_ledger(parser: argparse.ArgumentParser) -> None:
    _configure_governance_surface_inputs(parser)
    parser.add_argument('--board-label', default='default')
    parser.add_argument('--ledger-root', required=True)
    parser.add_argument('--reviewer-label', default='return-authorizer')


def _configure_oracle_operator_return_activation(parser: argparse.ArgumentParser) -> None:
    _configure_governance_surface_inputs(parser)
    parser.add_argument('--board-label', default='default')
    parser.add_argument('--activation-root', required=True)
    parser.add_argument('--activator-label', default='return-activator')


def _configure_oracle_operator_action_outcome_ledger(parser: argparse.ArgumentParser) -> None:
    _configure_governance_surface_inputs(parser)
    parser.add_argument('--board-label', default='default')
    parser.add_argument('--ledger-root', required=True)
    parser.add_argument('--outcome-state', default='ACKNOWLEDGED')
    parser.add_argument('--actor-label', default='operator')
    parser.add_argument('--note', default='')


def _configure_oracle_operator_feedback_state(parser: argparse.ArgumentParser) -> None:
    _configure_governance_surface_inputs(parser)
    parser.add_argument('--board-label', default='default')
    parser.add_argument('--state-root', required=True)
    parser.add_argument('--outcome-state', default='ACKNOWLEDGED')
    parser.add_argument('--actor-label', default='operator')
    parser.add_argument('--note', default='')


def _configure_oracle_operator_reentry_reassignment(parser: argparse.ArgumentParser) -> None:
    _configure_governance_surface_inputs(parser)
    parser.add_argument('--board-label', default='default')
    parser.add_argument('--reassignment-root', required=True)
    parser.add_argument('--accepted-at-utc', default='')
    parser.add_argument('--evaluated-at-utc', default='')
    parser.add_argument('--backup-assignee-label', default='operator-backup')
    parser.add_argument('--supervisor-assignee-label', default='supervisor-desk')


def _configure_oracle_operator_reentry_completion(parser: argparse.ArgumentParser) -> None:
    _configure_governance_surface_inputs(parser)
    parser.add_argument('--board-label', default='default')
    parser.add_argument('--completion-root', required=True)
    parser.add_argument('--accepted-at-utc', default='')
    parser.add_argument('--evaluated-at-utc', default='')
    parser.add_argument('--completed-at-utc', default='')


def _configure_oracle_operator_chronic_exit_return_bridge(parser: argparse.ArgumentParser) -> None:
    _configure_governance_surface_inputs(parser)
    parser.add_argument('--board-label', default='default')
    parser.add_argument('--bridge-root', required=True)
    parser.add_argument('--prior-reopen-count', action='append', default=[], help='Optional work_item_key=count mapping; may be passed multiple times')


def _configure_oracle_operator_monitored_rejoin_policy(parser: argparse.ArgumentParser) -> None:
    _configure_governance_surface_inputs(parser)
    parser.add_argument('--board-label', default='default')
    parser.add_argument('--policy-root', required=True)
    parser.add_argument('--prior-reopen-count', action='append', default=[], help='Optional work_item_key=count mapping; may be passed multiple times')


def _configure_oracle_operator_monitored_rejoin_activation(parser: argparse.ArgumentParser) -> None:
    _configure_governance_surface_inputs(parser)
    parser.add_argument('--board-label', default='default')
    parser.add_argument('--activation-root', required=True)
    parser.add_argument('--prior-reopen-count', action='append', default=[], help='Optional work_item_key=count mapping; may be passed multiple times')


def _configure_oracle_operator_chronic_watch_handoff(parser: argparse.ArgumentParser) -> None:
    _configure_governance_surface_inputs(parser)
    parser.add_argument('--board-label', default='default')
    parser.add_argument('--handoff-root', required=True)
    parser.add_argument('--prior-reopen-count', action='append', default=[], help='Optional work_item_key=count mapping; may be passed multiple times')


def _configure_oracle_operator_control_plane_bundle(parser: argparse.ArgumentParser) -> None:
    _configure_governance_surface_inputs(parser)
    parser.add_argument('--board-label', default='default')
    parser.add_argument('--bundle-root', required=True)
    parser.add_argument('--outcome-state', default='ACKNOWLEDGED')
    parser.add_argument('--actor-label', default='operator')
    parser.add_argument('--note', default='')


def _configure_oracle_operator_return_monitoring(parser: argparse.ArgumentParser) -> None:
    _configure_governance_surface_inputs(parser)
    parser.add_argument('--board-label', default='default')
    parser.add_argument('--monitoring-root', required=True)
    parser.add_argument('--monitor-label', default='return-monitor')
    parser.add_argument('--monitoring-started-at-utc', default='')


def _configure_oracle_operator_restoration_audit(parser: argparse.ArgumentParser) -> None:
    _configure_governance_surface_inputs(parser)
    parser.add_argument('--board-label', default='default')
    parser.add_argument('--audit-root', required=True)
    parser.add_argument('--auditor-label', default='restoration-auditor')


def _configure_oracle_operator_return_drift_breach(parser: argparse.ArgumentParser) -> None:
    _configure_governance_surface_inputs(parser)
    parser.add_argument('--board-label', default='default')
    parser.add_argument('--breach-root', required=True)
    parser.add_argument('--evaluator-label', default='return-drift-evaluator')
    parser.add_argument('--drift-signal-mode', default='AUTO')


def _configure_oracle_operator_return_reopen_loop(parser: argparse.ArgumentParser) -> None:
    _configure_governance_surface_inputs(parser)
    parser.add_argument('--board-label', default='default')
    parser.add_argument('--reopen-root', required=True)
    parser.add_argument('--reopen-label', default='return-reopen-controller')
    parser.add_argument('--drift-signal-mode', default='AUTO')


def _configure_oracle_operator_chronic_watch_outcome(parser: argparse.ArgumentParser) -> None:
    _configure_governance_surface_inputs(parser)
    parser.add_argument('--board-label', default='default')
    parser.add_argument('--outcome-root', required=True)
    parser.add_argument('--drift-signal-mode', default='AUTO')
    parser.add_argument('--prior-reopen-count', action='append', default=[])


def _configure_oracle_operator_monitored_rejoin_normalization_bridge(parser: argparse.ArgumentParser) -> None:
    _configure_governance_surface_inputs(parser)
    parser.add_argument('--board-label', default='default')
    parser.add_argument('--bridge-root', required=True)
    parser.add_argument('--drift-signal-mode', default='AUTO')
    parser.add_argument('--prior-reopen-count', action='append', default=[])


def _configure_oracle_operator_normalization_bridge_activation(parser: argparse.ArgumentParser) -> None:
    _configure_governance_surface_inputs(parser)
    parser.add_argument('--board-label', default='default')
    parser.add_argument('--activation-root', required=True)
    parser.add_argument('--activator-label', default='normalization-bridge-activator')
    parser.add_argument('--monitoring-started-at-utc', default='')


def _configure_oracle_operator_chronic_watch_audit_convergence(parser: argparse.ArgumentParser) -> None:
    _configure_governance_surface_inputs(parser)
    parser.add_argument('--board-label', default='default')
    parser.add_argument('--convergence-root', required=True)
    parser.add_argument('--converger-label', default='chronic-watch-audit-converger')
    parser.add_argument('--normalization-window-minutes', type=int, default=60)
    parser.add_argument('--monitoring-started-at-utc', default='')


def _configure_oracle_operator_converged_normalization_attestation(parser: argparse.ArgumentParser) -> None:
    _configure_governance_surface_inputs(parser)
    parser.add_argument('--board-label', default='default')
    parser.add_argument('--attestation-root', required=True)
    parser.add_argument('--attestor-label', default='converged-normalization-attestor')
    parser.add_argument('--monitoring-started-at-utc', default='')
    parser.add_argument('--normalization-window-minutes', type=int, default=60)


def _configure_oracle_operator_chronic_origin_restoration_provenance(parser: argparse.ArgumentParser) -> None:
    _configure_governance_surface_inputs(parser)
    parser.add_argument('--board-label', default='default')
    parser.add_argument('--provenance-root', required=True)
    parser.add_argument('--provenance-label', default='chronic-origin-provenance-recorder')
    parser.add_argument('--monitoring-started-at-utc', default='')
    parser.add_argument('--normalization-window-minutes', type=int, default=60)


def _configure_oracle_operator_chronic_origin_restoration_audit_overlay(parser: argparse.ArgumentParser) -> None:
    _configure_governance_surface_inputs(parser)
    parser.add_argument('--board-label', default='default')
    parser.add_argument('--overlay-root', required=True)
    parser.add_argument('--overlay-label', default='chronic-origin-audit-overlay')
    parser.add_argument('--monitoring-started-at-utc', default='')
    parser.add_argument('--normalization-window-minutes', type=int, default=60)


def _configure_oracle_operator_provenance_aware_drift_policy(parser: argparse.ArgumentParser) -> None:
    _configure_governance_surface_inputs(parser)
    parser.add_argument('--board-label', default='default')
    parser.add_argument('--policy-root', required=True)
    parser.add_argument('--policy-label', default='provenance-aware-drift-policy')


def _parse_prior_reopen_counts(values: list[str]) -> dict[str, int]:
    parsed: dict[str, int] = {}
    for raw in values:
        if '=' not in raw:
            continue
        key, value = raw.split('=', 1)
        key = key.strip()
        value = value.strip()
        if not key:
            continue
        parsed[key] = max(0, int(value or '0'))
    return parsed


def _configure_oracle_operator_reopen_lineage(parser: argparse.ArgumentParser) -> None:
    _configure_governance_surface_inputs(parser)
    parser.add_argument('--board-label', default='default')
    parser.add_argument('--lineage-root', required=True)
    parser.add_argument('--lineage-label', default='reopen-lineage-analyst')
    parser.add_argument('--drift-signal-mode', default='AUTO')
    parser.add_argument('--prior-reopen-count', action='append', default=[], help='Optional work_item_key=count mapping; may be passed multiple times')


def _configure_oracle_operator_reopen_recurrence_policy(parser: argparse.ArgumentParser) -> None:
    _configure_governance_surface_inputs(parser)
    parser.add_argument('--board-label', default='default')
    parser.add_argument('--policy-root', required=True)
    parser.add_argument('--evaluator-label', default='reopen-recurrence-policy')
    parser.add_argument('--drift-signal-mode', default='AUTO')
    parser.add_argument('--escalation-after-reopen-count', type=int, default=2)
    parser.add_argument('--chronic-after-reopen-count', type=int, default=3)
    parser.add_argument('--prior-reopen-count', action='append', default=[], help='Optional work_item_key=count mapping; may be passed multiple times')


def _configure_oracle_operator_chronic_instability_packet(parser: argparse.ArgumentParser) -> None:
    _configure_governance_surface_inputs(parser)
    parser.add_argument('--board-label', default='default')
    parser.add_argument('--packet-root', required=True)
    parser.add_argument('--evaluator-label', default='chronic-instability-packet')
    parser.add_argument('--drift-signal-mode', default='AUTO')
    parser.add_argument('--escalation-after-reopen-count', type=int, default=2)
    parser.add_argument('--chronic-after-reopen-count', type=int, default=3)
    parser.add_argument('--prior-reopen-count', action='append', default=[], help='Optional work_item_key=count mapping; may be passed multiple times')


def _configure_oracle_operator_recurrence_tribunal_lane(parser: argparse.ArgumentParser) -> None:
    _configure_governance_surface_inputs(parser)
    parser.add_argument('--board-label', default='default')
    parser.add_argument('--tribunal-root', required=True)
    parser.add_argument('--reviewer-label', default='recurrence-tribunal')
    parser.add_argument('--drift-signal-mode', default='AUTO')
    parser.add_argument('--escalation-after-reopen-count', type=int, default=2)
    parser.add_argument('--chronic-after-reopen-count', type=int, default=3)
    parser.add_argument('--prior-reopen-count', action='append', default=[], help='Optional work_item_key=count mapping; may be passed multiple times')


def _configure_oracle_operator_recurrence_tribunal_disposition(parser: argparse.ArgumentParser) -> None:
    _configure_governance_surface_inputs(parser)
    parser.add_argument('--board-label', default='default')
    parser.add_argument('--disposition-root', required=True)
    parser.add_argument('--prior-reopen-count', action='append', default=[], help='Optional work_item_key=count mapping; may be passed multiple times')


def _configure_oracle_operator_chronic_remediation_mandate_ledger(parser: argparse.ArgumentParser) -> None:
    _configure_governance_surface_inputs(parser)
    parser.add_argument('--board-label', default='default')
    parser.add_argument('--ledger-root', required=True)
    parser.add_argument('--prior-reopen-count', action='append', default=[], help='Optional work_item_key=count mapping; may be passed multiple times')


def _configure_oracle_operator_chronic_remediation_satisfaction(parser: argparse.ArgumentParser) -> None:
    _configure_governance_surface_inputs(parser)
    parser.add_argument('--board-label', default='default')
    parser.add_argument('--satisfaction-root', required=True)
    parser.add_argument('--prior-reopen-count', action='append', default=[], help='Optional work_item_key=count mapping; may be passed multiple times')


def _configure_oracle_operator_freeze_release_gate(parser: argparse.ArgumentParser) -> None:
    _configure_governance_surface_inputs(parser)
    parser.add_argument('--board-label', default='default')
    parser.add_argument('--gate-root', required=True)
    parser.add_argument('--prior-reopen-count', action='append', default=[], help='Optional work_item_key=count mapping; may be passed multiple times')


def _configure_oracle_operator_freeze_release_attestation(parser: argparse.ArgumentParser) -> None:
    _configure_governance_surface_inputs(parser)
    parser.add_argument('--board-label', default='default')
    parser.add_argument('--attestation-root', required=True)
    parser.add_argument('--prior-reopen-count', action='append', default=[], help='Optional work_item_key=count mapping; may be passed multiple times')


def _configure_oracle_operator_chronic_exit_certification(parser: argparse.ArgumentParser) -> None:
    _configure_governance_surface_inputs(parser)
    parser.add_argument('--board-label', default='default')
    parser.add_argument('--certification-root', required=True)
    parser.add_argument('--prior-reopen-count', action='append', default=[], help='Optional work_item_key=count mapping; may be passed multiple times')


