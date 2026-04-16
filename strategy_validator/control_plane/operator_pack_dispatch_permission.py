from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

from strategy_validator.control_plane.operator_pack_claim_lease import (
    OracleOperatorPackClaimLease,
    OracleOperatorPackClaimLeaseItem,
    OracleOperatorPackClaimLeaseRequest,
    build_operator_pack_claim_lease_request,
    materialize_operator_pack_claim_lease,
)
from strategy_validator.control_plane.operator_pack_execution_readiness import (
    OracleOperatorPackExecutionReadiness,
    OracleOperatorPackExecutionReadinessItem,
    OracleOperatorPackExecutionReadinessRequest,
    build_operator_pack_execution_readiness_request,
    materialize_operator_pack_execution_readiness,
)
from strategy_validator.control_plane.operator_workboard import OracleOperatorWorkboard


@dataclass(frozen=True)
class OracleOperatorPackDispatchPermissionRequest:
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
    lease_label_prefix: str | None = None
    lifecycle_label_prefix: str | None = None
    governance_label_prefix: str | None = None
    readiness_label_prefix: str | None = None
    dispatch_label_prefix: str | None = None


@dataclass(frozen=True)
class OracleOperatorPackDispatchPermissionItem:
    pack_kind: str
    execution_posture: str
    readiness_state: str
    execution_action: str
    claim_state: str
    lease_state: str
    governance_action: str
    dispatch_permission: str
    downstream_gate: str
    dispatch_action: str
    permission_key: str
    dispatch_label: str
    owner_lane: str
    ack_owner_lane: str
    routing_lane: str
    routing_target: str
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
class OracleOperatorPackDispatchPermission:
    schema_version: str
    search_root: str
    current_pack_kind: str | None
    queue_key: str | None
    review_target: str | None
    priority_band: str | None
    board_label: str | None
    total_dispatch_permission_count: int
    items: tuple[OracleOperatorPackDispatchPermissionItem, ...]

    def to_payload(self) -> dict[str, Any]:
        return {
            'schema_version': self.schema_version,
            'search_root': self.search_root,
            'current_pack_kind': self.current_pack_kind,
            'queue_key': self.queue_key,
            'review_target': self.review_target,
            'priority_band': self.priority_band,
            'board_label': self.board_label,
            'total_dispatch_permission_count': self.total_dispatch_permission_count,
            'item_count': len(self.items),
            'items': [
                {
                    'pack_kind': item.pack_kind,
                    'execution_posture': item.execution_posture,
                    'readiness_state': item.readiness_state,
                    'execution_action': item.execution_action,
                    'claim_state': item.claim_state,
                    'lease_state': item.lease_state,
                    'governance_action': item.governance_action,
                    'dispatch_permission': item.dispatch_permission,
                    'downstream_gate': item.downstream_gate,
                    'dispatch_action': item.dispatch_action,
                    'permission_key': item.permission_key,
                    'dispatch_label': item.dispatch_label,
                    'owner_lane': item.owner_lane,
                    'ack_owner_lane': item.ack_owner_lane,
                    'routing_lane': item.routing_lane,
                    'routing_target': item.routing_target,
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


def build_operator_pack_dispatch_permission_request(
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
    lease_label_prefix: str | None = None,
    lifecycle_label_prefix: str | None = None,
    governance_label_prefix: str | None = None,
    readiness_label_prefix: str | None = None,
    dispatch_label_prefix: str | None = None,
) -> OracleOperatorPackDispatchPermissionRequest:
    return OracleOperatorPackDispatchPermissionRequest(
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
    )


def _matching_claim_lease(
    readiness_item: OracleOperatorPackExecutionReadinessItem,
    claim_lease: OracleOperatorPackClaimLease | None,
) -> OracleOperatorPackClaimLeaseItem | None:
    if claim_lease is None:
        return None
    for claim_item in claim_lease.items:
        if claim_item.pack_kind != readiness_item.pack_kind:
            continue
        if claim_item.latest_manifest_path != readiness_item.latest_manifest_path:
            continue
        return claim_item
    return next((item for item in claim_lease.items if item.pack_kind == readiness_item.pack_kind), None)


def _classify_dispatch(
    readiness_item: OracleOperatorPackExecutionReadinessItem,
    claim_item: OracleOperatorPackClaimLeaseItem | None,
) -> tuple[str, str, str]:
    claim_state = claim_item.claim_state if claim_item is not None else 'CLAIM_UNCLAIMED'
    lease_state = claim_item.lease_state if claim_item is not None else 'NO_ACTIVE_LEASE'
    if readiness_item.execution_posture == 'BLOCK_EXECUTION':
        return 'DISPATCH_BLOCKED', 'DENY_DOWNSTREAM_ACTION', 'BLOCK_DISPATCH'
    if readiness_item.execution_posture == 'AWAIT_ACKNOWLEDGEMENT' or claim_state == 'CLAIM_PENDING' or lease_state == 'LEASE_PENDING_ACQUISITION':
        return 'DISPATCH_AWAITING_ACKNOWLEDGEMENT', 'HOLD_DOWNSTREAM_ACTION', 'AWAIT_ACK_BEFORE_DISPATCH'
    if claim_state == 'CLAIM_ACTIVE' and lease_state == 'LEASE_ACTIVE':
        return 'DISPATCH_PERMITTED', 'ALLOW_DOWNSTREAM_ACTION', 'AUTHORIZE_DISPATCH'
    return 'DISPATCH_AWAITING_ACKNOWLEDGEMENT', 'HOLD_DOWNSTREAM_ACTION', 'AWAIT_ACK_BEFORE_DISPATCH'


def _permission_key(item: OracleOperatorPackExecutionReadinessItem, dispatch_permission: str) -> str:
    return '::'.join((item.pack_kind, dispatch_permission, item.queue_key or 'no-queue'))


def _compose_actions(
    readiness_item: OracleOperatorPackExecutionReadinessItem,
    *,
    claim_item: OracleOperatorPackClaimLeaseItem | None,
    dispatch_permission: str,
    downstream_gate: str,
    dispatch_action: str,
    dispatch_label: str,
) -> tuple[str, ...]:
    actions: list[str] = []
    if dispatch_permission == 'DISPATCH_PERMITTED':
        actions.append(
            f'Authorize downstream dispatch for `{readiness_item.pack_kind}` under `{dispatch_label}` via `{readiness_item.routing_lane}` targeting `{readiness_item.routing_target}`.'
        )
    elif dispatch_permission == 'DISPATCH_BLOCKED':
        actions.append(
            f'Block downstream dispatch for `{readiness_item.pack_kind}` and honor governance action `{readiness_item.governance_action}` before any dispatch proceeds.'
        )
    else:
        actions.append(
            f'Hold downstream dispatch for `{readiness_item.pack_kind}` until acknowledgement/lease acquisition clears under `{readiness_item.routing_target}`.'
        )
    actions.append(f'Downstream gate is `{downstream_gate}` with dispatch action `{dispatch_action}`.')
    actions.extend(readiness_item.recommended_actions)
    if claim_item is not None:
        actions.extend(claim_item.recommended_actions)
    return tuple(dict.fromkeys(actions))


def materialize_operator_pack_dispatch_permission(
    request: OracleOperatorPackDispatchPermissionRequest,
    *,
    execution_readiness: OracleOperatorPackExecutionReadiness | None = None,
    execution_readiness_request: OracleOperatorPackExecutionReadinessRequest | None = None,
    claim_lease: OracleOperatorPackClaimLease | None = None,
    claim_lease_request: OracleOperatorPackClaimLeaseRequest | None = None,
    operator_workboard: OracleOperatorWorkboard | None = None,
) -> OracleOperatorPackDispatchPermission:
    if execution_readiness is None:
        execution_readiness = materialize_operator_pack_execution_readiness(
            execution_readiness_request or build_operator_pack_execution_readiness_request(
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
            ),
            operator_workboard=operator_workboard,
        )
    if claim_lease is None:
        claim_lease = materialize_operator_pack_claim_lease(
            claim_lease_request or build_operator_pack_claim_lease_request(
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
            ),
            operator_workboard=operator_workboard,
        )
    items: list[OracleOperatorPackDispatchPermissionItem] = []
    for readiness_item in execution_readiness.items[: request.max_items]:
        claim_item = _matching_claim_lease(readiness_item, claim_lease)
        claim_state = claim_item.claim_state if claim_item is not None else 'CLAIM_UNCLAIMED'
        lease_state = claim_item.lease_state if claim_item is not None else 'NO_ACTIVE_LEASE'
        dispatch_permission, downstream_gate, dispatch_action = _classify_dispatch(readiness_item, claim_item)
        dispatch_label = f"{request.dispatch_label_prefix or 'dispatch'}:{readiness_item.owner_lane}"
        items.append(
            OracleOperatorPackDispatchPermissionItem(
                pack_kind=readiness_item.pack_kind,
                execution_posture=readiness_item.execution_posture,
                readiness_state=readiness_item.readiness_state,
                execution_action=readiness_item.execution_action,
                claim_state=claim_state,
                lease_state=lease_state,
                governance_action=readiness_item.governance_action,
                dispatch_permission=dispatch_permission,
                downstream_gate=downstream_gate,
                dispatch_action=dispatch_action,
                permission_key=_permission_key(readiness_item, dispatch_permission),
                dispatch_label=dispatch_label,
                owner_lane=readiness_item.owner_lane,
                ack_owner_lane=readiness_item.ack_owner_lane,
                routing_lane=readiness_item.routing_lane,
                routing_target=readiness_item.routing_target,
                queue_key=readiness_item.queue_key,
                review_target=readiness_item.review_target,
                priority_band=readiness_item.priority_band,
                board_label=readiness_item.board_label,
                latest_trust_status=readiness_item.latest_trust_status,
                previous_trust_status=readiness_item.previous_trust_status,
                latest_summary_line=readiness_item.latest_summary_line,
                previous_summary_line=readiness_item.previous_summary_line,
                latest_manifest_path=readiness_item.latest_manifest_path,
                previous_manifest_path=readiness_item.previous_manifest_path,
                recommended_actions=_compose_actions(
                    readiness_item,
                    claim_item=claim_item,
                    dispatch_permission=dispatch_permission,
                    downstream_gate=downstream_gate,
                    dispatch_action=dispatch_action,
                    dispatch_label=dispatch_label,
                ),
                is_current_pack_kind=readiness_item.is_current_pack_kind,
            )
        )
    return OracleOperatorPackDispatchPermission(
        schema_version='oracle_operator_pack_dispatch_permission/v1',
        search_root=str(request.search_root),
        current_pack_kind=request.current_pack_kind,
        queue_key=request.queue_key or getattr(operator_workboard, 'queue_key', None),
        review_target=request.review_target or getattr(operator_workboard, 'review_target', None),
        priority_band=request.priority_band or getattr(operator_workboard, 'priority_band', None),
        board_label=request.board_label or getattr(operator_workboard, 'board_label', None),
        total_dispatch_permission_count=len(items),
        items=tuple(items),
    )


def render_operator_pack_dispatch_permission_markdown_lines(dispatch_permission: OracleOperatorPackDispatchPermission) -> list[str]:
    lines = ['## Operator Pack Dispatch Permission']
    if dispatch_permission.queue_key:
        lines.append(f"- Queue: `{dispatch_permission.queue_key}`")
    if dispatch_permission.review_target:
        lines.append(f"- Review target: `{dispatch_permission.review_target}`")
    if dispatch_permission.priority_band:
        lines.append(f"- Priority band: `{dispatch_permission.priority_band}`")
    if dispatch_permission.board_label:
        lines.append(f"- Board: `{dispatch_permission.board_label}`")
    for item in dispatch_permission.items:
        lines.append('')
        lines.append(f"### {item.pack_kind}")
        lines.append(f"- Dispatch permission: `{item.dispatch_permission}`")
        lines.append(f"- Downstream gate: `{item.downstream_gate}`")
        lines.append(f"- Dispatch action: `{item.dispatch_action}`")
        lines.append(f"- Execution posture: `{item.execution_posture}` / `{item.readiness_state}`")
        lines.append(f"- Claim / lease: `{item.claim_state}` / `{item.lease_state}`")
        lines.append(f"- Governance action: `{item.governance_action}`")
        lines.append(f"- Routing: `{item.routing_lane}` -> `{item.routing_target}`")
        lines.append(f"- Owner lane: `{item.owner_lane}`")
        lines.append(f"- Ack owner lane: `{item.ack_owner_lane}`")
        lines.append(f"- Dispatch label: `{item.dispatch_label}`")
        if item.latest_trust_status:
            lines.append(f"- Latest trust: `{item.latest_trust_status}`")
        if item.previous_trust_status:
            lines.append(f"- Previous trust: `{item.previous_trust_status}`")
        if item.latest_summary_line:
            lines.append(f"- Latest summary: {item.latest_summary_line}")
        if item.previous_summary_line:
            lines.append(f"- Previous summary: {item.previous_summary_line}")
        lines.append(f"- Latest manifest: `{item.latest_manifest_path}`")
        if item.previous_manifest_path:
            lines.append(f"- Previous manifest: `{item.previous_manifest_path}`")
        if item.recommended_actions:
            lines.append('- Recommended actions:')
            lines.extend([f'  - {action}' for action in item.recommended_actions])
    if len(lines) == 1:
        lines.append('- No operator pack dispatch permissions in scope.')
    return lines


__all__ = [
    'OracleOperatorPackDispatchPermissionRequest',
    'OracleOperatorPackDispatchPermissionItem',
    'OracleOperatorPackDispatchPermission',
    'build_operator_pack_dispatch_permission_request',
    'materialize_operator_pack_dispatch_permission',
    'render_operator_pack_dispatch_permission_markdown_lines',
]
