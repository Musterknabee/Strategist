from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

from strategy_validator.control_plane.operator_pack_dispatch_permission import (
    OracleOperatorPackDispatchPermission,
    OracleOperatorPackDispatchPermissionItem,
    OracleOperatorPackDispatchPermissionRequest,
    build_operator_pack_dispatch_permission_request,
    materialize_operator_pack_dispatch_permission,
)
from strategy_validator.control_plane.operator_pack_lease_governance import (
    OracleOperatorPackLeaseGovernance,
    OracleOperatorPackLeaseGovernanceItem,
    OracleOperatorPackLeaseGovernanceRequest,
    build_operator_pack_lease_governance_request,
    materialize_operator_pack_lease_governance,
)
from strategy_validator.control_plane.operator_workboard import OracleOperatorWorkboard


@dataclass(frozen=True)
class OracleOperatorPackDispatchOutcomeRequest:
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
    outcome_label_prefix: str | None = None


@dataclass(frozen=True)
class OracleOperatorPackDispatchOutcomeItem:
    pack_kind: str
    dispatch_permission: str
    downstream_gate: str
    dispatch_action: str
    governance_decision: str
    governance_action: str
    dispatch_outcome: str
    execution_outcome: str
    block_reason: str
    outcome_key: str
    outcome_label: str
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
class OracleOperatorPackDispatchOutcome:
    schema_version: str
    search_root: str
    current_pack_kind: str | None
    queue_key: str | None
    review_target: str | None
    priority_band: str | None
    board_label: str | None
    total_dispatch_outcome_count: int
    items: tuple[OracleOperatorPackDispatchOutcomeItem, ...]

    def to_payload(self) -> dict[str, Any]:
        return {
            'schema_version': self.schema_version,
            'search_root': self.search_root,
            'current_pack_kind': self.current_pack_kind,
            'queue_key': self.queue_key,
            'review_target': self.review_target,
            'priority_band': self.priority_band,
            'board_label': self.board_label,
            'total_dispatch_outcome_count': self.total_dispatch_outcome_count,
            'item_count': len(self.items),
            'items': [
                {
                    'pack_kind': item.pack_kind,
                    'dispatch_permission': item.dispatch_permission,
                    'downstream_gate': item.downstream_gate,
                    'dispatch_action': item.dispatch_action,
                    'governance_decision': item.governance_decision,
                    'governance_action': item.governance_action,
                    'dispatch_outcome': item.dispatch_outcome,
                    'execution_outcome': item.execution_outcome,
                    'block_reason': item.block_reason,
                    'outcome_key': item.outcome_key,
                    'outcome_label': item.outcome_label,
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


def build_operator_pack_dispatch_outcome_request(*, search_root: Path, repo_root: Path | None = None, current_pack_kind: str | None = None, pack_kinds: Sequence[str] = (), trust_statuses: Sequence[str] = (), summary_line_contains: str | None = None, output_artifact_label_contains: str | None = None, max_items: int = 4, sustained_degraded_threshold: int = 2, queue_key: str | None = None, review_target: str | None = None, priority_band: str | None = None, action_owner_lane: str | None = None, board_label: str | None = None, backup_owner_lane: str | None = None, owner_label_prefix: str | None = None, ack_owner_lane: str | None = None, lease_label_prefix: str | None = None, lifecycle_label_prefix: str | None = None, governance_label_prefix: str | None = None, readiness_label_prefix: str | None = None, dispatch_label_prefix: str | None = None, outcome_label_prefix: str | None = None) -> OracleOperatorPackDispatchOutcomeRequest:
    return OracleOperatorPackDispatchOutcomeRequest(
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
    )


def _matching_governance(permission_item: OracleOperatorPackDispatchPermissionItem, lease_governance: OracleOperatorPackLeaseGovernance | None) -> OracleOperatorPackLeaseGovernanceItem | None:
    if lease_governance is None:
        return None
    for item in lease_governance.items:
        if item.pack_kind != permission_item.pack_kind:
            continue
        if item.latest_manifest_path != permission_item.latest_manifest_path:
            continue
        return item
    return next((item for item in lease_governance.items if item.pack_kind == permission_item.pack_kind), None)


def _classify_outcome(permission_item: OracleOperatorPackDispatchPermissionItem, governance_item: OracleOperatorPackLeaseGovernanceItem | None) -> tuple[str, str, str]:
    governance_action = governance_item.governance_action if governance_item is not None else 'ALLOW_EXPIRY'
    if permission_item.dispatch_permission == 'DISPATCH_PERMITTED':
        return 'DISPATCH_EXECUTABLE', 'EXECUTION_AUTHORIZED', 'NO_BLOCK_REASON'
    if permission_item.dispatch_permission == 'DISPATCH_AWAITING_ACKNOWLEDGEMENT':
        return 'DISPATCH_HELD', 'EXECUTION_HELD', 'AWAITING_ACKNOWLEDGEMENT'
    if governance_action == 'RELEASE_LEASE':
        return 'DISPATCH_BLOCKED', 'EXECUTION_BLOCKED', 'LEASE_RELEASE_GOVERNED'
    if governance_action == 'ALLOW_EXPIRY':
        return 'DISPATCH_BLOCKED', 'EXECUTION_BLOCKED', 'LEASE_EXPIRY_ALLOWED'
    return 'DISPATCH_BLOCKED', 'EXECUTION_BLOCKED', 'DOWNSTREAM_GATE_BLOCKED'


def _outcome_key(item: OracleOperatorPackDispatchPermissionItem, dispatch_outcome: str, block_reason: str) -> str:
    return '::'.join((item.pack_kind, dispatch_outcome, block_reason, item.queue_key or 'no-queue'))


def _compose_actions(permission_item: OracleOperatorPackDispatchPermissionItem, *, governance_item: OracleOperatorPackLeaseGovernanceItem | None, dispatch_outcome: str, execution_outcome: str, block_reason: str, outcome_label: str) -> tuple[str, ...]:
    actions: list[str] = []
    if dispatch_outcome == 'DISPATCH_EXECUTABLE':
        actions.append(f'Proceed with `{outcome_label}` for `{permission_item.pack_kind}` because dispatch is permitted and execution is authorized.')
    elif dispatch_outcome == 'DISPATCH_HELD':
        actions.append(f'Hold `{permission_item.pack_kind}` until acknowledgement clears the block reason `{block_reason}` before any downstream execution proceeds.')
    else:
        actions.append(f'Block `{permission_item.pack_kind}` because execution outcome is `{execution_outcome}` with block reason `{block_reason}`.')
    actions.extend(permission_item.recommended_actions)
    if governance_item is not None:
        actions.extend(governance_item.recommended_actions)
    return tuple(dict.fromkeys(actions))


def materialize_operator_pack_dispatch_outcome(request: OracleOperatorPackDispatchOutcomeRequest, *, dispatch_permission: OracleOperatorPackDispatchPermission | None = None, dispatch_permission_request: OracleOperatorPackDispatchPermissionRequest | None = None, lease_governance: OracleOperatorPackLeaseGovernance | None = None, lease_governance_request: OracleOperatorPackLeaseGovernanceRequest | None = None, operator_workboard: OracleOperatorWorkboard | None = None) -> OracleOperatorPackDispatchOutcome:
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
    if lease_governance is None:
        lease_governance = materialize_operator_pack_lease_governance(
            lease_governance_request or build_operator_pack_lease_governance_request(
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
            ),
            operator_workboard=operator_workboard,
        )
    items: list[OracleOperatorPackDispatchOutcomeItem] = []
    for permission_item in dispatch_permission.items[: request.max_items]:
        governance_item = _matching_governance(permission_item, lease_governance)
        dispatch_outcome, execution_outcome, block_reason = _classify_outcome(permission_item, governance_item)
        outcome_label = f"{request.outcome_label_prefix}:{permission_item.pack_kind}:{dispatch_outcome.lower()}" if request.outcome_label_prefix else f"{permission_item.pack_kind}:{dispatch_outcome.lower()}"
        items.append(OracleOperatorPackDispatchOutcomeItem(
            pack_kind=permission_item.pack_kind,
            dispatch_permission=permission_item.dispatch_permission,
            downstream_gate=permission_item.downstream_gate,
            dispatch_action=permission_item.dispatch_action,
            governance_decision=governance_item.governance_decision if governance_item is not None else 'GOVERN_ALLOW_EXPIRY',
            governance_action=governance_item.governance_action if governance_item is not None else 'ALLOW_EXPIRY',
            dispatch_outcome=dispatch_outcome,
            execution_outcome=execution_outcome,
            block_reason=block_reason,
            outcome_key=_outcome_key(permission_item, dispatch_outcome, block_reason),
            outcome_label=outcome_label,
            owner_lane=permission_item.owner_lane,
            ack_owner_lane=permission_item.ack_owner_lane,
            routing_lane=permission_item.routing_lane,
            routing_target=permission_item.routing_target,
            queue_key=permission_item.queue_key,
            review_target=permission_item.review_target,
            priority_band=permission_item.priority_band,
            board_label=permission_item.board_label,
            latest_trust_status=permission_item.latest_trust_status,
            previous_trust_status=permission_item.previous_trust_status,
            latest_summary_line=permission_item.latest_summary_line,
            previous_summary_line=permission_item.previous_summary_line,
            latest_manifest_path=permission_item.latest_manifest_path,
            previous_manifest_path=permission_item.previous_manifest_path,
            recommended_actions=_compose_actions(permission_item, governance_item=governance_item, dispatch_outcome=dispatch_outcome, execution_outcome=execution_outcome, block_reason=block_reason, outcome_label=outcome_label),
            is_current_pack_kind=permission_item.is_current_pack_kind,
        ))
    return OracleOperatorPackDispatchOutcome(
        schema_version='oracle_operator_pack_dispatch_outcome/v1',
        search_root=str(request.search_root),
        current_pack_kind=request.current_pack_kind,
        queue_key=request.queue_key or getattr(operator_workboard, 'queue_key', None),
        review_target=request.review_target or getattr(operator_workboard, 'review_target', None),
        priority_band=request.priority_band or getattr(operator_workboard, 'priority_band', None),
        board_label=request.board_label or getattr(operator_workboard, 'board_label', None),
        total_dispatch_outcome_count=len(items),
        items=tuple(items),
    )


def render_operator_pack_dispatch_outcome_markdown_lines(dispatch_outcome: OracleOperatorPackDispatchOutcome) -> list[str]:
    lines = ['## Operator Pack Dispatch Outcomes']
    if dispatch_outcome.queue_key:
        lines.append(f"- Queue: `{dispatch_outcome.queue_key}`")
    if dispatch_outcome.review_target:
        lines.append(f"- Review target: `{dispatch_outcome.review_target}`")
    if dispatch_outcome.priority_band:
        lines.append(f"- Priority band: `{dispatch_outcome.priority_band}`")
    if dispatch_outcome.board_label:
        lines.append(f"- Board: `{dispatch_outcome.board_label}`")
    for item in dispatch_outcome.items:
        lines.append(f"- `{item.pack_kind}` → outcome `{item.dispatch_outcome}` / execution `{item.execution_outcome}` / block reason `{item.block_reason}`")
        if item.latest_summary_line:
            lines.append(f"  - Latest summary: {item.latest_summary_line}")
        for action in item.recommended_actions:
            lines.append(f"  - Action: {action}")
    return lines


__all__ = [
    'OracleOperatorPackDispatchOutcomeRequest',
    'OracleOperatorPackDispatchOutcomeItem',
    'OracleOperatorPackDispatchOutcome',
    'build_operator_pack_dispatch_outcome_request',
    'materialize_operator_pack_dispatch_outcome',
    'render_operator_pack_dispatch_outcome_markdown_lines',
]
