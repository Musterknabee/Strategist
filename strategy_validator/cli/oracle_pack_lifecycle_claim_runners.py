from __future__ import annotations

from strategy_validator.cli.oracle_pack_runner_common import *
from strategy_validator.cli.oracle_pack_runner_common import _emit_payload


def cmd_oracle_operator_pack_escalation(ns: argparse.Namespace) -> int:
    payload = build_pack_escalation_payload(
        search_root=Path(ns.search_root),
        repo_root=Path(ns.repo_root) if ns.repo_root else None,
        current_pack_kind=ns.current_pack_kind,
        pack_kinds=ns.pack_kind,
        trust_statuses=ns.trust_status,
        summary_line_contains=ns.summary_line_contains,
        output_artifact_label_contains=ns.output_artifact_label_contains,
        max_items=ns.max_items,
        sustained_degraded_threshold=ns.sustained_degraded_threshold,
        queue_key=ns.queue_key,
        review_target=ns.review_target,
        priority_band=ns.priority_band,
        action_owner_lane=ns.action_owner_lane,
        board_label=ns.board_label,
    )
    return _emit_payload(payload, ns.output)



def cmd_oracle_operator_pack_assignment(ns: argparse.Namespace) -> int:
    payload = build_pack_assignment_payload(
        search_root=Path(ns.search_root),
        repo_root=Path(ns.repo_root) if ns.repo_root else None,
        current_pack_kind=ns.current_pack_kind,
        pack_kinds=ns.pack_kind,
        trust_statuses=ns.trust_status,
        summary_line_contains=ns.summary_line_contains,
        output_artifact_label_contains=ns.output_artifact_label_contains,
        max_items=ns.max_items,
        sustained_degraded_threshold=ns.sustained_degraded_threshold,
        queue_key=ns.queue_key,
        review_target=ns.review_target,
        priority_band=ns.priority_band,
        action_owner_lane=ns.action_owner_lane,
        backup_owner_lane=ns.backup_owner_lane,
        board_label=ns.board_label,
        owner_label_prefix=ns.owner_label_prefix,
    )
    return _emit_payload(payload, ns.output)



def cmd_oracle_operator_pack_claim_lease(ns: argparse.Namespace) -> int:
    payload = build_pack_claim_lease_payload(
        search_root=Path(ns.search_root),
        repo_root=Path(ns.repo_root) if ns.repo_root else None,
        current_pack_kind=ns.current_pack_kind,
        pack_kinds=ns.pack_kind,
        trust_statuses=ns.trust_status,
        summary_line_contains=ns.summary_line_contains,
        output_artifact_label_contains=ns.output_artifact_label_contains,
        max_items=ns.max_items,
        sustained_degraded_threshold=ns.sustained_degraded_threshold,
        queue_key=ns.queue_key,
        review_target=ns.review_target,
        priority_band=ns.priority_band,
        action_owner_lane=ns.action_owner_lane,
        backup_owner_lane=ns.backup_owner_lane,
        ack_owner_lane=ns.ack_owner_lane,
        board_label=ns.board_label,
        owner_label_prefix=ns.owner_label_prefix,
        lease_label_prefix=ns.lease_label_prefix,
    )
    return _emit_payload(payload, ns.output)



def cmd_oracle_operator_pack_claim_operability(ns: argparse.Namespace) -> int:
    payload = build_pack_claim_operability_payload(
        search_root=Path(ns.search_root),
        repo_root=Path(ns.repo_root) if ns.repo_root else None,
        current_pack_kind=ns.current_pack_kind,
        pack_kinds=ns.pack_kind,
        trust_statuses=ns.trust_status,
        summary_line_contains=ns.summary_line_contains,
        output_artifact_label_contains=ns.output_artifact_label_contains,
        max_items=ns.max_items,
        sustained_degraded_threshold=ns.sustained_degraded_threshold,
        queue_key=ns.queue_key,
        review_target=ns.review_target,
        priority_band=ns.priority_band,
        action_owner_lane=ns.action_owner_lane,
        backup_owner_lane=ns.backup_owner_lane,
        ack_owner_lane=ns.ack_owner_lane,
        board_label=ns.board_label,
        owner_label_prefix=ns.owner_label_prefix,
        lease_label_prefix=ns.lease_label_prefix,
        lifecycle_label_prefix=ns.lifecycle_label_prefix,
        governance_label_prefix=ns.governance_label_prefix,
        readiness_label_prefix=ns.readiness_label_prefix,
        operability_label_prefix=ns.operability_label_prefix,
    )
    return _emit_payload(payload, ns.output)



def cmd_oracle_operator_pack_claim_lifecycle(ns: argparse.Namespace) -> int:
    payload = build_pack_claim_lifecycle_payload(
        search_root=Path(ns.search_root),
        repo_root=Path(ns.repo_root) if ns.repo_root else None,
        current_pack_kind=ns.current_pack_kind,
        pack_kinds=ns.pack_kind,
        trust_statuses=ns.trust_status,
        summary_line_contains=ns.summary_line_contains,
        output_artifact_label_contains=ns.output_artifact_label_contains,
        max_items=ns.max_items,
        sustained_degraded_threshold=ns.sustained_degraded_threshold,
        queue_key=ns.queue_key,
        review_target=ns.review_target,
        priority_band=ns.priority_band,
        action_owner_lane=ns.action_owner_lane,
        backup_owner_lane=ns.backup_owner_lane,
        ack_owner_lane=ns.ack_owner_lane,
        board_label=ns.board_label,
        owner_label_prefix=ns.owner_label_prefix,
        lease_label_prefix=ns.lease_label_prefix,
        lifecycle_label_prefix=ns.lifecycle_label_prefix,
    )
    return _emit_payload(payload, ns.output)


__all__ = [
    'cmd_oracle_operator_pack_escalation',
    'cmd_oracle_operator_pack_assignment',
    'cmd_oracle_operator_pack_claim_lease',
    'cmd_oracle_operator_pack_claim_operability',
    'cmd_oracle_operator_pack_claim_lifecycle',
]
