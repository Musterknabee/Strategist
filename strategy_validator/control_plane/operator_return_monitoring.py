from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from strategy_validator.control_plane.operator_return_activation import (
    OracleOperatorReturnActivation,
    build_operator_return_activation_request,
    materialize_operator_return_activation,
)


@dataclass(frozen=True)
class OracleOperatorReturnMonitoringRequest:
    monitoring_root: Path
    board_label: str = 'default'
    monitor_label: str = 'return-monitor'
    evaluated_at_utc: datetime | None = None
    monitoring_started_at_utc: datetime | None = None


@dataclass(frozen=True)
class OracleOperatorReturnMonitoringItem:
    monitoring_key: str
    activation_key: str
    ledger_entry_key: str
    work_item_key: str
    remediation_class: str
    activation_state: str
    monitoring_required: bool
    monitoring_window_minutes: int
    due_by_utc: str
    monitoring_state: str
    drift_watch_posture: str
    reopen_trigger: str
    policy_reason_code: str
    normalized_ready: bool
    monitor_label: str
    evaluated_at_utc: str

    def to_payload(self) -> dict[str, Any]:
        return self.__dict__.copy()


@dataclass(frozen=True)
class OracleOperatorReturnMonitoring:
    schema_version: str
    board_label: str
    monitoring_root: str
    monitor_label: str
    evaluated_at_utc: str
    item_count: int
    monitoring_required_count: int
    active_monitoring_count: int
    normalization_ready_count: int
    reopen_watch_count: int
    summary_output_path: str
    markdown_output_path: str
    items: tuple[OracleOperatorReturnMonitoringItem, ...]

    def to_payload(self) -> dict[str, Any]:
        return {
            'schema_version': self.schema_version,
            'board_label': self.board_label,
            'monitoring_root': self.monitoring_root,
            'monitor_label': self.monitor_label,
            'evaluated_at_utc': self.evaluated_at_utc,
            'item_count': self.item_count,
            'monitoring_required_count': self.monitoring_required_count,
            'active_monitoring_count': self.active_monitoring_count,
            'normalization_ready_count': self.normalization_ready_count,
            'reopen_watch_count': self.reopen_watch_count,
            'summary_output_path': self.summary_output_path,
            'markdown_output_path': self.markdown_output_path,
            'items': [i.to_payload() for i in self.items],
        }


def build_operator_return_monitoring_request(**kwargs: Any) -> OracleOperatorReturnMonitoringRequest:
    kwargs['monitoring_root'] = Path(kwargs['monitoring_root']).resolve()
    return OracleOperatorReturnMonitoringRequest(**kwargs)


def _normalize(ts: datetime | None) -> datetime:
    if ts is None:
        return datetime.now(tz=UTC).replace(microsecond=0)
    if ts.tzinfo is None:
        return ts.replace(tzinfo=UTC)
    return ts.astimezone(UTC).replace(microsecond=0)


def _derive_monitoring_item(item: Any, request: OracleOperatorReturnMonitoringRequest, evaluated_at_utc: datetime, monitoring_started_at_utc: datetime) -> OracleOperatorReturnMonitoringItem:
    window_minutes = 240 if item.monitoring_required else 0
    due_by_utc = monitoring_started_at_utc + timedelta(minutes=window_minutes)
    state = 'NO_MONITORING_REQUIRED'
    posture = 'NO_DRIFT_WATCH'
    reopen_trigger = 'NO_REOPEN_TRIGGER'
    reason = 'NORMAL_FLOW_RESTORED_WITHOUT_MONITORING'
    normalized_ready = item.normal_flow_restored and not item.monitoring_required

    if not item.normal_flow_restored:
        state = 'RETURN_NOT_RESTORED'
        posture = 'RESTORATION_NOT_ACTIVE'
        reopen_trigger = 'RETURN_REMAINED_BLOCKED'
        reason = 'RETURN_ACTIVATION_DID_NOT_RESTORE_NORMAL_FLOW'
        normalized_ready = False
        due_by_utc = evaluated_at_utc
    elif item.monitoring_required:
        state = 'MONITORING_ACTIVE'
        posture = 'HEIGHTENED_DRIFT_WATCH'
        reopen_trigger = 'REOPEN_ON_POST_RETURN_DRIFT'
        reason = 'HEIGHTENED_MONITORING_REQUIRED_AFTER_RESTORATION'
        normalized_ready = evaluated_at_utc >= due_by_utc
        if normalized_ready:
            state = 'MONITORING_WINDOW_COMPLETE'
            posture = 'DRIFT_WATCH_COMPLETE'
            reopen_trigger = 'REOPEN_ONLY_IF_NEW_EVIDENCE_APPEARS'
            reason = 'POST_RETURN_MONITORING_WINDOW_COMPLETED'

    return OracleOperatorReturnMonitoringItem(
        monitoring_key=f'return_monitoring:{item.activation_key}',
        activation_key=item.activation_key,
        ledger_entry_key=item.ledger_entry_key,
        work_item_key=item.work_item_key,
        remediation_class=item.remediation_class,
        activation_state=item.activation_state,
        monitoring_required=item.monitoring_required,
        monitoring_window_minutes=window_minutes,
        due_by_utc=due_by_utc.isoformat(),
        monitoring_state=state,
        drift_watch_posture=posture,
        reopen_trigger=reopen_trigger,
        policy_reason_code=reason,
        normalized_ready=normalized_ready,
        monitor_label=request.monitor_label,
        evaluated_at_utc=evaluated_at_utc.isoformat(),
    )


def materialize_operator_return_monitoring(
    request: OracleOperatorReturnMonitoringRequest,
    *,
    return_activation: OracleOperatorReturnActivation | None = None,
    operator_queue_query_result=None,
    board_label: str = 'default',
) -> OracleOperatorReturnMonitoring:
    if return_activation is None:
        return_activation = materialize_operator_return_activation(
            build_operator_return_activation_request(
                activation_root=request.monitoring_root / 'return_activation',
                board_label=board_label,
                activator_label=request.monitor_label,
                activated_at_utc=request.evaluated_at_utc,
            ),
            operator_queue_query_result=operator_queue_query_result,
            board_label=board_label,
        )
    evaluated_at_utc = _normalize(request.evaluated_at_utc)
    monitoring_started_at_utc = _normalize(request.monitoring_started_at_utc or request.evaluated_at_utc)
    items = tuple(_derive_monitoring_item(i, request, evaluated_at_utc, monitoring_started_at_utc) for i in return_activation.items)
    request.monitoring_root.mkdir(parents=True, exist_ok=True)
    summary_output_path = request.monitoring_root / 'ORACLE_OPERATOR_RETURN_MONITORING.json'
    markdown_output_path = request.monitoring_root / 'ORACLE_OPERATOR_RETURN_MONITORING.md'
    report = OracleOperatorReturnMonitoring(
        schema_version='oracle_operator_return_monitoring/v1',
        board_label=return_activation.board_label,
        monitoring_root=str(request.monitoring_root),
        monitor_label=request.monitor_label,
        evaluated_at_utc=evaluated_at_utc.isoformat(),
        item_count=len(items),
        monitoring_required_count=len([i for i in items if i.monitoring_required]),
        active_monitoring_count=len([i for i in items if i.monitoring_state == 'MONITORING_ACTIVE']),
        normalization_ready_count=len([i for i in items if i.normalized_ready]),
        reopen_watch_count=len([i for i in items if i.reopen_trigger != 'NO_REOPEN_TRIGGER']),
        summary_output_path=str(summary_output_path),
        markdown_output_path=str(markdown_output_path),
        items=items,
    )
    summary_output_path.write_text(json.dumps(report.to_payload(), indent=2) + '\n', encoding='utf-8')
    markdown_output_path.write_text('\n'.join([
        '## Operator Return Monitoring',
        f"- Board label: `{report.board_label}`",
        f"- Monitor label: `{report.monitor_label}`",
        f"- Monitoring required: `{report.monitoring_required_count}`",
        f"- Monitoring active: `{report.active_monitoring_count}`",
        f"- Normalization ready: `{report.normalization_ready_count}`",
        *[f"- {i.work_item_key}: {i.monitoring_state} -> {i.reopen_trigger}" for i in report.items],
        '',
    ]), encoding='utf-8')
    return report


__all__ = [
    'OracleOperatorReturnMonitoring',
    'OracleOperatorReturnMonitoringItem',
    'OracleOperatorReturnMonitoringRequest',
    'build_operator_return_monitoring_request',
    'materialize_operator_return_monitoring',
]
