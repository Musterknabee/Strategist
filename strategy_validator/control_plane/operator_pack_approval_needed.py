from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

from strategy_validator.control_plane.operator_pack_execution_exception import (
    OracleOperatorPackExecutionException,
    OracleOperatorPackExecutionExceptionItem,
    OracleOperatorPackExecutionExceptionRequest,
    build_operator_pack_execution_exception_request,
    materialize_operator_pack_execution_exception,
)
from strategy_validator.control_plane.operator_pack_handoff import (
    OracleOperatorPackHandoff,
    OracleOperatorPackHandoffItem,
    OracleOperatorPackHandoffRequest,
    build_operator_pack_handoff_request,
    materialize_operator_pack_handoff,
)
from strategy_validator.control_plane.operator_workboard import OracleOperatorWorkboard


@dataclass(frozen=True)
class OracleOperatorPackApprovalNeededRequest:
    search_root: Path
    repo_root: Path | None = None
    current_pack_kind: str | None = None
    pack_kinds: tuple[str, ...] = ()
    trust_statuses: tuple[str, ...] = ()
    summary_line_contains: str | None = None
    output_artifact_label_contains: str | None = None
    max_items: int = 3
    sustained_degraded_threshold: int = 2
    queue_key: str | None = None
    review_target: str | None = None
    priority_band: str | None = None
    action_owner_lane: str | None = None
    board_label: str | None = None
    backup_owner_lane: str | None = None
    owner_label_prefix: str | None = None
    ack_owner_lane: str | None = None
    lease_label_prefix: str | None = None
    lifecycle_label_prefix: str | None = None
    governance_label_prefix: str | None = None
    readiness_label_prefix: str | None = None
    dispatch_label_prefix: str | None = None
    outcome_label_prefix: str | None = None
    exception_label_prefix: str | None = None
    approval_label_prefix: str | None = None


@dataclass(frozen=True)
class OracleOperatorPackApprovalNeededItem:
    pack_kind: str
    exception_posture: str
    override_state: str
    handoff_state: str
    acceptance_state: str
    approval_posture: str
    approval_state: str
    approval_action: str
    memo_key: str
    memo_label: str
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
class OracleOperatorPackApprovalNeeded:
    schema_version: str
    search_root: str
    current_pack_kind: str | None
    queue_key: str | None
    review_target: str | None
    priority_band: str | None
    board_label: str | None
    total_approval_count: int
    items: tuple[OracleOperatorPackApprovalNeededItem, ...]

    def to_payload(self) -> dict[str, Any]:
        return {
            'schema_version': self.schema_version,
            'search_root': self.search_root,
            'current_pack_kind': self.current_pack_kind,
            'queue_key': self.queue_key,
            'review_target': self.review_target,
            'priority_band': self.priority_band,
            'board_label': self.board_label,
            'total_approval_count': self.total_approval_count,
            'item_count': len(self.items),
            'items': [
                {
                    'pack_kind': item.pack_kind,
                    'exception_posture': item.exception_posture,
                    'override_state': item.override_state,
                    'handoff_state': item.handoff_state,
                    'acceptance_state': item.acceptance_state,
                    'approval_posture': item.approval_posture,
                    'approval_state': item.approval_state,
                    'approval_action': item.approval_action,
                    'memo_key': item.memo_key,
                    'memo_label': item.memo_label,
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


def build_operator_pack_approval_needed_request(*, search_root: Path, repo_root: Path | None = None, current_pack_kind: str | None = None, pack_kinds: Sequence[str] = (), trust_statuses: Sequence[str] = (), summary_line_contains: str | None = None, output_artifact_label_contains: str | None = None, max_items: int = 3, sustained_degraded_threshold: int = 2, queue_key: str | None = None, review_target: str | None = None, priority_band: str | None = None, action_owner_lane: str | None = None, board_label: str | None = None, backup_owner_lane: str | None = None, owner_label_prefix: str | None = None, ack_owner_lane: str | None = None, lease_label_prefix: str | None = None, lifecycle_label_prefix: str | None = None, governance_label_prefix: str | None = None, readiness_label_prefix: str | None = None, dispatch_label_prefix: str | None = None, outcome_label_prefix: str | None = None, exception_label_prefix: str | None = None, approval_label_prefix: str | None = None) -> OracleOperatorPackApprovalNeededRequest:
    return OracleOperatorPackApprovalNeededRequest(
        search_root=search_root.resolve(),
        repo_root=repo_root.resolve() if repo_root is not None else None,
        current_pack_kind=current_pack_kind or None,
        pack_kinds=tuple(i for i in pack_kinds if i),
        trust_statuses=tuple(i for i in trust_statuses if i),
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
        lease_label_prefix=lease_label_prefix or None,
        lifecycle_label_prefix=lifecycle_label_prefix or None,
        governance_label_prefix=governance_label_prefix or None,
        readiness_label_prefix=readiness_label_prefix or None,
        dispatch_label_prefix=dispatch_label_prefix or None,
        outcome_label_prefix=outcome_label_prefix or None,
        exception_label_prefix=exception_label_prefix or None,
        approval_label_prefix=approval_label_prefix or None,
    )


def _matching_handoff(exception_item: OracleOperatorPackExecutionExceptionItem, handoff: OracleOperatorPackHandoff | None) -> OracleOperatorPackHandoffItem | None:
    if handoff is None:
        return None
    for item in handoff.items:
        if item.pack_kind != exception_item.pack_kind:
            continue
        if item.latest_manifest_path != exception_item.latest_manifest_path:
            continue
        return item
    return next((item for item in handoff.items if item.pack_kind == exception_item.pack_kind), None)


def _classify_approval(exception_item: OracleOperatorPackExecutionExceptionItem, handoff_item: OracleOperatorPackHandoffItem | None) -> tuple[str, str, str]:
    if exception_item.exception_posture == 'NO_OVERRIDE_REQUIRED':
        return 'NO_APPROVAL_NEEDED', 'NO_APPROVAL_REQUIRED', 'PROCEED_WITHOUT_APPROVAL'
    if exception_item.exception_posture == 'OVERRIDE_NEEDED':
        return 'APPROVAL_REQUIRED', 'APPROVAL_REQUIRED', 'ESCALATE_FOR_APPROVAL'
    acceptance = handoff_item.acceptance_state if handoff_item is not None else 'UNCLAIMED'
    if acceptance == 'ACCEPTED':
        return 'APPROVAL_REQUIRED', 'APPROVAL_REQUIRED', 'ESCALATE_FOR_APPROVAL'
    return 'APPROVAL_ELIGIBLE', 'APPROVAL_REVIEW_ELIGIBLE', 'REQUEST_APPROVAL_REVIEW'


def _memo_key(item: OracleOperatorPackExecutionExceptionItem, approval_state: str) -> str:
    return '::'.join((item.pack_kind, approval_state, item.override_state, item.queue_key or 'no-queue'))


def _compose_actions(exception_item: OracleOperatorPackExecutionExceptionItem, *, handoff_item: OracleOperatorPackHandoffItem | None, approval_posture: str, approval_action: str, memo_label: str) -> tuple[str, ...]:
    actions: list[str] = []
    if approval_posture == 'NO_APPROVAL_NEEDED':
        actions.append(f'Proceed without formal approval for `{exception_item.pack_kind}` and retain `{memo_label}` as the current memo state.')
    elif approval_posture == 'APPROVAL_REQUIRED':
        actions.append(f'Escalate `{exception_item.pack_kind}` for formal approval using `{memo_label}` before any exception-backed execution proceeds.')
    else:
        actions.append(f'Request approval review for `{exception_item.pack_kind}` using `{memo_label}` and confirm exception handling scope before execution proceeds.')
    if handoff_item is not None:
        actions.append(f'Approval path is currently tied to `{handoff_item.owner_label}` with handoff state `{handoff_item.handoff_state}`.')
        actions.extend(handoff_item.recommended_actions)
    actions.extend(exception_item.recommended_actions)
    # de-dupe preserve order
    seen = []
    for a in actions:
        if a not in seen:
            seen.append(a)
    return tuple(seen)


def materialize_operator_pack_approval_needed(request: OracleOperatorPackApprovalNeededRequest, *, execution_exception: OracleOperatorPackExecutionException | None = None, execution_exception_request: OracleOperatorPackExecutionExceptionRequest | None = None, handoff: OracleOperatorPackHandoff | None = None, handoff_request: OracleOperatorPackHandoffRequest | None = None, operator_workboard: OracleOperatorWorkboard | None = None) -> OracleOperatorPackApprovalNeeded:
    if execution_exception is None:
        execution_exception = materialize_operator_pack_execution_exception(
            execution_exception_request or build_operator_pack_execution_exception_request(
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
                ack_owner_lane=request.ack_owner_lane,
                lease_label_prefix=request.lease_label_prefix,
                lifecycle_label_prefix=request.lifecycle_label_prefix,
                governance_label_prefix=request.governance_label_prefix,
                readiness_label_prefix=request.readiness_label_prefix,
                dispatch_label_prefix=request.dispatch_label_prefix,
                outcome_label_prefix=request.outcome_label_prefix,
                exception_label_prefix=request.exception_label_prefix,
            ),
            operator_workboard=operator_workboard,
        )
    if handoff is None:
        handoff = materialize_operator_pack_handoff(
            handoff_request or build_operator_pack_handoff_request(
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
                ack_owner_lane=request.ack_owner_lane,
            ),
            operator_workboard=operator_workboard,
        )
    items: list[OracleOperatorPackApprovalNeededItem] = []
    for exception_item in execution_exception.items:
        handoff_item = _matching_handoff(exception_item, handoff)
        approval_posture, approval_state, approval_action = _classify_approval(exception_item, handoff_item)
        memo_label = f"{request.approval_label_prefix or 'approval'}:{exception_item.pack_kind}:{approval_state.lower()}"
        items.append(OracleOperatorPackApprovalNeededItem(
            pack_kind=exception_item.pack_kind,
            exception_posture=exception_item.exception_posture,
            override_state=exception_item.override_state,
            handoff_state=handoff_item.handoff_state if handoff_item is not None else 'HANDOFF_UNCLAIMED',
            acceptance_state=handoff_item.acceptance_state if handoff_item is not None else 'UNCLAIMED',
            approval_posture=approval_posture,
            approval_state=approval_state,
            approval_action=approval_action,
            memo_key=_memo_key(exception_item, approval_state),
            memo_label=memo_label,
            owner_lane=handoff_item.owner_lane if handoff_item is not None else exception_item.owner_lane,
            ack_owner_lane=handoff_item.ack_owner_lane if handoff_item is not None else exception_item.ack_owner_lane,
            backup_owner_lane=handoff_item.backup_owner_lane if handoff_item is not None else 'operator_support',
            owner_label=handoff_item.owner_label if handoff_item is not None else f"{exception_item.owner_lane}:{exception_item.routing_target}",
            handoff_target=handoff_item.handoff_target if handoff_item is not None else f"{exception_item.owner_lane}:{exception_item.routing_target}",
            queue_key=exception_item.queue_key,
            review_target=exception_item.review_target,
            priority_band=exception_item.priority_band,
            board_label=exception_item.board_label,
            latest_trust_status=exception_item.latest_trust_status,
            previous_trust_status=exception_item.previous_trust_status,
            latest_summary_line=exception_item.latest_summary_line,
            previous_summary_line=exception_item.previous_summary_line,
            latest_manifest_path=exception_item.latest_manifest_path,
            previous_manifest_path=exception_item.previous_manifest_path,
            recommended_actions=_compose_actions(exception_item, handoff_item=handoff_item, approval_posture=approval_posture, approval_action=approval_action, memo_label=memo_label),
            is_current_pack_kind=exception_item.is_current_pack_kind,
        ))
    return OracleOperatorPackApprovalNeeded(
        schema_version='oracle_operator_pack_approval_needed/v1',
        search_root=str(request.search_root),
        current_pack_kind=request.current_pack_kind,
        queue_key=request.queue_key,
        review_target=request.review_target,
        priority_band=request.priority_band,
        board_label=request.board_label,
        total_approval_count=len(items),
        items=tuple(items),
    )


def render_operator_pack_approval_needed_markdown_lines(approval_needed: OracleOperatorPackApprovalNeeded) -> list[str]:
    lines = ['## Operator Pack Approval Needed']
    if not approval_needed.items:
        lines.append('- No operator-pack approval-needed states matched the current filters.')
        return lines
    for item in approval_needed.items:
        lines.extend([
            f"- `{item.pack_kind}` → `{item.approval_posture}` / `{item.approval_state}`",
            f"  - Approval action: `{item.approval_action}`",
            f"  - Exception posture: `{item.exception_posture}` / `{item.override_state}`",
            f"  - Handoff: `{item.handoff_state}` / `{item.acceptance_state}`",
            f"  - Owner: `{item.owner_label}`",
        ])
        if item.latest_summary_line:
            lines.append(f"  - Latest summary: {item.latest_summary_line}")
        for action in item.recommended_actions:
            lines.append(f"  - Action: {action}")
    return lines


__all__ = [
    'OracleOperatorPackApprovalNeededRequest',
    'OracleOperatorPackApprovalNeededItem',
    'OracleOperatorPackApprovalNeeded',
    'build_operator_pack_approval_needed_request',
    'materialize_operator_pack_approval_needed',
    'render_operator_pack_approval_needed_markdown_lines',
]
