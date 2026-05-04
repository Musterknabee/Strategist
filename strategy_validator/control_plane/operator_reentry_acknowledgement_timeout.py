from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from strategy_validator.control_plane.operator_reentry_acceptance import (
    OracleOperatorReentryAcceptance,
    build_operator_reentry_acceptance_request,
    materialize_operator_reentry_acceptance,
)


@dataclass(frozen=True)
class OracleOperatorReentryAcknowledgementTimeoutRequest:
    timeout_root: Path
    board_label: str = 'default'
    evaluated_at_utc: datetime | None = None


@dataclass(frozen=True)
class OracleOperatorReentryAcknowledgementTimeoutItem:
    timeout_key: str
    acceptance_key: str
    assignment_key: str
    reentry_key: str
    work_item_key: str
    owner_lane: str
    assignee_label: str
    remediation_class: str
    acknowledgement_state: str
    handoff_required: bool
    handoff_target: str
    timeout_policy: str
    timeout_window_minutes: int
    timeout_due_by_utc: str | None
    timeout_status: str
    reminder_state: str
    escalation_trigger: str
    policy_reason_code: str
    next_action: str
    evaluated_at_utc: str

    def to_payload(self) -> dict[str, Any]:
        return self.__dict__.copy()


@dataclass(frozen=True)
class OracleOperatorReentryAcknowledgementTimeout:
    schema_version: str
    board_label: str
    timeout_root: str
    evaluated_at_utc: str
    total_item_count: int
    pending_item_count: int
    due_soon_count: int
    timed_out_count: int
    reminder_required_count: int
    escalation_required_count: int
    summary_output_path: str
    markdown_output_path: str
    items: tuple[OracleOperatorReentryAcknowledgementTimeoutItem, ...]

    def to_payload(self) -> dict[str, Any]:
        return {
            'schema_version': self.schema_version,
            'board_label': self.board_label,
            'timeout_root': self.timeout_root,
            'evaluated_at_utc': self.evaluated_at_utc,
            'total_item_count': self.total_item_count,
            'pending_item_count': self.pending_item_count,
            'due_soon_count': self.due_soon_count,
            'timed_out_count': self.timed_out_count,
            'reminder_required_count': self.reminder_required_count,
            'escalation_required_count': self.escalation_required_count,
            'summary_output_path': self.summary_output_path,
            'markdown_output_path': self.markdown_output_path,
            'items': [item.to_payload() for item in self.items],
        }


def build_operator_reentry_acknowledgement_timeout_request(**kwargs: Any) -> OracleOperatorReentryAcknowledgementTimeoutRequest:
    kwargs['timeout_root'] = Path(kwargs['timeout_root']).resolve()
    return OracleOperatorReentryAcknowledgementTimeoutRequest(**kwargs)


def _normalize(dt: datetime | None) -> datetime:
    value = dt or datetime.now(tz=UTC).replace(microsecond=0)
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.astimezone(UTC).replace(microsecond=0)


def _timeout_window_minutes(remediation_class: str, handoff_required: bool) -> int:
    if remediation_class == 'BREACH_REMEDIATION':
        return 10
    if remediation_class == 'CLAIM_REPAIR':
        return 30
    if remediation_class == 'DISPATCH_REPAIR':
        return 45
    return 60 if handoff_required else 120


def _age_acceptance(item, evaluated_at_utc: datetime) -> OracleOperatorReentryAcknowledgementTimeoutItem:
    if item.acknowledgement_state != 'ACKNOWLEDGEMENT_PENDING':
        return OracleOperatorReentryAcknowledgementTimeoutItem(
            timeout_key=f'timeout:{item.acceptance_key}',
            acceptance_key=item.acceptance_key,
            assignment_key=item.assignment_key,
            reentry_key=item.reentry_key,
            work_item_key=item.work_item_key,
            owner_lane=item.owner_lane,
            assignee_label=item.assignee_label,
            remediation_class=item.remediation_class,
            acknowledgement_state=item.acknowledgement_state,
            handoff_required=item.handoff_required,
            handoff_target=item.handoff_target,
            timeout_policy='NO_ACK_TIMEOUT_REQUIRED',
            timeout_window_minutes=0,
            timeout_due_by_utc=None,
            timeout_status='NO_TIMEOUT_REQUIRED',
            reminder_state='NO_REMINDER_REQUIRED',
            escalation_trigger='NO_ESCALATION_TRIGGER',
            policy_reason_code='ACKNOWLEDGEMENT_ALREADY_RECORDED',
            next_action='PROCEED_WITH_REMEDIATION',
            evaluated_at_utc=evaluated_at_utc.isoformat(),
        )

    start_at = _normalize(datetime.fromisoformat(item.acknowledgement_recorded_at_utc))
    window_minutes = _timeout_window_minutes(item.remediation_class, item.handoff_required)
    due_by = start_at + timedelta(minutes=window_minutes)
    remaining_minutes = int((due_by - evaluated_at_utc).total_seconds() // 60)

    timeout_status = 'WITHIN_TIMEOUT'
    reminder_state = 'NO_REMINDER_REQUIRED'
    escalation_trigger = 'WAIT_FOR_ACKNOWLEDGEMENT'
    policy_reason_code = 'ACKNOWLEDGEMENT_WAIT_WINDOW_OPEN'
    next_action = 'WAIT_FOR_ASSIGNEE_ACKNOWLEDGEMENT'

    if remaining_minutes < 0:
        timeout_status = 'TIMEOUT_BREACHED'
        reminder_state = 'REMINDER_OVERDUE'
        if item.remediation_class == 'BREACH_REMEDIATION':
            escalation_trigger = 'ESCALATE_TO_SUPERVISOR_IMMEDIATELY'
            policy_reason_code = 'BREACH_REMEDIATION_ACK_TIMEOUT'
            next_action = 'ESCALATE_PENDING_ACKNOWLEDGEMENT_TO_SUPERVISOR'
        elif item.handoff_required:
            escalation_trigger = 'ESCALATE_TO_HANDOFF_TARGET'
            policy_reason_code = 'HANDOFF_ACK_TIMEOUT'
            next_action = f'ESCALATE_PENDING_ACKNOWLEDGEMENT_TO_{item.handoff_target}'
        else:
            escalation_trigger = 'REASSIGN_TO_BACKUP_OWNER'
            policy_reason_code = 'ASSIGNEE_ACK_TIMEOUT'
            next_action = 'REASSIGN_PENDING_REMEDIATION_TO_BACKUP_OWNER'
    elif remaining_minutes <= 15:
        timeout_status = 'DUE_SOON'
        reminder_state = 'REMINDER_REQUIRED'
        if item.handoff_required:
            escalation_trigger = 'PREPARE_HANDOFF_ESCALATION'
            policy_reason_code = 'HANDOFF_ACK_DUE_SOON'
            next_action = f'SEND_REMINDER_AND_PREPARE_{item.handoff_target}'
        else:
            escalation_trigger = 'SEND_REMINDER_TO_ASSIGNEE'
            policy_reason_code = 'ASSIGNEE_ACK_DUE_SOON'
            next_action = 'SEND_ASSIGNEE_ACKNOWLEDGEMENT_REMINDER'

    return OracleOperatorReentryAcknowledgementTimeoutItem(
        timeout_key=f'timeout:{item.acceptance_key}',
        acceptance_key=item.acceptance_key,
        assignment_key=item.assignment_key,
        reentry_key=item.reentry_key,
        work_item_key=item.work_item_key,
        owner_lane=item.owner_lane,
        assignee_label=item.assignee_label,
        remediation_class=item.remediation_class,
        acknowledgement_state=item.acknowledgement_state,
        handoff_required=item.handoff_required,
        handoff_target=item.handoff_target,
        timeout_policy='REENTRY_ACKNOWLEDGEMENT_TIMEOUT_POLICY',
        timeout_window_minutes=window_minutes,
        timeout_due_by_utc=due_by.isoformat(),
        timeout_status=timeout_status,
        reminder_state=reminder_state,
        escalation_trigger=escalation_trigger,
        policy_reason_code=policy_reason_code,
        next_action=next_action,
        evaluated_at_utc=evaluated_at_utc.isoformat(),
    )


def materialize_operator_reentry_acknowledgement_timeout(
    request: OracleOperatorReentryAcknowledgementTimeoutRequest,
    *,
    reentry_acceptance: OracleOperatorReentryAcceptance | None = None,
    operator_queue_query_result=None,
    board_label: str = 'default',
) -> OracleOperatorReentryAcknowledgementTimeout:
    if reentry_acceptance is None:
        reentry_acceptance = materialize_operator_reentry_acceptance(
            build_operator_reentry_acceptance_request(
                acceptance_root=request.timeout_root / 'reentry_acceptance',
                board_label=board_label,
                accepted_at_utc=request.evaluated_at_utc,
            ),
            operator_queue_query_result=operator_queue_query_result,
            board_label=board_label,
        )

    evaluated_at_utc = _normalize(request.evaluated_at_utc)
    items = tuple(_age_acceptance(item, evaluated_at_utc) for item in reentry_acceptance.items)

    request.timeout_root.mkdir(parents=True, exist_ok=True)
    summary_output_path = request.timeout_root / 'ORACLE_OPERATOR_REENTRY_ACKNOWLEDGEMENT_TIMEOUT.json'
    markdown_output_path = request.timeout_root / 'ORACLE_OPERATOR_REENTRY_ACKNOWLEDGEMENT_TIMEOUT.md'
    report = OracleOperatorReentryAcknowledgementTimeout(
        schema_version='oracle_operator_reentry_acknowledgement_timeout/v1',
        board_label=reentry_acceptance.board_label,
        timeout_root=str(request.timeout_root),
        evaluated_at_utc=evaluated_at_utc.isoformat(),
        total_item_count=len(items),
        pending_item_count=len([item for item in items if item.acknowledgement_state == 'ACKNOWLEDGEMENT_PENDING']),
        due_soon_count=len([item for item in items if item.timeout_status == 'DUE_SOON']),
        timed_out_count=len([item for item in items if item.timeout_status == 'TIMEOUT_BREACHED']),
        reminder_required_count=len([item for item in items if item.reminder_state in {'REMINDER_REQUIRED', 'REMINDER_OVERDUE'}]),
        escalation_required_count=len([
            item for item in items if item.escalation_trigger not in {
                'NO_ESCALATION_TRIGGER', 'WAIT_FOR_ACKNOWLEDGEMENT', 'SEND_REMINDER_TO_ASSIGNEE'
            }
        ]),
        summary_output_path=str(summary_output_path),
        markdown_output_path=str(markdown_output_path),
        items=items,
    )
    summary_output_path.write_text(json.dumps(report.to_payload(), indent=2) + '\n', encoding='utf-8')
    markdown_output_path.write_text(
        '\n'.join([
            '## Operator Reentry Acknowledgement Timeout',
            f"- Board label: `{report.board_label}`",
            f"- Evaluated at: `{report.evaluated_at_utc}`",
            f"- Pending items: `{report.pending_item_count}` / `{report.total_item_count}`",
            f"- Due soon: `{report.due_soon_count}`",
            f"- Timed out: `{report.timed_out_count}`",
            *[
                f"- {item.work_item_key}: {item.timeout_status} / {item.reminder_state} -> {item.escalation_trigger}"
                for item in report.items
            ],
            '',
        ]),
        encoding='utf-8',
    )
    return report


__all__ = [
    'OracleOperatorReentryAcknowledgementTimeout',
    'OracleOperatorReentryAcknowledgementTimeoutItem',
    'OracleOperatorReentryAcknowledgementTimeoutRequest',
    'build_operator_reentry_acknowledgement_timeout_request',
    'materialize_operator_reentry_acknowledgement_timeout',
]
