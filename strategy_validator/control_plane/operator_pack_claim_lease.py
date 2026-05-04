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
from strategy_validator.control_plane.operator_workboard import OracleOperatorWorkboard


@dataclass(frozen=True)
class OracleOperatorPackClaimLeaseRequest:
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


@dataclass(frozen=True)
class OracleOperatorPackClaimLeaseItem:
    pack_kind: str
    handoff_state: str
    acceptance_state: str
    claim_state: str
    lease_state: str
    lease_action: str
    lease_key: str
    owner_lane: str
    ack_owner_lane: str
    backup_owner_lane: str
    owner_label: str
    lease_owner_label: str
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
class OracleOperatorPackClaimLease:
    schema_version: str
    search_root: str
    current_pack_kind: str | None
    queue_key: str | None
    review_target: str | None
    priority_band: str | None
    board_label: str | None
    total_claim_lease_count: int
    items: tuple[OracleOperatorPackClaimLeaseItem, ...]

    def to_payload(self) -> dict[str, Any]:
        return {
            'schema_version': self.schema_version,
            'search_root': self.search_root,
            'current_pack_kind': self.current_pack_kind,
            'queue_key': self.queue_key,
            'review_target': self.review_target,
            'priority_band': self.priority_band,
            'board_label': self.board_label,
            'total_claim_lease_count': self.total_claim_lease_count,
            'item_count': len(self.items),
            'items': [
                {
                    'pack_kind': item.pack_kind,
                    'handoff_state': item.handoff_state,
                    'acceptance_state': item.acceptance_state,
                    'claim_state': item.claim_state,
                    'lease_state': item.lease_state,
                    'lease_action': item.lease_action,
                    'lease_key': item.lease_key,
                    'owner_lane': item.owner_lane,
                    'ack_owner_lane': item.ack_owner_lane,
                    'backup_owner_lane': item.backup_owner_lane,
                    'owner_label': item.owner_label,
                    'lease_owner_label': item.lease_owner_label,
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


def build_operator_pack_claim_lease_request(
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
) -> OracleOperatorPackClaimLeaseRequest:
    return OracleOperatorPackClaimLeaseRequest(
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
    )


def _matching_workboard_entry(item: OracleOperatorPackHandoffItem, operator_workboard: OracleOperatorWorkboard | None):
    if operator_workboard is None:
        return None
    for entry in getattr(operator_workboard, 'entries', ()): 
        if item.queue_key and entry.queue_key != item.queue_key:
            continue
        if entry.review_target != item.review_target:
            continue
        if entry.action_owner_lane != item.owner_lane:
            continue
        return entry
    return None


def _claim_lease_state(item: OracleOperatorPackHandoffItem, operator_workboard: OracleOperatorWorkboard | None) -> tuple[str, str, str]:
    match = _matching_workboard_entry(item, operator_workboard)
    if match is not None and item.acceptance_state == 'ACCEPTED':
        return 'CLAIM_ACTIVE', 'LEASE_ACTIVE', 'MAINTAIN_LEASE'
    if item.acceptance_state == 'PENDING':
        return 'CLAIM_PENDING', 'LEASE_PENDING_ACQUISITION', 'ACQUIRE_LEASE'
    return 'CLAIM_UNCLAIMED', 'NO_ACTIVE_LEASE', 'NO_LEASE_ACTION'


def _lease_key(item: OracleOperatorPackHandoffItem) -> str:
    queue_key = item.queue_key or 'no-queue'
    return '::'.join((item.pack_kind, queue_key, item.review_target, item.owner_lane))


def _compose_actions(
    item: OracleOperatorPackHandoffItem,
    *,
    claim_state: str,
    lease_state: str,
    lease_action: str,
    lease_owner_label: str,
) -> tuple[str, ...]:
    actions: list[str] = []
    if claim_state == 'CLAIM_ACTIVE':
        actions.append(f'Keep claim ownership with `{lease_owner_label}` and maintain the current lease while `{item.pack_kind}` remains active.')
    elif claim_state == 'CLAIM_PENDING':
        actions.append(f'Acquire or confirm a governed lease for `{lease_owner_label}` before treating `{item.pack_kind}` as actively claimed.')
    else:
        actions.append(f'`{item.pack_kind}` has no active claim; assign an owner before attempting lease operations.')
    actions.append(f'Lease state is `{lease_state}` and lease action is `{lease_action}`.')
    actions.extend(item.recommended_actions)
    return tuple(actions)


def materialize_operator_pack_claim_lease(
    request: OracleOperatorPackClaimLeaseRequest,
    *,
    handoff: OracleOperatorPackHandoff | None = None,
    handoff_request: OracleOperatorPackHandoffRequest | None = None,
    operator_workboard: OracleOperatorWorkboard | None = None,
) -> OracleOperatorPackClaimLease:
    if handoff is None:
        handoff = materialize_operator_pack_handoff(
            handoff_request
            or build_operator_pack_handoff_request(
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
    items: list[OracleOperatorPackClaimLeaseItem] = []
    for handoff_item in handoff.items[: request.max_items]:
        claim_state, lease_state, lease_action = _claim_lease_state(handoff_item, operator_workboard)
        lease_owner_label = f"{request.lease_label_prefix or 'lease'}:{handoff_item.owner_lane}"
        items.append(
            OracleOperatorPackClaimLeaseItem(
                pack_kind=handoff_item.pack_kind,
                handoff_state=handoff_item.handoff_state,
                acceptance_state=handoff_item.acceptance_state,
                claim_state=claim_state,
                lease_state=lease_state,
                lease_action=lease_action,
                lease_key=_lease_key(handoff_item),
                owner_lane=handoff_item.owner_lane,
                ack_owner_lane=handoff_item.ack_owner_lane,
                backup_owner_lane=handoff_item.backup_owner_lane,
                owner_label=handoff_item.owner_label,
                lease_owner_label=lease_owner_label,
                handoff_target=handoff_item.handoff_target,
                queue_key=handoff_item.queue_key,
                review_target=handoff_item.review_target,
                priority_band=handoff_item.priority_band,
                board_label=handoff_item.board_label,
                latest_trust_status=handoff_item.latest_trust_status,
                previous_trust_status=handoff_item.previous_trust_status,
                latest_summary_line=handoff_item.latest_summary_line,
                previous_summary_line=handoff_item.previous_summary_line,
                latest_manifest_path=handoff_item.latest_manifest_path,
                previous_manifest_path=handoff_item.previous_manifest_path,
                recommended_actions=_compose_actions(
                    handoff_item,
                    claim_state=claim_state,
                    lease_state=lease_state,
                    lease_action=lease_action,
                    lease_owner_label=lease_owner_label,
                ),
                is_current_pack_kind=handoff_item.is_current_pack_kind,
            )
        )
    return OracleOperatorPackClaimLease(
        schema_version='oracle_operator_pack_claim_lease/v1',
        search_root=str(request.search_root),
        current_pack_kind=request.current_pack_kind,
        queue_key=request.queue_key or getattr(operator_workboard, 'queue_key', None),
        review_target=request.review_target or getattr(operator_workboard, 'review_target', None),
        priority_band=request.priority_band or getattr(operator_workboard, 'priority_band', None),
        board_label=request.board_label or getattr(operator_workboard, 'board_label', None),
        total_claim_lease_count=len(items),
        items=tuple(items),
    )


def render_operator_pack_claim_lease_markdown_lines(claim_lease: OracleOperatorPackClaimLease) -> list[str]:
    lines = ['## Operator Pack Claim Leases']
    if claim_lease.queue_key:
        lines.append(f"- Queue: `{claim_lease.queue_key}`")
    if claim_lease.review_target:
        lines.append(f"- Review target: `{claim_lease.review_target}`")
    if claim_lease.priority_band:
        lines.append(f"- Priority band: `{claim_lease.priority_band}`")
    if claim_lease.board_label:
        lines.append(f"- Board: `{claim_lease.board_label}`")
    for item in claim_lease.items:
        lines.extend([
            '',
            f"### {item.pack_kind}",
            f"- Claim state: `{item.claim_state}`",
            f"- Lease state: `{item.lease_state}` (`{item.lease_action}`)",
            f"- Lease key: `{item.lease_key}`",
            f"- Owner: `{item.owner_lane}` via `{item.lease_owner_label}`",
            f"- Acceptance: `{item.acceptance_state}` / handoff `{item.handoff_state}`",
            f"- Latest trust: `{item.latest_trust_status}`",
            f"- Summary: {item.latest_summary_line or 'none'}",
        ])
        if item.recommended_actions:
            lines.append('- Recommended actions:')
            lines.extend([f"  - {action}" for action in item.recommended_actions])
    lines.append('')
    return lines


__all__ = [
    'OracleOperatorPackClaimLeaseRequest',
    'OracleOperatorPackClaimLeaseItem',
    'OracleOperatorPackClaimLease',
    'build_operator_pack_claim_lease_request',
    'materialize_operator_pack_claim_lease',
    'render_operator_pack_claim_lease_markdown_lines',
]
