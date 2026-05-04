from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

from strategy_validator.control_plane.operator_pack_navigation import (
    OracleOperatorPackNavigation,
    build_operator_pack_navigation_request,
    materialize_operator_pack_navigation,
    render_operator_pack_navigation_markdown_lines,
)
from strategy_validator.control_plane.operator_pack_workbench import (
    OracleOperatorPackWorkbench,
    OracleOperatorPackWorkbenchColumn,
    build_operator_pack_workbench_request,
    materialize_operator_pack_workbench,
)


@dataclass(frozen=True)
class OracleOperatorPackDashboardRequest:
    search_root: Path
    repo_root: Path | None = None
    current_pack_kind: str | None = None
    preferred_pack_kinds: tuple[str, ...] = ()
    trust_statuses: tuple[str, ...] = ()
    summary_line_contains: str | None = None
    output_artifact_label_contains: str | None = None
    max_navigation_items: int = 3
    max_column_items: int = 3
    include_current_pack_kind: bool = True


@dataclass(frozen=True)
class OracleOperatorPackDashboardColumn:
    pack_kind: str
    item_count: int
    latest_generated_at_utc: str | None
    trust_statuses: tuple[str, ...]
    primary_summary_line: str | None
    primary_output_artifact_path: Path | None


@dataclass(frozen=True)
class OracleOperatorPackDashboardOverview:
    total_item_count: int
    pack_kind_count: int
    latest_generated_at_utc: str | None
    trust_statuses: tuple[str, ...]
    primary_pack_kind: str | None


@dataclass(frozen=True)
class OracleOperatorPackDashboard:
    schema_version: str
    search_root: str
    current_pack_kind: str | None
    preferred_pack_kinds: tuple[str, ...]
    trust_statuses: tuple[str, ...]
    summary_line_contains: str | None
    output_artifact_label_contains: str | None
    overview: OracleOperatorPackDashboardOverview
    columns: tuple[OracleOperatorPackDashboardColumn, ...]
    navigation: OracleOperatorPackNavigation

    def to_payload(self) -> dict[str, Any]:
        return {
            'schema_version': self.schema_version,
            'search_root': self.search_root,
            'current_pack_kind': self.current_pack_kind,
            'preferred_pack_kinds': list(self.preferred_pack_kinds),
            'trust_statuses': list(self.trust_statuses),
            'summary_line_contains': self.summary_line_contains,
            'output_artifact_label_contains': self.output_artifact_label_contains,
            'overview': {
                'total_item_count': self.overview.total_item_count,
                'pack_kind_count': self.overview.pack_kind_count,
                'latest_generated_at_utc': self.overview.latest_generated_at_utc,
                'trust_statuses': list(self.overview.trust_statuses),
                'primary_pack_kind': self.overview.primary_pack_kind,
            },
            'column_count': len(self.columns),
            'columns': [
                {
                    'pack_kind': column.pack_kind,
                    'item_count': column.item_count,
                    'latest_generated_at_utc': column.latest_generated_at_utc,
                    'trust_statuses': list(column.trust_statuses),
                    'primary_summary_line': column.primary_summary_line,
                    'primary_output_artifact_path': str(column.primary_output_artifact_path) if column.primary_output_artifact_path else None,
                }
                for column in self.columns
            ],
            'navigation': self.navigation.to_payload(),
        }


def build_operator_pack_dashboard_request(
    *,
    search_root: Path,
    repo_root: Path | None = None,
    current_pack_kind: str | None = None,
    preferred_pack_kinds: Sequence[str] = (),
    trust_statuses: Sequence[str] = (),
    summary_line_contains: str | None = None,
    output_artifact_label_contains: str | None = None,
    max_navigation_items: int = 3,
    max_column_items: int = 3,
    include_current_pack_kind: bool = True,
) -> OracleOperatorPackDashboardRequest:
    return OracleOperatorPackDashboardRequest(
        search_root=search_root.resolve(),
        repo_root=repo_root.resolve() if repo_root is not None else None,
        current_pack_kind=current_pack_kind or None,
        preferred_pack_kinds=tuple(item for item in preferred_pack_kinds if item),
        trust_statuses=tuple(item for item in trust_statuses if item),
        summary_line_contains=summary_line_contains or None,
        output_artifact_label_contains=output_artifact_label_contains or None,
        max_navigation_items=max(1, int(max_navigation_items)),
        max_column_items=max(1, int(max_column_items)),
        include_current_pack_kind=bool(include_current_pack_kind),
    )


def _dashboard_columns(workbench: OracleOperatorPackWorkbench, *, max_column_items: int) -> tuple[OracleOperatorPackDashboardColumn, ...]:
    columns: list[OracleOperatorPackDashboardColumn] = []
    for column in workbench.columns[:max_column_items]:
        primary_item = column.items[0] if column.items else None
        columns.append(
            OracleOperatorPackDashboardColumn(
                pack_kind=column.pack_kind,
                item_count=column.item_count,
                latest_generated_at_utc=column.latest_generated_at_utc,
                trust_statuses=column.trust_statuses,
                primary_summary_line=primary_item.summary_line if primary_item is not None else None,
                primary_output_artifact_path=primary_item.primary_output_artifact_path if primary_item is not None else None,
            )
        )
    return tuple(columns)


def _overview(workbench: OracleOperatorPackWorkbench, navigation: OracleOperatorPackNavigation) -> OracleOperatorPackDashboardOverview:
    trust_statuses = tuple(sorted({status for column in workbench.columns for status in column.trust_statuses if status}))
    latest_generated_at_utc = next((column.latest_generated_at_utc for column in workbench.columns if column.latest_generated_at_utc), None)
    primary_pack_kind = navigation.primary_item.pack_kind if navigation.primary_item is not None else (workbench.columns[0].pack_kind if workbench.columns else None)
    return OracleOperatorPackDashboardOverview(
        total_item_count=workbench.total_item_count,
        pack_kind_count=len(workbench.columns),
        latest_generated_at_utc=latest_generated_at_utc,
        trust_statuses=trust_statuses,
        primary_pack_kind=primary_pack_kind,
    )


def materialize_operator_pack_dashboard(request: OracleOperatorPackDashboardRequest) -> OracleOperatorPackDashboard:
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
    navigation = materialize_operator_pack_navigation(
        build_operator_pack_navigation_request(
            search_root=request.search_root,
            repo_root=request.repo_root,
            current_pack_kind=request.current_pack_kind,
            preferred_pack_kinds=request.preferred_pack_kinds,
            trust_statuses=request.trust_statuses,
            summary_line_contains=request.summary_line_contains,
            output_artifact_label_contains=request.output_artifact_label_contains,
            max_items=request.max_navigation_items,
            include_current_pack_kind=request.include_current_pack_kind,
        )
    )
    return OracleOperatorPackDashboard(
        schema_version='oracle_operator_pack_dashboard/v1',
        search_root=str(request.search_root),
        current_pack_kind=request.current_pack_kind,
        preferred_pack_kinds=request.preferred_pack_kinds,
        trust_statuses=request.trust_statuses,
        summary_line_contains=request.summary_line_contains,
        output_artifact_label_contains=request.output_artifact_label_contains,
        overview=_overview(workbench, navigation),
        columns=_dashboard_columns(workbench, max_column_items=request.max_column_items),
        navigation=navigation,
    )


def render_operator_pack_dashboard_markdown_lines(dashboard: OracleOperatorPackDashboard) -> list[str]:
    lines = ['## Operator Pack Dashboard']
    lines.extend([
        f"- Total indexed packs: `{dashboard.overview.total_item_count}`",
        f"- Indexed pack kinds: `{dashboard.overview.pack_kind_count}`",
        f"- Latest generated at: `{dashboard.overview.latest_generated_at_utc or 'unknown'}`",
        f"- Primary pack kind: `{dashboard.overview.primary_pack_kind or 'none'}`",
        f"- Trust statuses in scope: `{', '.join(dashboard.overview.trust_statuses) or 'none'}`",
    ])
    if dashboard.columns:
        lines.append('### Pack Family Overview')
        for column in dashboard.columns:
            lines.extend([
                f"- `{column.pack_kind}` — {column.primary_summary_line or 'No summary recorded.'}",
                f"  - Indexed items: `{column.item_count}`",
                f"  - Latest generated at: `{column.latest_generated_at_utc or 'unknown'}`",
                f"  - Trust statuses: `{', '.join(column.trust_statuses) or 'none'}`",
                f"  - Primary output: `{str(column.primary_output_artifact_path) if column.primary_output_artifact_path else 'no primary output recorded'}`",
            ])
    lines.extend(render_operator_pack_navigation_markdown_lines(dashboard.navigation))
    return lines


__all__ = [
    'OracleOperatorPackDashboardRequest',
    'OracleOperatorPackDashboardColumn',
    'OracleOperatorPackDashboardOverview',
    'OracleOperatorPackDashboard',
    'build_operator_pack_dashboard_request',
    'materialize_operator_pack_dashboard',
    'render_operator_pack_dashboard_markdown_lines',
]
