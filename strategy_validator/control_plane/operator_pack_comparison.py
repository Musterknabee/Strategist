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
class OracleOperatorPackComparisonRequest:
    search_root: Path
    repo_root: Path | None = None
    current_pack_kind: str | None = None
    pack_kinds: tuple[str, ...] = ()
    trust_statuses: tuple[str, ...] = ()
    summary_line_contains: str | None = None
    output_artifact_label_contains: str | None = None
    max_items: int = 3


@dataclass(frozen=True)
class OracleOperatorPackComparisonItem:
    pack_kind: str
    latest_generated_at_utc: str | None
    previous_generated_at_utc: str | None
    latest_trust_status: str | None
    previous_trust_status: str | None
    latest_summary_line: str | None
    previous_summary_line: str | None
    latest_manifest_path: Path
    previous_manifest_path: Path
    latest_primary_output_artifact_path: Path | None
    previous_primary_output_artifact_path: Path | None
    changed_fields: tuple[str, ...]
    is_current_pack_kind: bool


@dataclass(frozen=True)
class OracleOperatorPackComparison:
    schema_version: str
    search_root: str
    current_pack_kind: str | None
    pack_kinds: tuple[str, ...]
    trust_statuses: tuple[str, ...]
    summary_line_contains: str | None
    output_artifact_label_contains: str | None
    total_comparison_count: int
    items: tuple[OracleOperatorPackComparisonItem, ...]

    def to_payload(self) -> dict[str, Any]:
        return {
            'schema_version': self.schema_version,
            'search_root': self.search_root,
            'current_pack_kind': self.current_pack_kind,
            'pack_kinds': list(self.pack_kinds),
            'trust_statuses': list(self.trust_statuses),
            'summary_line_contains': self.summary_line_contains,
            'output_artifact_label_contains': self.output_artifact_label_contains,
            'total_comparison_count': self.total_comparison_count,
            'item_count': len(self.items),
            'items': [
                {
                    'pack_kind': item.pack_kind,
                    'latest_generated_at_utc': item.latest_generated_at_utc,
                    'previous_generated_at_utc': item.previous_generated_at_utc,
                    'latest_trust_status': item.latest_trust_status,
                    'previous_trust_status': item.previous_trust_status,
                    'latest_summary_line': item.latest_summary_line,
                    'previous_summary_line': item.previous_summary_line,
                    'latest_manifest_path': str(item.latest_manifest_path),
                    'previous_manifest_path': str(item.previous_manifest_path),
                    'latest_primary_output_artifact_path': str(item.latest_primary_output_artifact_path) if item.latest_primary_output_artifact_path else None,
                    'previous_primary_output_artifact_path': str(item.previous_primary_output_artifact_path) if item.previous_primary_output_artifact_path else None,
                    'changed_fields': list(item.changed_fields),
                    'is_current_pack_kind': item.is_current_pack_kind,
                }
                for item in self.items
            ],
        }


def build_operator_pack_comparison_request(
    *,
    search_root: Path,
    repo_root: Path | None = None,
    current_pack_kind: str | None = None,
    pack_kinds: Sequence[str] = (),
    trust_statuses: Sequence[str] = (),
    summary_line_contains: str | None = None,
    output_artifact_label_contains: str | None = None,
    max_items: int = 3,
) -> OracleOperatorPackComparisonRequest:
    return OracleOperatorPackComparisonRequest(
        search_root=search_root.resolve(),
        repo_root=repo_root.resolve() if repo_root is not None else None,
        current_pack_kind=current_pack_kind or None,
        pack_kinds=tuple(item for item in pack_kinds if item),
        trust_statuses=tuple(item for item in trust_statuses if item),
        summary_line_contains=summary_line_contains or None,
        output_artifact_label_contains=output_artifact_label_contains or None,
        max_items=max(1, int(max_items)),
    )


def _primary_output_path(match: OperatorPackDiscoveryMatch) -> Path | None:
    return match.output_artifact_paths[0] if match.output_artifact_paths else None


def _changed_fields(*, latest: OperatorPackDiscoveryMatch, previous: OperatorPackDiscoveryMatch) -> tuple[str, ...]:
    fields: list[str] = []
    if latest.trust_status != previous.trust_status:
        fields.append('trust_status')
    if (latest.summary_line or '') != (previous.summary_line or ''):
        fields.append('summary_line')
    if (latest.generated_at_utc or '') != (previous.generated_at_utc or ''):
        fields.append('generated_at_utc')
    if _primary_output_path(latest) != _primary_output_path(previous):
        fields.append('primary_output_artifact_path')
    return tuple(fields)


def materialize_operator_pack_comparison(request: OracleOperatorPackComparisonRequest) -> OracleOperatorPackComparison:
    query = build_operator_pack_query(
        search_root=request.search_root,
        repo_root=request.repo_root,
        pack_kinds=request.pack_kinds,
        trust_statuses=request.trust_statuses,
        summary_line_contains=request.summary_line_contains,
        output_artifact_label_contains=request.output_artifact_label_contains,
    )
    matches = list(discover_operator_pack_matches(query))
    grouped: dict[str, list[OperatorPackDiscoveryMatch]] = {}
    for match in matches:
        grouped.setdefault(match.pack_kind, []).append(match)
    comparisons: list[OracleOperatorPackComparisonItem] = []
    for pack_kind, pack_matches in grouped.items():
        pack_matches.sort(key=lambda item: ((item.generated_at_utc or ''), str(item.manifest_path)), reverse=True)
        if len(pack_matches) < 2:
            continue
        latest, previous = pack_matches[0], pack_matches[1]
        comparisons.append(
            OracleOperatorPackComparisonItem(
                pack_kind=pack_kind,
                latest_generated_at_utc=latest.generated_at_utc,
                previous_generated_at_utc=previous.generated_at_utc,
                latest_trust_status=latest.trust_status,
                previous_trust_status=previous.trust_status,
                latest_summary_line=latest.summary_line,
                previous_summary_line=previous.summary_line,
                latest_manifest_path=latest.manifest_path,
                previous_manifest_path=previous.manifest_path,
                latest_primary_output_artifact_path=_primary_output_path(latest),
                previous_primary_output_artifact_path=_primary_output_path(previous),
                changed_fields=_changed_fields(latest=latest, previous=previous),
                is_current_pack_kind=bool(request.current_pack_kind and pack_kind == request.current_pack_kind),
            )
        )
    comparisons.sort(key=lambda item: ((item.latest_generated_at_utc or ''), item.pack_kind), reverse=True)
    selected = tuple(comparisons[:request.max_items])
    return OracleOperatorPackComparison(
        schema_version='oracle_operator_pack_comparison/v1',
        search_root=str(request.search_root),
        current_pack_kind=request.current_pack_kind,
        pack_kinds=request.pack_kinds,
        trust_statuses=request.trust_statuses,
        summary_line_contains=request.summary_line_contains,
        output_artifact_label_contains=request.output_artifact_label_contains,
        total_comparison_count=len(comparisons),
        items=selected,
    )


def render_operator_pack_comparison_markdown_lines(comparison: OracleOperatorPackComparison) -> list[str]:
    lines = ['## Operator Pack Changes']
    lines.extend([
        f"- Comparable pack families: `{comparison.total_comparison_count}`",
        f"- Comparison items shown: `{len(comparison.items)}`",
    ])
    if not comparison.items:
        lines.append('- No comparable operator pack generations found for the current filters.')
        return lines
    for item in comparison.items:
        current = ' (current kind)' if item.is_current_pack_kind else ''
        change_summary = ', '.join(item.changed_fields) if item.changed_fields else 'no tracked field changes'
        lines.extend([
            f"- `{item.pack_kind}`{current} — changed fields: `{change_summary}`",
            f"  - Latest: `{item.latest_generated_at_utc or 'unknown'}` / `{item.latest_trust_status or 'unknown'}` / {item.latest_summary_line or 'No summary recorded.'}",
            f"  - Previous: `{item.previous_generated_at_utc or 'unknown'}` / `{item.previous_trust_status or 'unknown'}` / {item.previous_summary_line or 'No summary recorded.'}",
            f"  - Latest manifest: `{item.latest_manifest_path}`",
            f"  - Previous manifest: `{item.previous_manifest_path}`",
        ])
    return lines


__all__ = [
    'OracleOperatorPackComparisonRequest',
    'OracleOperatorPackComparisonItem',
    'OracleOperatorPackComparison',
    'build_operator_pack_comparison_request',
    'materialize_operator_pack_comparison',
    'render_operator_pack_comparison_markdown_lines',
]
