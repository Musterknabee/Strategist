from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from strategy_validator.control_plane.operator_return_drift_breach import (
    OracleOperatorReturnDriftBreach,
    build_operator_return_drift_breach_request,
    materialize_operator_return_drift_breach,
)


@dataclass(frozen=True)
class OracleOperatorReturnReopenLoopRequest:
    reopen_root: Path
    board_label: str = 'default'
    reopen_label: str = 'return-reopen-controller'
    reopened_at_utc: datetime | None = None
    drift_signal_mode: str = 'AUTO'


@dataclass(frozen=True)
class OracleOperatorReturnReopenLoopItem:
    reopen_key: str
    drift_breach_key: str
    work_item_key: str
    remediation_class: str
    drift_breach_state: str
    reopen_required: bool
    reopen_state: str
    reopen_reason_code: str
    reopened_queue_lane: str
    remediation_restarted: bool
    reopen_label: str
    reopened_at_utc: str

    def to_payload(self) -> dict[str, Any]:
        return self.__dict__.copy()


@dataclass(frozen=True)
class OracleOperatorReturnReopenLoop:
    schema_version: str
    board_label: str
    reopen_root: str
    reopen_label: str
    reopened_at_utc: str
    item_count: int
    reopened_count: int
    watch_count: int
    stable_count: int
    blocked_count: int
    summary_output_path: str
    markdown_output_path: str
    items: tuple[OracleOperatorReturnReopenLoopItem, ...]

    def to_payload(self) -> dict[str, Any]:
        return {
            'schema_version': self.schema_version,
            'board_label': self.board_label,
            'reopen_root': self.reopen_root,
            'reopen_label': self.reopen_label,
            'reopened_at_utc': self.reopened_at_utc,
            'item_count': self.item_count,
            'reopened_count': self.reopened_count,
            'watch_count': self.watch_count,
            'stable_count': self.stable_count,
            'blocked_count': self.blocked_count,
            'summary_output_path': self.summary_output_path,
            'markdown_output_path': self.markdown_output_path,
            'items': [i.to_payload() for i in self.items],
        }


def build_operator_return_reopen_loop_request(**kwargs: Any) -> OracleOperatorReturnReopenLoopRequest:
    kwargs['reopen_root'] = Path(kwargs['reopen_root']).resolve()
    return OracleOperatorReturnReopenLoopRequest(**kwargs)


def _normalize(ts: datetime | None) -> datetime:
    if ts is None:
        return datetime.now(tz=UTC).replace(microsecond=0)
    if ts.tzinfo is None:
        return ts.replace(tzinfo=UTC)
    return ts.astimezone(UTC).replace(microsecond=0)


def _derive_reopen_item(item: Any, request: OracleOperatorReturnReopenLoopRequest, reopened_at_utc: datetime) -> OracleOperatorReturnReopenLoopItem:
    reopen_state = 'RETURN_STABLE_NO_REOPEN'
    reason = 'POST_RETURN_STATE_STABLE'
    queue_lane = 'OPERATOR_NORMAL_QUEUE'
    restarted = False
    if item.drift_breach_state in {'DRIFT_BREACH_ACTIVE','DRIFT_BREACH_REOPENED','RESTORATION_STILL_BLOCKED'}:
        reopen_state = 'RETURN_REOPENED_TO_REMEDIATION'
        reason = 'POST_RETURN_BREACH_REQUIRES_REENTRY_REMEDIATION'
        queue_lane = 'REENTRY_QUEUE'
        restarted = True
    elif item.drift_breach_state == 'DRIFT_WATCH_ACTIVE':
        reopen_state = 'RETURN_UNDER_WATCH'
        reason = 'MONITORING_REMAINS_ACTIVE'
    return OracleOperatorReturnReopenLoopItem(
        reopen_key=f'return_reopen:{item.drift_breach_key}',
        drift_breach_key=item.drift_breach_key,
        work_item_key=item.work_item_key,
        remediation_class=item.remediation_class,
        drift_breach_state=item.drift_breach_state,
        reopen_required=item.reopen_required,
        reopen_state=reopen_state,
        reopen_reason_code=reason,
        reopened_queue_lane=queue_lane,
        remediation_restarted=restarted,
        reopen_label=request.reopen_label,
        reopened_at_utc=reopened_at_utc.isoformat(),
    )


def materialize_operator_return_reopen_loop(
    request: OracleOperatorReturnReopenLoopRequest,
    *,
    return_drift_breach: OracleOperatorReturnDriftBreach | None = None,
    operator_queue_query_result=None,
    board_label: str = 'default',
) -> OracleOperatorReturnReopenLoop:
    if return_drift_breach is None:
        return_drift_breach = materialize_operator_return_drift_breach(
            build_operator_return_drift_breach_request(
                breach_root=request.reopen_root / 'return_drift_breach',
                board_label=board_label,
                evaluator_label=request.reopen_label,
                evaluated_at_utc=request.reopened_at_utc,
                drift_signal_mode=request.drift_signal_mode,
            ),
            operator_queue_query_result=operator_queue_query_result,
            board_label=board_label,
        )
    reopened_at_utc = _normalize(request.reopened_at_utc)
    items = tuple(_derive_reopen_item(i, request, reopened_at_utc) for i in return_drift_breach.items)
    request.reopen_root.mkdir(parents=True, exist_ok=True)
    summary_output_path = request.reopen_root / 'ORACLE_OPERATOR_RETURN_REOPEN_LOOP.json'
    markdown_output_path = request.reopen_root / 'ORACLE_OPERATOR_RETURN_REOPEN_LOOP.md'
    report = OracleOperatorReturnReopenLoop(
        schema_version='oracle_operator_return_reopen_loop/v1',
        board_label=return_drift_breach.board_label,
        reopen_root=str(request.reopen_root),
        reopen_label=request.reopen_label,
        reopened_at_utc=reopened_at_utc.isoformat(),
        item_count=len(items),
        reopened_count=len([i for i in items if i.reopen_state == 'RETURN_REOPENED_TO_REMEDIATION']),
        watch_count=len([i for i in items if i.reopen_state == 'RETURN_UNDER_WATCH']),
        stable_count=len([i for i in items if i.reopen_state == 'RETURN_STABLE_NO_REOPEN']),
        blocked_count=len([i for i in items if i.drift_breach_state == 'RESTORATION_STILL_BLOCKED']),
        summary_output_path=str(summary_output_path),
        markdown_output_path=str(markdown_output_path),
        items=items,
    )
    summary_output_path.write_text(json.dumps(report.to_payload(), indent=2) + '\n', encoding='utf-8')
    markdown_output_path.write_text('\n'.join([
        '## Operator Return Reopen Loop',
        f"- Board label: `{report.board_label}`",
        f"- Reopen label: `{report.reopen_label}`",
        f"- Reopened: `{report.reopened_count}`",
        f"- Under watch: `{report.watch_count}`",
        f"- Stable: `{report.stable_count}`",
        *[f"- {i.work_item_key}: {i.reopen_state} -> {i.reopened_queue_lane}" for i in report.items],
        '',
    ]), encoding='utf-8')
    return report


__all__ = [
    'OracleOperatorReturnReopenLoop',
    'OracleOperatorReturnReopenLoopItem',
    'OracleOperatorReturnReopenLoopRequest',
    'build_operator_return_reopen_loop_request',
    'materialize_operator_return_reopen_loop',
]
