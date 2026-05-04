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
from strategy_validator.control_plane.operator_pack_escalation import (
    OracleOperatorPackEscalation,
    OracleOperatorPackEscalationItem,
    OracleOperatorPackEscalationRequest,
    build_operator_pack_escalation_request,
    materialize_operator_pack_escalation,
)


@dataclass(frozen=True)
class OracleOperatorPackLeaseGovernanceRequest:
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


@dataclass(frozen=True)
class OracleOperatorPackLeaseGovernanceItem:
    pack_kind: str
    lifecycle_state: str
    escalation_posture: str | None
    governance_decision: str
    governance_action: str
    release_decision: str
    governance_key: str
    governance_label: str
    owner_lane: str
    routing_lane: str
    routing_target: str
    priority_band: str
    queue_key: str | None
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
class OracleOperatorPackLeaseGovernance:
    schema_version: str
    search_root: str
    current_pack_kind: str | None
    queue_key: str | None
    review_target: str | None
    priority_band: str | None
    board_label: str | None
    total_governance_count: int
    items: tuple[OracleOperatorPackLeaseGovernanceItem, ...]

    def to_payload(self) -> dict[str, Any]:
        return {
            'schema_version': self.schema_version,
            'search_root': self.search_root,
            'current_pack_kind': self.current_pack_kind,
            'queue_key': self.queue_key,
            'review_target': self.review_target,
            'priority_band': self.priority_band,
            'board_label': self.board_label,
            'total_governance_count': self.total_governance_count,
            'item_count': len(self.items),
            'items': [
                {
                    'pack_kind': item.pack_kind,
                    'lifecycle_state': item.lifecycle_state,
                    'escalation_posture': item.escalation_posture,
                    'governance_decision': item.governance_decision,
                    'governance_action': item.governance_action,
                    'release_decision': item.release_decision,
                    'governance_key': item.governance_key,
                    'governance_label': item.governance_label,
                    'owner_lane': item.owner_lane,
                    'routing_lane': item.routing_lane,
                    'routing_target': item.routing_target,
                    'priority_band': item.priority_band,
                    'queue_key': item.queue_key,
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


def build_operator_pack_lease_governance_request(
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
) -> OracleOperatorPackLeaseGovernanceRequest:
    return OracleOperatorPackLeaseGovernanceRequest(
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
    )


def _governance_key(item: OracleOperatorPackClaimLifecycleItem) -> str:
    queue_key = item.queue_key or 'no-queue'
    return '::'.join((item.pack_kind, queue_key, item.review_target, item.owner_lane, item.lifecycle_state))


def _matching_escalation(item: OracleOperatorPackClaimLifecycleItem, escalation: OracleOperatorPackEscalation | None) -> OracleOperatorPackEscalationItem | None:
    if escalation is None:
        return None
    for esc in escalation.items:
        if esc.pack_kind != item.pack_kind:
            continue
        if item.latest_manifest_path != esc.latest_manifest_path:
            continue
        return esc
    return next((esc for esc in escalation.items if esc.pack_kind == item.pack_kind), None)


def _classify_governance(item: OracleOperatorPackClaimLifecycleItem, escalation_item: OracleOperatorPackEscalationItem | None) -> tuple[str, str, str]:
    if item.lifecycle_state == 'ACTIVE_RELEASE_RECOMMENDED':
        return 'GOVERN_RELEASE', 'RELEASE_LEASE', 'RELEASE_OR_EXPIRE'
    if item.lifecycle_state == 'ACTIVE_RENEWAL_REQUIRED':
        return 'GOVERN_RETAIN_AND_RENEW', 'RETAIN_AND_RENEW', 'RETAIN_UNDER_GOVERNANCE'
    if item.lifecycle_state == 'PENDING_ACQUISITION':
        posture = escalation_item.escalation_posture if escalation_item is not None else None
        if posture == 'IMMEDIATE_OPERATOR_REVIEW':
            return 'GOVERN_ESCALATED_ACQUISITION', 'ACQUIRE_UNDER_ESCALATION', 'ESCALATE_BEFORE_ACQUISITION'
        return 'GOVERN_ACQUIRE_PENDING', 'ACQUIRE_PENDING_LEASE', 'ACQUIRE_BEFORE_RETAIN'
    return 'GOVERN_ALLOW_EXPIRY', 'ALLOW_EXPIRY', 'ALLOW_EXPIRY'


def _compose_actions(
    item: OracleOperatorPackClaimLifecycleItem,
    *,
    governance_decision: str,
    governance_action: str,
    release_decision: str,
    governance_label: str,
    routing_lane: str,
    routing_target: str,
) -> tuple[str, ...]:
    actions: list[str] = []
    if governance_action == 'RETAIN_AND_RENEW':
        actions.append(f'Retain and renew `{governance_label}` for `{item.pack_kind}` under `{routing_lane}` governance.')
    elif governance_action == 'RELEASE_LEASE':
        actions.append(f'Release `{governance_label}` for `{item.pack_kind}` and downshift the active lease through `{routing_target}`.')
    elif governance_action == 'ACQUIRE_UNDER_ESCALATION':
        actions.append(f'Escalate `{item.pack_kind}` through `{routing_lane}` before acquiring `{governance_label}`.')
    elif governance_action == 'ACQUIRE_PENDING_LEASE':
        actions.append(f'Acquire the pending lease for `{governance_label}` before retaining `{item.pack_kind}` under governance.')
    else:
        actions.append(f'Allow `{item.pack_kind}` to expire without retaining the lease governance state.')
    actions.append(f'Governance decision is `{governance_decision}` with release decision `{release_decision}`.')
    actions.extend(item.recommended_actions)
    return tuple(actions)


def materialize_operator_pack_lease_governance(
    request: OracleOperatorPackLeaseGovernanceRequest,
    *,
    claim_lifecycle: OracleOperatorPackClaimLifecycle | None = None,
    claim_lifecycle_request: OracleOperatorPackClaimLifecycleRequest | None = None,
    escalation: OracleOperatorPackEscalation | None = None,
    escalation_request: OracleOperatorPackEscalationRequest | None = None,
    operator_workboard=None,
) -> OracleOperatorPackLeaseGovernance:
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
    if escalation is None:
        escalation = materialize_operator_pack_escalation(
            escalation_request or build_operator_pack_escalation_request(
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
            )
        )
    items=[]
    for lifecycle_item in claim_lifecycle.items[: request.max_items]:
        esc_item = _matching_escalation(lifecycle_item, escalation)
        governance_decision, governance_action, release_decision = _classify_governance(lifecycle_item, esc_item)
        routing_lane = esc_item.routing_lane if esc_item is not None else (request.action_owner_lane or lifecycle_item.owner_lane)
        routing_target = esc_item.routing_target if esc_item is not None else (request.review_target or lifecycle_item.review_target)
        priority_band = esc_item.priority_band if esc_item is not None else lifecycle_item.priority_band
        governance_label = f"{request.governance_label_prefix or 'governance'}:{lifecycle_item.owner_lane}"
        items.append(OracleOperatorPackLeaseGovernanceItem(
            pack_kind=lifecycle_item.pack_kind,
            lifecycle_state=lifecycle_item.lifecycle_state,
            escalation_posture=esc_item.escalation_posture if esc_item is not None else None,
            governance_decision=governance_decision,
            governance_action=governance_action,
            release_decision=release_decision,
            governance_key=_governance_key(lifecycle_item),
            governance_label=governance_label,
            owner_lane=lifecycle_item.owner_lane,
            routing_lane=routing_lane,
            routing_target=routing_target,
            priority_band=priority_band,
            queue_key=lifecycle_item.queue_key,
            board_label=lifecycle_item.board_label,
            latest_trust_status=lifecycle_item.latest_trust_status,
            previous_trust_status=lifecycle_item.previous_trust_status,
            latest_summary_line=lifecycle_item.latest_summary_line,
            previous_summary_line=lifecycle_item.previous_summary_line,
            latest_manifest_path=lifecycle_item.latest_manifest_path,
            previous_manifest_path=lifecycle_item.previous_manifest_path,
            recommended_actions=_compose_actions(lifecycle_item, governance_decision=governance_decision, governance_action=governance_action, release_decision=release_decision, governance_label=governance_label, routing_lane=routing_lane, routing_target=routing_target),
            is_current_pack_kind=lifecycle_item.is_current_pack_kind,
        ))
    return OracleOperatorPackLeaseGovernance(
        schema_version='oracle_operator_pack_lease_governance/v1',
        search_root=str(request.search_root),
        current_pack_kind=request.current_pack_kind,
        queue_key=request.queue_key,
        review_target=request.review_target,
        priority_band=request.priority_band,
        board_label=request.board_label,
        total_governance_count=len(items),
        items=tuple(items),
    )


def render_operator_pack_lease_governance_markdown_lines(lease_governance: OracleOperatorPackLeaseGovernance) -> list[str]:
    lines = ['## Operator Pack Lease Governance']
    if lease_governance.queue_key:
        lines.append(f"- Queue: `{lease_governance.queue_key}`")
    if lease_governance.review_target:
        lines.append(f"- Review target: `{lease_governance.review_target}`")
    if lease_governance.priority_band:
        lines.append(f"- Priority band: `{lease_governance.priority_band}`")
    if lease_governance.board_label:
        lines.append(f"- Board: `{lease_governance.board_label}`")
    for item in lease_governance.items:
        lines.append('')
        lines.append(f"### {item.pack_kind}")
        lines.append(f"- Governance decision: `{item.governance_decision}`")
        lines.append(f"- Governance action: `{item.governance_action}`")
        lines.append(f"- Release decision: `{item.release_decision}`")
        lines.append(f"- Lifecycle state: `{item.lifecycle_state}`")
        if item.escalation_posture:
            lines.append(f"- Escalation posture: `{item.escalation_posture}`")
        lines.append(f"- Routing: `{item.routing_lane}` -> `{item.routing_target}`")
        lines.append(f"- Owner lane: `{item.owner_lane}`")
        lines.append(f"- Governance label: `{item.governance_label}`")
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
            lines.extend([f"  - {action}" for action in item.recommended_actions])
    if len(lines) == 1:
        lines.append('- No operator pack lease governance decisions in scope.')
    return lines


__all__ = [
    'OracleOperatorPackLeaseGovernanceRequest',
    'OracleOperatorPackLeaseGovernanceItem',
    'OracleOperatorPackLeaseGovernance',
    'build_operator_pack_lease_governance_request',
    'materialize_operator_pack_lease_governance',
    'render_operator_pack_lease_governance_markdown_lines',
]
