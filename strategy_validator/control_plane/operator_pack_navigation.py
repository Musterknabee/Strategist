from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

from strategy_validator.control_plane.operator_pack_workbench import (
    OracleOperatorPackWorkbench,
    OracleOperatorPackWorkbenchItem,
    build_operator_pack_workbench_request,
    materialize_operator_pack_workbench,
)


@dataclass(frozen=True)
class OracleOperatorPackNavigationRequest:
    search_root: Path
    repo_root: Path | None = None
    current_pack_kind: str | None = None
    preferred_pack_kinds: tuple[str, ...] = ()
    trust_statuses: tuple[str, ...] = ()
    summary_line_contains: str | None = None
    output_artifact_label_contains: str | None = None
    max_items: int = 3
    include_current_pack_kind: bool = True


@dataclass(frozen=True)
class OracleOperatorPackNavigationItem:
    pack_kind: str
    trust_status: str | None
    summary_line: str | None
    generated_at_utc: str | None
    manifest_path: Path
    pack_root: Path
    primary_output_artifact_path: Path | None
    output_artifact_labels: tuple[str, ...]
    output_artifact_paths: tuple[Path, ...]
    selected_reason: str
    is_primary: bool = False


@dataclass(frozen=True)
class OracleOperatorPackNavigation:
    schema_version: str
    search_root: str
    current_pack_kind: str | None
    preferred_pack_kinds: tuple[str, ...]
    trust_statuses: tuple[str, ...]
    summary_line_contains: str | None
    output_artifact_label_contains: str | None
    primary_item: OracleOperatorPackNavigationItem | None
    items: tuple[OracleOperatorPackNavigationItem, ...]

    def to_payload(self) -> dict[str, Any]:
        return {
            'schema_version': self.schema_version,
            'search_root': self.search_root,
            'current_pack_kind': self.current_pack_kind,
            'preferred_pack_kinds': list(self.preferred_pack_kinds),
            'trust_statuses': list(self.trust_statuses),
            'summary_line_contains': self.summary_line_contains,
            'output_artifact_label_contains': self.output_artifact_label_contains,
            'item_count': len(self.items),
            'primary_item': _item_payload(self.primary_item) if self.primary_item is not None else None,
            'items': [_item_payload(item) for item in self.items],
        }


def _item_payload(item: OracleOperatorPackNavigationItem) -> dict[str, Any]:
    return {
        'pack_kind': item.pack_kind,
        'trust_status': item.trust_status,
        'summary_line': item.summary_line,
        'generated_at_utc': item.generated_at_utc,
        'manifest_path': str(item.manifest_path),
        'pack_root': str(item.pack_root),
        'primary_output_artifact_path': str(item.primary_output_artifact_path) if item.primary_output_artifact_path else None,
        'output_artifact_labels': list(item.output_artifact_labels),
        'output_artifact_paths': [str(path) for path in item.output_artifact_paths],
        'selected_reason': item.selected_reason,
        'is_primary': item.is_primary,
    }


def build_operator_pack_navigation_request(
    *,
    search_root: Path,
    repo_root: Path | None = None,
    current_pack_kind: str | None = None,
    preferred_pack_kinds: Sequence[str] = (),
    trust_statuses: Sequence[str] = (),
    summary_line_contains: str | None = None,
    output_artifact_label_contains: str | None = None,
    max_items: int = 3,
    include_current_pack_kind: bool = True,
) -> OracleOperatorPackNavigationRequest:
    return OracleOperatorPackNavigationRequest(
        search_root=search_root.resolve(),
        repo_root=repo_root.resolve() if repo_root is not None else None,
        current_pack_kind=current_pack_kind or None,
        preferred_pack_kinds=tuple(item for item in preferred_pack_kinds if item),
        trust_statuses=tuple(item for item in trust_statuses if item),
        summary_line_contains=summary_line_contains or None,
        output_artifact_label_contains=output_artifact_label_contains or None,
        max_items=max(1, int(max_items)),
        include_current_pack_kind=bool(include_current_pack_kind),
    )


def _reason_for(pack_kind: str, request: OracleOperatorPackNavigationRequest) -> str:
    if request.current_pack_kind and pack_kind == request.current_pack_kind:
        return 'current_pack_kind_latest'
    if pack_kind in request.preferred_pack_kinds:
        return 'preferred_pack_kind_latest'
    return 'latest_pack_kind_match'


def _build_item(item: OracleOperatorPackWorkbenchItem, *, request: OracleOperatorPackNavigationRequest, is_primary: bool) -> OracleOperatorPackNavigationItem:
    return OracleOperatorPackNavigationItem(
        pack_kind=item.pack_kind,
        trust_status=item.trust_status,
        summary_line=item.summary_line,
        generated_at_utc=item.generated_at_utc,
        manifest_path=item.manifest_path,
        pack_root=item.pack_root,
        primary_output_artifact_path=item.primary_output_artifact_path,
        output_artifact_labels=item.output_artifact_labels,
        output_artifact_paths=item.output_artifact_paths,
        selected_reason=_reason_for(item.pack_kind, request),
        is_primary=is_primary,
    )


def _kind_sort_key(pack_kind: str, workbench: OracleOperatorPackWorkbench, request: OracleOperatorPackNavigationRequest) -> tuple[int, int, str]:
    if request.preferred_pack_kinds and pack_kind in request.preferred_pack_kinds:
        return (0, request.preferred_pack_kinds.index(pack_kind), pack_kind)
    if request.current_pack_kind and pack_kind == request.current_pack_kind:
        return (1, 0, pack_kind)
    workbench_index = next((idx for idx, column in enumerate(workbench.columns) if column.pack_kind == pack_kind), 999)
    return (2, workbench_index, pack_kind)


def materialize_operator_pack_navigation(request: OracleOperatorPackNavigationRequest) -> OracleOperatorPackNavigation:
    workbench = materialize_operator_pack_workbench(
        build_operator_pack_workbench_request(
            search_root=request.search_root,
            repo_root=request.repo_root,
            pack_kinds=request.preferred_pack_kinds,
            trust_statuses=request.trust_statuses,
            summary_line_contains=request.summary_line_contains,
            output_artifact_label_contains=request.output_artifact_label_contains,
        ) if request.preferred_pack_kinds else build_operator_pack_workbench_request(
            search_root=request.search_root,
            repo_root=request.repo_root,
            trust_statuses=request.trust_statuses,
            summary_line_contains=request.summary_line_contains,
            output_artifact_label_contains=request.output_artifact_label_contains,
        )
    )
    selected: list[OracleOperatorPackNavigationItem] = []
    chosen_kinds = sorted((column.pack_kind for column in workbench.columns), key=lambda kind: _kind_sort_key(kind, workbench, request))
    for pack_kind in chosen_kinds:
        if request.current_pack_kind and not request.include_current_pack_kind and pack_kind == request.current_pack_kind:
            continue
        column = next(column for column in workbench.columns if column.pack_kind == pack_kind)
        if not column.items:
            continue
        selected.append(_build_item(column.items[0], request=request, is_primary=False))
        if len(selected) >= request.max_items:
            break
    primary_item = selected[0] if selected else None
    if primary_item is not None:
        selected[0] = OracleOperatorPackNavigationItem(**{**primary_item.__dict__, 'is_primary': True})
        primary_item = selected[0]
    return OracleOperatorPackNavigation(
        schema_version='oracle_operator_pack_navigation/v1',
        search_root=str(request.search_root),
        current_pack_kind=request.current_pack_kind,
        preferred_pack_kinds=request.preferred_pack_kinds,
        trust_statuses=request.trust_statuses,
        summary_line_contains=request.summary_line_contains,
        output_artifact_label_contains=request.output_artifact_label_contains,
        primary_item=primary_item,
        items=tuple(selected),
    )


def render_operator_pack_navigation_markdown_lines(navigation: OracleOperatorPackNavigation) -> list[str]:
    lines = ['## Related Operator Packs']
    if navigation.primary_item is not None:
        lines.append(f"- Primary selection: `{navigation.primary_item.pack_kind}` — {navigation.primary_item.summary_line or 'No summary recorded.'}")
    else:
        lines.append('- No related indexed operator packs found.')
        return lines
    for item in navigation.items:
        output_path = str(item.primary_output_artifact_path) if item.primary_output_artifact_path is not None else 'no primary output recorded'
        lines.extend([
            f"### {item.pack_kind}",
            f"- Summary: {item.summary_line or 'No summary recorded.'}",
            f"- Trust status: `{item.trust_status or 'UNKNOWN'}`",
            f"- Generated at: `{item.generated_at_utc or 'unknown'}`",
            f"- Selected reason: `{item.selected_reason}`",
            f"- Primary output: `{output_path}`",
        ])
    lines.append('')
    return lines


__all__ = [
    'OracleOperatorPackNavigationRequest',
    'OracleOperatorPackNavigationItem',
    'OracleOperatorPackNavigation',
    'build_operator_pack_navigation_request',
    'materialize_operator_pack_navigation',
    'render_operator_pack_navigation_markdown_lines',
]
