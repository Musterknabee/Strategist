from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from strategy_validator.control_plane.operator_reentry_acknowledgement_timeout import (
    OracleOperatorReentryAcknowledgementTimeout,
    build_operator_reentry_acknowledgement_timeout_request,
    materialize_operator_reentry_acknowledgement_timeout,
)


@dataclass(frozen=True)
class OracleOperatorReentryReassignmentRequest:
    reassignment_root: Path
    board_label: str = 'default'
    backup_assignee_label: str = 'operator-backup'
    supervisor_assignee_label: str = 'supervisor-desk'
    evaluated_at_utc: datetime | None = None


@dataclass(frozen=True)
class OracleOperatorReentryReassignmentItem:
    reassignment_key: str
    timeout_key: str
    acceptance_key: str
    assignment_key: str
    reentry_key: str
    work_item_key: str
    owner_lane: str
    remediation_class: str
    previous_assignee_label: str
    next_assignee_label: str
    handoff_required: bool
    handoff_target: str
    timeout_status: str
    escalation_trigger: str
    reassignment_required: bool
    reassignment_state: str
    reassignment_reason_code: str
    next_queue_lane: str
    evaluated_at_utc: str

    def to_payload(self) -> dict[str, Any]:
        return self.__dict__.copy()


@dataclass(frozen=True)
class OracleOperatorReentryReassignment:
    schema_version: str
    board_label: str
    reassignment_root: str
    evaluated_at_utc: str
    reassignment_count: int
    reassignment_required_count: int
    backup_reassignment_count: int
    supervisor_reassignment_count: int
    unchanged_count: int
    summary_output_path: str
    markdown_output_path: str
    items: tuple[OracleOperatorReentryReassignmentItem, ...]

    def to_payload(self) -> dict[str, Any]:
        return {
            'schema_version': self.schema_version,
            'board_label': self.board_label,
            'reassignment_root': self.reassignment_root,
            'evaluated_at_utc': self.evaluated_at_utc,
            'reassignment_count': self.reassignment_count,
            'reassignment_required_count': self.reassignment_required_count,
            'backup_reassignment_count': self.backup_reassignment_count,
            'supervisor_reassignment_count': self.supervisor_reassignment_count,
            'unchanged_count': self.unchanged_count,
            'summary_output_path': self.summary_output_path,
            'markdown_output_path': self.markdown_output_path,
            'items': [item.to_payload() for item in self.items],
        }


def build_operator_reentry_reassignment_request(**kwargs: Any) -> OracleOperatorReentryReassignmentRequest:
    kwargs['reassignment_root'] = Path(kwargs['reassignment_root']).resolve()
    return OracleOperatorReentryReassignmentRequest(**kwargs)


def _normalize(ts: datetime | None) -> datetime:
    value = ts or datetime.now(tz=UTC).replace(microsecond=0)
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.astimezone(UTC).replace(microsecond=0)


def _derive_item(item: Any, *, request: OracleOperatorReentryReassignmentRequest, evaluated_at_utc: datetime) -> OracleOperatorReentryReassignmentItem:
    reassignment_required = False
    reassignment_state = 'NO_REASSIGNMENT_REQUIRED'
    reassignment_reason_code = 'ACKNOWLEDGEMENT_STILL_WITHIN_POLICY'
    next_assignee_label = item.assignee_label
    next_queue_lane = 'OPERATOR_REMEDIATION_QUEUE'

    if item.timeout_status == 'TIMEOUT_BREACHED':
        reassignment_required = True
        if item.escalation_trigger == 'REASSIGN_TO_BACKUP_OWNER':
            reassignment_state = 'REASSIGNED_TO_BACKUP_OWNER'
            reassignment_reason_code = 'ASSIGNEE_ACK_TIMEOUT_REASSIGNED_TO_BACKUP'
            next_assignee_label = request.backup_assignee_label
        elif item.escalation_trigger == 'ESCALATE_TO_HANDOFF_TARGET':
            reassignment_state = 'REASSIGNED_TO_HANDOFF_TARGET'
            reassignment_reason_code = 'HANDOFF_ACK_TIMEOUT_ESCALATED_TO_TARGET'
            next_assignee_label = item.handoff_target
            next_queue_lane = 'HANDOFF_ESCALATION_QUEUE'
        elif item.escalation_trigger == 'ESCALATE_TO_SUPERVISOR_IMMEDIATELY':
            reassignment_state = 'ESCALATED_TO_SUPERVISOR_REASSIGNMENT'
            reassignment_reason_code = 'BREACH_REMEDIATION_ACK_TIMEOUT_ESCALATED'
            next_assignee_label = request.supervisor_assignee_label
            next_queue_lane = 'SUPERVISOR_ESCALATION_QUEUE'
        else:
            reassignment_required = False
            reassignment_reason_code = 'NO_REASSIGNMENT_POLICY_TRIGGER'
    elif item.timeout_status == 'DUE_SOON' and item.escalation_trigger == 'PREPARE_HANDOFF_ESCALATION':
        reassignment_state = 'REASSIGNMENT_PREPARED'
        reassignment_reason_code = 'HANDOFF_DUE_SOON_PREPARE_ESCALATION'
        next_assignee_label = item.assignee_label
        next_queue_lane = 'OPERATOR_REMEDIATION_QUEUE'

    return OracleOperatorReentryReassignmentItem(
        reassignment_key=f"reassignment:{item.timeout_key}",
        timeout_key=item.timeout_key,
        acceptance_key=item.acceptance_key,
        assignment_key=item.assignment_key,
        reentry_key=item.reentry_key,
        work_item_key=item.work_item_key,
        owner_lane=item.owner_lane,
        remediation_class=item.remediation_class,
        previous_assignee_label=item.assignee_label,
        next_assignee_label=next_assignee_label,
        handoff_required=item.handoff_required,
        handoff_target=item.handoff_target,
        timeout_status=item.timeout_status,
        escalation_trigger=item.escalation_trigger,
        reassignment_required=reassignment_required,
        reassignment_state=reassignment_state,
        reassignment_reason_code=reassignment_reason_code,
        next_queue_lane=next_queue_lane,
        evaluated_at_utc=evaluated_at_utc.isoformat(),
    )


def materialize_operator_reentry_reassignment(
    request: OracleOperatorReentryReassignmentRequest,
    *,
    reentry_acknowledgement_timeout: OracleOperatorReentryAcknowledgementTimeout | None = None,
    operator_queue_query_result=None,
    board_label: str = 'default',
) -> OracleOperatorReentryReassignment:
    if reentry_acknowledgement_timeout is None:
        reentry_acknowledgement_timeout = materialize_operator_reentry_acknowledgement_timeout(
            build_operator_reentry_acknowledgement_timeout_request(
                timeout_root=request.reassignment_root / 'reentry_acknowledgement_timeout',
                board_label=board_label,
                evaluated_at_utc=request.evaluated_at_utc,
            ),
            operator_queue_query_result=operator_queue_query_result,
            board_label=board_label,
        )

    evaluated_at_utc = _normalize(request.evaluated_at_utc)
    items = tuple(
        _derive_item(item, request=request, evaluated_at_utc=evaluated_at_utc)
        for item in reentry_acknowledgement_timeout.items
    )

    request.reassignment_root.mkdir(parents=True, exist_ok=True)
    summary_output_path = request.reassignment_root / 'ORACLE_OPERATOR_REENTRY_REASSIGNMENT.json'
    markdown_output_path = request.reassignment_root / 'ORACLE_OPERATOR_REENTRY_REASSIGNMENT.md'
    report = OracleOperatorReentryReassignment(
        schema_version='oracle_operator_reentry_reassignment/v1',
        board_label=reentry_acknowledgement_timeout.board_label,
        reassignment_root=str(request.reassignment_root),
        evaluated_at_utc=evaluated_at_utc.isoformat(),
        reassignment_count=len(items),
        reassignment_required_count=len([item for item in items if item.reassignment_required]),
        backup_reassignment_count=len([item for item in items if item.reassignment_state == 'REASSIGNED_TO_BACKUP_OWNER']),
        supervisor_reassignment_count=len([item for item in items if item.reassignment_state == 'ESCALATED_TO_SUPERVISOR_REASSIGNMENT']),
        unchanged_count=len([item for item in items if item.reassignment_state == 'NO_REASSIGNMENT_REQUIRED']),
        summary_output_path=str(summary_output_path),
        markdown_output_path=str(markdown_output_path),
        items=items,
    )
    summary_output_path.write_text(json.dumps(report.to_payload(), indent=2) + '\n', encoding='utf-8')
    markdown_output_path.write_text(
        '\n'.join([
            '## Operator Reentry Reassignment',
            f"- Board label: `{report.board_label}`" ,
            f"- Evaluated at: `{report.evaluated_at_utc}`" ,
            f"- Reassignment required: `{report.reassignment_required_count}` / `{report.reassignment_count}`" ,
            f"- Backup reassignments: `{report.backup_reassignment_count}`" ,
            f"- Supervisor reassignments: `{report.supervisor_reassignment_count}`" ,
            *[
                f"- {item.work_item_key}: {item.previous_assignee_label} -> {item.next_assignee_label} [{item.reassignment_state}]"
                for item in report.items
            ],
            '',
        ]),
        encoding='utf-8',
    )
    return report


__all__ = [
    'OracleOperatorReentryReassignment',
    'OracleOperatorReentryReassignmentItem',
    'OracleOperatorReentryReassignmentRequest',
    'build_operator_reentry_reassignment_request',
    'materialize_operator_reentry_reassignment',
]
