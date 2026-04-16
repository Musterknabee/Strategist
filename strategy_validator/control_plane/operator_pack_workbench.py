from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

from strategy_validator.projections.operator_pack_discovery import (
    OperatorPackDiscoveryMatch,
    build_operator_pack_query,
    discover_operator_pack_matches,
)


@dataclass(frozen=True)
class OracleOperatorPackWorkbenchRequest:
    search_root: Path
    repo_root: Path | None = None
    pack_kinds: tuple[str, ...] = ()
    trust_statuses: tuple[str, ...] = ()
    summary_line_contains: str | None = None
    output_artifact_label_contains: str | None = None


@dataclass(frozen=True)
class OracleOperatorPackWorkbenchItem:
    pack_kind: str
    trust_status: str | None
    summary_line: str | None
    generated_at_utc: str | None
    manifest_path: Path
    pack_root: Path
    primary_output_artifact_path: Path | None
    output_artifact_labels: tuple[str, ...]
    output_artifact_paths: tuple[Path, ...]


@dataclass(frozen=True)
class OracleOperatorPackWorkbenchColumn:
    pack_kind: str
    item_count: int
    latest_generated_at_utc: str | None
    trust_statuses: tuple[str, ...]
    items: tuple[OracleOperatorPackWorkbenchItem, ...]


@dataclass(frozen=True)
class OracleOperatorPackWorkbench:
    schema_version: str
    search_root: str
    pack_kinds: tuple[str, ...]
    trust_statuses: tuple[str, ...]
    summary_line_contains: str | None
    output_artifact_label_contains: str | None
    total_item_count: int
    columns: tuple[OracleOperatorPackWorkbenchColumn, ...]

    def to_payload(self) -> dict[str, Any]:
        return {
            'schema_version': self.schema_version,
            'search_root': self.search_root,
            'pack_kinds': list(self.pack_kinds),
            'trust_statuses': list(self.trust_statuses),
            'summary_line_contains': self.summary_line_contains,
            'output_artifact_label_contains': self.output_artifact_label_contains,
            'total_item_count': self.total_item_count,
            'column_count': len(self.columns),
            'columns': [
                {
                    'pack_kind': column.pack_kind,
                    'item_count': column.item_count,
                    'latest_generated_at_utc': column.latest_generated_at_utc,
                    'trust_statuses': list(column.trust_statuses),
                    'items': [
                        {
                            'pack_kind': item.pack_kind,
                            'trust_status': item.trust_status,
                            'summary_line': item.summary_line,
                            'generated_at_utc': item.generated_at_utc,
                            'manifest_path': str(item.manifest_path),
                            'pack_root': str(item.pack_root),
                            'primary_output_artifact_path': str(item.primary_output_artifact_path) if item.primary_output_artifact_path else None,
                            'output_artifact_labels': list(item.output_artifact_labels),
                            'output_artifact_paths': [str(path) for path in item.output_artifact_paths],
                        }
                        for item in column.items
                    ],
                }
                for column in self.columns
            ],
        }


def build_operator_pack_workbench_request(
    *,
    search_root: Path,
    repo_root: Path | None = None,
    pack_kinds: Sequence[str] = (),
    trust_statuses: Sequence[str] = (),
    summary_line_contains: str | None = None,
    output_artifact_label_contains: str | None = None,
) -> OracleOperatorPackWorkbenchRequest:
    return OracleOperatorPackWorkbenchRequest(
        search_root=search_root.resolve(),
        repo_root=repo_root.resolve() if repo_root is not None else None,
        pack_kinds=tuple(item for item in pack_kinds if item),
        trust_statuses=tuple(item for item in trust_statuses if item),
        summary_line_contains=summary_line_contains or None,
        output_artifact_label_contains=output_artifact_label_contains or None,
    )


def _primary_output_path(match: OperatorPackDiscoveryMatch) -> Path | None:
    if match.output_artifact_paths:
        return match.output_artifact_paths[0]
    return None


def _build_item(match: OperatorPackDiscoveryMatch) -> OracleOperatorPackWorkbenchItem:
    return OracleOperatorPackWorkbenchItem(
        pack_kind=match.pack_kind,
        trust_status=match.trust_status,
        summary_line=match.summary_line,
        generated_at_utc=match.generated_at_utc,
        manifest_path=match.manifest_path,
        pack_root=match.pack_root,
        primary_output_artifact_path=_primary_output_path(match),
        output_artifact_labels=match.output_artifact_labels,
        output_artifact_paths=match.output_artifact_paths,
    )


def materialize_operator_pack_workbench(request: OracleOperatorPackWorkbenchRequest) -> OracleOperatorPackWorkbench:
    query = build_operator_pack_query(
        search_root=request.search_root,
        repo_root=request.repo_root,
        pack_kinds=request.pack_kinds,
        trust_statuses=request.trust_statuses,
        summary_line_contains=request.summary_line_contains,
        output_artifact_label_contains=request.output_artifact_label_contains,
    )
    matches = discover_operator_pack_matches(query)
    by_kind: dict[str, list[OracleOperatorPackWorkbenchItem]] = {}
    for match in matches:
        by_kind.setdefault(match.pack_kind, []).append(_build_item(match))
    columns: list[OracleOperatorPackWorkbenchColumn] = []
    for pack_kind, items in sorted(by_kind.items(), key=lambda kv: kv[0]):
        ordered_items = tuple(sorted(items, key=lambda item: ((item.generated_at_utc or ''), str(item.manifest_path)), reverse=True))
        trust_statuses = tuple(sorted({status for status in (item.trust_status for item in ordered_items) if status}))
        columns.append(
            OracleOperatorPackWorkbenchColumn(
                pack_kind=pack_kind,
                item_count=len(ordered_items),
                latest_generated_at_utc=ordered_items[0].generated_at_utc if ordered_items else None,
                trust_statuses=trust_statuses,
                items=ordered_items,
            )
        )
    columns.sort(key=lambda column: ((column.latest_generated_at_utc or ''), column.pack_kind), reverse=True)
    return OracleOperatorPackWorkbench(
        schema_version='oracle_operator_pack_workbench/v1',
        search_root=str(request.search_root),
        pack_kinds=request.pack_kinds,
        trust_statuses=request.trust_statuses,
        summary_line_contains=request.summary_line_contains,
        output_artifact_label_contains=request.output_artifact_label_contains,
        total_item_count=len(matches),
        columns=tuple(columns),
    )


__all__ = [
    'OracleOperatorPackWorkbenchRequest',
    'OracleOperatorPackWorkbenchItem',
    'OracleOperatorPackWorkbenchColumn',
    'OracleOperatorPackWorkbench',
    'build_operator_pack_workbench_request',
    'materialize_operator_pack_workbench',
]
