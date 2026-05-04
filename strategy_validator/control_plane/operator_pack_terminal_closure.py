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
from strategy_validator.control_plane.operator_pack_terminal_resolution import (
    OracleOperatorPackTerminalResolution,
    OracleOperatorPackTerminalResolutionItem,
    OracleOperatorPackTerminalResolutionRequest,
    build_operator_pack_terminal_resolution_request,
    materialize_operator_pack_terminal_resolution,
)
from strategy_validator.control_plane.operator_workboard import OracleOperatorWorkboard


@dataclass(frozen=True)
class OracleOperatorPackTerminalClosureRequest:
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
    closure_label_prefix: str | None = None


@dataclass(frozen=True)
class OracleOperatorPackTerminalClosureItem:
    pack_kind: str
    resolution_posture: str
    resolution_state: str
    lifecycle_state: str
    renewal_action: str
    expiry_action: str
    closure_posture: str
    closure_state: str
    closure_action: str
    closure_key: str
    closure_label: str
    owner_lane: str
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
class OracleOperatorPackTerminalClosure:
    schema_version: str
    search_root: str
    current_pack_kind: str | None
    queue_key: str | None
    review_target: str | None
    priority_band: str | None
    board_label: str | None
    total_closure_count: int
    items: tuple[OracleOperatorPackTerminalClosureItem, ...]

    def to_payload(self) -> dict[str, Any]:
        return {
            'schema_version': self.schema_version,
            'search_root': self.search_root,
            'current_pack_kind': self.current_pack_kind,
            'queue_key': self.queue_key,
            'review_target': self.review_target,
            'priority_band': self.priority_band,
            'board_label': self.board_label,
            'total_closure_count': self.total_closure_count,
            'items': [
                {
                    'pack_kind': item.pack_kind,
                    'resolution_posture': item.resolution_posture,
                    'resolution_state': item.resolution_state,
                    'lifecycle_state': item.lifecycle_state,
                    'renewal_action': item.renewal_action,
                    'expiry_action': item.expiry_action,
                    'closure_posture': item.closure_posture,
                    'closure_state': item.closure_state,
                    'closure_action': item.closure_action,
                    'closure_key': item.closure_key,
                    'closure_label': item.closure_label,
                    'owner_lane': item.owner_lane,
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


def build_operator_pack_terminal_closure_request(*, search_root: Path, repo_root: Path | None = None, current_pack_kind: str | None = None, pack_kinds: Sequence[str] = (), trust_statuses: Sequence[str] = (), summary_line_contains: str | None = None, output_artifact_label_contains: str | None = None, max_items: int = 3, sustained_degraded_threshold: int = 2, queue_key: str | None = None, review_target: str | None = None, priority_band: str | None = None, action_owner_lane: str | None = None, board_label: str | None = None, backup_owner_lane: str | None = None, owner_label_prefix: str | None = None, ack_owner_lane: str | None = None, lease_label_prefix: str | None = None, lifecycle_label_prefix: str | None = None, governance_label_prefix: str | None = None, readiness_label_prefix: str | None = None, dispatch_label_prefix: str | None = None, outcome_label_prefix: str | None = None, exception_label_prefix: str | None = None, approval_label_prefix: str | None = None, disposition_label_prefix: str | None = None, authorization_label_prefix: str | None = None, force_label_prefix: str | None = None, finality_label_prefix: str | None = None, resolution_label_prefix: str | None = None, closure_label_prefix: str | None = None) -> OracleOperatorPackTerminalClosureRequest:
    return OracleOperatorPackTerminalClosureRequest(
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
        closure_label_prefix=closure_label_prefix or None,
    )


def _matching_lifecycle(resolution_item: OracleOperatorPackTerminalResolutionItem, claim_lifecycle: OracleOperatorPackClaimLifecycle | None) -> OracleOperatorPackClaimLifecycleItem | None:
    if claim_lifecycle is None:
        return None
    for item in claim_lifecycle.items:
        if item.pack_kind == resolution_item.pack_kind and item.latest_manifest_path == resolution_item.latest_manifest_path:
            return item
    return next((item for item in claim_lifecycle.items if item.pack_kind == resolution_item.pack_kind), None)


def _classify_closure(resolution_item: OracleOperatorPackTerminalResolutionItem, lifecycle_item: OracleOperatorPackClaimLifecycleItem | None) -> tuple[str, str, str]:
    lifecycle_state = lifecycle_item.lifecycle_state if lifecycle_item is not None else 'UNCLAIMED_EXPIRABLE'
    if resolution_item.resolution_posture == 'RESOLVED':
        if lifecycle_state in {'ACTIVE_RELEASE_RECOMMENDED', 'UNCLAIMED_EXPIRABLE'}:
            return 'ARCHIVE_READY', 'TERMINAL_ARCHIVE_READY', 'ARCHIVE_CASE'
        return 'CLOSE_READY', 'TERMINAL_CLOSURE_READY', 'CLOSE_CASE'
    return 'RETAIN_OPEN', 'TERMINAL_RETAIN_OPEN', 'RETAIN_OPEN_CASE'


def _closure_key(item: OracleOperatorPackTerminalResolutionItem, closure_state: str) -> str:
    return '::'.join((item.pack_kind, closure_state, item.queue_key or 'no-queue', item.owner_lane))


def _closure_label(item: OracleOperatorPackTerminalResolutionItem, closure_posture: str, prefix: str | None) -> str:
    base = f"{item.pack_kind.replace('_', ' ')} {closure_posture.replace('_', ' ').lower()}"
    return f"{prefix.strip()} {base}" if prefix else base


def materialize_operator_pack_terminal_closure(request: OracleOperatorPackTerminalClosureRequest, *, operator_workboard: OracleOperatorWorkboard | None = None, terminal_resolution: OracleOperatorPackTerminalResolution | None = None, claim_lifecycle: OracleOperatorPackClaimLifecycle | None = None) -> OracleOperatorPackTerminalClosure:
    if terminal_resolution is None:
        terminal_resolution = materialize_operator_pack_terminal_resolution(
            build_operator_pack_terminal_resolution_request(
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
                dispatch_label_prefix=request.dispatch_label_prefix,
                outcome_label_prefix=request.outcome_label_prefix,
                exception_label_prefix=request.exception_label_prefix,
                approval_label_prefix=request.approval_label_prefix,
                disposition_label_prefix=request.disposition_label_prefix,
                authorization_label_prefix=request.authorization_label_prefix,
                force_label_prefix=request.force_label_prefix,
                finality_label_prefix=request.finality_label_prefix,
                resolution_label_prefix=request.resolution_label_prefix,
            ),
            operator_workboard=operator_workboard,
        )
    if claim_lifecycle is None:
        claim_lifecycle = materialize_operator_pack_claim_lifecycle(
            build_operator_pack_claim_lifecycle_request(
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
    items: list[OracleOperatorPackTerminalClosureItem] = []
    for resolution_item in terminal_resolution.items[: request.max_items]:
        lifecycle_item = _matching_lifecycle(resolution_item, claim_lifecycle)
        closure_posture, closure_state, closure_action = _classify_closure(resolution_item, lifecycle_item)
        recommended = list(resolution_item.recommended_actions)
        if lifecycle_item is not None:
            for action in lifecycle_item.recommended_actions:
                if action not in recommended:
                    recommended.append(action)
        items.append(OracleOperatorPackTerminalClosureItem(
            pack_kind=resolution_item.pack_kind,
            resolution_posture=resolution_item.resolution_posture,
            resolution_state=resolution_item.resolution_state,
            lifecycle_state=lifecycle_item.lifecycle_state if lifecycle_item is not None else 'UNCLAIMED_EXPIRABLE',
            renewal_action=lifecycle_item.renewal_action if lifecycle_item is not None else 'NO_RENEWAL_ACTION',
            expiry_action=lifecycle_item.expiry_action if lifecycle_item is not None else 'ALLOW_EXPIRY',
            closure_posture=closure_posture,
            closure_state=closure_state,
            closure_action=closure_action,
            closure_key=_closure_key(resolution_item, closure_state),
            closure_label=_closure_label(resolution_item, closure_posture, request.closure_label_prefix),
            owner_lane=resolution_item.owner_lane,
            queue_key=resolution_item.queue_key,
            review_target=resolution_item.review_target,
            priority_band=resolution_item.priority_band,
            board_label=resolution_item.board_label,
            latest_trust_status=resolution_item.latest_trust_status,
            previous_trust_status=resolution_item.previous_trust_status,
            latest_summary_line=resolution_item.latest_summary_line,
            previous_summary_line=resolution_item.previous_summary_line,
            latest_manifest_path=resolution_item.latest_manifest_path,
            previous_manifest_path=resolution_item.previous_manifest_path,
            recommended_actions=tuple(dict.fromkeys(recommended + [closure_action.replace('_', ' ').lower()])),
            is_current_pack_kind=resolution_item.is_current_pack_kind,
        ))
    return OracleOperatorPackTerminalClosure(
        schema_version='oracle_operator_pack_terminal_closure/v1',
        search_root=str(request.search_root),
        current_pack_kind=request.current_pack_kind,
        queue_key=request.queue_key,
        review_target=request.review_target,
        priority_band=request.priority_band,
        board_label=request.board_label,
        total_closure_count=len(items),
        items=tuple(items),
    )


def render_operator_pack_terminal_closure_markdown_lines(closure: OracleOperatorPackTerminalClosure) -> list[str]:
    if not closure.items:
        return []
    lines = ['## Operator Pack Terminal Closure', '']
    for item in closure.items:
        lines.append(f"- **{item.pack_kind}** — {item.closure_posture} ({item.closure_state}); action: {item.closure_action}; lifecycle: {item.lifecycle_state}; trust: {item.latest_trust_status or 'unknown'}")
    lines.append('')
    return lines


__all__ = [
    'OracleOperatorPackTerminalClosureRequest',
    'OracleOperatorPackTerminalClosureItem',
    'OracleOperatorPackTerminalClosure',
    'build_operator_pack_terminal_closure_request',
    'materialize_operator_pack_terminal_closure',
    'render_operator_pack_terminal_closure_markdown_lines',
]
