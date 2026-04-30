from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

from strategy_validator.control_plane.operator_pack_terminal_closure import (
    OracleOperatorPackTerminalClosure,
    OracleOperatorPackTerminalClosureItem,
    OracleOperatorPackTerminalClosureRequest,
    build_operator_pack_terminal_closure_request,
    materialize_operator_pack_terminal_closure,
)
from strategy_validator.projections.operator_pack_registry import discover_latest_operator_pack, load_operator_pack_index


@dataclass(frozen=True)
class OracleOperatorPackTerminalArchiveRequest:
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
    archive_label_prefix: str | None = None


@dataclass(frozen=True)
class OracleOperatorPackTerminalArchiveItem:
    pack_kind: str
    closure_posture: str
    closure_state: str
    retention_posture: str
    retention_state: str
    retention_action: str
    archive_manifest_key: str
    archive_manifest_label: str
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
    pack_root: str | None
    pack_digest_sha256: str | None
    output_artifact_labels: tuple[str, ...]
    recommended_actions: tuple[str, ...]
    is_current_pack_kind: bool


@dataclass(frozen=True)
class OracleOperatorPackTerminalArchive:
    schema_version: str
    search_root: str
    current_pack_kind: str | None
    queue_key: str | None
    review_target: str | None
    priority_band: str | None
    board_label: str | None
    total_archive_count: int
    items: tuple[OracleOperatorPackTerminalArchiveItem, ...]

    def to_payload(self) -> dict[str, Any]:
        return {
            'schema_version': self.schema_version,
            'search_root': self.search_root,
            'current_pack_kind': self.current_pack_kind,
            'queue_key': self.queue_key,
            'review_target': self.review_target,
            'priority_band': self.priority_band,
            'board_label': self.board_label,
            'total_archive_count': self.total_archive_count,
            'items': [
                {
                    'pack_kind': item.pack_kind,
                    'closure_posture': item.closure_posture,
                    'closure_state': item.closure_state,
                    'retention_posture': item.retention_posture,
                    'retention_state': item.retention_state,
                    'retention_action': item.retention_action,
                    'archive_manifest_key': item.archive_manifest_key,
                    'archive_manifest_label': item.archive_manifest_label,
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
                    'pack_root': item.pack_root,
                    'pack_digest_sha256': item.pack_digest_sha256,
                    'output_artifact_labels': list(item.output_artifact_labels),
                    'recommended_actions': list(item.recommended_actions),
                    'is_current_pack_kind': item.is_current_pack_kind,
                }
                for item in self.items
            ],
        }


def build_operator_pack_terminal_archive_request(**kwargs: Any) -> OracleOperatorPackTerminalArchiveRequest:
    kwargs['search_root'] = Path(kwargs['search_root']).resolve()
    if kwargs.get('repo_root') is not None:
        kwargs['repo_root'] = Path(kwargs['repo_root']).resolve()
    for key in ('pack_kinds','trust_statuses'):
        kwargs[key] = tuple(i for i in kwargs.get(key, ()) if i)
    kwargs['max_items'] = max(1, int(kwargs.get('max_items', 3)))
    kwargs['sustained_degraded_threshold'] = max(2, int(kwargs.get('sustained_degraded_threshold', 2)))
    return OracleOperatorPackTerminalArchiveRequest(**kwargs)


def _classify(item: OracleOperatorPackTerminalClosureItem) -> tuple[str,str,str]:
    if item.closure_posture == 'ARCHIVE_READY':
        return 'ARCHIVE_MANIFEST_READY', 'RETENTION_ARCHIVE_READY', 'ARCHIVE_WITH_MANIFEST'
    if item.closure_posture == 'CLOSE_READY':
        return 'RETAIN_CLOSURE_RECORD', 'RETENTION_CLOSURE_RETAINED', 'RETAIN_CLOSURE_RECORD'
    return 'RETAIN_OPEN_CASE', 'RETENTION_ACTIVE_OPEN', 'RETAIN_OPEN_CASE'


def _lookup_registry(search_root: Path, pack_kind: str) -> dict[str, Any] | None:
    return discover_latest_operator_pack(search_root, pack_kind=pack_kind)


def materialize_operator_pack_terminal_archive(request: OracleOperatorPackTerminalArchiveRequest, *, terminal_closure: OracleOperatorPackTerminalClosure | None = None, terminal_closure_request: OracleOperatorPackTerminalClosureRequest | None = None) -> OracleOperatorPackTerminalArchive:
    if terminal_closure is None:
        terminal_closure = materialize_operator_pack_terminal_closure(
            terminal_closure_request or build_operator_pack_terminal_closure_request(
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
                closure_label_prefix=request.closure_label_prefix,
            )
        )
    items=[]
    for closure_item in terminal_closure.items[:request.max_items]:
        retention_posture, retention_state, retention_action = _classify(closure_item)
        reg = _lookup_registry(request.search_root, closure_item.pack_kind) or {}
        label_prefix = request.archive_label_prefix or request.closure_label_prefix or 'archive'
        manifest_key = f"{closure_item.pack_kind}::{retention_state}::{closure_item.queue_key or 'no-queue'}::{closure_item.owner_lane}"
        manifest_label = f"{label_prefix}:{closure_item.pack_kind}:{retention_posture.lower()}"
        actions = []
        if retention_posture == 'ARCHIVE_MANIFEST_READY':
            actions.append(f'Archive `{closure_item.pack_kind}` with manifest `{manifest_label}` and retain registry linkage.')
        elif retention_posture == 'RETAIN_CLOSURE_RECORD':
            actions.append(f'Retain terminal closure record `{manifest_label}` for `{closure_item.pack_kind}` before archival.')
        else:
            actions.append(f'Retain `{closure_item.pack_kind}` as open because terminal closure is not archive-ready yet.')
        actions.extend(closure_item.recommended_actions)
        items.append(OracleOperatorPackTerminalArchiveItem(
            pack_kind=closure_item.pack_kind,
            closure_posture=closure_item.closure_posture,
            closure_state=closure_item.closure_state,
            retention_posture=retention_posture,
            retention_state=retention_state,
            retention_action=retention_action,
            archive_manifest_key=manifest_key,
            archive_manifest_label=manifest_label,
            owner_lane=closure_item.owner_lane,
            queue_key=closure_item.queue_key,
            review_target=closure_item.review_target,
            priority_band=closure_item.priority_band,
            board_label=closure_item.board_label,
            latest_trust_status=closure_item.latest_trust_status,
            previous_trust_status=closure_item.previous_trust_status,
            latest_summary_line=closure_item.latest_summary_line,
            previous_summary_line=closure_item.previous_summary_line,
            latest_manifest_path=closure_item.latest_manifest_path,
            previous_manifest_path=closure_item.previous_manifest_path,
            pack_root=reg.get('pack_root'),
            pack_digest_sha256=reg.get('pack_digest_sha256'),
            output_artifact_labels=tuple(reg.get('output_artifact_labels', []) or ()),
            recommended_actions=tuple(dict.fromkeys(actions)),
            is_current_pack_kind=closure_item.is_current_pack_kind,
        ))
    return OracleOperatorPackTerminalArchive(
        schema_version='oracle_operator_pack_terminal_archive/v1',
        search_root=str(request.search_root),
        current_pack_kind=request.current_pack_kind,
        queue_key=request.queue_key,
        review_target=request.review_target,
        priority_band=request.priority_band,
        board_label=request.board_label,
        total_archive_count=len(items),
        items=tuple(items),
    )


def render_operator_pack_terminal_archive_markdown_lines(archive: OracleOperatorPackTerminalArchive) -> list[str]:
    if not archive.items:
        return []
    lines=['', '## Operator Pack Terminal Archive']
    for item in archive.items:
        lines.append(f"- `{item.pack_kind}` → **{item.retention_posture}** ({item.retention_action}); manifest `{item.archive_manifest_label}`")
        if item.pack_root:
            lines.append(f"  - Pack root: `{item.pack_root}`")
        if item.pack_digest_sha256:
            lines.append(f"  - Pack digest: `{item.pack_digest_sha256}`")
    return lines


__all__ = [
    'OracleOperatorPackTerminalArchive',
    'OracleOperatorPackTerminalArchiveItem',
    'OracleOperatorPackTerminalArchiveRequest',
    'build_operator_pack_terminal_archive_request',
    'materialize_operator_pack_terminal_archive',
    'render_operator_pack_terminal_archive_markdown_lines',
]
