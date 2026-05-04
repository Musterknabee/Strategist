from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from strategy_validator.control_plane.operator_reentry_acceptance import (
    OracleOperatorReentryAcceptance,
    build_operator_reentry_acceptance_request,
    materialize_operator_reentry_acceptance,
)
from strategy_validator.control_plane.operator_reentry_reassignment import (
    OracleOperatorReentryReassignment,
    build_operator_reentry_reassignment_request,
    materialize_operator_reentry_reassignment,
)


@dataclass(frozen=True)
class OracleOperatorReentryCompletionRequest:
    completion_root: Path
    board_label: str = 'default'
    completion_policy: str = 'AUTO_INFERRED'
    completed_at_utc: datetime | None = None


@dataclass(frozen=True)
class OracleOperatorReentryCompletionItem:
    completion_key: str
    reassignment_key: str
    acceptance_key: str
    assignment_key: str
    reentry_key: str
    work_item_key: str
    assignee_label: str
    remediation_class: str
    completion_state: str
    evidence_posture: str
    evidence_reason_code: str
    closure_reason_code: str
    return_to_normal_state: str
    next_queue_lane: str
    remediation_reopen_required: bool
    completed_at_utc: str

    def to_payload(self) -> dict[str, Any]:
        return self.__dict__.copy()


@dataclass(frozen=True)
class OracleOperatorReentryCompletion:
    schema_version: str
    board_label: str
    completion_root: str
    completion_policy: str
    completed_at_utc: str
    total_item_count: int
    completed_count: int
    reassigned_cycle_count: int
    escalated_cycle_count: int
    pending_cycle_count: int
    returned_to_normal_count: int
    summary_output_path: str
    markdown_output_path: str
    items: tuple[OracleOperatorReentryCompletionItem, ...]

    def to_payload(self) -> dict[str, Any]:
        return {
            'schema_version': self.schema_version,
            'board_label': self.board_label,
            'completion_root': self.completion_root,
            'completion_policy': self.completion_policy,
            'completed_at_utc': self.completed_at_utc,
            'total_item_count': self.total_item_count,
            'completed_count': self.completed_count,
            'reassigned_cycle_count': self.reassigned_cycle_count,
            'escalated_cycle_count': self.escalated_cycle_count,
            'pending_cycle_count': self.pending_cycle_count,
            'returned_to_normal_count': self.returned_to_normal_count,
            'summary_output_path': self.summary_output_path,
            'markdown_output_path': self.markdown_output_path,
            'items': [item.to_payload() for item in self.items],
        }


def build_operator_reentry_completion_request(**kwargs: Any) -> OracleOperatorReentryCompletionRequest:
    kwargs['completion_root'] = Path(kwargs['completion_root']).resolve()
    return OracleOperatorReentryCompletionRequest(**kwargs)


def _normalize(dt: datetime | None) -> datetime:
    value = dt or datetime.now(tz=UTC).replace(microsecond=0)
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.astimezone(UTC).replace(microsecond=0)


def _index_acceptance_items(reentry_acceptance: OracleOperatorReentryAcceptance) -> dict[str, Any]:
    return {item.assignment_key: item for item in reentry_acceptance.items}


def _derive_completion_item(item: Any, acceptance_by_assignment: dict[str, Any], completed_at_utc: datetime) -> OracleOperatorReentryCompletionItem:
    acceptance = acceptance_by_assignment[item.assignment_key]
    assignee_label = item.next_assignee_label
    completion_state = 'REMEDIATION_CYCLE_OPEN'
    evidence_posture = 'EVIDENCE_NOT_YET_DUE'
    evidence_reason_code = 'REMEDIATION_HANDSHAKE_NOT_YET_CLOSED'
    closure_reason_code = 'REMEDIATION_STILL_IN_FLIGHT'
    return_to_normal_state = 'REMEDIATION_REMAINS_OPEN'
    next_queue_lane = item.next_queue_lane
    remediation_reopen_required = False

    if item.reassignment_state == 'NO_REASSIGNMENT_REQUIRED':
        if acceptance.acknowledgement_state in {'ACKNOWLEDGED_ACCEPTED', 'AUTO_ACKNOWLEDGED'}:
            completion_state = 'REMEDIATION_COMPLETED_VERIFIED'
            evidence_posture = 'EVIDENCE_ATTESTED_FOR_COMPLETION'
            evidence_reason_code = 'OWNER_ACKNOWLEDGEMENT_AND_POLICY_COMPLETION'
            closure_reason_code = 'REMEDIATION_COMPLETED_BY_ASSIGNED_OWNER'
            return_to_normal_state = 'RETURNED_TO_NORMAL_OPERATOR_FLOW'
            next_queue_lane = 'OPERATOR_NORMAL_QUEUE'
        else:
            completion_state = 'REMEDIATION_OPEN_PENDING_ACKNOWLEDGEMENT'
            evidence_posture = 'EVIDENCE_PENDING_ASSIGNEE_ACKNOWLEDGEMENT'
            evidence_reason_code = 'ACKNOWLEDGEMENT_REQUIRED_BEFORE_COMPLETION'
            closure_reason_code = 'ASSIGNEE_ACKNOWLEDGEMENT_STILL_PENDING'
            return_to_normal_state = 'REMEDIATION_REMAINS_OPEN'
    elif item.reassignment_state in {'REASSIGNED_TO_BACKUP_OWNER', 'REASSIGNED_TO_HANDOFF_TARGET'}:
        completion_state = 'REMEDIATION_CYCLE_CLOSED_REASSIGNED'
        evidence_posture = 'REASSIGNMENT_EVIDENCE_RECORDED'
        evidence_reason_code = 'OWNERSHIP_FAILURE_AND_REASSIGNMENT_CAPTURED'
        closure_reason_code = item.reassignment_reason_code
        return_to_normal_state = 'RETURNED_TO_REENTRY_QUEUE'
        remediation_reopen_required = True
        next_queue_lane = item.next_queue_lane
    elif item.reassignment_state == 'ESCALATED_TO_SUPERVISOR_REASSIGNMENT':
        completion_state = 'REMEDIATION_CYCLE_ESCALATED'
        evidence_posture = 'ESCALATION_EVIDENCE_RECORDED'
        evidence_reason_code = 'SUPERVISOR_REASSIGNMENT_REQUIRED'
        closure_reason_code = item.reassignment_reason_code
        return_to_normal_state = 'SUPERVISOR_INTERVENTION_REQUIRED'
        remediation_reopen_required = False
        next_queue_lane = item.next_queue_lane
    elif item.reassignment_state == 'REASSIGNMENT_PREPARED':
        completion_state = 'REMEDIATION_CYCLE_PREPARED_FOR_REASSIGNMENT'
        evidence_posture = 'REASSIGNMENT_PREPARATION_RECORDED'
        evidence_reason_code = 'HANDOFF_ESCALATION_PREPARED'
        closure_reason_code = item.reassignment_reason_code
        return_to_normal_state = 'REMEDIATION_REMAINS_OPEN'
        remediation_reopen_required = False
        next_queue_lane = item.next_queue_lane

    return OracleOperatorReentryCompletionItem(
        completion_key=f'completion:{item.reassignment_key}',
        reassignment_key=item.reassignment_key,
        acceptance_key=item.acceptance_key,
        assignment_key=item.assignment_key,
        reentry_key=item.reentry_key,
        work_item_key=item.work_item_key,
        assignee_label=assignee_label,
        remediation_class=item.remediation_class,
        completion_state=completion_state,
        evidence_posture=evidence_posture,
        evidence_reason_code=evidence_reason_code,
        closure_reason_code=closure_reason_code,
        return_to_normal_state=return_to_normal_state,
        next_queue_lane=next_queue_lane,
        remediation_reopen_required=remediation_reopen_required,
        completed_at_utc=completed_at_utc.isoformat(),
    )


def materialize_operator_reentry_completion(
    request: OracleOperatorReentryCompletionRequest,
    *,
    reentry_reassignment: OracleOperatorReentryReassignment | None = None,
    reentry_acceptance: OracleOperatorReentryAcceptance | None = None,
    operator_queue_query_result=None,
    board_label: str = 'default',
) -> OracleOperatorReentryCompletion:
    if reentry_reassignment is None:
        reentry_reassignment = materialize_operator_reentry_reassignment(
            build_operator_reentry_reassignment_request(
                reassignment_root=request.completion_root / 'reentry_reassignment',
                board_label=board_label,
                evaluated_at_utc=request.completed_at_utc,
            ),
            operator_queue_query_result=operator_queue_query_result,
            board_label=board_label,
        )
    if reentry_acceptance is None:
        reentry_acceptance = materialize_operator_reentry_acceptance(
            build_operator_reentry_acceptance_request(
                acceptance_root=request.completion_root / 'reentry_acceptance',
                board_label=board_label,
                accepted_at_utc=request.completed_at_utc,
            ),
            operator_queue_query_result=operator_queue_query_result,
            board_label=board_label,
        )

    completed_at_utc = _normalize(request.completed_at_utc)
    acceptance_by_assignment = _index_acceptance_items(reentry_acceptance)
    items = tuple(_derive_completion_item(item, acceptance_by_assignment, completed_at_utc) for item in reentry_reassignment.items)

    request.completion_root.mkdir(parents=True, exist_ok=True)
    summary_output_path = request.completion_root / 'ORACLE_OPERATOR_REENTRY_COMPLETION.json'
    markdown_output_path = request.completion_root / 'ORACLE_OPERATOR_REENTRY_COMPLETION.md'
    report = OracleOperatorReentryCompletion(
        schema_version='oracle_operator_reentry_completion/v1',
        board_label=reentry_reassignment.board_label,
        completion_root=str(request.completion_root),
        completion_policy=request.completion_policy,
        completed_at_utc=completed_at_utc.isoformat(),
        total_item_count=len(items),
        completed_count=len([item for item in items if item.completion_state == 'REMEDIATION_COMPLETED_VERIFIED']),
        reassigned_cycle_count=len([item for item in items if item.completion_state == 'REMEDIATION_CYCLE_CLOSED_REASSIGNED']),
        escalated_cycle_count=len([item for item in items if item.completion_state == 'REMEDIATION_CYCLE_ESCALATED']),
        pending_cycle_count=len([item for item in items if item.completion_state in {'REMEDIATION_CYCLE_OPEN', 'REMEDIATION_OPEN_PENDING_ACKNOWLEDGEMENT', 'REMEDIATION_CYCLE_PREPARED_FOR_REASSIGNMENT'}]),
        returned_to_normal_count=len([item for item in items if item.return_to_normal_state == 'RETURNED_TO_NORMAL_OPERATOR_FLOW']),
        summary_output_path=str(summary_output_path),
        markdown_output_path=str(markdown_output_path),
        items=items,
    )
    summary_output_path.write_text(json.dumps(report.to_payload(), indent=2) + '\n', encoding='utf-8')
    markdown_output_path.write_text(
        '\n'.join([
            '## Operator Reentry Completion',
            f"- Board label: `{report.board_label}`",
            f"- Completion policy: `{report.completion_policy}`",
            f"- Completed cycles: `{report.completed_count}`",
            f"- Reassigned cycles: `{report.reassigned_cycle_count}`",
            f"- Escalated cycles: `{report.escalated_cycle_count}`",
            f"- Pending cycles: `{report.pending_cycle_count}`",
            f"- Returned to normal: `{report.returned_to_normal_count}`",
            *[
                f"- {item.work_item_key}: {item.completion_state} -> {item.return_to_normal_state} [{item.evidence_posture}]"
                for item in report.items
            ],
            '',
        ]),
        encoding='utf-8',
    )
    return report


__all__ = [
    'OracleOperatorReentryCompletion',
    'OracleOperatorReentryCompletionItem',
    'OracleOperatorReentryCompletionRequest',
    'build_operator_reentry_completion_request',
    'materialize_operator_reentry_completion',
]
