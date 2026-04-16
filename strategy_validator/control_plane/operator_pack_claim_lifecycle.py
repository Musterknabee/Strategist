from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

from strategy_validator.control_plane.operator_pack_claim_lease import (
    OracleOperatorPackClaimLease,
    OracleOperatorPackClaimLeaseItem,
    OracleOperatorPackClaimLeaseRequest,
    build_operator_pack_claim_lease_request,
    materialize_operator_pack_claim_lease,
)
from strategy_validator.control_plane.operator_workboard import OracleOperatorWorkboard

_DEGRADED_STATUSES = {"TRUST_RESTRICTED", "UNTRUSTED"}


@dataclass(frozen=True)
class OracleOperatorPackClaimLifecycleRequest:
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


@dataclass(frozen=True)
class OracleOperatorPackClaimLifecycleItem:
    pack_kind: str
    claim_state: str
    lease_state: str
    lifecycle_state: str
    renewal_action: str
    expiry_action: str
    lifecycle_key: str
    lease_key: str
    owner_lane: str
    lease_owner_label: str
    lifecycle_label: str
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
class OracleOperatorPackClaimLifecycle:
    schema_version: str
    search_root: str
    current_pack_kind: str | None
    queue_key: str | None
    review_target: str | None
    priority_band: str | None
    board_label: str | None
    total_claim_lifecycle_count: int
    items: tuple[OracleOperatorPackClaimLifecycleItem, ...]

    def to_payload(self) -> dict[str, Any]:
        return {
            'schema_version': self.schema_version,
            'search_root': self.search_root,
            'current_pack_kind': self.current_pack_kind,
            'queue_key': self.queue_key,
            'review_target': self.review_target,
            'priority_band': self.priority_band,
            'board_label': self.board_label,
            'total_claim_lifecycle_count': self.total_claim_lifecycle_count,
            'item_count': len(self.items),
            'items': [
                {
                    'pack_kind': item.pack_kind,
                    'claim_state': item.claim_state,
                    'lease_state': item.lease_state,
                    'lifecycle_state': item.lifecycle_state,
                    'renewal_action': item.renewal_action,
                    'expiry_action': item.expiry_action,
                    'lifecycle_key': item.lifecycle_key,
                    'lease_key': item.lease_key,
                    'owner_lane': item.owner_lane,
                    'lease_owner_label': item.lease_owner_label,
                    'lifecycle_label': item.lifecycle_label,
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


def build_operator_pack_claim_lifecycle_request(
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
) -> OracleOperatorPackClaimLifecycleRequest:
    return OracleOperatorPackClaimLifecycleRequest(
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
    )


def _lifecycle_key(item: OracleOperatorPackClaimLeaseItem) -> str:
    queue_key = item.queue_key or 'no-queue'
    return '::'.join((item.pack_kind, queue_key, item.review_target, item.owner_lane, item.claim_state))


def _classify_lifecycle(item: OracleOperatorPackClaimLeaseItem) -> tuple[str, str, str]:
    latest = item.latest_trust_status or ''
    previous = item.previous_trust_status or ''
    if item.claim_state == 'CLAIM_ACTIVE':
        if latest in _DEGRADED_STATUSES and previous != latest:
            return 'ACTIVE_RELEASE_RECOMMENDED', 'RELEASE_CLAIM', 'RELEASE_OR_EXPIRE'
        return 'ACTIVE_RENEWAL_REQUIRED', 'RENEW_CLAIM', 'MAINTAIN_ACTIVE_CLAIM'
    if item.claim_state == 'CLAIM_PENDING':
        return 'PENDING_ACQUISITION', 'ACQUIRE_AND_RENEW', 'HOLD_PENDING_CLAIM'
    return 'UNCLAIMED_EXPIRABLE', 'NO_RENEWAL_ACTION', 'ALLOW_EXPIRY'


def _compose_actions(
    item: OracleOperatorPackClaimLeaseItem,
    *,
    lifecycle_state: str,
    renewal_action: str,
    expiry_action: str,
    lifecycle_label: str,
) -> tuple[str, ...]:
    actions: list[str] = []
    if renewal_action == 'RENEW_CLAIM':
        actions.append(f'Renew the active claim lifecycle for `{lifecycle_label}` and keep `{item.pack_kind}` under governed review.')
    elif renewal_action == 'RELEASE_CLAIM':
        actions.append(f'Release or downshift the active claim lifecycle for `{lifecycle_label}` because `{item.pack_kind}` degraded materially.')
    elif renewal_action == 'ACQUIRE_AND_RENEW':
        actions.append(f'Acquire the pending claim for `{lifecycle_label}` before starting any renewal window for `{item.pack_kind}`.')
    else:
        actions.append(f'Allow `{item.pack_kind}` to expire unclaimed until an operator explicitly acquires ownership.')
    actions.append(f'Lifecycle state is `{lifecycle_state}` with expiry action `{expiry_action}`.')
    actions.extend(item.recommended_actions)
    return tuple(actions)


def materialize_operator_pack_claim_lifecycle(
    request: OracleOperatorPackClaimLifecycleRequest,
    *,
    claim_lease: OracleOperatorPackClaimLease | None = None,
    claim_lease_request: OracleOperatorPackClaimLeaseRequest | None = None,
    operator_workboard: OracleOperatorWorkboard | None = None,
) -> OracleOperatorPackClaimLifecycle:
    if claim_lease is None:
        claim_lease = materialize_operator_pack_claim_lease(
            claim_lease_request
            or build_operator_pack_claim_lease_request(
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
            ),
            operator_workboard=operator_workboard,
        )
    items = []
    for claim_item in claim_lease.items[: request.max_items]:
        lifecycle_state, renewal_action, expiry_action = _classify_lifecycle(claim_item)
        lifecycle_label = f"{request.lifecycle_label_prefix or 'lifecycle'}:{claim_item.pack_kind}:{claim_item.owner_lane}"
        items.append(
            OracleOperatorPackClaimLifecycleItem(
                pack_kind=claim_item.pack_kind,
                claim_state=claim_item.claim_state,
                lease_state=claim_item.lease_state,
                lifecycle_state=lifecycle_state,
                renewal_action=renewal_action,
                expiry_action=expiry_action,
                lifecycle_key=_lifecycle_key(claim_item),
                lease_key=claim_item.lease_key,
                owner_lane=claim_item.owner_lane,
                lease_owner_label=claim_item.lease_owner_label,
                lifecycle_label=lifecycle_label,
                queue_key=claim_item.queue_key,
                review_target=claim_item.review_target,
                priority_band=claim_item.priority_band,
                board_label=claim_item.board_label,
                latest_trust_status=claim_item.latest_trust_status,
                previous_trust_status=claim_item.previous_trust_status,
                latest_summary_line=claim_item.latest_summary_line,
                previous_summary_line=claim_item.previous_summary_line,
                latest_manifest_path=claim_item.latest_manifest_path,
                previous_manifest_path=claim_item.previous_manifest_path,
                recommended_actions=_compose_actions(
                    claim_item,
                    lifecycle_state=lifecycle_state,
                    renewal_action=renewal_action,
                    expiry_action=expiry_action,
                    lifecycle_label=lifecycle_label,
                ),
                is_current_pack_kind=claim_item.is_current_pack_kind,
            )
        )
    return OracleOperatorPackClaimLifecycle(
        schema_version='oracle_operator_pack_claim_lifecycle/v1',
        search_root=str(request.search_root),
        current_pack_kind=request.current_pack_kind,
        queue_key=request.queue_key or getattr(operator_workboard, 'queue_key', None),
        review_target=request.review_target or getattr(operator_workboard, 'review_target', None),
        priority_band=request.priority_band or getattr(operator_workboard, 'priority_band', None),
        board_label=request.board_label or getattr(operator_workboard, 'board_label', None),
        total_claim_lifecycle_count=len(items),
        items=tuple(items),
    )


def render_operator_pack_claim_lifecycle_markdown_lines(claim_lifecycle: OracleOperatorPackClaimLifecycle) -> list[str]:
    lines = ['## Operator Pack Claim Lifecycles']
    if claim_lifecycle.queue_key:
        lines.append(f"- Queue: `{claim_lifecycle.queue_key}`")
    if claim_lifecycle.review_target:
        lines.append(f"- Review target: `{claim_lifecycle.review_target}`")
    if claim_lifecycle.priority_band:
        lines.append(f"- Priority band: `{claim_lifecycle.priority_band}`")
    if claim_lifecycle.board_label:
        lines.append(f"- Board: `{claim_lifecycle.board_label}`")
    for item in claim_lifecycle.items:
        lines.extend([
            '',
            f"### {item.pack_kind}",
            f"- Lifecycle state: `{item.lifecycle_state}`",
            f"- Renewal action: `{item.renewal_action}`",
            f"- Expiry action: `{item.expiry_action}`",
            f"- Claim / lease: `{item.claim_state}` / `{item.lease_state}`",
            f"- Lifecycle key: `{item.lifecycle_key}`",
            f"- Owner: `{item.owner_lane}` via `{item.lifecycle_label}`",
            f"- Latest trust: `{item.latest_trust_status}`",
            f"- Summary: {item.latest_summary_line or 'none'}",
        ])
        if item.recommended_actions:
            lines.append('- Recommended actions:')
            lines.extend([f"  - {action}" for action in item.recommended_actions])
    lines.append('')
    return lines


__all__ = [
    'OracleOperatorPackClaimLifecycleRequest',
    'OracleOperatorPackClaimLifecycleItem',
    'OracleOperatorPackClaimLifecycle',
    'build_operator_pack_claim_lifecycle_request',
    'materialize_operator_pack_claim_lifecycle',
    'render_operator_pack_claim_lifecycle_markdown_lines',
]
