from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

from strategy_validator.control_plane.operator_pack_execution_authorization import (
    OracleOperatorPackExecutionAuthorization,
    OracleOperatorPackExecutionAuthorizationItem,
    OracleOperatorPackExecutionAuthorizationRequest,
    build_operator_pack_execution_authorization_request,
    materialize_operator_pack_execution_authorization,
)
from strategy_validator.control_plane.operator_pack_execution_exception import (
    OracleOperatorPackExecutionException,
    OracleOperatorPackExecutionExceptionItem,
    OracleOperatorPackExecutionExceptionRequest,
    build_operator_pack_execution_exception_request,
    materialize_operator_pack_execution_exception,
)
from strategy_validator.control_plane.operator_workboard import OracleOperatorWorkboard


@dataclass(frozen=True)
class OracleOperatorPackExecutionForceRequest:
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


@dataclass(frozen=True)
class OracleOperatorPackExecutionForceItem:
    pack_kind: str
    authorization_posture: str
    authority_state: str
    exception_posture: str
    override_state: str
    force_posture: str
    force_state: str
    force_action: str
    force_key: str
    force_label: str
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
class OracleOperatorPackExecutionForce:
    schema_version: str
    search_root: str
    current_pack_kind: str | None
    queue_key: str | None
    review_target: str | None
    priority_band: str | None
    board_label: str | None
    total_force_count: int
    items: tuple[OracleOperatorPackExecutionForceItem, ...]

    def to_payload(self) -> dict[str, Any]:
        return {
            'schema_version': self.schema_version,
            'search_root': self.search_root,
            'current_pack_kind': self.current_pack_kind,
            'queue_key': self.queue_key,
            'review_target': self.review_target,
            'priority_band': self.priority_band,
            'board_label': self.board_label,
            'total_force_count': self.total_force_count,
            'item_count': len(self.items),
            'items': [
                {
                    'pack_kind': item.pack_kind,
                    'authorization_posture': item.authorization_posture,
                    'authority_state': item.authority_state,
                    'exception_posture': item.exception_posture,
                    'override_state': item.override_state,
                    'force_posture': item.force_posture,
                    'force_state': item.force_state,
                    'force_action': item.force_action,
                    'force_key': item.force_key,
                    'force_label': item.force_label,
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


def build_operator_pack_execution_force_request(*, search_root: Path, repo_root: Path | None = None, current_pack_kind: str | None = None, pack_kinds: Sequence[str] = (), trust_statuses: Sequence[str] = (), summary_line_contains: str | None = None, output_artifact_label_contains: str | None = None, max_items: int = 3, sustained_degraded_threshold: int = 2, queue_key: str | None = None, review_target: str | None = None, priority_band: str | None = None, action_owner_lane: str | None = None, board_label: str | None = None, backup_owner_lane: str | None = None, owner_label_prefix: str | None = None, ack_owner_lane: str | None = None, lease_label_prefix: str | None = None, lifecycle_label_prefix: str | None = None, governance_label_prefix: str | None = None, readiness_label_prefix: str | None = None, dispatch_label_prefix: str | None = None, outcome_label_prefix: str | None = None, exception_label_prefix: str | None = None, approval_label_prefix: str | None = None, disposition_label_prefix: str | None = None, authorization_label_prefix: str | None = None, force_label_prefix: str | None = None) -> OracleOperatorPackExecutionForceRequest:
    return OracleOperatorPackExecutionForceRequest(
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
    )


def _matching_exception(item: OracleOperatorPackExecutionAuthorizationItem, execution_exception: OracleOperatorPackExecutionException | None) -> OracleOperatorPackExecutionExceptionItem | None:
    if execution_exception is None:
        return None
    for entry in execution_exception.items:
        if entry.pack_kind != item.pack_kind:
            continue
        if entry.latest_manifest_path != item.latest_manifest_path:
            continue
        return entry
    return next((entry for entry in execution_exception.items if entry.pack_kind == item.pack_kind), None)


def _classify_force(auth_item: OracleOperatorPackExecutionAuthorizationItem, exception_item: OracleOperatorPackExecutionExceptionItem | None) -> tuple[str, str, str]:
    if auth_item.authorization_posture == 'AUTHORIZED':
        return 'NO_FORCE_REQUIRED', 'FORCE_NOT_NEEDED', 'PROCEED_WITH_AUTHORITY'
    if exception_item is not None and exception_item.exception_posture == 'EXCEPTION_ELIGIBLE':
        return 'FORCED_EXECUTION_ELIGIBLE', 'FORCE_EXCEPTION_ELIGIBLE', 'REQUEST_FORCED_EXECUTION_EXCEPTION'
    return 'NON_OVERRIDABLE_REJECTION', 'FORCE_REJECTED', 'REJECT_FORCED_EXECUTION'


def _force_key(item: OracleOperatorPackExecutionAuthorizationItem, force_state: str) -> str:
    return '::'.join((item.pack_kind, force_state, item.queue_key or 'no-queue', item.owner_lane))


def _compose_actions(auth_item: OracleOperatorPackExecutionAuthorizationItem, *, exception_item: OracleOperatorPackExecutionExceptionItem | None, force_posture: str, force_action: str, force_label: str) -> tuple[str, ...]:
    actions: list[str] = []
    if force_posture == 'NO_FORCE_REQUIRED':
        actions.append(f'Proceed under existing authority for `{auth_item.pack_kind}`; `{force_label}` is informational only.')
    elif force_posture == 'FORCED_EXECUTION_ELIGIBLE':
        actions.append(f'Request forced-execution exception for `{auth_item.pack_kind}` under `{force_label}`.')
    else:
        actions.append(f'Reject forced execution for `{auth_item.pack_kind}` under `{force_label}` because the rejection is non-overridable.')
    if exception_item is not None:
        actions.append(f'Exception posture is `{exception_item.exception_posture}` with override state `{exception_item.override_state}`.')
    actions.append(f'Force action is `{force_action}`.')
    actions.extend(auth_item.recommended_actions)
    if exception_item is not None:
        actions.extend(exception_item.recommended_actions)
    return tuple(dict.fromkeys(actions))


def materialize_operator_pack_execution_force(request: OracleOperatorPackExecutionForceRequest, *, execution_authorization: OracleOperatorPackExecutionAuthorization | None = None, execution_authorization_request: OracleOperatorPackExecutionAuthorizationRequest | None = None, execution_exception: OracleOperatorPackExecutionException | None = None, execution_exception_request: OracleOperatorPackExecutionExceptionRequest | None = None, operator_workboard: OracleOperatorWorkboard | None = None) -> OracleOperatorPackExecutionForce:
    if execution_authorization is None:
        execution_authorization = materialize_operator_pack_execution_authorization(
            execution_authorization_request or build_operator_pack_execution_authorization_request(
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
                authorization_label_prefix=request.authorization_label_prefix,
            ),
            operator_workboard=operator_workboard,
        )
    if execution_exception is None:
        execution_exception = materialize_operator_pack_execution_exception(
            execution_exception_request or build_operator_pack_execution_exception_request(
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
            ),
            operator_workboard=operator_workboard,
        )

    items: list[OracleOperatorPackExecutionForceItem] = []
    for auth_item in execution_authorization.items[: request.max_items]:
        exception_item = _matching_exception(auth_item, execution_exception)
        force_posture, force_state, force_action = _classify_force(auth_item, exception_item)
        force_label = f"{request.force_label_prefix or 'forced_execution'}:{force_posture.lower()}:{auth_item.pack_kind}"
        items.append(OracleOperatorPackExecutionForceItem(
            pack_kind=auth_item.pack_kind,
            authorization_posture=auth_item.authorization_posture,
            authority_state=auth_item.authority_state,
            exception_posture=exception_item.exception_posture if exception_item is not None else 'NO_OVERRIDE_REQUIRED',
            override_state=exception_item.override_state if exception_item is not None else 'NO_OVERRIDE_NEEDED',
            force_posture=force_posture,
            force_state=force_state,
            force_action=force_action,
            force_key=_force_key(auth_item, force_state),
            force_label=force_label,
            owner_lane=auth_item.owner_lane,
            ack_owner_lane=auth_item.ack_owner_lane,
            queue_key=auth_item.queue_key,
            review_target=auth_item.review_target,
            priority_band=auth_item.priority_band,
            board_label=auth_item.board_label,
            latest_trust_status=auth_item.latest_trust_status,
            previous_trust_status=auth_item.previous_trust_status,
            latest_summary_line=auth_item.latest_summary_line,
            previous_summary_line=auth_item.previous_summary_line,
            latest_manifest_path=auth_item.latest_manifest_path,
            previous_manifest_path=auth_item.previous_manifest_path,
            recommended_actions=_compose_actions(auth_item, exception_item=exception_item, force_posture=force_posture, force_action=force_action, force_label=force_label),
            is_current_pack_kind=auth_item.is_current_pack_kind,
        ))
    return OracleOperatorPackExecutionForce(
        schema_version='oracle_operator_pack_execution_force/v1',
        search_root=str(request.search_root),
        current_pack_kind=request.current_pack_kind,
        queue_key=request.queue_key,
        review_target=request.review_target,
        priority_band=request.priority_band,
        board_label=request.board_label,
        total_force_count=len(items),
        items=tuple(items),
    )


def render_operator_pack_execution_force_markdown_lines(execution_force: OracleOperatorPackExecutionForce) -> list[str]:
    lines = ['## Operator Pack Forced Execution']
    if not execution_force.items:
        lines.append('- No operator-pack forced-execution states matched the current filters.')
        return lines
    for item in execution_force.items:
        lines.extend([
            f"- `{item.pack_kind}` → `{item.force_posture}` / `{item.force_state}`",
            f"  - Force action: `{item.force_action}`",
            f"  - Authorization: `{item.authorization_posture}` / `{item.authority_state}`",
            f"  - Exception posture: `{item.exception_posture}` / `{item.override_state}`",
            f"  - Owner lane: `{item.owner_lane}`",
        ])
        if item.latest_summary_line:
            lines.append(f"  - Latest summary: {item.latest_summary_line}")
        for action in item.recommended_actions:
            lines.append(f"  - Action: {action}")
    return lines


__all__ = [
    'OracleOperatorPackExecutionForceRequest',
    'OracleOperatorPackExecutionForceItem',
    'OracleOperatorPackExecutionForce',
    'build_operator_pack_execution_force_request',
    'materialize_operator_pack_execution_force',
    'render_operator_pack_execution_force_markdown_lines',
]
