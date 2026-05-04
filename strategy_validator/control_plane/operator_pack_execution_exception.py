from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

from strategy_validator.control_plane.operator_pack_dispatch_outcome import (
    OracleOperatorPackDispatchOutcome,
    OracleOperatorPackDispatchOutcomeItem,
    OracleOperatorPackDispatchOutcomeRequest,
    build_operator_pack_dispatch_outcome_request,
    materialize_operator_pack_dispatch_outcome,
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
class OracleOperatorPackExecutionExceptionRequest:
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
    exception_label_prefix: str | None = None


@dataclass(frozen=True)
class OracleOperatorPackExecutionExceptionItem:
    pack_kind: str
    dispatch_outcome: str
    execution_outcome: str
    block_reason: str
    governance_decision: str
    governance_action: str
    exception_posture: str
    override_state: str
    override_action: str
    exception_key: str
    exception_label: str
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
class OracleOperatorPackExecutionException:
    schema_version: str
    search_root: str
    current_pack_kind: str | None
    queue_key: str | None
    review_target: str | None
    priority_band: str | None
    board_label: str | None
    total_exception_count: int
    items: tuple[OracleOperatorPackExecutionExceptionItem, ...]

    def to_payload(self) -> dict[str, Any]:
        return {
            'schema_version': self.schema_version,
            'search_root': self.search_root,
            'current_pack_kind': self.current_pack_kind,
            'queue_key': self.queue_key,
            'review_target': self.review_target,
            'priority_band': self.priority_band,
            'board_label': self.board_label,
            'total_exception_count': self.total_exception_count,
            'item_count': len(self.items),
            'items': [
                {
                    'pack_kind': item.pack_kind,
                    'dispatch_outcome': item.dispatch_outcome,
                    'execution_outcome': item.execution_outcome,
                    'block_reason': item.block_reason,
                    'governance_decision': item.governance_decision,
                    'governance_action': item.governance_action,
                    'exception_posture': item.exception_posture,
                    'override_state': item.override_state,
                    'override_action': item.override_action,
                    'exception_key': item.exception_key,
                    'exception_label': item.exception_label,
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


def build_operator_pack_execution_exception_request(
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
    outcome_label_prefix: str | None = None,
    exception_label_prefix: str | None = None,
) -> OracleOperatorPackExecutionExceptionRequest:
    return OracleOperatorPackExecutionExceptionRequest(
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
    )


def _matching_governance(outcome_item: OracleOperatorPackDispatchOutcomeItem, lease_governance: OracleOperatorPackLeaseGovernance | None) -> OracleOperatorPackLeaseGovernanceItem | None:
    if lease_governance is None:
        return None
    for item in lease_governance.items:
        if item.pack_kind != outcome_item.pack_kind:
            continue
        if item.latest_manifest_path != outcome_item.latest_manifest_path:
            continue
        return item
    return next((item for item in lease_governance.items if item.pack_kind == outcome_item.pack_kind), None)


def _classify_exception(outcome_item: OracleOperatorPackDispatchOutcomeItem, governance_item: OracleOperatorPackLeaseGovernanceItem | None) -> tuple[str, str, str]:
    if outcome_item.dispatch_outcome == 'DISPATCH_EXECUTABLE':
        return 'NO_OVERRIDE_REQUIRED', 'NO_OVERRIDE_NEEDED', 'PROCEED_WITHOUT_OVERRIDE'
    governance_action = governance_item.governance_action if governance_item is not None else outcome_item.governance_action
    if outcome_item.block_reason in {'LEASE_RELEASE_GOVERNED', 'LEASE_EXPIRY_ALLOWED'} or governance_action in {'RELEASE_LEASE', 'ALLOW_EXPIRY'}:
        return 'OVERRIDE_NEEDED', 'OVERRIDE_REQUIRED', 'ESCALATE_OVERRIDE'
    return 'EXCEPTION_ELIGIBLE', 'EXCEPTION_REVIEW_ELIGIBLE', 'REQUEST_EXCEPTION_REVIEW'


def _exception_key(item: OracleOperatorPackDispatchOutcomeItem, override_state: str) -> str:
    return '::'.join((item.pack_kind, override_state, item.block_reason, item.queue_key or 'no-queue'))


def _compose_actions(
    outcome_item: OracleOperatorPackDispatchOutcomeItem,
    *,
    governance_item: OracleOperatorPackLeaseGovernanceItem | None,
    exception_posture: str,
    override_state: str,
    override_action: str,
    exception_label: str,
) -> tuple[str, ...]:
    actions: list[str] = []
    if exception_posture == 'NO_OVERRIDE_REQUIRED':
        actions.append(f'Proceed with `{exception_label}` for `{outcome_item.pack_kind}` because dispatch is executable without override.')
    elif exception_posture == 'EXCEPTION_ELIGIBLE':
        actions.append(f'Request exception review for `{exception_label}` on `{outcome_item.pack_kind}` because execution is held for `{outcome_item.block_reason}`.')
    else:
        actions.append(f'Escalate override for `{exception_label}` on `{outcome_item.pack_kind}` because governance action `{outcome_item.governance_action}` blocks execution.')
    actions.append(f'Override state is `{override_state}` with action `{override_action}`.')
    actions.extend(outcome_item.recommended_actions)
    if governance_item is not None:
        actions.extend(governance_item.recommended_actions)
    return tuple(dict.fromkeys(actions))


def materialize_operator_pack_execution_exception(
    request: OracleOperatorPackExecutionExceptionRequest,
    *,
    dispatch_outcome: OracleOperatorPackDispatchOutcome | None = None,
    dispatch_outcome_request: OracleOperatorPackDispatchOutcomeRequest | None = None,
    lease_governance: OracleOperatorPackLeaseGovernance | None = None,
    lease_governance_request: OracleOperatorPackLeaseGovernanceRequest | None = None,
    operator_workboard: OracleOperatorWorkboard | None = None,
) -> OracleOperatorPackExecutionException:
    if dispatch_outcome is None:
        dispatch_outcome = materialize_operator_pack_dispatch_outcome(
            dispatch_outcome_request or build_operator_pack_dispatch_outcome_request(
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
    items: list[OracleOperatorPackExecutionExceptionItem] = []
    for outcome_item in dispatch_outcome.items:
        governance_item = _matching_governance(outcome_item, lease_governance)
        exception_posture, override_state, override_action = _classify_exception(outcome_item, governance_item)
        exception_label = f"{request.exception_label_prefix or 'exception'}:{outcome_item.pack_kind}:{override_state.lower()}"
        items.append(OracleOperatorPackExecutionExceptionItem(
            pack_kind=outcome_item.pack_kind,
            dispatch_outcome=outcome_item.dispatch_outcome,
            execution_outcome=outcome_item.execution_outcome,
            block_reason=outcome_item.block_reason,
            governance_decision=outcome_item.governance_decision,
            governance_action=outcome_item.governance_action,
            exception_posture=exception_posture,
            override_state=override_state,
            override_action=override_action,
            exception_key=_exception_key(outcome_item, override_state),
            exception_label=exception_label,
            owner_lane=outcome_item.owner_lane,
            ack_owner_lane=outcome_item.ack_owner_lane,
            routing_lane=outcome_item.routing_lane,
            routing_target=outcome_item.routing_target,
            queue_key=outcome_item.queue_key,
            review_target=outcome_item.review_target,
            priority_band=outcome_item.priority_band,
            board_label=outcome_item.board_label,
            latest_trust_status=outcome_item.latest_trust_status,
            previous_trust_status=outcome_item.previous_trust_status,
            latest_summary_line=outcome_item.latest_summary_line,
            previous_summary_line=outcome_item.previous_summary_line,
            latest_manifest_path=outcome_item.latest_manifest_path,
            previous_manifest_path=outcome_item.previous_manifest_path,
            recommended_actions=_compose_actions(
                outcome_item,
                governance_item=governance_item,
                exception_posture=exception_posture,
                override_state=override_state,
                override_action=override_action,
                exception_label=exception_label,
            ),
            is_current_pack_kind=outcome_item.is_current_pack_kind,
        ))
    return OracleOperatorPackExecutionException(
        schema_version='oracle_operator_pack_execution_exception/v1',
        search_root=str(request.search_root),
        current_pack_kind=request.current_pack_kind,
        queue_key=request.queue_key,
        review_target=request.review_target,
        priority_band=request.priority_band,
        board_label=request.board_label,
        total_exception_count=len(items),
        items=tuple(items),
    )


def render_operator_pack_execution_exception_markdown_lines(execution_exception: OracleOperatorPackExecutionException) -> list[str]:
    lines = ['## Operator Pack Execution Exceptions']
    if not execution_exception.items:
        lines.append('- No operator-pack execution exception states matched the current filters.')
        return lines
    for item in execution_exception.items:
        lines.extend([
            f"- `{item.pack_kind}` → `{item.exception_posture}` / `{item.override_state}`",
            f"  - Override action: `{item.override_action}`",
            f"  - Dispatch outcome: `{item.dispatch_outcome}` ({item.block_reason})",
            f"  - Governance: `{item.governance_decision}` / `{item.governance_action}`",
            f"  - Owner lane: `{item.owner_lane}`",
            f"  - Routing: `{item.routing_lane}` -> `{item.routing_target}`",
        ])
        if item.latest_summary_line:
            lines.append(f"  - Latest summary: {item.latest_summary_line}")
        for action in item.recommended_actions:
            lines.append(f"  - Action: {action}")
    return lines


__all__ = [
    'OracleOperatorPackExecutionExceptionRequest',
    'OracleOperatorPackExecutionExceptionItem',
    'OracleOperatorPackExecutionException',
    'build_operator_pack_execution_exception_request',
    'materialize_operator_pack_execution_exception',
    'render_operator_pack_execution_exception_markdown_lines',
]
