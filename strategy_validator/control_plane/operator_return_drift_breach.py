from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from strategy_validator.control_plane.operator_restoration_audit import (
    OracleOperatorRestorationAudit,
    build_operator_restoration_audit_request,
    materialize_operator_restoration_audit,
)


@dataclass(frozen=True)
class OracleOperatorReturnDriftBreachRequest:
    breach_root: Path
    board_label: str = 'default'
    evaluator_label: str = 'return-drift-evaluator'
    evaluated_at_utc: datetime | None = None
    drift_signal_mode: str = 'AUTO'


@dataclass(frozen=True)
class OracleOperatorReturnDriftBreachItem:
    drift_breach_key: str
    audit_key: str
    monitoring_key: str
    work_item_key: str
    remediation_class: str
    audit_state: str
    normalization_state: str
    drift_signal_mode: str
    drift_breach_state: str
    breach_reason_code: str
    reopen_required: bool
    next_queue_lane: str
    evaluator_label: str
    evaluated_at_utc: str

    def to_payload(self) -> dict[str, Any]:
        return self.__dict__.copy()


@dataclass(frozen=True)
class OracleOperatorReturnDriftBreach:
    schema_version: str
    board_label: str
    breach_root: str
    evaluator_label: str
    evaluated_at_utc: str
    item_count: int
    breach_count: int
    watch_count: int
    reopened_count: int
    stable_count: int
    summary_output_path: str
    markdown_output_path: str
    items: tuple[OracleOperatorReturnDriftBreachItem, ...]

    def to_payload(self) -> dict[str, Any]:
        return {
            'schema_version': self.schema_version,
            'board_label': self.board_label,
            'breach_root': self.breach_root,
            'evaluator_label': self.evaluator_label,
            'evaluated_at_utc': self.evaluated_at_utc,
            'item_count': self.item_count,
            'breach_count': self.breach_count,
            'watch_count': self.watch_count,
            'reopened_count': self.reopened_count,
            'stable_count': self.stable_count,
            'summary_output_path': self.summary_output_path,
            'markdown_output_path': self.markdown_output_path,
            'items': [i.to_payload() for i in self.items],
        }


def build_operator_return_drift_breach_request(**kwargs: Any) -> OracleOperatorReturnDriftBreachRequest:
    kwargs['breach_root'] = Path(kwargs['breach_root']).resolve()
    return OracleOperatorReturnDriftBreachRequest(**kwargs)


def _normalize(ts: datetime | None) -> datetime:
    if ts is None:
        return datetime.now(tz=UTC).replace(microsecond=0)
    if ts.tzinfo is None:
        return ts.replace(tzinfo=UTC)
    return ts.astimezone(UTC).replace(microsecond=0)


def _derive_breach_item(item: Any, request: OracleOperatorReturnDriftBreachRequest, evaluated_at_utc: datetime) -> OracleOperatorReturnDriftBreachItem:
    state = 'NO_DRIFT_BREACH'
    reason = 'POST_RETURN_NORMALIZATION_CONFIRMED'
    reopen_required = False
    next_queue_lane = 'OPERATOR_NORMAL_QUEUE'
    if item.audit_state == 'RESTORATION_AUDIT_REOPENED':
        state = 'DRIFT_BREACH_REOPENED'
        reason = 'RESTORATION_ATTEMPT_REOPENED_AFTER_RETURN'
        reopen_required = True
        next_queue_lane = 'REENTRY_QUEUE'
    elif request.drift_signal_mode == 'DETECTED' and item.audit_state in {'RESTORATION_AUDIT_MONITORED', 'RESTORATION_AUDIT_NORMALIZED'}:
        state = 'DRIFT_BREACH_ACTIVE'
        reason = 'POST_RETURN_DRIFT_SIGNAL_DETECTED'
        reopen_required = True
        next_queue_lane = 'REENTRY_QUEUE'
    elif item.audit_state == 'RESTORATION_AUDIT_MONITORED':
        state = 'DRIFT_WATCH_ACTIVE'
        reason = 'POST_RETURN_MONITORING_STILL_ACTIVE'
        next_queue_lane = 'OPERATOR_NORMAL_QUEUE'
    elif item.audit_state == 'RESTORATION_AUDIT_BLOCKED':
        state = 'RESTORATION_STILL_BLOCKED'
        reason = 'NORMALIZATION_NOT_YET_CONFIRMED'
        reopen_required = True
        next_queue_lane = 'REENTRY_QUEUE'
    return OracleOperatorReturnDriftBreachItem(
        drift_breach_key=f'return_drift_breach:{item.audit_key}',
        audit_key=item.audit_key,
        monitoring_key=item.monitoring_key,
        work_item_key=item.work_item_key,
        remediation_class=item.remediation_class,
        audit_state=item.audit_state,
        normalization_state=item.normalization_state,
        drift_signal_mode=request.drift_signal_mode,
        drift_breach_state=state,
        breach_reason_code=reason,
        reopen_required=reopen_required,
        next_queue_lane=next_queue_lane,
        evaluator_label=request.evaluator_label,
        evaluated_at_utc=evaluated_at_utc.isoformat(),
    )


def materialize_operator_return_drift_breach(
    request: OracleOperatorReturnDriftBreachRequest,
    *,
    restoration_audit: OracleOperatorRestorationAudit | None = None,
    operator_queue_query_result=None,
    board_label: str = 'default',
) -> OracleOperatorReturnDriftBreach:
    if restoration_audit is None:
        restoration_audit = materialize_operator_restoration_audit(
            build_operator_restoration_audit_request(
                audit_root=request.breach_root / 'restoration_audit',
                board_label=board_label,
                auditor_label=request.evaluator_label,
                audited_at_utc=request.evaluated_at_utc,
            ),
            operator_queue_query_result=operator_queue_query_result,
            board_label=board_label,
        )
    evaluated_at_utc = _normalize(request.evaluated_at_utc)
    items = tuple(_derive_breach_item(i, request, evaluated_at_utc) for i in restoration_audit.items)
    request.breach_root.mkdir(parents=True, exist_ok=True)
    summary_output_path = request.breach_root / 'ORACLE_OPERATOR_RETURN_DRIFT_BREACH.json'
    markdown_output_path = request.breach_root / 'ORACLE_OPERATOR_RETURN_DRIFT_BREACH.md'
    report = OracleOperatorReturnDriftBreach(
        schema_version='oracle_operator_return_drift_breach/v1',
        board_label=restoration_audit.board_label,
        breach_root=str(request.breach_root),
        evaluator_label=request.evaluator_label,
        evaluated_at_utc=evaluated_at_utc.isoformat(),
        item_count=len(items),
        breach_count=len([i for i in items if i.drift_breach_state in {'DRIFT_BREACH_ACTIVE','DRIFT_BREACH_REOPENED','RESTORATION_STILL_BLOCKED'}]),
        watch_count=len([i for i in items if i.drift_breach_state == 'DRIFT_WATCH_ACTIVE']),
        reopened_count=len([i for i in items if i.reopen_required]),
        stable_count=len([i for i in items if i.drift_breach_state == 'NO_DRIFT_BREACH']),
        summary_output_path=str(summary_output_path),
        markdown_output_path=str(markdown_output_path),
        items=items,
    )
    summary_output_path.write_text(json.dumps(report.to_payload(), indent=2) + '\n', encoding='utf-8')
    markdown_output_path.write_text('\n'.join([
        '## Operator Return Drift Breach',
        f"- Board label: `{report.board_label}`",
        f"- Evaluator label: `{report.evaluator_label}`",
        f"- Breaches: `{report.breach_count}`",
        f"- Watch active: `{report.watch_count}`",
        f"- Reopen required: `{report.reopened_count}`",
        *[f"- {i.work_item_key}: {i.drift_breach_state} -> {i.next_queue_lane}" for i in report.items],
        '',
    ]), encoding='utf-8')
    return report


__all__ = [
    'OracleOperatorReturnDriftBreach',
    'OracleOperatorReturnDriftBreachItem',
    'OracleOperatorReturnDriftBreachRequest',
    'build_operator_return_drift_breach_request',
    'materialize_operator_return_drift_breach',
]
