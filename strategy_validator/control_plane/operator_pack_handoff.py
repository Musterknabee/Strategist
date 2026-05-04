from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

from strategy_validator.control_plane.operator_pack_assignment import (
    OracleOperatorPackAssignment,
    OracleOperatorPackAssignmentItem,
    OracleOperatorPackAssignmentRequest,
    build_operator_pack_assignment_request,
    materialize_operator_pack_assignment,
)
from strategy_validator.control_plane.operator_workboard import OracleOperatorWorkboard


@dataclass(frozen=True)
class OracleOperatorPackHandoffRequest:
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
    ack_owner_lane: str | None = None


@dataclass(frozen=True)
class OracleOperatorPackHandoffItem:
    pack_kind: str
    ownership_posture: str
    handoff_state: str
    acceptance_state: str
    owner_lane: str
    ack_owner_lane: str
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
class OracleOperatorPackHandoff:
    schema_version: str
    search_root: str
    current_pack_kind: str | None
    queue_key: str | None
    review_target: str | None
    priority_band: str | None
    board_label: str | None
    total_handoff_count: int
    items: tuple[OracleOperatorPackHandoffItem, ...]

    def to_payload(self) -> dict[str, Any]:
        return {
            'schema_version': self.schema_version,
            'search_root': self.search_root,
            'current_pack_kind': self.current_pack_kind,
            'queue_key': self.queue_key,
            'review_target': self.review_target,
            'priority_band': self.priority_band,
            'board_label': self.board_label,
            'total_handoff_count': self.total_handoff_count,
            'item_count': len(self.items),
            'items': [
                {
                    'pack_kind': item.pack_kind,
                    'ownership_posture': item.ownership_posture,
                    'handoff_state': item.handoff_state,
                    'acceptance_state': item.acceptance_state,
                    'owner_lane': item.owner_lane,
                    'ack_owner_lane': item.ack_owner_lane,
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


def build_operator_pack_handoff_request(
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
    ack_owner_lane: str | None = None,
) -> OracleOperatorPackHandoffRequest:
    return OracleOperatorPackHandoffRequest(
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
        ack_owner_lane=ack_owner_lane or None,
    )


def _matching_workboard_entry(item: OracleOperatorPackAssignmentItem, operator_workboard: OracleOperatorWorkboard | None):
    if operator_workboard is None:
        return None
    for entry in getattr(operator_workboard, 'entries', ()):
        if item.queue_key and entry.queue_key != item.queue_key:
            continue
        if entry.review_target != item.review_target:
            continue
        if entry.action_owner_lane != item.owner_lane:
            continue
        return entry
    return None


def _handoff_state(item: OracleOperatorPackAssignmentItem, operator_workboard: OracleOperatorWorkboard | None) -> tuple[str, str, str]:
    match = _matching_workboard_entry(item, operator_workboard)
    if match is not None:
        return 'HANDOFF_ACCEPTED', 'ACCEPTED', match.action_owner_lane
    if item.queue_key or item.review_target:
        return 'HANDOFF_PENDING_ACKNOWLEDGEMENT', 'PENDING', item.owner_lane
    return 'HANDOFF_UNCLAIMED', 'UNCLAIMED', item.owner_lane


def _compose_actions(
    item: OracleOperatorPackAssignmentItem,
    *,
    handoff_state: str,
    acceptance_state: str,
    ack_owner_lane: str,
) -> tuple[str, ...]:
    actions = []
    if handoff_state == 'HANDOFF_ACCEPTED':
        actions.append(f'Confirm `{item.pack_kind}` remains with `{ack_owner_lane}` and keep queue progression active.')
    elif handoff_state == 'HANDOFF_PENDING_ACKNOWLEDGEMENT':
        actions.append(f'Request acknowledgement from `{ack_owner_lane}` for `{item.handoff_target}` and record acceptance state in the operator board.')
    else:
        actions.append(f'No owner has claimed `{item.pack_kind}` yet; route handoff through `{item.handoff_target}` or assign backup `{item.backup_owner_lane}`.')
    actions.append(f'Acceptance state is `{acceptance_state}` for `{item.owner_label}`.')
    actions.extend(item.recommended_actions)
    return tuple(actions)


def materialize_operator_pack_handoff(
    request: OracleOperatorPackHandoffRequest,
    *,
    assignment: OracleOperatorPackAssignment | None = None,
    assignment_request: OracleOperatorPackAssignmentRequest | None = None,
    operator_workboard: OracleOperatorWorkboard | None = None,
) -> OracleOperatorPackHandoff:
    if assignment is None:
        assignment = materialize_operator_pack_assignment(
            assignment_request
            or build_operator_pack_assignment_request(
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
                backup_owner_lane=request.backup_owner_lane,
                owner_label_prefix=request.owner_label_prefix,
            ),
            operator_workboard=operator_workboard,
        )
    items = []
    for assignment_item in assignment.items[: request.max_items]:
        handoff_state, acceptance_state, matched_lane = _handoff_state(assignment_item, operator_workboard)
        ack_owner_lane = request.ack_owner_lane or matched_lane or assignment_item.owner_lane
        items.append(
            OracleOperatorPackHandoffItem(
                pack_kind=assignment_item.pack_kind,
                ownership_posture=assignment_item.ownership_posture,
                handoff_state=handoff_state,
                acceptance_state=acceptance_state,
                owner_lane=assignment_item.owner_lane,
                ack_owner_lane=ack_owner_lane,
                backup_owner_lane=assignment_item.backup_owner_lane,
                owner_label=assignment_item.owner_label,
                handoff_target=assignment_item.handoff_target,
                queue_key=assignment_item.queue_key,
                review_target=assignment_item.review_target,
                priority_band=assignment_item.priority_band,
                board_label=assignment_item.board_label,
                latest_trust_status=assignment_item.latest_trust_status,
                previous_trust_status=assignment_item.previous_trust_status,
                latest_summary_line=assignment_item.latest_summary_line,
                previous_summary_line=assignment_item.previous_summary_line,
                latest_manifest_path=assignment_item.latest_manifest_path,
                previous_manifest_path=assignment_item.previous_manifest_path,
                recommended_actions=_compose_actions(
                    assignment_item,
                    handoff_state=handoff_state,
                    acceptance_state=acceptance_state,
                    ack_owner_lane=ack_owner_lane,
                ),
                is_current_pack_kind=assignment_item.is_current_pack_kind,
            )
        )
    return OracleOperatorPackHandoff(
        schema_version='oracle_operator_pack_handoff/v1',
        search_root=str(request.search_root),
        current_pack_kind=request.current_pack_kind,
        queue_key=request.queue_key or getattr(operator_workboard, 'queue_key', None),
        review_target=request.review_target or getattr(operator_workboard, 'review_target', None),
        priority_band=request.priority_band or getattr(operator_workboard, 'priority_band', None),
        board_label=request.board_label or getattr(operator_workboard, 'board_label', None),
        total_handoff_count=len(items),
        items=tuple(items),
    )


def render_operator_pack_handoff_markdown_lines(handoff: OracleOperatorPackHandoff) -> list[str]:
    lines = ['## Operator Pack Handoffs']
    if not handoff.items:
        return lines + ['- No operator pack handoffs are currently active.', '']
    for item in handoff.items:
        lines.extend([
            f"- `{item.pack_kind}` → `{item.owner_label}` ({item.handoff_state}; acceptance=`{item.acceptance_state}`; ack_owner=`{item.ack_owner_lane}`)",
            f"  - Trust: latest=`{item.latest_trust_status or 'unknown'}` previous=`{item.previous_trust_status or 'unknown'}`",
            f"  - Summary: {item.latest_summary_line or 'No latest summary recorded.'}",
        ])
        if item.recommended_actions:
            lines.append('  - Recommended actions:')
            lines.extend([f'    - {action}' for action in item.recommended_actions])
    lines.append('')
    return lines


__all__ = [
    'OracleOperatorPackHandoffRequest',
    'OracleOperatorPackHandoffItem',
    'OracleOperatorPackHandoff',
    'build_operator_pack_handoff_request',
    'materialize_operator_pack_handoff',
    'render_operator_pack_handoff_markdown_lines',
]
