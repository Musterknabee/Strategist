from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from strategy_validator.control_plane.operator_pack_terminal_archive import (
    OracleOperatorPackTerminalArchive,
    OracleOperatorPackTerminalArchiveItem,
    OracleOperatorPackTerminalArchiveRequest,
    build_operator_pack_terminal_archive_request,
    materialize_operator_pack_terminal_archive,
)
from strategy_validator.projections.operator_pack_registry import load_operator_pack_index


@dataclass(frozen=True)
class OracleOperatorPackTerminalRecordRequest:
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
    record_label_prefix: str | None = None


@dataclass(frozen=True)
class OracleOperatorPackTerminalRecordItem:
    pack_kind: str
    retention_posture: str
    retention_state: str
    record_posture: str
    record_state: str
    record_action: str
    terminal_record_key: str
    terminal_record_label: str
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
    record_index_path: str | None
    index_entry_count: int | None
    recommended_actions: tuple[str, ...]
    is_current_pack_kind: bool


@dataclass(frozen=True)
class OracleOperatorPackTerminalRecord:
    schema_version: str
    search_root: str
    current_pack_kind: str | None
    queue_key: str | None
    review_target: str | None
    priority_band: str | None
    board_label: str | None
    total_record_count: int
    items: tuple[OracleOperatorPackTerminalRecordItem, ...]

    def to_payload(self) -> dict[str, Any]:
        return {
            'schema_version': self.schema_version,
            'search_root': self.search_root,
            'current_pack_kind': self.current_pack_kind,
            'queue_key': self.queue_key,
            'review_target': self.review_target,
            'priority_band': self.priority_band,
            'board_label': self.board_label,
            'total_record_count': self.total_record_count,
            'items': [
                {
                    'pack_kind': item.pack_kind,
                    'retention_posture': item.retention_posture,
                    'retention_state': item.retention_state,
                    'record_posture': item.record_posture,
                    'record_state': item.record_state,
                    'record_action': item.record_action,
                    'terminal_record_key': item.terminal_record_key,
                    'terminal_record_label': item.terminal_record_label,
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
                    'record_index_path': item.record_index_path,
                    'index_entry_count': item.index_entry_count,
                    'recommended_actions': list(item.recommended_actions),
                    'is_current_pack_kind': item.is_current_pack_kind,
                }
                for item in self.items
            ],
        }


def build_operator_pack_terminal_record_request(**kwargs: Any) -> OracleOperatorPackTerminalRecordRequest:
    kwargs['search_root'] = Path(kwargs['search_root']).resolve()
    if kwargs.get('repo_root') is not None:
        kwargs['repo_root'] = Path(kwargs['repo_root']).resolve()
    for key in ('pack_kinds', 'trust_statuses'):
        kwargs[key] = tuple(i for i in kwargs.get(key, ()) if i)
    kwargs['max_items'] = max(1, int(kwargs.get('max_items', 3)))
    kwargs['sustained_degraded_threshold'] = max(2, int(kwargs.get('sustained_degraded_threshold', 2)))
    return OracleOperatorPackTerminalRecordRequest(**kwargs)


def _classify(item: OracleOperatorPackTerminalArchiveItem) -> tuple[str, str, str]:
    if item.retention_posture == 'ARCHIVE_MANIFEST_READY':
        return 'TERMINAL_RECORD_PUBLISH_READY', 'TERMINAL_RECORD_PUBLICATION_READY', 'PUBLISH_TERMINAL_RECORD'
    if item.retention_posture == 'RETAIN_CLOSURE_RECORD':
        return 'TERMINAL_RECORD_INDEX_UPDATE_READY', 'TERMINAL_RECORD_INDEX_UPDATE_READY', 'UPDATE_TERMINAL_RECORD_INDEX'
    return 'TERMINAL_RECORD_RETAIN_OPEN', 'TERMINAL_RECORD_OPEN_RETAINED', 'RETAIN_OPEN_TERMINAL_RECORD'


def _index_meta(search_root: Path) -> tuple[str | None, int | None]:
    index_path = search_root / 'ORACLE_OPERATOR_PACK_INDEX.json'
    if not index_path.exists():
        return None, None
    payload = load_operator_pack_index(index_path)
    return str(index_path), int(payload.get('entry_count', 0))


def materialize_operator_pack_terminal_record(
    request: OracleOperatorPackTerminalRecordRequest,
    *,
    terminal_archive: OracleOperatorPackTerminalArchive | None = None,
    terminal_archive_request: OracleOperatorPackTerminalArchiveRequest | None = None,
) -> OracleOperatorPackTerminalRecord:
    if terminal_archive is None:
        terminal_archive = materialize_operator_pack_terminal_archive(
            terminal_archive_request or build_operator_pack_terminal_archive_request(
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
                archive_label_prefix=request.archive_label_prefix,
            )
        )
    index_path, entry_count = _index_meta(request.search_root)
    items: list[OracleOperatorPackTerminalRecordItem] = []
    for archive_item in terminal_archive.items[:request.max_items]:
        record_posture, record_state, record_action = _classify(archive_item)
        label_prefix = request.record_label_prefix or request.archive_label_prefix or 'terminal-record'
        record_key = f"{archive_item.pack_kind}::{record_state}::{archive_item.queue_key or 'no-queue'}::{archive_item.owner_lane}"
        record_label = f"{label_prefix}:{archive_item.pack_kind}:{record_posture.lower()}"
        actions = []
        if record_posture == 'TERMINAL_RECORD_PUBLISH_READY':
            actions.append(f'Publish terminal record `{record_label}` for `{archive_item.pack_kind}` with archive manifest linkage.')
        elif record_posture == 'TERMINAL_RECORD_INDEX_UPDATE_READY':
            actions.append(f'Update terminal record index for `{archive_item.pack_kind}` under `{record_label}`.')
        else:
            actions.append(f'Retain open terminal record tracking for `{archive_item.pack_kind}` under `{record_label}`.')
        actions.extend(archive_item.recommended_actions)
        items.append(OracleOperatorPackTerminalRecordItem(
            pack_kind=archive_item.pack_kind,
            retention_posture=archive_item.retention_posture,
            retention_state=archive_item.retention_state,
            record_posture=record_posture,
            record_state=record_state,
            record_action=record_action,
            terminal_record_key=record_key,
            terminal_record_label=record_label,
            owner_lane=archive_item.owner_lane,
            queue_key=archive_item.queue_key,
            review_target=archive_item.review_target,
            priority_band=archive_item.priority_band,
            board_label=archive_item.board_label,
            latest_trust_status=archive_item.latest_trust_status,
            previous_trust_status=archive_item.previous_trust_status,
            latest_summary_line=archive_item.latest_summary_line,
            previous_summary_line=archive_item.previous_summary_line,
            latest_manifest_path=archive_item.latest_manifest_path,
            previous_manifest_path=archive_item.previous_manifest_path,
            pack_root=archive_item.pack_root,
            pack_digest_sha256=archive_item.pack_digest_sha256,
            output_artifact_labels=archive_item.output_artifact_labels,
            record_index_path=index_path,
            index_entry_count=entry_count,
            recommended_actions=tuple(dict.fromkeys(actions)),
            is_current_pack_kind=archive_item.is_current_pack_kind,
        ))
    return OracleOperatorPackTerminalRecord(
        schema_version='oracle_operator_pack_terminal_record/v1',
        search_root=str(request.search_root),
        current_pack_kind=request.current_pack_kind,
        queue_key=request.queue_key,
        review_target=request.review_target,
        priority_band=request.priority_band,
        board_label=request.board_label,
        total_record_count=len(items),
        items=tuple(items),
    )


def render_operator_pack_terminal_record_markdown_lines(record: OracleOperatorPackTerminalRecord) -> list[str]:
    if not record.items:
        return []
    lines = ['', '## Operator Pack Terminal Record']
    for item in record.items:
        lines.append(f"- `{item.pack_kind}` → **{item.record_posture}** ({item.record_action}); record `{item.terminal_record_label}`")
        if item.record_index_path:
            lines.append(f"  - Record index: `{item.record_index_path}`")
        if item.index_entry_count is not None:
            lines.append(f"  - Indexed entries: `{item.index_entry_count}`")
    return lines


__all__ = [
    'OracleOperatorPackTerminalRecord',
    'OracleOperatorPackTerminalRecordItem',
    'OracleOperatorPackTerminalRecordRequest',
    'build_operator_pack_terminal_record_request',
    'materialize_operator_pack_terminal_record',
    'render_operator_pack_terminal_record_markdown_lines',
]
