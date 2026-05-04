from __future__ import annotations

from strategy_validator.cli.oracle_queue_runner_common import *
from strategy_validator.cli.oracle_queue_runner_common import _build_queue_kwargs, _emit_payload


def cmd_oracle_operator_workboard_action_contract(ns: argparse.Namespace) -> int:
    payload = build_workboard_action_contract_payload(
        board_label=ns.board_label,
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
    return _emit_payload(payload, ns.output)


def cmd_oracle_operator_transition_policy(ns: argparse.Namespace) -> int:
    payload = build_transition_policy_payload(board_label=ns.board_label, **_build_queue_kwargs(ns))
    return _emit_payload(payload, ns.output)
