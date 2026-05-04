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
class OracleOperatorPackTimelineRequest:
    search_root: Path
    repo_root: Path | None = None
    current_pack_kind: str | None = None
    pack_kinds: tuple[str, ...] = ()
    trust_statuses: tuple[str, ...] = ()
    summary_line_contains: str | None = None
    output_artifact_label_contains: str | None = None
    max_items: int = 8


@dataclass(frozen=True)
class OracleOperatorPackTimelineItem:
    pack_kind: str
    generated_at_utc: str | None
    trust_status: str | None
    summary_line: str | None
    manifest_path: Path
    pack_root: Path
    primary_output_artifact_path: Path | None
    is_current_pack_kind: bool


@dataclass(frozen=True)
class OracleOperatorPackTimeline:
    schema_version: str
    search_root: str
    current_pack_kind: str | None
    pack_kinds: tuple[str, ...]
    trust_statuses: tuple[str, ...]
    summary_line_contains: str | None
    output_artifact_label_contains: str | None
    total_match_count: int
    items: tuple[OracleOperatorPackTimelineItem, ...]

    def to_payload(self) -> dict[str, Any]:
        return {
            'schema_version': self.schema_version,
            'search_root': self.search_root,
            'current_pack_kind': self.current_pack_kind,
            'pack_kinds': list(self.pack_kinds),
            'trust_statuses': list(self.trust_statuses),
            'summary_line_contains': self.summary_line_contains,
            'output_artifact_label_contains': self.output_artifact_label_contains,
            'total_match_count': self.total_match_count,
            'item_count': len(self.items),
            'items': [
                {
                    'pack_kind': item.pack_kind,
                    'generated_at_utc': item.generated_at_utc,
                    'trust_status': item.trust_status,
                    'summary_line': item.summary_line,
                    'manifest_path': str(item.manifest_path),
                    'pack_root': str(item.pack_root),
                    'primary_output_artifact_path': str(item.primary_output_artifact_path) if item.primary_output_artifact_path else None,
                    'is_current_pack_kind': item.is_current_pack_kind,
                }
                for item in self.items
            ],
        }


def build_operator_pack_timeline_request(
    *,
    search_root: Path,
    repo_root: Path | None = None,
    current_pack_kind: str | None = None,
    pack_kinds: Sequence[str] = (),
    trust_statuses: Sequence[str] = (),
    summary_line_contains: str | None = None,
    output_artifact_label_contains: str | None = None,
    max_items: int = 8,
) -> OracleOperatorPackTimelineRequest:
    return OracleOperatorPackTimelineRequest(
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


def materialize_operator_pack_timeline(request: OracleOperatorPackTimelineRequest) -> OracleOperatorPackTimeline:
    query = build_operator_pack_query(
        search_root=request.search_root,
        repo_root=request.repo_root,
        pack_kinds=request.pack_kinds,
        trust_statuses=request.trust_statuses,
        summary_line_contains=request.summary_line_contains,
        output_artifact_label_contains=request.output_artifact_label_contains,
    )
    matches = list(discover_operator_pack_matches(query))
    matches.sort(key=lambda item: ((item.generated_at_utc or ''), str(item.manifest_path)), reverse=True)
    items = tuple(
        OracleOperatorPackTimelineItem(
            pack_kind=match.pack_kind,
            generated_at_utc=match.generated_at_utc,
            trust_status=match.trust_status,
            summary_line=match.summary_line,
            manifest_path=match.manifest_path,
            pack_root=match.pack_root,
            primary_output_artifact_path=_primary_output_path(match),
            is_current_pack_kind=bool(request.current_pack_kind and match.pack_kind == request.current_pack_kind),
        )
        for match in matches[:request.max_items]
    )
    return OracleOperatorPackTimeline(
        schema_version='oracle_operator_pack_timeline/v1',
        search_root=str(request.search_root),
        current_pack_kind=request.current_pack_kind,
        pack_kinds=request.pack_kinds,
        trust_statuses=request.trust_statuses,
        summary_line_contains=request.summary_line_contains,
        output_artifact_label_contains=request.output_artifact_label_contains,
        total_match_count=len(matches),
        items=items,
    )


def render_operator_pack_timeline_markdown_lines(timeline: OracleOperatorPackTimeline) -> list[str]:
    lines = ['## Operator Pack Timeline']
    lines.extend([
        f"- Indexed timeline matches: `{timeline.total_match_count}`",
        f"- Timeline items shown: `{len(timeline.items)}`",
    ])
    if not timeline.items:
        lines.append('- No operator pack activity found for the current filters.')
        return lines
    for item in timeline.items:
        current = ' (current kind)' if item.is_current_pack_kind else ''
        lines.extend([
            f"- `{item.generated_at_utc or 'unknown'}` — `{item.pack_kind}`{current}",
            f"  - Trust status: `{item.trust_status or 'unknown'}`",
            f"  - Summary: {item.summary_line or 'No summary recorded.'}",
            f"  - Manifest: `{item.manifest_path}`",
            f"  - Primary output: `{str(item.primary_output_artifact_path) if item.primary_output_artifact_path else 'no primary output recorded'}`",
        ])
    return lines


__all__ = [
    'OracleOperatorPackTimelineRequest',
    'OracleOperatorPackTimelineItem',
    'OracleOperatorPackTimeline',
    'build_operator_pack_timeline_request',
    'materialize_operator_pack_timeline',
    'render_operator_pack_timeline_markdown_lines',
]
