from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from strategy_validator.control_plane.operator_reentry_queue_state import (
    OracleOperatorReentryQueueState,
    build_operator_reentry_queue_state_request,
    materialize_operator_reentry_queue_state,
)


@dataclass(frozen=True)
class OracleOperatorReentryAssignmentRequest:
    assignment_root: Path
    board_label: str = 'default'
    ownership_mode: str = 'CLASS_ROUTED'
    default_assignee_label: str = 'operator-primary'
    fallback_assignee_label: str = 'operator-backup'
    assigned_at_utc: datetime | None = None


@dataclass(frozen=True)
class OracleOperatorReentryAssignmentItem:
    assignment_key: str
    reentry_key: str
    work_item_key: str
    reentry_queue_lane: str
    remediation_class: str
    operator_action_required: str
    owner_lane: str
    assignee_label: str
    ownership_status: str
    acceptance_posture: str
    handoff_required: bool
    handoff_target: str
    assignment_reason_code: str
    assigned_at_utc: str

    def to_payload(self) -> dict[str, Any]:
        return self.__dict__.copy()


@dataclass(frozen=True)
class OracleOperatorReentryAssignment:
    schema_version: str
    board_label: str
    assignment_root: str
    ownership_mode: str
    assignment_count: int
    handoff_required_count: int
    acceptance_required_count: int
    summary_output_path: str
    markdown_output_path: str
    items: tuple[OracleOperatorReentryAssignmentItem, ...]

    def to_payload(self) -> dict[str, Any]:
        return {
            'schema_version': self.schema_version,
            'board_label': self.board_label,
            'assignment_root': self.assignment_root,
            'ownership_mode': self.ownership_mode,
            'assignment_count': self.assignment_count,
            'handoff_required_count': self.handoff_required_count,
            'acceptance_required_count': self.acceptance_required_count,
            'summary_output_path': self.summary_output_path,
            'markdown_output_path': self.markdown_output_path,
            'items': [item.to_payload() for item in self.items],
        }


def build_operator_reentry_assignment_request(**kwargs: Any) -> OracleOperatorReentryAssignmentRequest:
    kwargs['assignment_root'] = Path(kwargs['assignment_root']).resolve()
    return OracleOperatorReentryAssignmentRequest(**kwargs)


def _normalize(ts: datetime | None) -> datetime:
    if ts is None:
        return datetime.now(tz=UTC).replace(microsecond=0)
    if ts.tzinfo is None:
        return ts.replace(tzinfo=UTC)
    return ts.astimezone(UTC).replace(microsecond=0)


def _assignment_policy(remediation_class: str, request: OracleOperatorReentryAssignmentRequest) -> tuple[str, str, str, bool, str, str]:
    if remediation_class == 'CLAIM_REPAIR':
        return ('CLAIM_REMEDIATION_LANE', 'claims-operator', 'ASSIGNED_PENDING_ACCEPTANCE', True, 'CLAIMS_DESK', 'CLAIM_SPECIALIST_REQUIRED')
    if remediation_class == 'DISPATCH_REPAIR':
        return ('DISPATCH_REMEDIATION_LANE', 'dispatch-operator', 'ASSIGNED_PENDING_ACCEPTANCE', True, 'DISPATCH_DESK', 'DISPATCH_GUARD_REPAIR_REQUIRED')
    if remediation_class == 'BREACH_REMEDIATION':
        return ('PRIORITY_REMEDIATION_LANE', 'senior-operator', 'ASSIGNED_PENDING_ACCEPTANCE', True, 'PRIORITY_REVIEW_DESK', 'SLA_BREACH_REMEDIATION_REQUIRED')
    return ('GENERAL_REMEDIATION_LANE', request.default_assignee_label, 'ASSIGNED_READY', False, 'OPERATOR_QUEUE', 'GENERAL_REMEDIATION_ROUTED')


def materialize_operator_reentry_assignment(
    request: OracleOperatorReentryAssignmentRequest,
    *,
    reentry_queue_state: OracleOperatorReentryQueueState | None = None,
    operator_queue_query_result=None,
    board_label: str = 'default',
) -> OracleOperatorReentryAssignment:
    if reentry_queue_state is None:
        reentry_queue_state = materialize_operator_reentry_queue_state(
            build_operator_reentry_queue_state_request(
                reentry_root=request.assignment_root / 'reentry_queue_state',
                board_label=board_label,
                reopened_at_utc=request.assigned_at_utc,
            ),
            operator_queue_query_result=operator_queue_query_result,
            board_label=board_label,
        )

    assigned_at_utc = _normalize(request.assigned_at_utc)
    items: list[OracleOperatorReentryAssignmentItem] = []
    for entry in reentry_queue_state.items:
        owner_lane, assignee_label, ownership_status, handoff_required, handoff_target, reason_code = _assignment_policy(entry.remediation_class, request)
        acceptance_posture = 'ACCEPTANCE_REQUIRED' if ownership_status.endswith('PENDING_ACCEPTANCE') else 'AUTO_ACCEPTED'
        items.append(OracleOperatorReentryAssignmentItem(
            assignment_key=f'assignment:{entry.reentry_key}',
            reentry_key=entry.reentry_key,
            work_item_key=entry.work_item_key,
            reentry_queue_lane=entry.reentry_queue_lane,
            remediation_class=entry.remediation_class,
            operator_action_required=entry.operator_action_required,
            owner_lane=owner_lane,
            assignee_label=assignee_label,
            ownership_status=ownership_status,
            acceptance_posture=acceptance_posture,
            handoff_required=handoff_required,
            handoff_target=handoff_target,
            assignment_reason_code=reason_code,
            assigned_at_utc=assigned_at_utc.isoformat(),
        ))

    request.assignment_root.mkdir(parents=True, exist_ok=True)
    summary_output_path = request.assignment_root / 'ORACLE_OPERATOR_REENTRY_ASSIGNMENT.json'
    markdown_output_path = request.assignment_root / 'ORACLE_OPERATOR_REENTRY_ASSIGNMENT.md'
    report = OracleOperatorReentryAssignment(
        schema_version='oracle_operator_reentry_assignment/v1',
        board_label=reentry_queue_state.board_label,
        assignment_root=str(request.assignment_root),
        ownership_mode=request.ownership_mode,
        assignment_count=len(items),
        handoff_required_count=len([item for item in items if item.handoff_required]),
        acceptance_required_count=len([item for item in items if item.acceptance_posture == 'ACCEPTANCE_REQUIRED']),
        summary_output_path=str(summary_output_path),
        markdown_output_path=str(markdown_output_path),
        items=tuple(items),
    )
    summary_output_path.write_text(json.dumps(report.to_payload(), indent=2) + '\n', encoding='utf-8')
    markdown_output_path.write_text('\n'.join([
        '## Operator Reentry Assignment',
        f"- Board label: `{report.board_label}`",
        f"- Ownership mode: `{report.ownership_mode}`",
        f"- Assignments: `{report.assignment_count}`",
        f"- Handoffs required: `{report.handoff_required_count}`",
        f"- Acceptance required: `{report.acceptance_required_count}`",
        *[
            f"- {item.work_item_key}: {item.assignee_label} [{item.owner_lane}] -> {item.acceptance_posture}"
            for item in report.items
        ],
        '',
    ]), encoding='utf-8')
    return report


__all__ = [
    'OracleOperatorReentryAssignment',
    'OracleOperatorReentryAssignmentItem',
    'OracleOperatorReentryAssignmentRequest',
    'build_operator_reentry_assignment_request',
    'materialize_operator_reentry_assignment',
]
