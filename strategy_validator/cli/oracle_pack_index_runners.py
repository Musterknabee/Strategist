from __future__ import annotations

from strategy_validator.cli.oracle_pack_runner_common import *
from strategy_validator.cli.oracle_pack_runner_common import _emit_payload

def cmd_oracle_operator_pack_query(ns: argparse.Namespace) -> int:
    payload = build_operator_pack_query_payload(
        search_root=Path(ns.search_root),
        repo_root=Path(ns.repo_root) if ns.repo_root else None,
        pack_kinds=ns.pack_kind,
        trust_statuses=ns.trust_status,
        summary_line_contains=ns.summary_line_contains,
        output_artifact_label_contains=ns.output_artifact_label_contains,
    )
    return _emit_payload(payload, ns.output)


def cmd_oracle_operator_pack_workbench(ns: argparse.Namespace) -> int:
    payload = build_operator_pack_workbench_payload(
        search_root=Path(ns.search_root),
        repo_root=Path(ns.repo_root) if ns.repo_root else None,
        pack_kinds=ns.pack_kind,
        trust_statuses=ns.trust_status,
        summary_line_contains=ns.summary_line_contains,
        output_artifact_label_contains=ns.output_artifact_label_contains,
    )
    return _emit_payload(payload, ns.output)


def cmd_oracle_operator_pack_navigation(ns: argparse.Namespace) -> int:
    payload = build_operator_pack_navigation_payload(
        search_root=Path(ns.search_root),
        repo_root=Path(ns.repo_root) if ns.repo_root else None,
        current_pack_kind=ns.current_pack_kind,
        preferred_pack_kinds=ns.preferred_pack_kind or ns.pack_kind,
        trust_statuses=ns.trust_status,
        summary_line_contains=ns.summary_line_contains,
        output_artifact_label_contains=ns.output_artifact_label_contains,
        max_items=ns.max_items,
        include_current_pack_kind=not ns.exclude_current_pack_kind,
    )
    return _emit_payload(payload, ns.output)


def cmd_oracle_operator_pack_timeline(ns: argparse.Namespace) -> int:
    payload = build_operator_pack_timeline_payload(
        search_root=Path(ns.search_root),
        repo_root=Path(ns.repo_root) if ns.repo_root else None,
        current_pack_kind=ns.current_pack_kind,
        pack_kinds=ns.pack_kind,
        trust_statuses=ns.trust_status,
        summary_line_contains=ns.summary_line_contains,
        output_artifact_label_contains=ns.output_artifact_label_contains,
        max_items=ns.max_items,
    )
    return _emit_payload(payload, ns.output)


def cmd_oracle_operator_pack_dashboard(ns: argparse.Namespace) -> int:
    payload = materialize_operator_pack_dashboard(
        build_operator_pack_dashboard_request(
            search_root=Path(ns.search_root),
            repo_root=Path(ns.repo_root) if ns.repo_root else None,
            current_pack_kind=ns.current_pack_kind,
            preferred_pack_kinds=ns.preferred_pack_kind or ns.pack_kind,
            trust_statuses=ns.trust_status,
            summary_line_contains=ns.summary_line_contains,
            output_artifact_label_contains=ns.output_artifact_label_contains,
            max_navigation_items=ns.max_navigation_items,
            max_column_items=ns.max_column_items,
            include_current_pack_kind=ns.include_current_pack_kind,
        )
    ).to_payload()
    return _emit_payload(payload, ns.output)


def cmd_oracle_operator_pack_comparison(ns: argparse.Namespace) -> int:
    payload = materialize_operator_pack_comparison(
        build_operator_pack_comparison_request(
            search_root=Path(ns.search_root),
            repo_root=Path(ns.repo_root) if ns.repo_root else None,
            current_pack_kind=ns.current_pack_kind,
            pack_kinds=ns.pack_kind,
            trust_statuses=ns.trust_status,
            summary_line_contains=ns.summary_line_contains,
            output_artifact_label_contains=ns.output_artifact_label_contains,
            max_items=ns.max_items,
        )
    ).to_payload()
    return _emit_payload(payload, ns.output)


def cmd_oracle_operator_pack_drift(ns: argparse.Namespace) -> int:
    payload = materialize_operator_pack_drift(
        build_operator_pack_drift_request(
            search_root=Path(ns.search_root),
            repo_root=Path(ns.repo_root) if ns.repo_root else None,
            current_pack_kind=ns.current_pack_kind,
            pack_kinds=ns.pack_kind,
            trust_statuses=ns.trust_status,
            summary_line_contains=ns.summary_line_contains,
            output_artifact_label_contains=ns.output_artifact_label_contains,
            max_items=ns.max_items,
            sustained_degraded_threshold=ns.sustained_degraded_threshold,
        )
    ).to_payload()
    return _emit_payload(payload, ns.output)


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

__all__ = [
    'cmd_oracle_operator_pack_query',
    'cmd_oracle_operator_pack_workbench',
    'cmd_oracle_operator_pack_navigation',
    'cmd_oracle_operator_pack_timeline',
    'cmd_oracle_operator_pack_dashboard',
    'cmd_oracle_operator_pack_comparison',
    'cmd_oracle_operator_pack_drift',
    'cmd_oracle_operator_pack_escalation',
    'cmd_oracle_operator_pack_assignment',
]
