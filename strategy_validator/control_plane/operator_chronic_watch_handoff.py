from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from strategy_validator.control_plane.operator_monitored_rejoin_activation import (
    OracleOperatorMonitoredRejoinActivation,
    build_operator_monitored_rejoin_activation_request,
    materialize_operator_monitored_rejoin_activation,
)


@dataclass(frozen=True)
class OracleOperatorChronicWatchHandoffRequest:
    handoff_root: Path
    board_label: str = 'default'
    handoff_label: str = 'chronic-watch-handoff'
    handed_off_at_utc: datetime | None = None


@dataclass(frozen=True)
class OracleOperatorChronicWatchHandoffItem:
    handoff_key: str
    activation_key: str
    policy_key: str
    work_item_key: str
    activation_state: str
    handoff_state: str
    watch_authority: str
    watch_window_minutes: int
    watch_due_by_utc: str
    return_monitoring_target: str
    reopen_escalation_target: str
    handoff_reason_code: str
    handoff_label: str
    handed_off_at_utc: str

    def to_payload(self) -> dict[str, Any]:
        return self.__dict__.copy()


@dataclass(frozen=True)
class OracleOperatorChronicWatchHandoff:
    schema_version: str
    board_label: str
    handoff_root: str
    handoff_label: str
    handed_off_at_utc: str
    handoff_count: int
    monitoring_handoff_count: int
    supervisor_handoff_count: int
    blocked_handoff_count: int
    summary_output_path: str
    markdown_output_path: str
    items: tuple[OracleOperatorChronicWatchHandoffItem, ...]

    def to_payload(self) -> dict[str, Any]:
        return {
            'schema_version': self.schema_version,
            'board_label': self.board_label,
            'handoff_root': self.handoff_root,
            'handoff_label': self.handoff_label,
            'handed_off_at_utc': self.handed_off_at_utc,
            'handoff_count': self.handoff_count,
            'monitoring_handoff_count': self.monitoring_handoff_count,
            'supervisor_handoff_count': self.supervisor_handoff_count,
            'blocked_handoff_count': self.blocked_handoff_count,
            'summary_output_path': self.summary_output_path,
            'markdown_output_path': self.markdown_output_path,
            'items': [i.to_payload() for i in self.items],
        }


def build_operator_chronic_watch_handoff_request(**kwargs: Any) -> OracleOperatorChronicWatchHandoffRequest:
    kwargs['handoff_root'] = Path(kwargs['handoff_root']).resolve()
    return OracleOperatorChronicWatchHandoffRequest(**kwargs)


def _normalize(ts: datetime | None) -> datetime:
    if ts is None:
        return datetime.now(tz=UTC).replace(microsecond=0)
    if ts.tzinfo is None:
        return ts.replace(tzinfo=UTC)
    return ts.astimezone(UTC).replace(microsecond=0)


def _derive_item(item: Any, request: OracleOperatorChronicWatchHandoffRequest, handed_off_at_utc: datetime) -> OracleOperatorChronicWatchHandoffItem:
    due_by = handed_off_at_utc + timedelta(minutes=item.monitoring_window_minutes)
    if item.activation_state == 'MONITORED_REJOIN_ACTIVATED':
        handoff_state = 'CHRONIC_WATCH_HANDOFF_ACTIVE'
        authority = 'SUPERVISOR_MONITORING_AUTHORITY'
        target = 'operator_return_monitoring'
        reopen_target = 'operator_return_reopen_loop'
        reason = 'HEIGHTENED_MONITORED_REJOIN_REQUIRES_CHRONIC_WATCH_HANDOFF'
    elif item.activation_state == 'STANDARD_REJOIN_ACTIVATED':
        handoff_state = 'STANDARD_RETURN_MONITORING_HANDOFF'
        authority = 'RETURN_MONITOR'
        target = 'operator_return_monitoring'
        reopen_target = 'operator_return_reopen_loop'
        reason = 'STANDARD_CHRONIC_REJOIN_BRIDGED_BACK_TO_RETURN_MONITORING'
    else:
        handoff_state = 'WATCH_HANDOFF_BLOCKED'
        authority = 'CHRONIC_REMEDIATION_AUTHORITY'
        target = 'blocked'
        reopen_target = 'operator_recurrence_tribunal_lane'
        reason = 'REJOIN_ACTIVATION_DID_NOT_AUTHORIZE_MONITORING_HANDOFF'
        due_by = handed_off_at_utc
    return OracleOperatorChronicWatchHandoffItem(
        handoff_key=f'chronic_watch_handoff:{item.activation_key}',
        activation_key=item.activation_key,
        policy_key=item.policy_key,
        work_item_key=item.work_item_key,
        activation_state=item.activation_state,
        handoff_state=handoff_state,
        watch_authority=authority,
        watch_window_minutes=item.monitoring_window_minutes,
        watch_due_by_utc=due_by.isoformat(),
        return_monitoring_target=target,
        reopen_escalation_target=reopen_target,
        handoff_reason_code=reason,
        handoff_label=request.handoff_label,
        handed_off_at_utc=handed_off_at_utc.isoformat(),
    )


def materialize_operator_chronic_watch_handoff(
    request: OracleOperatorChronicWatchHandoffRequest,
    *,
    monitored_rejoin_activation: OracleOperatorMonitoredRejoinActivation | None = None,
    operator_queue_query_result=None,
    board_label: str = 'default',
) -> OracleOperatorChronicWatchHandoff:
    if monitored_rejoin_activation is None:
        monitored_rejoin_activation = materialize_operator_monitored_rejoin_activation(
            build_operator_monitored_rejoin_activation_request(
                activation_root=request.handoff_root / 'monitored_rejoin_activation',
                board_label=board_label,
                activator_label=request.handoff_label,
                activated_at_utc=request.handed_off_at_utc,
            ),
            operator_queue_query_result=operator_queue_query_result,
            board_label=board_label,
        )
    handed_off_at_utc = _normalize(request.handed_off_at_utc)
    items = tuple(_derive_item(i, request, handed_off_at_utc) for i in monitored_rejoin_activation.items)
    request.handoff_root.mkdir(parents=True, exist_ok=True)
    summary_output_path = request.handoff_root / 'ORACLE_OPERATOR_CHRONIC_WATCH_HANDOFF.json'
    markdown_output_path = request.handoff_root / 'ORACLE_OPERATOR_CHRONIC_WATCH_HANDOFF.md'
    report = OracleOperatorChronicWatchHandoff(
        schema_version='oracle_operator_chronic_watch_handoff/v1',
        board_label=monitored_rejoin_activation.board_label,
        handoff_root=str(request.handoff_root),
        handoff_label=request.handoff_label,
        handed_off_at_utc=handed_off_at_utc.isoformat(),
        handoff_count=len(items),
        monitoring_handoff_count=len([i for i in items if i.handoff_state in ('CHRONIC_WATCH_HANDOFF_ACTIVE', 'STANDARD_RETURN_MONITORING_HANDOFF')]),
        supervisor_handoff_count=len([i for i in items if i.watch_authority == 'SUPERVISOR_MONITORING_AUTHORITY']),
        blocked_handoff_count=len([i for i in items if i.handoff_state == 'WATCH_HANDOFF_BLOCKED']),
        summary_output_path=str(summary_output_path),
        markdown_output_path=str(markdown_output_path),
        items=items,
    )
    summary_output_path.write_text(json.dumps(report.to_payload(), indent=2) + '\n', encoding='utf-8')
    markdown_output_path.write_text(
        '\n'.join([
            '## Operator Chronic Watch Handoff',
            f"- Board label: `{report.board_label}`",
            f"- Handoff label: `{report.handoff_label}`",
            f"- Monitoring handoff count: `{report.monitoring_handoff_count}`",
            f"- Supervisor handoff count: `{report.supervisor_handoff_count}`",
            f"- Blocked handoff count: `{report.blocked_handoff_count}`",
            *[f"- {i.work_item_key}: {i.handoff_state} -> {i.return_monitoring_target}" for i in report.items],
            '',
        ]),
        encoding='utf-8',
    )
    return report


__all__ = [
    'OracleOperatorChronicWatchHandoff',
    'OracleOperatorChronicWatchHandoffItem',
    'OracleOperatorChronicWatchHandoffRequest',
    'build_operator_chronic_watch_handoff_request',
    'materialize_operator_chronic_watch_handoff',
]
