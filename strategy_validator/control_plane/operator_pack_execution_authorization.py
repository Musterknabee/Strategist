from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

from strategy_validator.control_plane.operator_pack_approval_disposition import (
    OracleOperatorPackApprovalDisposition,
    OracleOperatorPackApprovalDispositionItem,
    OracleOperatorPackApprovalDispositionRequest,
    build_operator_pack_approval_disposition_request,
    materialize_operator_pack_approval_disposition,
)
from strategy_validator.control_plane.operator_pack_dispatch_permission import (
    OracleOperatorPackDispatchPermission,
    OracleOperatorPackDispatchPermissionItem,
    OracleOperatorPackDispatchPermissionRequest,
    build_operator_pack_dispatch_permission_request,
    materialize_operator_pack_dispatch_permission,
)
from strategy_validator.control_plane.operator_workboard import OracleOperatorWorkboard


@dataclass(frozen=True)
class OracleOperatorPackExecutionAuthorizationRequest:
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
    disposition_label_prefix: str | None = None
    authorization_label_prefix: str | None = None


@dataclass(frozen=True)
class OracleOperatorPackExecutionAuthorizationItem:
    pack_kind: str
    disposition_posture: str
    signoff_state: str
    dispatch_permission: str
    downstream_gate: str
    authorization_posture: str
    authority_state: str
    authority_action: str
    authorization_key: str
    authorization_label: str
    owner_lane: str
    ack_owner_lane: str
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
class OracleOperatorPackExecutionAuthorization:
    schema_version: str
    search_root: str
    current_pack_kind: str | None
    queue_key: str | None
    review_target: str | None
    priority_band: str | None
    board_label: str | None
    total_authorization_count: int
    items: tuple[OracleOperatorPackExecutionAuthorizationItem, ...]

    def to_payload(self) -> dict[str, Any]:
        return {
            'schema_version': self.schema_version,
            'search_root': self.search_root,
            'current_pack_kind': self.current_pack_kind,
            'queue_key': self.queue_key,
            'review_target': self.review_target,
            'priority_band': self.priority_band,
            'board_label': self.board_label,
            'total_authorization_count': self.total_authorization_count,
            'items': [
                {
                    'pack_kind': item.pack_kind,
                    'disposition_posture': item.disposition_posture,
                    'signoff_state': item.signoff_state,
                    'dispatch_permission': item.dispatch_permission,
                    'downstream_gate': item.downstream_gate,
                    'authorization_posture': item.authorization_posture,
                    'authority_state': item.authority_state,
                    'authority_action': item.authority_action,
                    'authorization_key': item.authorization_key,
                    'authorization_label': item.authorization_label,
                    'owner_lane': item.owner_lane,
                    'ack_owner_lane': item.ack_owner_lane,
                    'queue_key': item.queue_key,
                    'review_target': item.review_target,
                    'priority_band': item.priority_band,
                    'board_label': item.board_label,
                    'latest_trust_status': item.latest_trust_status,
                    'previous_trust_status': item.previous_trust_status,
                    'latest_summary_line': item.latest_summary_line,
                    'previous_summary_line': item.previous_summary_line,
                    'latest_manifest_path': str(item.latest_manifest_path),
                    'previous_manifest_path': str(item.previous_manifest_path) if item.previous_manifest_path is not None else None,
                    'recommended_actions': list(item.recommended_actions),
                    'is_current_pack_kind': item.is_current_pack_kind,
                }
                for item in self.items
            ],
        }


def build_operator_pack_execution_authorization_request(
    *,
    search_root: Path,
    repo_root: Path | None = None,
    current_pack_kind: str | None = None,
    pack_kinds: Sequence[str] = (),
    trust_statuses: Sequence[str] = (),
    summary_line_contains: str | None = None,
    output_artifact_label_contains: str | None = None,
    max_items: int = 3,
    sustained_degraded_threshold: int = 2,
    queue_key: str | None = None,
    review_target: str | None = None,
    priority_band: str | None = None,
    action_owner_lane: str | None = None,
    board_label: str | None = None,
    backup_owner_lane: str | None = None,
    owner_label_prefix: str | None = None,
    ack_owner_lane: str | None = None,
    lease_label_prefix: str | None = None,
    lifecycle_label_prefix: str | None = None,
    governance_label_prefix: str | None = None,
    readiness_label_prefix: str | None = None,
    dispatch_label_prefix: str | None = None,
    outcome_label_prefix: str | None = None,
    exception_label_prefix: str | None = None,
    approval_label_prefix: str | None = None,
    disposition_label_prefix: str | None = None,
    authorization_label_prefix: str | None = None,
) -> OracleOperatorPackExecutionAuthorizationRequest:
    return OracleOperatorPackExecutionAuthorizationRequest(
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
        lease_label_prefix=lease_label_prefix or None,
        lifecycle_label_prefix=lifecycle_label_prefix or None,
        governance_label_prefix=governance_label_prefix or None,
        readiness_label_prefix=readiness_label_prefix or None,
        dispatch_label_prefix=dispatch_label_prefix or None,
        outcome_label_prefix=outcome_label_prefix or None,
        exception_label_prefix=exception_label_prefix or None,
        approval_label_prefix=approval_label_prefix or None,
        disposition_label_prefix=disposition_label_prefix or None,
        authorization_label_prefix=authorization_label_prefix or None,
    )


def _matching_dispatch(disposition_item: OracleOperatorPackApprovalDispositionItem, dispatch_permission: OracleOperatorPackDispatchPermission | None) -> OracleOperatorPackDispatchPermissionItem | None:
    if dispatch_permission is None:
        return None
    for item in dispatch_permission.items:
        if item.pack_kind != disposition_item.pack_kind:
            continue
        if item.latest_manifest_path != disposition_item.latest_manifest_path:
            continue
        return item
    return next((item for item in dispatch_permission.items if item.pack_kind == disposition_item.pack_kind), None)


def _classify_authorization(
    disposition_item: OracleOperatorPackApprovalDispositionItem,
    dispatch_item: OracleOperatorPackDispatchPermissionItem | None,
) -> tuple[str, str, str]:
    permission = dispatch_item.dispatch_permission if dispatch_item is not None else 'DISPATCH_BLOCKED'
    if disposition_item.disposition_posture == 'APPROVED' and permission == 'DISPATCH_PERMITTED':
        return 'AUTHORIZED', 'EXECUTION_AUTHORIZED', 'AUTHORIZE_EXECUTION'
    if disposition_item.disposition_posture == 'PENDING_SIGNOFF' or permission == 'DISPATCH_AWAITING_ACKNOWLEDGEMENT':
        return 'HOLD', 'EXECUTION_HELD_PENDING_SIGNOFF', 'HOLD_EXECUTION_AUTHORITY'
    return 'REJECTED', 'EXECUTION_REJECTED', 'REJECT_EXECUTION_AUTHORITY'


def _authorization_key(item: OracleOperatorPackApprovalDispositionItem, authority_state: str) -> str:
    return '::'.join((item.pack_kind, authority_state, item.queue_key or 'no-queue', item.owner_lane))


def _compose_actions(
    disposition_item: OracleOperatorPackApprovalDispositionItem,
    *,
    dispatch_item: OracleOperatorPackDispatchPermissionItem | None,
    authorization_posture: str,
    authority_action: str,
    authorization_label: str,
) -> tuple[str, ...]:
    actions: list[str] = []
    if authorization_posture == 'AUTHORIZED':
        actions.append(f'Authorize execution for `{disposition_item.pack_kind}` under `{authorization_label}`.')
    elif authorization_posture == 'HOLD':
        actions.append(f'Hold execution authority for `{disposition_item.pack_kind}` under `{authorization_label}` pending sign-off or acknowledgement.')
    else:
        actions.append(f'Reject execution authority for `{disposition_item.pack_kind}` under `{authorization_label}` until approval/disposition and dispatch prerequisites are satisfied.')
    if dispatch_item is not None:
        actions.append(f'Dispatch permission is `{dispatch_item.dispatch_permission}` with downstream gate `{dispatch_item.downstream_gate}`.')
    actions.append(f'Authority action is `{authority_action}`.')
    actions.extend(disposition_item.recommended_actions)
    return tuple(actions)


def materialize_operator_pack_execution_authorization(
    request: OracleOperatorPackExecutionAuthorizationRequest,
    *,
    approval_disposition: OracleOperatorPackApprovalDisposition | None = None,
    approval_disposition_request: OracleOperatorPackApprovalDispositionRequest | None = None,
    dispatch_permission: OracleOperatorPackDispatchPermission | None = None,
    dispatch_permission_request: OracleOperatorPackDispatchPermissionRequest | None = None,
    operator_workboard: OracleOperatorWorkboard | None = None,
) -> OracleOperatorPackExecutionAuthorization:
    if approval_disposition is None:
        approval_disposition = materialize_operator_pack_approval_disposition(
            approval_disposition_request or build_operator_pack_approval_disposition_request(
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
                approval_label_prefix=request.approval_label_prefix,
                disposition_label_prefix=request.disposition_label_prefix,
            ),
            operator_workboard=operator_workboard,
        )
    if dispatch_permission is None:
        dispatch_permission = materialize_operator_pack_dispatch_permission(
            dispatch_permission_request or build_operator_pack_dispatch_permission_request(
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
            ),
            operator_workboard=operator_workboard,
        )

    items: list[OracleOperatorPackExecutionAuthorizationItem] = []
    for disposition_item in approval_disposition.items[: request.max_items]:
        dispatch_item = _matching_dispatch(disposition_item, dispatch_permission)
        authorization_posture, authority_state, authority_action = _classify_authorization(disposition_item, dispatch_item)
        authorization_key = _authorization_key(disposition_item, authority_state)
        authorization_label = f"{request.authorization_label_prefix or 'execution_authority'}:{authorization_posture.lower()}:{disposition_item.pack_kind}"
        items.append(
            OracleOperatorPackExecutionAuthorizationItem(
                pack_kind=disposition_item.pack_kind,
                disposition_posture=disposition_item.disposition_posture,
                signoff_state=disposition_item.signoff_state,
                dispatch_permission=dispatch_item.dispatch_permission if dispatch_item is not None else 'DISPATCH_BLOCKED',
                downstream_gate=dispatch_item.downstream_gate if dispatch_item is not None else 'DENY_DOWNSTREAM_ACTION',
                authorization_posture=authorization_posture,
                authority_state=authority_state,
                authority_action=authority_action,
                authorization_key=authorization_key,
                authorization_label=authorization_label,
                owner_lane=disposition_item.owner_lane,
                ack_owner_lane=disposition_item.ack_owner_lane,
                queue_key=disposition_item.queue_key,
                review_target=disposition_item.review_target,
                priority_band=disposition_item.priority_band,
                board_label=disposition_item.board_label,
                latest_trust_status=disposition_item.latest_trust_status,
                previous_trust_status=disposition_item.previous_trust_status,
                latest_summary_line=disposition_item.latest_summary_line,
                previous_summary_line=disposition_item.previous_summary_line,
                latest_manifest_path=disposition_item.latest_manifest_path,
                previous_manifest_path=disposition_item.previous_manifest_path,
                recommended_actions=_compose_actions(
                    disposition_item,
                    dispatch_item=dispatch_item,
                    authorization_posture=authorization_posture,
                    authority_action=authority_action,
                    authorization_label=authorization_label,
                ),
                is_current_pack_kind=disposition_item.is_current_pack_kind,
            )
        )
    return OracleOperatorPackExecutionAuthorization(
        schema_version='oracle_operator_pack_execution_authorization/v1',
        search_root=str(request.search_root),
        current_pack_kind=request.current_pack_kind,
        queue_key=request.queue_key or getattr(operator_workboard, 'queue_key', None),
        review_target=request.review_target or getattr(operator_workboard, 'review_target', None),
        priority_band=request.priority_band or getattr(operator_workboard, 'priority_band', None),
        board_label=request.board_label or getattr(operator_workboard, 'board_label', None),
        total_authorization_count=len(items),
        items=tuple(items),
    )


def render_operator_pack_execution_authorization_markdown_lines(execution_authorization: OracleOperatorPackExecutionAuthorization) -> list[str]:
    lines = ['## Operator Pack Execution Authorization']
    if not execution_authorization.items:
        lines.append('- No operator-pack execution authorization states matched the current filters.')
        return lines
    for item in execution_authorization.items:
        lines.extend([
            f"- `{item.pack_kind}` → `{item.authorization_posture}` / `{item.authority_state}`",
            f"  - Authority action: `{item.authority_action}`",
            f"  - Approval disposition: `{item.disposition_posture}` / `{item.signoff_state}`",
            f"  - Dispatch permission: `{item.dispatch_permission}` / `{item.downstream_gate}`",
            f"  - Owner lane: `{item.owner_lane}`",
        ])
        if item.latest_summary_line:
            lines.append(f"  - Latest summary: {item.latest_summary_line}")
        for action in item.recommended_actions:
            lines.append(f"  - Action: {action}")
    return lines


__all__ = [
    'OracleOperatorPackExecutionAuthorizationRequest',
    'OracleOperatorPackExecutionAuthorizationItem',
    'OracleOperatorPackExecutionAuthorization',
    'build_operator_pack_execution_authorization_request',
    'materialize_operator_pack_execution_authorization',
    'render_operator_pack_execution_authorization_markdown_lines',
]
