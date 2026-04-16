from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any, Sequence

from strategy_validator.control_plane.operator_workboard import OracleOperatorWorkboard

if TYPE_CHECKING:
    from strategy_validator.control_plane.operator_pack_approval_needed import (
        OracleOperatorPackApprovalNeeded,
        OracleOperatorPackApprovalNeededItem,
        OracleOperatorPackApprovalNeededRequest,
    )
    from strategy_validator.control_plane.operator_pack_claim_lease import (
        OracleOperatorPackClaimLease,
        OracleOperatorPackClaimLeaseItem,
        OracleOperatorPackClaimLeaseRequest,
    )


@dataclass(frozen=True)
class OracleOperatorPackApprovalDispositionRequest:
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


@dataclass(frozen=True)
class OracleOperatorPackApprovalDispositionItem:
    pack_kind: str
    approval_posture: str
    approval_state: str
    approval_action: str
    claim_state: str
    lease_state: str
    disposition_posture: str
    signoff_state: str
    signoff_action: str
    memo_key: str
    memo_label: str
    signoff_key: str
    signoff_label: str
    owner_lane: str
    ack_owner_lane: str
    backup_owner_lane: str
    owner_label: str
    handoff_target: str
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
class OracleOperatorPackApprovalDisposition:
    schema_version: str
    search_root: str
    current_pack_kind: str | None
    queue_key: str | None
    review_target: str | None
    priority_band: str | None
    board_label: str | None
    total_disposition_count: int
    items: tuple[OracleOperatorPackApprovalDispositionItem, ...]

    def to_payload(self) -> dict[str, Any]:
        return {
            'schema_version': self.schema_version,
            'search_root': self.search_root,
            'current_pack_kind': self.current_pack_kind,
            'queue_key': self.queue_key,
            'review_target': self.review_target,
            'priority_band': self.priority_band,
            'board_label': self.board_label,
            'total_disposition_count': self.total_disposition_count,
            'item_count': len(self.items),
            'items': [
                {
                    'pack_kind': item.pack_kind,
                    'approval_posture': item.approval_posture,
                    'approval_state': item.approval_state,
                    'approval_action': item.approval_action,
                    'claim_state': item.claim_state,
                    'lease_state': item.lease_state,
                    'disposition_posture': item.disposition_posture,
                    'signoff_state': item.signoff_state,
                    'signoff_action': item.signoff_action,
                    'memo_key': item.memo_key,
                    'memo_label': item.memo_label,
                    'signoff_key': item.signoff_key,
                    'signoff_label': item.signoff_label,
                    'owner_lane': item.owner_lane,
                    'ack_owner_lane': item.ack_owner_lane,
                    'backup_owner_lane': item.backup_owner_lane,
                    'owner_label': item.owner_label,
                    'handoff_target': item.handoff_target,
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


def build_operator_pack_approval_disposition_request(*, search_root: Path, repo_root: Path | None = None, current_pack_kind: str | None = None, pack_kinds: Sequence[str] = (), trust_statuses: Sequence[str] = (), summary_line_contains: str | None = None, output_artifact_label_contains: str | None = None, max_items: int = 3, sustained_degraded_threshold: int = 2, queue_key: str | None = None, review_target: str | None = None, priority_band: str | None = None, action_owner_lane: str | None = None, board_label: str | None = None, backup_owner_lane: str | None = None, owner_label_prefix: str | None = None, ack_owner_lane: str | None = None, lease_label_prefix: str | None = None, lifecycle_label_prefix: str | None = None, governance_label_prefix: str | None = None, readiness_label_prefix: str | None = None, dispatch_label_prefix: str | None = None, outcome_label_prefix: str | None = None, exception_label_prefix: str | None = None, approval_label_prefix: str | None = None, disposition_label_prefix: str | None = None) -> OracleOperatorPackApprovalDispositionRequest:
    return OracleOperatorPackApprovalDispositionRequest(
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
    )


def _matching_claim(item: OracleOperatorPackApprovalNeededItem, claim_lease: OracleOperatorPackClaimLease | None) -> OracleOperatorPackClaimLeaseItem | None:
    if claim_lease is None:
        return None
    for entry in claim_lease.items:
        if entry.pack_kind != item.pack_kind:
            continue
        if entry.latest_manifest_path != item.latest_manifest_path:
            continue
        return entry
    return next((entry for entry in claim_lease.items if entry.pack_kind == item.pack_kind), None)


def _classify_disposition(approval_item: OracleOperatorPackApprovalNeededItem, claim_item: OracleOperatorPackClaimLeaseItem | None) -> tuple[str, str, str]:
    claim_state = claim_item.claim_state if claim_item is not None else 'CLAIM_UNCLAIMED'
    lease_state = claim_item.lease_state if claim_item is not None else 'NO_ACTIVE_LEASE'
    if approval_item.approval_posture == 'NO_APPROVAL_NEEDED':
        return 'APPROVED', 'SIGNED_OFF', 'PROCEED_WITH_SIGNOFF'
    if claim_state == 'CLAIM_ACTIVE' and lease_state == 'LEASE_ACTIVE':
        return 'PENDING_SIGNOFF', 'SIGNOFF_PENDING', 'REQUEST_SIGNOFF'
    if claim_state == 'CLAIM_PENDING' or lease_state == 'LEASE_PENDING_ACQUISITION':
        return 'PENDING_SIGNOFF', 'SIGNOFF_PENDING', 'REQUEST_SIGNOFF'
    return 'DENIED', 'SIGNOFF_DENIED', 'DENY_SIGNOFF'


def _signoff_key(item: OracleOperatorPackApprovalNeededItem, signoff_state: str) -> str:
    return '::'.join((item.pack_kind, signoff_state, item.queue_key or 'no-queue', item.owner_lane))


def _compose_actions(approval_item: OracleOperatorPackApprovalNeededItem, *, claim_item: OracleOperatorPackClaimLeaseItem | None, disposition_posture: str, signoff_action: str, signoff_label: str) -> tuple[str, ...]:
    actions: list[str] = []
    if disposition_posture == 'APPROVED':
        actions.append(f'Proceed with `{approval_item.pack_kind}` under `{signoff_label}`; no additional sign-off is needed.')
    elif disposition_posture == 'PENDING_SIGNOFF':
        actions.append(f'Request formal sign-off for `{approval_item.pack_kind}` under `{signoff_label}` before proceeding.')
    else:
        actions.append(f'Deny sign-off for `{approval_item.pack_kind}` under `{signoff_label}` until claim/lease prerequisites are satisfied.')
    if claim_item is not None:
        actions.append(f'Claim/lease context is `{claim_item.claim_state}` / `{claim_item.lease_state}`.')
    actions.append(f'Sign-off action is `{signoff_action}`.')
    actions.extend(approval_item.recommended_actions)
    return tuple(actions)


def materialize_operator_pack_approval_disposition(request: OracleOperatorPackApprovalDispositionRequest, *, approval_needed: OracleOperatorPackApprovalNeeded | None = None, approval_needed_request: OracleOperatorPackApprovalNeededRequest | None = None, claim_lease: OracleOperatorPackClaimLease | None = None, claim_lease_request: OracleOperatorPackClaimLeaseRequest | None = None, operator_workboard: OracleOperatorWorkboard | None = None) -> OracleOperatorPackApprovalDisposition:
    from strategy_validator.control_plane.operator_pack_approval_needed import (
        build_operator_pack_approval_needed_request,
        materialize_operator_pack_approval_needed,
    )
    from strategy_validator.control_plane.operator_pack_claim_lease import (
        build_operator_pack_claim_lease_request,
        materialize_operator_pack_claim_lease,
    )
    if approval_needed is None:
        approval_needed = materialize_operator_pack_approval_needed(
            approval_needed_request or build_operator_pack_approval_needed_request(
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
                queue_key=request.queue_key,
                review_target=request.review_target,
                priority_band=request.priority_band,
                action_owner_lane=request.action_owner_lane,
                board_label=request.board_label,
                backup_owner_lane=request.backup_owner_lane,
                owner_label_prefix=request.owner_label_prefix,
                ack_owner_lane=request.ack_owner_lane,
                lease_label_prefix=request.lease_label_prefix,
            ),
            operator_workboard=operator_workboard,
        )
    items: list[OracleOperatorPackApprovalDispositionItem] = []
    for approval_item in approval_needed.items:
        claim_item = _matching_claim(approval_item, claim_lease)
        disposition_posture, signoff_state, signoff_action = _classify_disposition(approval_item, claim_item)
        signoff_label = f"{request.disposition_label_prefix or 'signoff'}:{approval_item.owner_lane}"
        items.append(OracleOperatorPackApprovalDispositionItem(
            pack_kind=approval_item.pack_kind,
            approval_posture=approval_item.approval_posture,
            approval_state=approval_item.approval_state,
            approval_action=approval_item.approval_action,
            claim_state=claim_item.claim_state if claim_item is not None else 'CLAIM_UNCLAIMED',
            lease_state=claim_item.lease_state if claim_item is not None else 'NO_ACTIVE_LEASE',
            disposition_posture=disposition_posture,
            signoff_state=signoff_state,
            signoff_action=signoff_action,
            memo_key=approval_item.memo_key,
            memo_label=approval_item.memo_label,
            signoff_key=_signoff_key(approval_item, signoff_state),
            signoff_label=signoff_label,
            owner_lane=approval_item.owner_lane,
            ack_owner_lane=approval_item.ack_owner_lane,
            backup_owner_lane=approval_item.backup_owner_lane,
            owner_label=approval_item.owner_label,
            handoff_target=approval_item.handoff_target,
            queue_key=approval_item.queue_key,
            review_target=approval_item.review_target,
            priority_band=approval_item.priority_band,
            board_label=approval_item.board_label,
            latest_trust_status=approval_item.latest_trust_status,
            previous_trust_status=approval_item.previous_trust_status,
            latest_summary_line=approval_item.latest_summary_line,
            previous_summary_line=approval_item.previous_summary_line,
            latest_manifest_path=approval_item.latest_manifest_path,
            previous_manifest_path=approval_item.previous_manifest_path,
            recommended_actions=_compose_actions(approval_item, claim_item=claim_item, disposition_posture=disposition_posture, signoff_action=signoff_action, signoff_label=signoff_label),
            is_current_pack_kind=approval_item.is_current_pack_kind,
        ))
    return OracleOperatorPackApprovalDisposition(
        schema_version='oracle_operator_pack_approval_disposition/v1',
        search_root=str(request.search_root),
        current_pack_kind=request.current_pack_kind,
        queue_key=request.queue_key,
        review_target=request.review_target,
        priority_band=request.priority_band,
        board_label=request.board_label,
        total_disposition_count=len(items),
        items=tuple(items),
    )


def render_operator_pack_approval_disposition_markdown_lines(approval_disposition: OracleOperatorPackApprovalDisposition) -> list[str]:
    lines = ['## Operator Pack Approval Disposition']
    if not approval_disposition.items:
        lines.append('- No operator-pack approval disposition states matched the current filters.')
        return lines
    for item in approval_disposition.items:
        lines.extend([
            f"- `{item.pack_kind}` → `{item.disposition_posture}` / `{item.signoff_state}`",
            f"  - Sign-off action: `{item.signoff_action}`",
            f"  - Approval posture: `{item.approval_posture}` / `{item.approval_state}`",
            f"  - Claim/lease: `{item.claim_state}` / `{item.lease_state}`",
            f"  - Owner: `{item.owner_label}`",
        ])
        if item.latest_summary_line:
            lines.append(f"  - Latest summary: {item.latest_summary_line}")
        for action in item.recommended_actions:
            lines.append(f"  - Action: {action}")
    return lines


__all__ = [
    'OracleOperatorPackApprovalDispositionRequest',
    'OracleOperatorPackApprovalDispositionItem',
    'OracleOperatorPackApprovalDisposition',
    'build_operator_pack_approval_disposition_request',
    'materialize_operator_pack_approval_disposition',
    'render_operator_pack_approval_disposition_markdown_lines',
]
