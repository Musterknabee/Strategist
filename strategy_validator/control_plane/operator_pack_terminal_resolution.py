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
from strategy_validator.control_plane.operator_pack_execution_finality import (
    OracleOperatorPackExecutionFinality,
    OracleOperatorPackExecutionFinalityItem,
    OracleOperatorPackExecutionFinalityRequest,
    build_operator_pack_execution_finality_request,
    materialize_operator_pack_execution_finality,
)
from strategy_validator.control_plane.operator_workboard import OracleOperatorWorkboard


@dataclass(frozen=True)
class OracleOperatorPackTerminalResolutionRequest:
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
    resolution_label_prefix: str | None = None


@dataclass(frozen=True)
class OracleOperatorPackTerminalResolutionItem:
    pack_kind: str
    terminal_decision: str
    terminal_state: str
    approval_disposition: str
    signoff_state: str
    resolution_posture: str
    resolution_state: str
    resolution_action: str
    resolution_key: str
    resolution_label: str
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
class OracleOperatorPackTerminalResolution:
    schema_version: str
    search_root: str
    current_pack_kind: str | None
    queue_key: str | None
    review_target: str | None
    priority_band: str | None
    board_label: str | None
    total_resolution_count: int
    items: tuple[OracleOperatorPackTerminalResolutionItem, ...]

    def to_payload(self) -> dict[str, Any]:
        return {
            'schema_version': self.schema_version,
            'search_root': self.search_root,
            'current_pack_kind': self.current_pack_kind,
            'queue_key': self.queue_key,
            'review_target': self.review_target,
            'priority_band': self.priority_band,
            'board_label': self.board_label,
            'total_resolution_count': self.total_resolution_count,
            'items': [
                {
                    'pack_kind': item.pack_kind,
                    'terminal_decision': item.terminal_decision,
                    'terminal_state': item.terminal_state,
                    'approval_disposition': item.approval_disposition,
                    'signoff_state': item.signoff_state,
                    'resolution_posture': item.resolution_posture,
                    'resolution_state': item.resolution_state,
                    'resolution_action': item.resolution_action,
                    'resolution_key': item.resolution_key,
                    'resolution_label': item.resolution_label,
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


def build_operator_pack_terminal_resolution_request(*, search_root: Path, repo_root: Path | None = None, current_pack_kind: str | None = None, pack_kinds: Sequence[str] = (), trust_statuses: Sequence[str] = (), summary_line_contains: str | None = None, output_artifact_label_contains: str | None = None, max_items: int = 3, sustained_degraded_threshold: int = 2, queue_key: str | None = None, review_target: str | None = None, priority_band: str | None = None, action_owner_lane: str | None = None, board_label: str | None = None, backup_owner_lane: str | None = None, owner_label_prefix: str | None = None, ack_owner_lane: str | None = None, lease_label_prefix: str | None = None, lifecycle_label_prefix: str | None = None, governance_label_prefix: str | None = None, readiness_label_prefix: str | None = None, dispatch_label_prefix: str | None = None, outcome_label_prefix: str | None = None, exception_label_prefix: str | None = None, approval_label_prefix: str | None = None, disposition_label_prefix: str | None = None, authorization_label_prefix: str | None = None, force_label_prefix: str | None = None, finality_label_prefix: str | None = None, resolution_label_prefix: str | None = None) -> OracleOperatorPackTerminalResolutionRequest:
    return OracleOperatorPackTerminalResolutionRequest(
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
        resolution_label_prefix=resolution_label_prefix or None,
    )


def _matching_disposition(finality_item: OracleOperatorPackExecutionFinalityItem, approval_disposition: OracleOperatorPackApprovalDisposition | None) -> OracleOperatorPackApprovalDispositionItem | None:
    if approval_disposition is None:
        return None
    for item in approval_disposition.items:
        if item.pack_kind == finality_item.pack_kind and item.latest_manifest_path == finality_item.latest_manifest_path:
            return item
    return next((item for item in approval_disposition.items if item.pack_kind == finality_item.pack_kind), None)


def _classify_resolution(finality_item: OracleOperatorPackExecutionFinalityItem, disposition_item: OracleOperatorPackApprovalDispositionItem | None) -> tuple[str, str, str]:
    disposition = disposition_item.disposition_posture if disposition_item is not None else 'PENDING_SIGNOFF'
    if finality_item.terminal_decision == 'TERMINAL_EXECUTE' and disposition == 'APPROVED':
        return 'RESOLVED', 'TERMINAL_RESOLUTION_RECORDED', 'RECORD_RESOLUTION'
    if finality_item.terminal_decision == 'TERMINAL_REJECT' or disposition == 'DENIED':
        return 'REJECTED_RESOLUTION', 'TERMINAL_RESOLUTION_REJECTED', 'REJECT_RESOLUTION'
    return 'PENDING_RESOLUTION', 'TERMINAL_RESOLUTION_PENDING', 'AWAIT_TERMINAL_RESOLUTION'


def _resolution_key(item: OracleOperatorPackExecutionFinalityItem, resolution_state: str) -> str:
    return '::'.join((item.pack_kind, resolution_state, item.queue_key or 'no-queue', item.owner_lane))


def _compose_actions(finality_item: OracleOperatorPackExecutionFinalityItem, *, disposition_item: OracleOperatorPackApprovalDispositionItem | None, resolution_posture: str, resolution_label: str) -> tuple[str, ...]:
    actions: list[str] = []
    if resolution_posture == 'RESOLVED':
        actions.append(f'Record `{resolution_label}` for `{finality_item.pack_kind}` because terminal execution is approved and sign-off is complete.')
    elif resolution_posture == 'PENDING_RESOLUTION':
        actions.append(f'Hold `{finality_item.pack_kind}` at `{resolution_label}` until sign-off and forced-terminal review complete.')
    else:
        actions.append(f'Reject `{finality_item.pack_kind}` at `{resolution_label}` because terminal execution is denied or terminally rejected.')
    actions.extend(finality_item.recommended_actions)
    if disposition_item is not None:
        actions.extend(disposition_item.recommended_actions)
    return tuple(dict.fromkeys(actions))


def materialize_operator_pack_terminal_resolution(request: OracleOperatorPackTerminalResolutionRequest, *, execution_finality: OracleOperatorPackExecutionFinality | None = None, execution_finality_request: OracleOperatorPackExecutionFinalityRequest | None = None, approval_disposition: OracleOperatorPackApprovalDisposition | None = None, approval_disposition_request: OracleOperatorPackApprovalDispositionRequest | None = None, operator_workboard: OracleOperatorWorkboard | None = None) -> OracleOperatorPackTerminalResolution:
    if execution_finality is None:
        execution_finality = materialize_operator_pack_execution_finality(
            execution_finality_request or build_operator_pack_execution_finality_request(
                search_root=request.search_root, repo_root=request.repo_root, current_pack_kind=request.current_pack_kind, pack_kinds=request.pack_kinds, trust_statuses=request.trust_statuses, summary_line_contains=request.summary_line_contains, output_artifact_label_contains=request.output_artifact_label_contains, max_items=request.max_items, sustained_degraded_threshold=request.sustained_degraded_threshold, queue_key=request.queue_key or getattr(operator_workboard, 'queue_key', None), review_target=request.review_target or getattr(operator_workboard, 'review_target', None), priority_band=request.priority_band or getattr(operator_workboard, 'priority_band', None), action_owner_lane=request.action_owner_lane or ((operator_workboard.entries[0].action_owner_lane if getattr(operator_workboard, 'entries', None) else None)), board_label=request.board_label or getattr(operator_workboard, 'board_label', None), backup_owner_lane=request.backup_owner_lane, owner_label_prefix=request.owner_label_prefix, ack_owner_lane=request.ack_owner_lane, lease_label_prefix=request.lease_label_prefix, lifecycle_label_prefix=request.lifecycle_label_prefix, governance_label_prefix=request.governance_label_prefix, readiness_label_prefix=request.readiness_label_prefix, dispatch_label_prefix=request.dispatch_label_prefix, outcome_label_prefix=request.outcome_label_prefix, exception_label_prefix=request.exception_label_prefix, approval_label_prefix=request.approval_label_prefix, disposition_label_prefix=request.disposition_label_prefix, authorization_label_prefix=request.authorization_label_prefix, force_label_prefix=request.force_label_prefix, finality_label_prefix=request.finality_label_prefix,
            ), operator_workboard=operator_workboard,
        )
    if approval_disposition is None:
        approval_disposition = materialize_operator_pack_approval_disposition(
            approval_disposition_request or build_operator_pack_approval_disposition_request(
                search_root=request.search_root, repo_root=request.repo_root, current_pack_kind=request.current_pack_kind, pack_kinds=request.pack_kinds, trust_statuses=request.trust_statuses, summary_line_contains=request.summary_line_contains, output_artifact_label_contains=request.output_artifact_label_contains, max_items=request.max_items, sustained_degraded_threshold=request.sustained_degraded_threshold, queue_key=request.queue_key or getattr(operator_workboard, 'queue_key', None), review_target=request.review_target or getattr(operator_workboard, 'review_target', None), priority_band=request.priority_band or getattr(operator_workboard, 'priority_band', None), action_owner_lane=request.action_owner_lane or ((operator_workboard.entries[0].action_owner_lane if getattr(operator_workboard, 'entries', None) else None)), board_label=request.board_label or getattr(operator_workboard, 'board_label', None), backup_owner_lane=request.backup_owner_lane, owner_label_prefix=request.owner_label_prefix, ack_owner_lane=request.ack_owner_lane, lease_label_prefix=request.lease_label_prefix, lifecycle_label_prefix=request.lifecycle_label_prefix, governance_label_prefix=request.governance_label_prefix, readiness_label_prefix=request.readiness_label_prefix, dispatch_label_prefix=request.dispatch_label_prefix, outcome_label_prefix=request.outcome_label_prefix, exception_label_prefix=request.exception_label_prefix, approval_label_prefix=request.approval_label_prefix, disposition_label_prefix=request.disposition_label_prefix,
            ), operator_workboard=operator_workboard,
        )
    items:list[OracleOperatorPackTerminalResolutionItem]=[]
    for finality_item in execution_finality.items[:request.max_items]:
        disposition_item = _matching_disposition(finality_item, approval_disposition)
        resolution_posture, resolution_state, resolution_action = _classify_resolution(finality_item, disposition_item)
        resolution_label = f"{request.resolution_label_prefix or 'terminal_resolution'}:{resolution_posture.lower()}:{finality_item.pack_kind}"
        items.append(OracleOperatorPackTerminalResolutionItem(
            pack_kind=finality_item.pack_kind,
            terminal_decision=finality_item.terminal_decision,
            terminal_state=finality_item.terminal_state,
            approval_disposition=disposition_item.disposition_posture if disposition_item is not None else 'PENDING_SIGNOFF',
            signoff_state=disposition_item.signoff_state if disposition_item is not None else 'SIGNOFF_PENDING',
            resolution_posture=resolution_posture,
            resolution_state=resolution_state,
            resolution_action=resolution_action,
            resolution_key=_resolution_key(finality_item, resolution_state),
            resolution_label=resolution_label,
            owner_lane=finality_item.owner_lane,
            ack_owner_lane=finality_item.ack_owner_lane,
            queue_key=finality_item.queue_key,
            review_target=finality_item.review_target,
            priority_band=finality_item.priority_band,
            board_label=finality_item.board_label,
            latest_trust_status=finality_item.latest_trust_status,
            previous_trust_status=finality_item.previous_trust_status,
            latest_summary_line=finality_item.latest_summary_line,
            previous_summary_line=finality_item.previous_summary_line,
            latest_manifest_path=finality_item.latest_manifest_path,
            previous_manifest_path=finality_item.previous_manifest_path,
            recommended_actions=_compose_actions(finality_item, disposition_item=disposition_item, resolution_posture=resolution_posture, resolution_label=resolution_label),
            is_current_pack_kind=finality_item.is_current_pack_kind,
        ))
    return OracleOperatorPackTerminalResolution(schema_version='oracle_operator_pack_terminal_resolution/v1', search_root=str(request.search_root), current_pack_kind=request.current_pack_kind, queue_key=request.queue_key, review_target=request.review_target, priority_band=request.priority_band, board_label=request.board_label, total_resolution_count=len(items), items=tuple(items))


def render_operator_pack_terminal_resolution_markdown_lines(terminal_resolution: OracleOperatorPackTerminalResolution) -> list[str]:
    lines = ['## Operator Pack Terminal Resolution']
    if not terminal_resolution.items:
        lines.append('- No operator-pack terminal resolutions matched the current filters.')
        return lines
    for item in terminal_resolution.items:
        lines.extend([
            f"- `{item.pack_kind}` → `{item.resolution_posture}` / `{item.resolution_state}`",
            f"  - Resolution action: `{item.resolution_action}`",
            f"  - Terminal decision: `{item.terminal_decision}` / `{item.terminal_state}`",
            f"  - Approval disposition: `{item.approval_disposition}` / `{item.signoff_state}`",
            f"  - Owner lane: `{item.owner_lane}`",
        ])
        if item.latest_summary_line:
            lines.append(f"  - Latest summary: {item.latest_summary_line}")
        for action in item.recommended_actions:
            lines.append(f"  - Action: {action}")
    return lines


__all__ = [
    'OracleOperatorPackTerminalResolutionRequest',
    'OracleOperatorPackTerminalResolutionItem',
    'OracleOperatorPackTerminalResolution',
    'build_operator_pack_terminal_resolution_request',
    'materialize_operator_pack_terminal_resolution',
    'render_operator_pack_terminal_resolution_markdown_lines',
]
