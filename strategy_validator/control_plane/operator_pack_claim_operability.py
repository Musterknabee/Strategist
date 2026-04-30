from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

from strategy_validator.control_plane.operator_pack_claim_lifecycle import (
    OracleOperatorPackClaimLifecycle,
    OracleOperatorPackClaimLifecycleItem,
    OracleOperatorPackClaimLifecycleRequest,
    build_operator_pack_claim_lifecycle_request,
    materialize_operator_pack_claim_lifecycle,
)
from strategy_validator.control_plane.operator_pack_execution_readiness import (
    OracleOperatorPackExecutionReadiness,
    OracleOperatorPackExecutionReadinessItem,
    OracleOperatorPackExecutionReadinessRequest,
    build_operator_pack_execution_readiness_request,
    materialize_operator_pack_execution_readiness,
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
class OracleOperatorPackClaimOperabilityRequest:
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
    operability_label_prefix: str | None = None


@dataclass(frozen=True)
class OracleOperatorPackClaimOperabilityItem:
    pack_kind: str
    lifecycle_state: str
    governance_decision: str
    governance_action: str
    execution_posture: str
    readiness_state: str
    operability_posture: str
    operability_state: str
    operability_action: str
    operability_key: str
    operability_label: str
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
class OracleOperatorPackClaimOperability:
    schema_version: str
    search_root: str
    current_pack_kind: str | None
    queue_key: str | None
    review_target: str | None
    priority_band: str | None
    board_label: str | None
    total_claim_operability_count: int
    items: tuple[OracleOperatorPackClaimOperabilityItem, ...]

    def to_payload(self) -> dict[str, Any]:
        return {
            'schema_version': self.schema_version,
            'search_root': self.search_root,
            'current_pack_kind': self.current_pack_kind,
            'queue_key': self.queue_key,
            'review_target': self.review_target,
            'priority_band': self.priority_band,
            'board_label': self.board_label,
            'total_claim_operability_count': self.total_claim_operability_count,
            'item_count': len(self.items),
            'items': [
                {
                    'pack_kind': item.pack_kind,
                    'lifecycle_state': item.lifecycle_state,
                    'governance_decision': item.governance_decision,
                    'governance_action': item.governance_action,
                    'execution_posture': item.execution_posture,
                    'readiness_state': item.readiness_state,
                    'operability_posture': item.operability_posture,
                    'operability_state': item.operability_state,
                    'operability_action': item.operability_action,
                    'operability_key': item.operability_key,
                    'operability_label': item.operability_label,
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


def build_operator_pack_claim_operability_request(
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
    operability_label_prefix: str | None = None,
) -> OracleOperatorPackClaimOperabilityRequest:
    return OracleOperatorPackClaimOperabilityRequest(
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
        operability_label_prefix=operability_label_prefix or None,
    )


def _matching_lifecycle(
    item: OracleOperatorPackExecutionReadinessItem,
    claim_lifecycle: OracleOperatorPackClaimLifecycle | None,
) -> OracleOperatorPackClaimLifecycleItem | None:
    if claim_lifecycle is None:
        return None
    for lifecycle_item in claim_lifecycle.items:
        if lifecycle_item.pack_kind != item.pack_kind:
            continue
        if lifecycle_item.latest_manifest_path != item.latest_manifest_path:
            continue
        return lifecycle_item
    return next((lifecycle_item for lifecycle_item in claim_lifecycle.items if lifecycle_item.pack_kind == item.pack_kind), None)


def _matching_governance(
    item: OracleOperatorPackExecutionReadinessItem,
    lease_governance: OracleOperatorPackLeaseGovernance | None,
) -> OracleOperatorPackLeaseGovernanceItem | None:
    if lease_governance is None:
        return None
    for governance_item in lease_governance.items:
        if governance_item.pack_kind != item.pack_kind:
            continue
        if governance_item.latest_manifest_path != item.latest_manifest_path:
            continue
        return governance_item
    return next((governance_item for governance_item in lease_governance.items if governance_item.pack_kind == item.pack_kind), None)


def _classify_operability(
    execution_item: OracleOperatorPackExecutionReadinessItem,
    lifecycle_item: OracleOperatorPackClaimLifecycleItem | None,
) -> tuple[str, str, str]:
    lifecycle_state = lifecycle_item.lifecycle_state if lifecycle_item is not None else 'UNCLAIMED_EXPIRABLE'
    if execution_item.execution_posture == 'EXECUTE_NOW' and lifecycle_state in {'ACTIVE_RENEWAL_REQUIRED', 'ACTIVE_RELEASE_RECOMMENDED'}:
        return 'CLAIM_OPERABLE', 'CLAIM_OPERABILITY_READY', 'OPERATE_UNDER_GOVERNED_LEASE'
    if execution_item.execution_posture == 'AWAIT_ACKNOWLEDGEMENT' or lifecycle_state == 'PENDING_ACQUISITION':
        return 'CLAIM_CONSTRAINED', 'CLAIM_OPERABILITY_CONSTRAINED', 'ACKNOWLEDGE_OR_ACQUIRE_CLAIM'
    return 'CLAIM_INOPERABLE', 'CLAIM_OPERABILITY_BLOCKED', 'BLOCK_CLAIM_WORK'


def _operability_key(item: OracleOperatorPackExecutionReadinessItem, operability_state: str) -> str:
    return '::'.join((item.pack_kind, operability_state, item.queue_key or 'no-queue', item.owner_lane))


def _compose_actions(
    execution_item: OracleOperatorPackExecutionReadinessItem,
    *,
    lifecycle_item: OracleOperatorPackClaimLifecycleItem | None,
    operability_posture: str,
    operability_state: str,
    operability_action: str,
    operability_label: str,
) -> tuple[str, ...]:
    actions: list[str] = []
    if operability_posture == 'CLAIM_OPERABLE':
        actions.append(f'Operate `{execution_item.pack_kind}` under `{operability_label}` while the governed lease remains active and executable.')
    elif operability_posture == 'CLAIM_CONSTRAINED':
        actions.append(f'Constrain `{execution_item.pack_kind}` under `{operability_label}` until acknowledgement or claim acquisition completes.')
    else:
        actions.append(f'Block claim work for `{execution_item.pack_kind}` under `{operability_label}` until governance clears the current posture.')
    actions.append(f'Claim operability is `{operability_state}` with action `{operability_action}`.')
    if lifecycle_item is not None:
        actions.append(f'Lifecycle posture is `{lifecycle_item.lifecycle_state}` with lease owner `{lifecycle_item.lease_owner_label}`.')
        actions.extend(lifecycle_item.recommended_actions)
    actions.extend(execution_item.recommended_actions)
    return tuple(dict.fromkeys(actions))


def materialize_operator_pack_claim_operability(
    request: OracleOperatorPackClaimOperabilityRequest,
    *,
    execution_readiness: OracleOperatorPackExecutionReadiness | None = None,
    execution_readiness_request: OracleOperatorPackExecutionReadinessRequest | None = None,
    claim_lifecycle: OracleOperatorPackClaimLifecycle | None = None,
    claim_lifecycle_request: OracleOperatorPackClaimLifecycleRequest | None = None,
    lease_governance: OracleOperatorPackLeaseGovernance | None = None,
    lease_governance_request: OracleOperatorPackLeaseGovernanceRequest | None = None,
    operator_workboard: OracleOperatorWorkboard | None = None,
) -> OracleOperatorPackClaimOperability:
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
                queue_key=request.queue_key,
                review_target=request.review_target,
                priority_band=request.priority_band,
                action_owner_lane=request.action_owner_lane,
                board_label=request.board_label,
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
    if claim_lifecycle is None:
        claim_lifecycle = materialize_operator_pack_claim_lifecycle(
            claim_lifecycle_request or build_operator_pack_claim_lifecycle_request(
                search_root=request.search_root,
                repo_root=request.repo_root,
                current_pack_kind=request.current_pack_kind,
                pack_kinds=request.pack_kinds,
                trust_statuses=request.trust_statuses,
                summary_line_contains=request.summary_line_contains,
                output_artifact_label_contains=request.output_artifact_label_contains,
                max_items=request.max_items,
                sustained_degraded_threshold=request.sustained_degraded_threshold,
                queue_key=request.queue_key,
                review_target=request.review_target,
                priority_band=request.priority_band,
                action_owner_lane=request.action_owner_lane,
                board_label=request.board_label,
                backup_owner_lane=request.backup_owner_lane,
                owner_label_prefix=request.owner_label_prefix,
                ack_owner_lane=request.ack_owner_lane,
                lease_label_prefix=request.lease_label_prefix,
                lifecycle_label_prefix=request.lifecycle_label_prefix,
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
                queue_key=request.queue_key,
                review_target=request.review_target,
                priority_band=request.priority_band,
                action_owner_lane=request.action_owner_lane,
                board_label=request.board_label,
                backup_owner_lane=request.backup_owner_lane,
                owner_label_prefix=request.owner_label_prefix,
                ack_owner_lane=request.ack_owner_lane,
                lease_label_prefix=request.lease_label_prefix,
                lifecycle_label_prefix=request.lifecycle_label_prefix,
                governance_label_prefix=request.governance_label_prefix,
            ),
            operator_workboard=operator_workboard,
        )

    items: list[OracleOperatorPackClaimOperabilityItem] = []
    for execution_item in execution_readiness.items[: request.max_items]:
        lifecycle_item = _matching_lifecycle(execution_item, claim_lifecycle)
        governance_item = _matching_governance(execution_item, lease_governance)
        operability_posture, operability_state, operability_action = _classify_operability(execution_item, lifecycle_item)
        operability_key = _operability_key(execution_item, operability_state)
        label_prefix = request.operability_label_prefix or request.readiness_label_prefix or 'claim-operability'
        operability_label = f"{label_prefix}:{execution_item.pack_kind}:{operability_posture.lower()}"
        items.append(OracleOperatorPackClaimOperabilityItem(
            pack_kind=execution_item.pack_kind,
            lifecycle_state=lifecycle_item.lifecycle_state if lifecycle_item is not None else 'UNCLAIMED_EXPIRABLE',
            governance_decision=governance_item.governance_decision if governance_item is not None else execution_item.governance_decision,
            governance_action=governance_item.governance_action if governance_item is not None else execution_item.governance_action,
            execution_posture=execution_item.execution_posture,
            readiness_state=execution_item.readiness_state,
            operability_posture=operability_posture,
            operability_state=operability_state,
            operability_action=operability_action,
            operability_key=operability_key,
            operability_label=operability_label,
            owner_lane=execution_item.owner_lane,
            ack_owner_lane=execution_item.ack_owner_lane,
            routing_lane=execution_item.routing_lane,
            routing_target=execution_item.routing_target,
            queue_key=execution_item.queue_key,
            review_target=execution_item.review_target,
            priority_band=execution_item.priority_band,
            board_label=execution_item.board_label,
            latest_trust_status=execution_item.latest_trust_status,
            previous_trust_status=execution_item.previous_trust_status,
            latest_summary_line=execution_item.latest_summary_line,
            previous_summary_line=execution_item.previous_summary_line,
            latest_manifest_path=execution_item.latest_manifest_path,
            previous_manifest_path=execution_item.previous_manifest_path,
            recommended_actions=_compose_actions(
                execution_item,
                lifecycle_item=lifecycle_item,
                operability_posture=operability_posture,
                operability_state=operability_state,
                operability_action=operability_action,
                operability_label=operability_label,
            ),
            is_current_pack_kind=execution_item.is_current_pack_kind,
        ))
    return OracleOperatorPackClaimOperability(
        schema_version='oracle_operator_pack_claim_operability/v1',
        search_root=str(request.search_root),
        current_pack_kind=request.current_pack_kind,
        queue_key=request.queue_key,
        review_target=request.review_target,
        priority_band=request.priority_band,
        board_label=request.board_label,
        total_claim_operability_count=len(items),
        items=tuple(items),
    )


def render_operator_pack_claim_operability_markdown_lines(report: OracleOperatorPackClaimOperability) -> list[str]:
    lines = ['## Operator Pack Claim Operability', '']
    if not report.items:
        lines.append('- No claim-operability items found.')
        return lines
    for item in report.items:
        lines.extend([
            f"### {item.pack_kind}",
            f"- Operability: `{item.operability_posture}`",
            f"- State / action: `{item.operability_state}` / `{item.operability_action}`",
            f"- Execution posture: `{item.execution_posture}` ({item.readiness_state})",
            f"- Lifecycle / governance: `{item.lifecycle_state}` / `{item.governance_decision}`",
            f"- Queue / owner: `{item.queue_key or 'no-queue'}` / `{item.owner_lane}`",
            f"- Summary: {item.latest_summary_line or 'n/a'}",
            f"- Manifest: `{item.latest_manifest_path}`",
        ])
        if item.recommended_actions:
            lines.append('- Recommended actions:')
            lines.extend([f"  - {action}" for action in item.recommended_actions[:4]])
        lines.append('')
    return lines


__all__ = [
    'OracleOperatorPackClaimOperabilityRequest',
    'OracleOperatorPackClaimOperabilityItem',
    'OracleOperatorPackClaimOperability',
    'build_operator_pack_claim_operability_request',
    'materialize_operator_pack_claim_operability',
    'render_operator_pack_claim_operability_markdown_lines',
]
