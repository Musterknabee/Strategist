from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from strategy_validator.control_plane.operator_reentry_assignment import (
    OracleOperatorReentryAssignment,
    build_operator_reentry_assignment_request,
    materialize_operator_reentry_assignment,
)


@dataclass(frozen=True)
class OracleOperatorReentryAcceptanceRequest:
    acceptance_root: Path
    board_label: str = 'default'
    acknowledgement_mode: str = 'POLICY_ROUTED'
    accepted_at_utc: datetime | None = None


@dataclass(frozen=True)
class OracleOperatorReentryAcceptanceItem:
    acceptance_key: str
    assignment_key: str
    reentry_key: str
    work_item_key: str
    owner_lane: str
    assignee_label: str
    remediation_class: str
    ownership_status: str
    acceptance_posture: str
    acknowledgement_state: str
    acknowledgement_reason_code: str
    handoff_required: bool
    handoff_target: str
    acknowledgement_recorded_at_utc: str

    def to_payload(self) -> dict[str, Any]:
        return self.__dict__.copy()


@dataclass(frozen=True)
class OracleOperatorReentryAcceptance:
    schema_version: str
    board_label: str
    acceptance_root: str
    acknowledgement_mode: str
    acceptance_count: int
    accepted_count: int
    pending_count: int
    auto_acknowledged_count: int
    handoff_pending_count: int
    summary_output_path: str
    markdown_output_path: str
    items: tuple[OracleOperatorReentryAcceptanceItem, ...]

    def to_payload(self) -> dict[str, Any]:
        return {
            'schema_version': self.schema_version,
            'board_label': self.board_label,
            'acceptance_root': self.acceptance_root,
            'acknowledgement_mode': self.acknowledgement_mode,
            'acceptance_count': self.acceptance_count,
            'accepted_count': self.accepted_count,
            'pending_count': self.pending_count,
            'auto_acknowledged_count': self.auto_acknowledged_count,
            'handoff_pending_count': self.handoff_pending_count,
            'summary_output_path': self.summary_output_path,
            'markdown_output_path': self.markdown_output_path,
            'items': [item.to_payload() for item in self.items],
        }


def build_operator_reentry_acceptance_request(**kwargs: Any) -> OracleOperatorReentryAcceptanceRequest:
    kwargs['acceptance_root'] = Path(kwargs['acceptance_root']).resolve()
    return OracleOperatorReentryAcceptanceRequest(**kwargs)


def _normalize(ts: datetime | None) -> datetime:
    if ts is None:
        return datetime.now(tz=UTC).replace(microsecond=0)
    if ts.tzinfo is None:
        return ts.replace(tzinfo=UTC)
    return ts.astimezone(UTC).replace(microsecond=0)


def _acknowledgement_policy(assignment: Any) -> tuple[str, str]:
    if assignment.acceptance_posture == 'AUTO_ACCEPTED':
        return 'AUTO_ACKNOWLEDGED', 'AUTO_ACCEPTED_BY_ASSIGNMENT_POLICY'
    if assignment.handoff_required:
        return 'ACKNOWLEDGEMENT_PENDING', 'HANDOFF_ACCEPTANCE_REQUIRED'
    if assignment.remediation_class == 'BREACH_REMEDIATION':
        return 'ACKNOWLEDGED_ACCEPTED', 'PRIORITY_BREACH_REMEDIATION_AUTO_ACCEPTED'
    return 'ACKNOWLEDGEMENT_PENDING', 'ASSIGNEE_ACKNOWLEDGEMENT_REQUIRED'


def materialize_operator_reentry_acceptance(
    request: OracleOperatorReentryAcceptanceRequest,
    *,
    reentry_assignment: OracleOperatorReentryAssignment | None = None,
    operator_queue_query_result=None,
    board_label: str = 'default',
) -> OracleOperatorReentryAcceptance:
    if reentry_assignment is None:
        reentry_assignment = materialize_operator_reentry_assignment(
            build_operator_reentry_assignment_request(
                assignment_root=request.acceptance_root / 'reentry_assignment',
                board_label=board_label,
                assigned_at_utc=request.accepted_at_utc,
            ),
            operator_queue_query_result=operator_queue_query_result,
            board_label=board_label,
        )

    accepted_at_utc = _normalize(request.accepted_at_utc)
    items: list[OracleOperatorReentryAcceptanceItem] = []
    for assignment in reentry_assignment.items:
        acknowledgement_state, reason_code = _acknowledgement_policy(assignment)
        items.append(
            OracleOperatorReentryAcceptanceItem(
                acceptance_key=f'acceptance:{assignment.assignment_key}',
                assignment_key=assignment.assignment_key,
                reentry_key=assignment.reentry_key,
                work_item_key=assignment.work_item_key,
                owner_lane=assignment.owner_lane,
                assignee_label=assignment.assignee_label,
                remediation_class=assignment.remediation_class,
                ownership_status=assignment.ownership_status,
                acceptance_posture=assignment.acceptance_posture,
                acknowledgement_state=acknowledgement_state,
                acknowledgement_reason_code=reason_code,
                handoff_required=assignment.handoff_required,
                handoff_target=assignment.handoff_target,
                acknowledgement_recorded_at_utc=accepted_at_utc.isoformat(),
            )
        )

    request.acceptance_root.mkdir(parents=True, exist_ok=True)
    summary_output_path = request.acceptance_root / 'ORACLE_OPERATOR_REENTRY_ACCEPTANCE.json'
    markdown_output_path = request.acceptance_root / 'ORACLE_OPERATOR_REENTRY_ACCEPTANCE.md'
    report = OracleOperatorReentryAcceptance(
        schema_version='oracle_operator_reentry_acceptance/v1',
        board_label=reentry_assignment.board_label,
        acceptance_root=str(request.acceptance_root),
        acknowledgement_mode=request.acknowledgement_mode,
        acceptance_count=len(items),
        accepted_count=len([item for item in items if item.acknowledgement_state == 'ACKNOWLEDGED_ACCEPTED']),
        pending_count=len([item for item in items if item.acknowledgement_state == 'ACKNOWLEDGEMENT_PENDING']),
        auto_acknowledged_count=len([item for item in items if item.acknowledgement_state == 'AUTO_ACKNOWLEDGED']),
        handoff_pending_count=len(
            [item for item in items if item.handoff_required and item.acknowledgement_state == 'ACKNOWLEDGEMENT_PENDING']
        ),
        summary_output_path=str(summary_output_path),
        markdown_output_path=str(markdown_output_path),
        items=tuple(items),
    )
    summary_output_path.write_text(json.dumps(report.to_payload(), indent=2) + '\n', encoding='utf-8')
    markdown_output_path.write_text(
        '\n'.join(
            [
                '## Operator Reentry Acceptance',
                f"- Board label: `{report.board_label}`",
                f"- Acknowledgement mode: `{report.acknowledgement_mode}`",
                f"- Acceptance items: `{report.acceptance_count}`",
                f"- Accepted: `{report.accepted_count}`",
                f"- Pending: `{report.pending_count}`",
                f"- Auto-acknowledged: `{report.auto_acknowledged_count}`",
                *[
                    f"- {item.work_item_key}: {item.assignee_label} -> {item.acknowledgement_state} [{item.acknowledgement_reason_code}]"
                    for item in report.items
                ],
                '',
            ]
        ),
        encoding='utf-8',
    )
    return report


__all__ = [
    'OracleOperatorReentryAcceptance',
    'OracleOperatorReentryAcceptanceItem',
    'OracleOperatorReentryAcceptanceRequest',
    'build_operator_reentry_acceptance_request',
    'materialize_operator_reentry_acceptance',
]
