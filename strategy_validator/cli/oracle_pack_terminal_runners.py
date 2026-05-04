from __future__ import annotations

from strategy_validator.cli.oracle_pack_runner_common import *
from strategy_validator.cli.oracle_pack_runner_common import _emit_payload

def cmd_oracle_operator_pack_terminal_resolution(ns: argparse.Namespace) -> int:
    payload = materialize_operator_pack_terminal_resolution(
        build_operator_pack_terminal_resolution_request(
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
            backup_owner_lane=ns.backup_owner_lane,
            owner_label_prefix=ns.owner_label_prefix,
            ack_owner_lane=ns.ack_owner_lane,
            lease_label_prefix=ns.lease_label_prefix,
            lifecycle_label_prefix=ns.lifecycle_label_prefix,
            governance_label_prefix=ns.governance_label_prefix,
            readiness_label_prefix=ns.readiness_label_prefix,
            dispatch_label_prefix=ns.dispatch_label_prefix,
            outcome_label_prefix=ns.outcome_label_prefix,
            exception_label_prefix=ns.exception_label_prefix,
            approval_label_prefix=ns.approval_label_prefix,
            disposition_label_prefix=ns.disposition_label_prefix,
            authorization_label_prefix=ns.authorization_label_prefix,
            force_label_prefix=ns.force_label_prefix,
            finality_label_prefix=ns.finality_label_prefix,
            resolution_label_prefix=ns.resolution_label_prefix,
        )
    ).to_payload()
    return _emit_payload(payload, ns.output)


def cmd_oracle_operator_pack_terminal_record_publish(ns: argparse.Namespace) -> int:
    record = materialize_operator_pack_terminal_record(
        build_operator_pack_terminal_record_request(
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
            backup_owner_lane=ns.backup_owner_lane,
            owner_label_prefix=ns.owner_label_prefix,
            ack_owner_lane=ns.ack_owner_lane,
            lease_label_prefix=ns.lease_label_prefix,
            lifecycle_label_prefix=ns.lifecycle_label_prefix,
            governance_label_prefix=ns.governance_label_prefix,
            readiness_label_prefix=ns.readiness_label_prefix,
            dispatch_label_prefix=ns.dispatch_label_prefix,
            outcome_label_prefix=ns.outcome_label_prefix,
            exception_label_prefix=ns.exception_label_prefix,
            approval_label_prefix=ns.approval_label_prefix,
            disposition_label_prefix=ns.disposition_label_prefix,
            authorization_label_prefix=ns.authorization_label_prefix,
            force_label_prefix=ns.force_label_prefix,
            finality_label_prefix=ns.finality_label_prefix,
            resolution_label_prefix=ns.resolution_label_prefix,
            closure_label_prefix=ns.closure_label_prefix,
            archive_label_prefix=ns.archive_label_prefix,
            record_label_prefix=ns.record_label_prefix,
        )
    )
    payload = publish_operator_terminal_record_payload(
        publication_root=Path(ns.publication_root),
        record=record,
        repo_root=Path(ns.repo_root) if ns.repo_root else None,
        index_path=Path(ns.index_path) if ns.index_path else None,
    )
    if ns.manifest_output:
        Path(ns.manifest_output).write_text(json.dumps(payload['manifest'], indent=2, default=str) + '\n', encoding='utf-8')
    return _emit_payload(payload, ns.output)


def cmd_oracle_operator_pack_terminal_closure(ns: argparse.Namespace) -> int:
    payload = materialize_operator_pack_terminal_closure(
        build_operator_pack_terminal_closure_request(
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
            backup_owner_lane=ns.backup_owner_lane,
            owner_label_prefix=ns.owner_label_prefix,
            ack_owner_lane=ns.ack_owner_lane,
            lease_label_prefix=ns.lease_label_prefix,
            lifecycle_label_prefix=ns.lifecycle_label_prefix,
            governance_label_prefix=ns.governance_label_prefix,
            readiness_label_prefix=ns.readiness_label_prefix,
            dispatch_label_prefix=ns.dispatch_label_prefix,
            outcome_label_prefix=ns.outcome_label_prefix,
            exception_label_prefix=ns.exception_label_prefix,
            approval_label_prefix=ns.approval_label_prefix,
            disposition_label_prefix=ns.disposition_label_prefix,
            authorization_label_prefix=ns.authorization_label_prefix,
            force_label_prefix=ns.force_label_prefix,
            finality_label_prefix=ns.finality_label_prefix,
            resolution_label_prefix=ns.resolution_label_prefix,
            closure_label_prefix=ns.closure_label_prefix,
        )
    ).to_payload()
    return _emit_payload(payload, ns.output)


def cmd_oracle_operator_pack_terminal_archive(ns: argparse.Namespace) -> int:
    payload = materialize_operator_pack_terminal_archive(
        build_operator_pack_terminal_archive_request(
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
            backup_owner_lane=ns.backup_owner_lane,
            owner_label_prefix=ns.owner_label_prefix,
            ack_owner_lane=ns.ack_owner_lane,
            lease_label_prefix=ns.lease_label_prefix,
            lifecycle_label_prefix=ns.lifecycle_label_prefix,
            governance_label_prefix=ns.governance_label_prefix,
            readiness_label_prefix=ns.readiness_label_prefix,
            dispatch_label_prefix=ns.dispatch_label_prefix,
            outcome_label_prefix=ns.outcome_label_prefix,
            exception_label_prefix=ns.exception_label_prefix,
            approval_label_prefix=ns.approval_label_prefix,
            disposition_label_prefix=ns.disposition_label_prefix,
            authorization_label_prefix=ns.authorization_label_prefix,
            force_label_prefix=ns.force_label_prefix,
            finality_label_prefix=ns.finality_label_prefix,
            resolution_label_prefix=ns.resolution_label_prefix,
            closure_label_prefix=ns.closure_label_prefix,
            archive_label_prefix=ns.archive_label_prefix,
        )
    ).to_payload()
    return _emit_payload(payload, ns.output)


def cmd_oracle_operator_pack_terminal_record(ns: argparse.Namespace) -> int:
    payload = materialize_operator_pack_terminal_record(
        build_operator_pack_terminal_record_request(
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
            backup_owner_lane=ns.backup_owner_lane,
            owner_label_prefix=ns.owner_label_prefix,
            ack_owner_lane=ns.ack_owner_lane,
            lease_label_prefix=ns.lease_label_prefix,
            lifecycle_label_prefix=ns.lifecycle_label_prefix,
            governance_label_prefix=ns.governance_label_prefix,
            readiness_label_prefix=ns.readiness_label_prefix,
            dispatch_label_prefix=ns.dispatch_label_prefix,
            outcome_label_prefix=ns.outcome_label_prefix,
            exception_label_prefix=ns.exception_label_prefix,
            approval_label_prefix=ns.approval_label_prefix,
            disposition_label_prefix=ns.disposition_label_prefix,
            authorization_label_prefix=ns.authorization_label_prefix,
            force_label_prefix=ns.force_label_prefix,
            finality_label_prefix=ns.finality_label_prefix,
            resolution_label_prefix=ns.resolution_label_prefix,
            closure_label_prefix=ns.closure_label_prefix,
            archive_label_prefix=ns.archive_label_prefix,
            record_label_prefix=ns.record_label_prefix,
        )
    ).to_payload()
    return _emit_payload(payload, ns.output)


def cmd_oracle_operator_pack_execution_finality(ns: argparse.Namespace) -> int:
    payload = materialize_operator_pack_execution_finality(
        build_operator_pack_execution_finality_request(
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
            backup_owner_lane=ns.backup_owner_lane,
            owner_label_prefix=ns.owner_label_prefix,
            ack_owner_lane=ns.ack_owner_lane,
            lease_label_prefix=ns.lease_label_prefix,
            lifecycle_label_prefix=ns.lifecycle_label_prefix,
            governance_label_prefix=ns.governance_label_prefix,
            readiness_label_prefix=ns.readiness_label_prefix,
            dispatch_label_prefix=ns.dispatch_label_prefix,
            outcome_label_prefix=ns.outcome_label_prefix,
            exception_label_prefix=ns.exception_label_prefix,
            approval_label_prefix=ns.approval_label_prefix,
            disposition_label_prefix=ns.disposition_label_prefix,
            authorization_label_prefix=ns.authorization_label_prefix,
            force_label_prefix=ns.force_label_prefix,
            finality_label_prefix=ns.finality_label_prefix,
        )
    ).to_payload()
    return _emit_payload(payload, ns.output)



__all__ = [
    'cmd_oracle_operator_pack_terminal_resolution',
    'cmd_oracle_operator_pack_terminal_record_publish',
    'cmd_oracle_operator_pack_terminal_closure',
    'cmd_oracle_operator_pack_terminal_archive',
    'cmd_oracle_operator_pack_terminal_record',
    'cmd_oracle_operator_pack_execution_finality',
]
