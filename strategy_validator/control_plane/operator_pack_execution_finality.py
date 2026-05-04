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
from strategy_validator.control_plane.operator_pack_execution_force import (
    OracleOperatorPackExecutionForce,
    OracleOperatorPackExecutionForceItem,
    OracleOperatorPackExecutionForceRequest,
    build_operator_pack_execution_force_request,
    materialize_operator_pack_execution_force,
)
from strategy_validator.control_plane.operator_workboard import OracleOperatorWorkboard


@dataclass(frozen=True)
class OracleOperatorPackExecutionFinalityRequest:
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
    force_label_prefix: str | None = None
    finality_label_prefix: str | None = None


@dataclass(frozen=True)
class OracleOperatorPackExecutionFinalityItem:
    pack_kind: str
    force_posture: str
    force_state: str
    dispatch_outcome: str
    execution_outcome: str
    terminal_decision: str
    terminal_state: str
    terminal_action: str
    finality_key: str
    finality_label: str
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
class OracleOperatorPackExecutionFinality:
    schema_version: str
    search_root: str
    current_pack_kind: str | None
    queue_key: str | None
    review_target: str | None
    priority_band: str | None
    board_label: str | None
    total_terminal_count: int
    items: tuple[OracleOperatorPackExecutionFinalityItem, ...]

    def to_payload(self) -> dict[str, Any]:
        return {
            'schema_version': self.schema_version,
            'search_root': self.search_root,
            'current_pack_kind': self.current_pack_kind,
            'queue_key': self.queue_key,
            'review_target': self.review_target,
            'priority_band': self.priority_band,
            'board_label': self.board_label,
            'total_terminal_count': self.total_terminal_count,
            'items': [
                {
                    'pack_kind': item.pack_kind,
                    'force_posture': item.force_posture,
                    'force_state': item.force_state,
                    'dispatch_outcome': item.dispatch_outcome,
                    'execution_outcome': item.execution_outcome,
                    'terminal_decision': item.terminal_decision,
                    'terminal_state': item.terminal_state,
                    'terminal_action': item.terminal_action,
                    'finality_key': item.finality_key,
                    'finality_label': item.finality_label,
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
                    'previous_manifest_path': str(item.previous_manifest_path) if item.previous_manifest_path else None,
                    'recommended_actions': list(item.recommended_actions),
                    'is_current_pack_kind': item.is_current_pack_kind,
                }
                for item in self.items
            ],
        }


def build_operator_pack_execution_finality_request(*, search_root: Path, repo_root: Path | None = None, current_pack_kind: str | None = None, pack_kinds: Sequence[str] = (), trust_statuses: Sequence[str] = (), summary_line_contains: str | None = None, output_artifact_label_contains: str | None = None, max_items: int = 3, sustained_degraded_threshold: int = 2, queue_key: str | None = None, review_target: str | None = None, priority_band: str | None = None, action_owner_lane: str | None = None, board_label: str | None = None, backup_owner_lane: str | None = None, owner_label_prefix: str | None = None, ack_owner_lane: str | None = None, lease_label_prefix: str | None = None, lifecycle_label_prefix: str | None = None, governance_label_prefix: str | None = None, readiness_label_prefix: str | None = None, dispatch_label_prefix: str | None = None, outcome_label_prefix: str | None = None, exception_label_prefix: str | None = None, approval_label_prefix: str | None = None, disposition_label_prefix: str | None = None, authorization_label_prefix: str | None = None, force_label_prefix: str | None = None, finality_label_prefix: str | None = None) -> OracleOperatorPackExecutionFinalityRequest:
    return OracleOperatorPackExecutionFinalityRequest(
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
        disposition_label_prefix=disposition_label_prefix or None,
        authorization_label_prefix=authorization_label_prefix or None,
        force_label_prefix=force_label_prefix or None,
        finality_label_prefix=finality_label_prefix or None,
    )


def _matching_outcome(force_item: OracleOperatorPackExecutionForceItem, dispatch_outcome: OracleOperatorPackDispatchOutcome | None) -> OracleOperatorPackDispatchOutcomeItem | None:
    if dispatch_outcome is None:
        return None
    for item in dispatch_outcome.items:
        if item.pack_kind == force_item.pack_kind and item.latest_manifest_path == force_item.latest_manifest_path:
            return item
    return next((item for item in dispatch_outcome.items if item.pack_kind == force_item.pack_kind), None)


def _classify_finality(force_item: OracleOperatorPackExecutionForceItem, outcome_item: OracleOperatorPackDispatchOutcomeItem | None) -> tuple[str, str, str]:
    if force_item.force_posture == 'NO_FORCE_REQUIRED' and outcome_item is not None and outcome_item.dispatch_outcome == 'DISPATCH_EXECUTABLE':
        return 'TERMINAL_EXECUTE', 'TERMINAL_EXECUTION_READY', 'EXECUTE_TERMINAL_DECISION'
    if force_item.force_posture == 'FORCED_EXECUTION_ELIGIBLE':
        return 'TERMINAL_FORCE_ELIGIBLE', 'TERMINAL_FORCE_REVIEW_REQUIRED', 'ESCALATE_FORCED_TERMINAL_DECISION'
    return 'TERMINAL_REJECT', 'TERMINAL_EXECUTION_REJECTED', 'REJECT_TERMINAL_DECISION'


def _finality_key(item: OracleOperatorPackExecutionForceItem, terminal_state: str) -> str:
    return '::'.join((item.pack_kind, terminal_state, item.queue_key or 'no-queue', item.owner_lane))


def _compose_actions(force_item: OracleOperatorPackExecutionForceItem, *, outcome_item: OracleOperatorPackDispatchOutcomeItem | None, terminal_decision: str, terminal_action: str, finality_label: str) -> tuple[str, ...]:
    actions: list[str] = []
    if terminal_decision == 'TERMINAL_EXECUTE':
        actions.append(f'Proceed with `{finality_label}` for `{force_item.pack_kind}` because execution is already authorized and no force is required.')
    elif terminal_decision == 'TERMINAL_FORCE_ELIGIBLE':
        reason = outcome_item.block_reason if outcome_item is not None else 'FORCED_EXECUTION_ELIGIBLE'
        actions.append(f'Escalate `{force_item.pack_kind}` for forced terminal review because outcome remains blocked by `{reason}` but forced execution is eligible.')
    else:
        actions.append(f'Reject terminal execution for `{force_item.pack_kind}` because forced execution is not eligible and the path remains blocked.')
    actions.extend(force_item.recommended_actions)
    if outcome_item is not None:
        actions.extend(outcome_item.recommended_actions)
    return tuple(dict.fromkeys(actions))


def materialize_operator_pack_execution_finality(request: OracleOperatorPackExecutionFinalityRequest, *, execution_force: OracleOperatorPackExecutionForce | None = None, execution_force_request: OracleOperatorPackExecutionForceRequest | None = None, dispatch_outcome: OracleOperatorPackDispatchOutcome | None = None, dispatch_outcome_request: OracleOperatorPackDispatchOutcomeRequest | None = None, operator_workboard: OracleOperatorWorkboard | None = None) -> OracleOperatorPackExecutionFinality:
    if execution_force is None:
        execution_force = materialize_operator_pack_execution_force(
            execution_force_request or build_operator_pack_execution_force_request(
                search_root=request.search_root, repo_root=request.repo_root, current_pack_kind=request.current_pack_kind, pack_kinds=request.pack_kinds, trust_statuses=request.trust_statuses, summary_line_contains=request.summary_line_contains, output_artifact_label_contains=request.output_artifact_label_contains, max_items=request.max_items, sustained_degraded_threshold=request.sustained_degraded_threshold, queue_key=request.queue_key or getattr(operator_workboard, 'queue_key', None), review_target=request.review_target or getattr(operator_workboard, 'review_target', None), priority_band=request.priority_band or getattr(operator_workboard, 'priority_band', None), action_owner_lane=request.action_owner_lane or ((operator_workboard.entries[0].action_owner_lane if getattr(operator_workboard, 'entries', None) else None)), board_label=request.board_label or getattr(operator_workboard, 'board_label', None), backup_owner_lane=request.backup_owner_lane, owner_label_prefix=request.owner_label_prefix, ack_owner_lane=request.ack_owner_lane, lease_label_prefix=request.lease_label_prefix, lifecycle_label_prefix=request.lifecycle_label_prefix, governance_label_prefix=request.governance_label_prefix, readiness_label_prefix=request.readiness_label_prefix, dispatch_label_prefix=request.dispatch_label_prefix, outcome_label_prefix=request.outcome_label_prefix, exception_label_prefix=request.exception_label_prefix, approval_label_prefix=request.approval_label_prefix, disposition_label_prefix=request.disposition_label_prefix, authorization_label_prefix=request.authorization_label_prefix, force_label_prefix=request.force_label_prefix,
            ), operator_workboard=operator_workboard,
        )
    if dispatch_outcome is None:
        dispatch_outcome = materialize_operator_pack_dispatch_outcome(
            dispatch_outcome_request or build_operator_pack_dispatch_outcome_request(
                search_root=request.search_root, repo_root=request.repo_root, current_pack_kind=request.current_pack_kind, pack_kinds=request.pack_kinds, trust_statuses=request.trust_statuses, summary_line_contains=request.summary_line_contains, output_artifact_label_contains=request.output_artifact_label_contains, max_items=request.max_items, sustained_degraded_threshold=request.sustained_degraded_threshold, queue_key=request.queue_key or getattr(operator_workboard, 'queue_key', None), review_target=request.review_target or getattr(operator_workboard, 'review_target', None), priority_band=request.priority_band or getattr(operator_workboard, 'priority_band', None), action_owner_lane=request.action_owner_lane or ((operator_workboard.entries[0].action_owner_lane if getattr(operator_workboard, 'entries', None) else None)), board_label=request.board_label or getattr(operator_workboard, 'board_label', None), backup_owner_lane=request.backup_owner_lane, owner_label_prefix=request.owner_label_prefix, ack_owner_lane=request.ack_owner_lane, lease_label_prefix=request.lease_label_prefix, lifecycle_label_prefix=request.lifecycle_label_prefix, governance_label_prefix=request.governance_label_prefix, readiness_label_prefix=request.readiness_label_prefix, dispatch_label_prefix=request.dispatch_label_prefix, outcome_label_prefix=request.outcome_label_prefix,
            ), operator_workboard=operator_workboard,
        )
    items: list[OracleOperatorPackExecutionFinalityItem] = []
    for force_item in execution_force.items[:request.max_items]:
        outcome_item = _matching_outcome(force_item, dispatch_outcome)
        terminal_decision, terminal_state, terminal_action = _classify_finality(force_item, outcome_item)
        finality_label = f"{request.finality_label_prefix or 'execution_finality'}:{terminal_decision.lower()}:{force_item.pack_kind}"
        items.append(OracleOperatorPackExecutionFinalityItem(
            pack_kind=force_item.pack_kind,
            force_posture=force_item.force_posture,
            force_state=force_item.force_state,
            dispatch_outcome=outcome_item.dispatch_outcome if outcome_item is not None else 'DISPATCH_BLOCKED',
            execution_outcome=outcome_item.execution_outcome if outcome_item is not None else 'EXECUTION_BLOCKED',
            terminal_decision=terminal_decision,
            terminal_state=terminal_state,
            terminal_action=terminal_action,
            finality_key=_finality_key(force_item, terminal_state),
            finality_label=finality_label,
            owner_lane=force_item.owner_lane,
            ack_owner_lane=force_item.ack_owner_lane,
            queue_key=force_item.queue_key,
            review_target=force_item.review_target,
            priority_band=force_item.priority_band,
            board_label=force_item.board_label,
            latest_trust_status=force_item.latest_trust_status,
            previous_trust_status=force_item.previous_trust_status,
            latest_summary_line=force_item.latest_summary_line,
            previous_summary_line=force_item.previous_summary_line,
            latest_manifest_path=force_item.latest_manifest_path,
            previous_manifest_path=force_item.previous_manifest_path,
            recommended_actions=_compose_actions(force_item, outcome_item=outcome_item, terminal_decision=terminal_decision, terminal_action=terminal_action, finality_label=finality_label),
            is_current_pack_kind=force_item.is_current_pack_kind,
        ))
    return OracleOperatorPackExecutionFinality(schema_version='oracle_operator_pack_execution_finality/v1', search_root=str(request.search_root), current_pack_kind=request.current_pack_kind, queue_key=request.queue_key, review_target=request.review_target, priority_band=request.priority_band, board_label=request.board_label, total_terminal_count=len(items), items=tuple(items))


def render_operator_pack_execution_finality_markdown_lines(execution_finality: OracleOperatorPackExecutionFinality) -> list[str]:
    lines = ['## Operator Pack Execution Finality']
    if not execution_finality.items:
        lines.append('- No operator-pack terminal execution decisions matched the current filters.')
        return lines
    for item in execution_finality.items:
        lines.extend([
            f"- `{item.pack_kind}` → `{item.terminal_decision}` / `{item.terminal_state}`",
            f"  - Terminal action: `{item.terminal_action}`",
            f"  - Force posture: `{item.force_posture}` / `{item.force_state}`",
            f"  - Dispatch outcome: `{item.dispatch_outcome}` / `{item.execution_outcome}`",
            f"  - Owner lane: `{item.owner_lane}`",
        ])
        if item.latest_summary_line:
            lines.append(f"  - Latest summary: {item.latest_summary_line}")
        for action in item.recommended_actions:
            lines.append(f"  - Action: {action}")
    return lines


__all__ = [
    'OracleOperatorPackExecutionFinalityRequest',
    'OracleOperatorPackExecutionFinalityItem',
    'OracleOperatorPackExecutionFinality',
    'build_operator_pack_execution_finality_request',
    'materialize_operator_pack_execution_finality',
    'render_operator_pack_execution_finality_markdown_lines',
]
