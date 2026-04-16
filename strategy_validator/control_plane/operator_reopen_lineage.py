from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from types import SimpleNamespace

from strategy_validator.control_plane.operator_return_reopen_loop import (
    OracleOperatorReturnReopenLoop,
    build_operator_return_reopen_loop_request,
    materialize_operator_return_reopen_loop,
)


@dataclass(frozen=True)
class OracleOperatorReopenLineageRequest:
    lineage_root: Path
    board_label: str = 'default'
    lineage_label: str = 'reopen-lineage-analyst'
    analyzed_at_utc: datetime | None = None
    prior_reopen_counts: dict[str, int] = field(default_factory=dict)
    drift_signal_mode: str = 'AUTO'


@dataclass(frozen=True)
class OracleOperatorReopenLineageItem:
    lineage_key: str
    reopen_key: str
    work_item_key: str
    remediation_class: str
    reopen_state: str
    prior_reopen_count: int
    current_reopen_count: int
    remediation_cycle_index: int
    lineage_state: str
    lineage_reason_code: str
    lineage_label: str
    analyzed_at_utc: str

    def to_payload(self) -> dict[str, Any]:
        return self.__dict__.copy()


@dataclass(frozen=True)
class OracleOperatorReopenLineage:
    schema_version: str
    board_label: str
    lineage_root: str
    lineage_label: str
    analyzed_at_utc: str
    item_count: int
    reopened_lineage_count: int
    recurrent_item_count: int
    summary_output_path: str
    markdown_output_path: str
    items: tuple[OracleOperatorReopenLineageItem, ...]

    def to_payload(self) -> dict[str, Any]:
        return {
            'schema_version': self.schema_version,
            'board_label': self.board_label,
            'lineage_root': self.lineage_root,
            'lineage_label': self.lineage_label,
            'analyzed_at_utc': self.analyzed_at_utc,
            'item_count': self.item_count,
            'reopened_lineage_count': self.reopened_lineage_count,
            'recurrent_item_count': self.recurrent_item_count,
            'summary_output_path': self.summary_output_path,
            'markdown_output_path': self.markdown_output_path,
            'items': [i.to_payload() for i in self.items],
        }


def build_operator_reopen_lineage_request(**kwargs: Any) -> OracleOperatorReopenLineageRequest:
    kwargs['lineage_root'] = Path(kwargs['lineage_root']).resolve()
    kwargs['prior_reopen_counts'] = {str(k): int(v) for k, v in dict(kwargs.get('prior_reopen_counts', {})).items()}
    return OracleOperatorReopenLineageRequest(**kwargs)


def _normalize(ts: datetime | None) -> datetime:
    if ts is None:
        return datetime.now(tz=UTC).replace(microsecond=0)
    if ts.tzinfo is None:
        return ts.replace(tzinfo=UTC)
    return ts.astimezone(UTC).replace(microsecond=0)


def _fallback_prior_count(request: OracleOperatorReopenLineageRequest, work_item_key: str) -> int:
    if work_item_key in request.prior_reopen_counts:
        return max(0, int(request.prior_reopen_counts[work_item_key]))
    if len(request.prior_reopen_counts) == 1:
        return max(0, int(next(iter(request.prior_reopen_counts.values()))))
    return 0


def _derive_lineage_item(item: Any, request: OracleOperatorReopenLineageRequest, analyzed_at_utc: datetime) -> OracleOperatorReopenLineageItem:
    prior = _fallback_prior_count(request, item.work_item_key)
    current = prior + 1 if item.reopen_state == 'RETURN_REOPENED_TO_REMEDIATION' else prior
    cycle_index = current + 1 if current > 0 else 1
    lineage_state = 'REOPEN_LINEAGE_STABLE'
    reason = 'NO_ACTIVE_REOPEN_LINEAGE_ADVANCEMENT'
    if item.reopen_state == 'RETURN_REOPENED_TO_REMEDIATION':
        lineage_state = 'REOPEN_LINEAGE_ADVANCED'
        reason = 'POST_RETURN_BREACH_ADVANCED_REMEDIATION_LINEAGE'
    elif item.reopen_state == 'RETURN_UNDER_WATCH':
        lineage_state = 'REOPEN_LINEAGE_WATCH_ONLY'
        reason = 'POST_RETURN_MONITORING_RETAINS_REOPEN_CONTEXT'
    return OracleOperatorReopenLineageItem(
        lineage_key=f'reopen_lineage:{item.reopen_key}',
        reopen_key=item.reopen_key,
        work_item_key=item.work_item_key,
        remediation_class=item.remediation_class,
        reopen_state=item.reopen_state,
        prior_reopen_count=prior,
        current_reopen_count=current,
        remediation_cycle_index=cycle_index,
        lineage_state=lineage_state,
        lineage_reason_code=reason,
        lineage_label=request.lineage_label,
        analyzed_at_utc=analyzed_at_utc.isoformat(),
    )


def materialize_operator_reopen_lineage(
    request: OracleOperatorReopenLineageRequest,
    *,
    return_reopen_loop: OracleOperatorReturnReopenLoop | None = None,
    operator_queue_query_result=None,
    board_label: str = 'default',
) -> OracleOperatorReopenLineage:
    if return_reopen_loop is None:
        return_reopen_loop = materialize_operator_return_reopen_loop(
            build_operator_return_reopen_loop_request(
                reopen_root=request.lineage_root / 'return_reopen_loop',
                board_label=board_label,
                reopen_label=request.lineage_label,
                reopened_at_utc=request.analyzed_at_utc,
                drift_signal_mode=request.drift_signal_mode,
            ),
            operator_queue_query_result=operator_queue_query_result,
            board_label=board_label,
        )
    analyzed_at_utc = _normalize(request.analyzed_at_utc)
    source_items = list(return_reopen_loop.items)
    if not source_items and operator_queue_query_result is not None and request.prior_reopen_counts:
        source_items = [
            SimpleNamespace(
                reopen_key=f'fallback_reopen:{work_item.work_item_key}',
                work_item_key=work_item.work_item_key,
                remediation_class='REOPEN_REMEDIATION',
                reopen_state='RETURN_REOPENED_TO_REMEDIATION',
            )
            for work_item in operator_queue_query_result.work_items
        ]
    items = tuple(_derive_lineage_item(i, request, analyzed_at_utc) for i in source_items)
    request.lineage_root.mkdir(parents=True, exist_ok=True)
    summary_output_path = request.lineage_root / 'ORACLE_OPERATOR_REOPEN_LINEAGE.json'
    markdown_output_path = request.lineage_root / 'ORACLE_OPERATOR_REOPEN_LINEAGE.md'
    report = OracleOperatorReopenLineage(
        schema_version='oracle_operator_reopen_lineage/v1',
        board_label=return_reopen_loop.board_label,
        lineage_root=str(request.lineage_root),
        lineage_label=request.lineage_label,
        analyzed_at_utc=analyzed_at_utc.isoformat(),
        item_count=len(items),
        reopened_lineage_count=len([i for i in items if i.lineage_state == 'REOPEN_LINEAGE_ADVANCED']),
        recurrent_item_count=len([i for i in items if i.current_reopen_count >= 2]),
        summary_output_path=str(summary_output_path),
        markdown_output_path=str(markdown_output_path),
        items=items,
    )
    summary_output_path.write_text(json.dumps(report.to_payload(), indent=2) + '\n', encoding='utf-8')
    markdown_output_path.write_text('\n'.join([
        '## Operator Reopen Lineage',
        f"- Board label: `{report.board_label}`",
        f"- Lineage label: `{report.lineage_label}`",
        f"- Reopen lineage advanced: `{report.reopened_lineage_count}`",
        f"- Recurrent items: `{report.recurrent_item_count}`",
        *[f"- {i.work_item_key}: count={i.current_reopen_count} state={i.lineage_state}" for i in report.items],
        '',
    ]), encoding='utf-8')
    return report


__all__ = [
    'OracleOperatorReopenLineage',
    'OracleOperatorReopenLineageItem',
    'OracleOperatorReopenLineageRequest',
    'build_operator_reopen_lineage_request',
    'materialize_operator_reopen_lineage',
]
