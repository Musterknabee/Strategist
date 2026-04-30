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


__all__ = [
    'cmd_oracle_operator_pack_query',
    'cmd_oracle_operator_pack_workbench',
    'cmd_oracle_operator_pack_navigation',
]
