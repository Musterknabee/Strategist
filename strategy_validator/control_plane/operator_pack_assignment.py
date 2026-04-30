from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

from strategy_validator.control_plane.operator_pack_escalation import (
    OracleOperatorPackEscalation,
    OracleOperatorPackEscalationItem,
    OracleOperatorPackEscalationRequest,
    build_operator_pack_escalation_request,
    materialize_operator_pack_escalation,
)
from strategy_validator.control_plane.operator_workboard import OracleOperatorWorkboard


@dataclass(frozen=True)
class OracleOperatorPackAssignmentRequest:
    search_root: Path
    repo_root: Path | None = None
    current_pack_kind: str | None = None
    pack_kinds: tuple[str, ...] = ()
    trust_statuses: tuple[str, ...] = ()
    summary_line_contains: str | None = None
    output_artifact_label_contains: str | None = None
    max_items: int = 4
    sustained_degraded_threshold: int = 2
    queue_key: str | None = None
    review_target: str | None = None
    priority_band: str | None = None
    action_owner_lane: str | None = None
    board_label: str | None = None
    backup_owner_lane: str | None = None
    owner_label_prefix: str | None = None


@dataclass(frozen=True)
class OracleOperatorPackAssignmentItem:
    pack_kind: str
    escalation_posture: str
    ownership_posture: str
    owner_lane: str
    backup_owner_lane: str
    owner_label: str
    handoff_target: str
    queue_key: str | None
    review_target: str
    priority_band: str
    board_label: str | None
    latest_trust_status: str | None
    previous_trust_status: str | None
    latest_summary_line: str | None
    previous_summary_line: str | None
    latest_manifest_path: Path
    previous_manifest_path: Path | None
    recommended_actions: tuple[str, ...]
    is_current_pack_kind: bool


@dataclass(frozen=True)
class OracleOperatorPackAssignment:
    schema_version: str
    search_root: str
    current_pack_kind: str | None
    queue_key: str | None
    review_target: str | None
    priority_band: str | None
    board_label: str | None
    total_assignment_count: int
    items: tuple[OracleOperatorPackAssignmentItem, ...]

    def to_payload(self) -> dict[str, Any]:
        return {
            'schema_version': self.schema_version,
            'search_root': self.search_root,
            'current_pack_kind': self.current_pack_kind,
            'queue_key': self.queue_key,
            'review_target': self.review_target,
            'priority_band': self.priority_band,
            'board_label': self.board_label,
            'total_assignment_count': self.total_assignment_count,
            'item_count': len(self.items),
            'items': [
                {
                    'pack_kind': item.pack_kind,
                    'escalation_posture': item.escalation_posture,
                    'ownership_posture': item.ownership_posture,
                    'owner_lane': item.owner_lane,
                    'backup_owner_lane': item.backup_owner_lane,
                    'owner_label': item.owner_label,
                    'handoff_target': item.handoff_target,
                    'queue_key': item.queue_key,
                    'review_target': item.review_target,
                    'priority_band': item.priority_band,
                    'board_label': item.board_label,
                    'latest_trust_status': item.latest_trust_status,
                    'previous_trust_status': item.previous_trust_status,
                    'latest_summary_line': item.latest_summary_line,
                    'previous_summary_line': item.previous_summary_line,
                    'latest_manifest_path': str(item.latest_manifest_path),
                    'previous_manifest_path': str(item.previous_manifest_path) if item.previous_manifest_path else None,
                    'recommended_actions': list(item.recommended_actions),
                    'is_current_pack_kind': item.is_current_pack_kind,
                }
                for item in self.items
            ],
        }


def build_operator_pack_assignment_request(
    *,
    search_root: Path,
    repo_root: Path | None = None,
    current_pack_kind: str | None = None,
    pack_kinds: Sequence[str] = (),
    trust_statuses: Sequence[str] = (),
    summary_line_contains: str | None = None,
    output_artifact_label_contains: str | None = None,
    max_items: int = 4,
    sustained_degraded_threshold: int = 2,
    queue_key: str | None = None,
    review_target: str | None = None,
    priority_band: str | None = None,
    action_owner_lane: str | None = None,
    board_label: str | None = None,
    backup_owner_lane: str | None = None,
    owner_label_prefix: str | None = None,
) -> OracleOperatorPackAssignmentRequest:
    return OracleOperatorPackAssignmentRequest(
        search_root=search_root.resolve(),
        repo_root=repo_root.resolve() if repo_root is not None else None,
        current_pack_kind=current_pack_kind or None,
        pack_kinds=tuple(item for item in pack_kinds if item),
        trust_statuses=tuple(item for item in trust_statuses if item),
        summary_line_contains=summary_line_contains or None,
        output_artifact_label_contains=output_artifact_label_contains or None,
        max_items=max(1, int(max_items)),
        sustained_degraded_threshold=max(2, int(sustained_degraded_threshold)),
        queue_key=queue_key or None,
        review_target=review_target or None,
        priority_band=priority_band or None,
        action_owner_lane=action_owner_lane or None,
        board_label=board_label or None,
        backup_owner_lane=backup_owner_lane or None,
        owner_label_prefix=owner_label_prefix or None,
    )


def _infer_backup_owner_lane(pack_kind: str, owner_lane: str, explicit: str | None) -> str:
    if explicit:
        return explicit
    defaults = {
        'incident_pack': 'governance_ops',
        'status_pack': 'research_ops',
        'briefing_pack': 'governance_ops',
    }
    return defaults.get(pack_kind, 'operator_support') if defaults.get(pack_kind, 'operator_support') != owner_lane else 'operator_support'


def _ownership_posture(item: OracleOperatorPackEscalationItem) -> str:
    if item.escalation_posture == 'IMMEDIATE_OPERATOR_REVIEW':
        return 'ASSIGN_IMMEDIATE_OWNER'
    if item.escalation_posture == 'EXPEDITED_QUEUE_REVIEW':
        return 'ASSIGN_QUEUE_OWNER'
    return 'RETAIN_WATCH_OWNER'


def _build_owner_label(*, owner_lane: str, routing_target: str, prefix: str | None) -> str:
    base = f'{owner_lane}:{routing_target}'
    return f'{prefix}/{base}' if prefix else base


def _build_handoff_target(item: OracleOperatorPackEscalationItem, owner_lane: str) -> str:
    if item.queue_key:
        return f'{owner_lane}:{item.queue_key}'
    return f'{owner_lane}:{item.routing_target}'


def _compose_actions(
    item: OracleOperatorPackEscalationItem,
    *,
    owner_lane: str,
    backup_owner_lane: str,
    owner_label: str,
    handoff_target: str,
) -> tuple[str, ...]:
    actions = [
        f'Assign `{item.pack_kind}` to `{owner_label}` via `{handoff_target}`.',
        f'Keep backup coverage on `{backup_owner_lane}` if `{owner_lane}` cannot accept the handoff.',
    ]
    actions.extend(item.recommended_actions)
    return tuple(actions)


def materialize_operator_pack_assignment(
    request: OracleOperatorPackAssignmentRequest,
    *,
    escalation: OracleOperatorPackEscalation | None = None,
    escalation_request: OracleOperatorPackEscalationRequest | None = None,
    operator_workboard: OracleOperatorWorkboard | None = None,
) -> OracleOperatorPackAssignment:
    if escalation is None:
        escalation = materialize_operator_pack_escalation(
            escalation_request
            or build_operator_pack_escalation_request(
                search_root=request.search_root,
                repo_root=request.repo_root,
                current_pack_kind=request.current_pack_kind,
                pack_kinds=request.pack_kinds,
                trust_statuses=request.trust_statuses,
                summary_line_contains=request.summary_line_contains,
                output_artifact_label_contains=request.output_artifact_label_contains,
                max_items=request.max_items,
                sustained_degraded_threshold=request.sustained_degraded_threshold,
                queue_key=request.queue_key or getattr(operator_workboard, 'queue_key', None),
                review_target=request.review_target or getattr(operator_workboard, 'review_target', None),
                priority_band=request.priority_band or getattr(operator_workboard, 'priority_band', None),
                action_owner_lane=request.action_owner_lane or ((operator_workboard.entries[0].action_owner_lane if getattr(operator_workboard, 'entries', None) else None)),
                board_label=request.board_label or getattr(operator_workboard, 'board_label', None),
            )
        )
    items: list[OracleOperatorPackAssignmentItem] = []
    for escalation_item in escalation.items[: request.max_items]:
        owner_lane = request.action_owner_lane or escalation_item.routing_lane
        backup_owner_lane = _infer_backup_owner_lane(escalation_item.pack_kind, owner_lane, request.backup_owner_lane)
        owner_label = _build_owner_label(owner_lane=owner_lane, routing_target=escalation_item.routing_target, prefix=request.owner_label_prefix)
        handoff_target = _build_handoff_target(escalation_item, owner_lane)
        items.append(
            OracleOperatorPackAssignmentItem(
                pack_kind=escalation_item.pack_kind,
                escalation_posture=escalation_item.escalation_posture,
                ownership_posture=_ownership_posture(escalation_item),
                owner_lane=owner_lane,
                backup_owner_lane=backup_owner_lane,
                owner_label=owner_label,
                handoff_target=handoff_target,
                queue_key=escalation_item.queue_key,
                review_target=escalation_item.routing_target,
                priority_band=escalation_item.priority_band,
                board_label=escalation_item.board_label,
                latest_trust_status=escalation_item.latest_trust_status,
                previous_trust_status=escalation_item.previous_trust_status,
                latest_summary_line=escalation_item.latest_summary_line,
                previous_summary_line=escalation_item.previous_summary_line,
                latest_manifest_path=escalation_item.latest_manifest_path,
                previous_manifest_path=escalation_item.previous_manifest_path,
                recommended_actions=_compose_actions(
                    escalation_item,
                    owner_lane=owner_lane,
                    backup_owner_lane=backup_owner_lane,
                    owner_label=owner_label,
                    handoff_target=handoff_target,
                ),
                is_current_pack_kind=escalation_item.is_current_pack_kind,
            )
        )
    return OracleOperatorPackAssignment(
        schema_version='oracle_operator_pack_assignment/v1',
        search_root=str(request.search_root),
        current_pack_kind=request.current_pack_kind,
        queue_key=request.queue_key or getattr(operator_workboard, 'queue_key', None),
        review_target=request.review_target or getattr(operator_workboard, 'review_target', None),
        priority_band=request.priority_band or getattr(operator_workboard, 'priority_band', None),
        board_label=request.board_label or getattr(operator_workboard, 'board_label', None),
        total_assignment_count=len(items),
        items=tuple(items),
    )


def render_operator_pack_assignment_markdown_lines(assignment: OracleOperatorPackAssignment) -> list[str]:
    lines = ['## Operator Pack Assignments']
    if not assignment.items:
        return lines + ['- No operator pack ownership recommendations are currently active.', '']
    for item in assignment.items:
        lines.extend([
            f"- `{item.pack_kind}` → `{item.owner_label}` ({item.ownership_posture}; backup=`{item.backup_owner_lane}`; handoff=`{item.handoff_target}`)",
            f"  - Trust: latest=`{item.latest_trust_status or 'unknown'}` previous=`{item.previous_trust_status or 'unknown'}`",
            f"  - Summary: {item.latest_summary_line or 'No latest summary recorded.'}",
        ])
        if item.recommended_actions:
            lines.append('  - Recommended actions:')
            lines.extend([f'    - {action}' for action in item.recommended_actions])
    lines.append('')
    return lines


__all__ = [
    'OracleOperatorPackAssignmentRequest',
    'OracleOperatorPackAssignmentItem',
    'OracleOperatorPackAssignment',
    'build_operator_pack_assignment_request',
    'materialize_operator_pack_assignment',
    'render_operator_pack_assignment_markdown_lines',
]
