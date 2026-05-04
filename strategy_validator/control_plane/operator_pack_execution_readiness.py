from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

from strategy_validator.control_plane.operator_pack_handoff import (
    OracleOperatorPackHandoff,
    OracleOperatorPackHandoffItem,
    OracleOperatorPackHandoffRequest,
    build_operator_pack_handoff_request,
    materialize_operator_pack_handoff,
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
class OracleOperatorPackExecutionReadinessRequest:
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


@dataclass(frozen=True)
class OracleOperatorPackExecutionReadinessItem:
    pack_kind: str
    governance_decision: str
    governance_action: str
    handoff_state: str
    acceptance_state: str
    execution_posture: str
    readiness_state: str
    execution_action: str
    decision_key: str
    readiness_label: str
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
class OracleOperatorPackExecutionReadiness:
    schema_version: str
    search_root: str
    current_pack_kind: str | None
    queue_key: str | None
    review_target: str | None
    priority_band: str | None
    board_label: str | None
    total_execution_readiness_count: int
    items: tuple[OracleOperatorPackExecutionReadinessItem, ...]

    def to_payload(self) -> dict[str, Any]:
        return {
            'schema_version': self.schema_version,
            'search_root': self.search_root,
            'current_pack_kind': self.current_pack_kind,
            'queue_key': self.queue_key,
            'review_target': self.review_target,
            'priority_band': self.priority_band,
            'board_label': self.board_label,
            'total_execution_readiness_count': self.total_execution_readiness_count,
            'item_count': len(self.items),
            'items': [
                {
                    'pack_kind': item.pack_kind,
                    'governance_decision': item.governance_decision,
                    'governance_action': item.governance_action,
                    'handoff_state': item.handoff_state,
                    'acceptance_state': item.acceptance_state,
                    'execution_posture': item.execution_posture,
                    'readiness_state': item.readiness_state,
                    'execution_action': item.execution_action,
                    'decision_key': item.decision_key,
                    'readiness_label': item.readiness_label,
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


def build_operator_pack_execution_readiness_request(
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
) -> OracleOperatorPackExecutionReadinessRequest:
    return OracleOperatorPackExecutionReadinessRequest(
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
    )


def _matching_handoff(item: OracleOperatorPackLeaseGovernanceItem, handoff: OracleOperatorPackHandoff | None) -> OracleOperatorPackHandoffItem | None:
    if handoff is None:
        return None
    for handoff_item in handoff.items:
        if handoff_item.pack_kind != item.pack_kind:
            continue
        if handoff_item.latest_manifest_path != item.latest_manifest_path:
            continue
        return handoff_item
    return next((handoff_item for handoff_item in handoff.items if handoff_item.pack_kind == item.pack_kind), None)


def _classify_execution(item: OracleOperatorPackLeaseGovernanceItem, handoff_item: OracleOperatorPackHandoffItem | None) -> tuple[str, str, str]:
    acceptance_state = handoff_item.acceptance_state if handoff_item is not None else 'UNCLAIMED'
    if item.governance_action in {'RELEASE_LEASE', 'ALLOW_EXPIRY'}:
        return 'BLOCK_EXECUTION', 'EXECUTION_BLOCKED', 'BLOCK_AND_RELEASE'
    if acceptance_state != 'ACCEPTED':
        return 'AWAIT_ACKNOWLEDGEMENT', 'AWAITING_ACKNOWLEDGEMENT', 'REQUEST_ACKNOWLEDGEMENT'
    return 'EXECUTE_NOW', 'READY_TO_EXECUTE', 'EXECUTE_DECISION'


def _decision_key(item: OracleOperatorPackLeaseGovernanceItem, readiness_state: str) -> str:
    return '::'.join((item.pack_kind, item.governance_decision, readiness_state, item.queue_key or 'no-queue'))


def _compose_actions(
    item: OracleOperatorPackLeaseGovernanceItem,
    *,
    handoff_item: OracleOperatorPackHandoffItem | None,
    execution_posture: str,
    readiness_state: str,
    execution_action: str,
    readiness_label: str,
) -> tuple[str, ...]:
    actions: list[str] = []
    if execution_posture == 'EXECUTE_NOW':
        actions.append(f'Execute `{readiness_label}` for `{item.pack_kind}` now under `{item.routing_lane}` targeting `{item.routing_target}`.')
    elif execution_posture == 'AWAIT_ACKNOWLEDGEMENT':
        ack_lane = handoff_item.ack_owner_lane if handoff_item is not None else item.owner_lane
        actions.append(f'Await acknowledgement from `{ack_lane}` before executing `{item.pack_kind}` under `{item.routing_target}`.')
    else:
        actions.append(f'Block execution for `{item.pack_kind}` and honor governance action `{item.governance_action}` before any operator action proceeds.')
    actions.append(f'Execution readiness is `{readiness_state}` with action `{execution_action}`.')
    actions.extend(item.recommended_actions)
    if handoff_item is not None:
        actions.extend(handoff_item.recommended_actions)
    return tuple(dict.fromkeys(actions))


def materialize_operator_pack_execution_readiness(
    request: OracleOperatorPackExecutionReadinessRequest,
    *,
    lease_governance: OracleOperatorPackLeaseGovernance | None = None,
    lease_governance_request: OracleOperatorPackLeaseGovernanceRequest | None = None,
    handoff: OracleOperatorPackHandoff | None = None,
    handoff_request: OracleOperatorPackHandoffRequest | None = None,
    operator_workboard: OracleOperatorWorkboard | None = None,
) -> OracleOperatorPackExecutionReadiness:
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
    items: list[OracleOperatorPackExecutionReadinessItem] = []
    for governance_item in lease_governance.items[: request.max_items]:
        handoff_item = _matching_handoff(governance_item, handoff)
        execution_posture, readiness_state, execution_action = _classify_execution(governance_item, handoff_item)
        ack_owner_lane = handoff_item.ack_owner_lane if handoff_item is not None else (request.ack_owner_lane or governance_item.owner_lane)
        readiness_label = f"{request.readiness_label_prefix or 'readiness'}:{governance_item.owner_lane}"
        items.append(
            OracleOperatorPackExecutionReadinessItem(
                pack_kind=governance_item.pack_kind,
                governance_decision=governance_item.governance_decision,
                governance_action=governance_item.governance_action,
                handoff_state=handoff_item.handoff_state if handoff_item is not None else 'HANDOFF_UNCLAIMED',
                acceptance_state=handoff_item.acceptance_state if handoff_item is not None else 'UNCLAIMED',
                execution_posture=execution_posture,
                readiness_state=readiness_state,
                execution_action=execution_action,
                decision_key=_decision_key(governance_item, readiness_state),
                readiness_label=readiness_label,
                owner_lane=governance_item.owner_lane,
                ack_owner_lane=ack_owner_lane,
                routing_lane=governance_item.routing_lane,
                routing_target=governance_item.routing_target,
                queue_key=governance_item.queue_key,
                review_target=governance_item.routing_target,
                priority_band=governance_item.priority_band,
                board_label=governance_item.board_label,
                latest_trust_status=governance_item.latest_trust_status,
                previous_trust_status=governance_item.previous_trust_status,
                latest_summary_line=governance_item.latest_summary_line,
                previous_summary_line=governance_item.previous_summary_line,
                latest_manifest_path=governance_item.latest_manifest_path,
                previous_manifest_path=governance_item.previous_manifest_path,
                recommended_actions=_compose_actions(
                    governance_item,
                    handoff_item=handoff_item,
                    execution_posture=execution_posture,
                    readiness_state=readiness_state,
                    execution_action=execution_action,
                    readiness_label=readiness_label,
                ),
                is_current_pack_kind=governance_item.is_current_pack_kind,
            )
        )
    return OracleOperatorPackExecutionReadiness(
        schema_version='oracle_operator_pack_execution_readiness/v1',
        search_root=str(request.search_root),
        current_pack_kind=request.current_pack_kind,
        queue_key=request.queue_key or getattr(operator_workboard, 'queue_key', None),
        review_target=request.review_target or getattr(operator_workboard, 'review_target', None),
        priority_band=request.priority_band or getattr(operator_workboard, 'priority_band', None),
        board_label=request.board_label or getattr(operator_workboard, 'board_label', None),
        total_execution_readiness_count=len(items),
        items=tuple(items),
    )


def render_operator_pack_execution_readiness_markdown_lines(execution_readiness: OracleOperatorPackExecutionReadiness) -> list[str]:
    lines = ['## Operator Pack Execution Readiness']
    if execution_readiness.queue_key:
        lines.append(f"- Queue: `{execution_readiness.queue_key}`")
    if execution_readiness.review_target:
        lines.append(f"- Review target: `{execution_readiness.review_target}`")
    if execution_readiness.priority_band:
        lines.append(f"- Priority band: `{execution_readiness.priority_band}`")
    if execution_readiness.board_label:
        lines.append(f"- Board: `{execution_readiness.board_label}`")
    for item in execution_readiness.items:
        lines.append('')
        lines.append(f"### {item.pack_kind}")
        lines.append(f"- Execution posture: `{item.execution_posture}`")
        lines.append(f"- Readiness state: `{item.readiness_state}`")
        lines.append(f"- Execution action: `{item.execution_action}`")
        lines.append(f"- Governance: `{item.governance_decision}` / `{item.governance_action}`")
        lines.append(f"- Handoff: `{item.handoff_state}` / `{item.acceptance_state}`")
        lines.append(f"- Routing: `{item.routing_lane}` -> `{item.routing_target}`")
        lines.append(f"- Owner lane: `{item.owner_lane}`")
        lines.append(f"- Ack owner lane: `{item.ack_owner_lane}`")
        lines.append(f"- Readiness label: `{item.readiness_label}`")
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
        lines.append('- No operator pack execution readiness decisions in scope.')
    return lines


__all__ = [
    'OracleOperatorPackExecutionReadinessRequest',
    'OracleOperatorPackExecutionReadinessItem',
    'OracleOperatorPackExecutionReadiness',
    'build_operator_pack_execution_readiness_request',
    'materialize_operator_pack_execution_readiness',
    'render_operator_pack_execution_readiness_markdown_lines',
]
