from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from strategy_validator.control_plane.operator_chronic_exit_return_bridge import (
    OracleOperatorChronicExitReturnBridge,
    build_operator_chronic_exit_return_bridge_request,
    materialize_operator_chronic_exit_return_bridge,
)


@dataclass(frozen=True)
class OracleOperatorMonitoredRejoinPolicyRequest:
    policy_root: Path
    board_label: str = 'default'
    evaluated_at_utc: datetime | None = None


@dataclass(frozen=True)
class OracleOperatorMonitoredRejoinPolicyItem:
    policy_key: str
    bridge_key: str
    certification_key: str
    work_item_key: str
    bridge_state: str
    monitoring_profile: str
    rejoin_policy_state: str
    policy_reason_code: str
    monitoring_window_minutes: int
    supervisor_monitoring_required: bool
    rejoin_queue_lane: str
    evaluated_at_utc: str

    def to_payload(self) -> dict[str, Any]:
        return self.__dict__.copy()


@dataclass(frozen=True)
class OracleOperatorMonitoredRejoinPolicy:
    schema_version: str
    board_label: str
    policy_root: str
    evaluated_at_utc: str
    policy_count: int
    monitored_rejoin_count: int
    standard_rejoin_count: int
    blocked_rejoin_count: int
    summary_output_path: str
    markdown_output_path: str
    items: tuple[OracleOperatorMonitoredRejoinPolicyItem, ...]

    def to_payload(self) -> dict[str, Any]:
        return {
            'schema_version': self.schema_version,
            'board_label': self.board_label,
            'policy_root': self.policy_root,
            'evaluated_at_utc': self.evaluated_at_utc,
            'policy_count': self.policy_count,
            'monitored_rejoin_count': self.monitored_rejoin_count,
            'standard_rejoin_count': self.standard_rejoin_count,
            'blocked_rejoin_count': self.blocked_rejoin_count,
            'summary_output_path': self.summary_output_path,
            'markdown_output_path': self.markdown_output_path,
            'items': [i.to_payload() for i in self.items],
        }


def build_operator_monitored_rejoin_policy_request(**kwargs: Any) -> OracleOperatorMonitoredRejoinPolicyRequest:
    kwargs['policy_root'] = Path(kwargs['policy_root']).resolve()
    return OracleOperatorMonitoredRejoinPolicyRequest(**kwargs)


def _normalize(ts: datetime | None) -> datetime:
    if ts is None:
        return datetime.now(tz=UTC).replace(microsecond=0)
    if ts.tzinfo is None:
        return ts.replace(tzinfo=UTC)
    return ts.astimezone(UTC).replace(microsecond=0)


def _derive_item(item: Any, evaluated_at_utc: datetime) -> OracleOperatorMonitoredRejoinPolicyItem:
    state = 'CHRONIC_REJOIN_BLOCKED'
    reason = 'RETURN_BRIDGE_NOT_AUTHORIZED'
    mins = 0
    sup = False
    lane = 'CHRONIC_REMEDIATION_QUEUE'
    if item.bridge_authorized and 'MONITORED' in item.bridge_state:
        state = 'CHRONIC_REJOIN_MONITORED'
        reason = 'CERTIFIED_CHRONIC_REJOIN_REQUIRES_HEIGHTENED_MONITORING'
        mins = 1440
        sup = True
        lane = 'SUPERVISOR_MONITORED_RETURN_QUEUE'
    elif item.bridge_authorized:
        state = 'CHRONIC_REJOIN_STANDARD_GUARDRAILS'
        reason = 'CERTIFIED_CHRONIC_REJOIN_ALLOWED_UNDER_STANDARD_GUARDRAILS'
        mins = 720
        lane = 'RETURN_AUTHORIZATION_REENTRY_QUEUE'
    return OracleOperatorMonitoredRejoinPolicyItem(
        policy_key=f'monitored_rejoin_policy:{item.bridge_key}',
        bridge_key=item.bridge_key,
        certification_key=item.certification_key,
        work_item_key=item.work_item_key,
        bridge_state=item.bridge_state,
        monitoring_profile=item.monitoring_profile,
        rejoin_policy_state=state,
        policy_reason_code=reason,
        monitoring_window_minutes=mins,
        supervisor_monitoring_required=sup,
        rejoin_queue_lane=lane,
        evaluated_at_utc=evaluated_at_utc.isoformat(),
    )


def materialize_operator_monitored_rejoin_policy(
    request: OracleOperatorMonitoredRejoinPolicyRequest,
    *,
    chronic_exit_return_bridge: OracleOperatorChronicExitReturnBridge | None = None,
    operator_queue_query_result=None,
    board_label: str = 'default',
) -> OracleOperatorMonitoredRejoinPolicy:
    if chronic_exit_return_bridge is None:
        chronic_exit_return_bridge = materialize_operator_chronic_exit_return_bridge(
            build_operator_chronic_exit_return_bridge_request(
                bridge_root=request.policy_root / 'chronic_exit_return_bridge',
                board_label=board_label,
                bridged_at_utc=request.evaluated_at_utc,
            ),
            operator_queue_query_result=operator_queue_query_result,
            board_label=board_label,
        )
    evaluated_at_utc = _normalize(request.evaluated_at_utc)
    items = tuple(_derive_item(item, evaluated_at_utc) for item in chronic_exit_return_bridge.items)
    request.policy_root.mkdir(parents=True, exist_ok=True)
    summary_output_path = request.policy_root / 'ORACLE_OPERATOR_MONITORED_REJOIN_POLICY.json'
    markdown_output_path = request.policy_root / 'ORACLE_OPERATOR_MONITORED_REJOIN_POLICY.md'
    report = OracleOperatorMonitoredRejoinPolicy(
        schema_version='oracle_operator_monitored_rejoin_policy/v1',
        board_label=chronic_exit_return_bridge.board_label,
        policy_root=str(request.policy_root),
        evaluated_at_utc=evaluated_at_utc.isoformat(),
        policy_count=len(items),
        monitored_rejoin_count=len([i for i in items if i.rejoin_policy_state == 'CHRONIC_REJOIN_MONITORED']),
        standard_rejoin_count=len([i for i in items if i.rejoin_policy_state == 'CHRONIC_REJOIN_STANDARD_GUARDRAILS']),
        blocked_rejoin_count=len([i for i in items if i.rejoin_policy_state == 'CHRONIC_REJOIN_BLOCKED']),
        summary_output_path=str(summary_output_path),
        markdown_output_path=str(markdown_output_path),
        items=items,
    )
    summary_output_path.write_text(json.dumps(report.to_payload(), indent=2) + "\n", encoding='utf-8')
    markdown_output_path.write_text("\n".join([
        '## Operator Monitored Rejoin Policy',
        f"- Board label: `{report.board_label}`",
        f"- Monitored rejoin count: `{report.monitored_rejoin_count}`",
        f"- Standard rejoin count: `{report.standard_rejoin_count}`",
        f"- Blocked rejoin count: `{report.blocked_rejoin_count}`",
        *[f"- {item.work_item_key}: {item.rejoin_policy_state} -> {item.rejoin_queue_lane}" for item in report.items],
        '',
    ]), encoding='utf-8')
    return report


__all__ = [
    'OracleOperatorMonitoredRejoinPolicy',
    'OracleOperatorMonitoredRejoinPolicyItem',
    'OracleOperatorMonitoredRejoinPolicyRequest',
    'build_operator_monitored_rejoin_policy_request',
    'materialize_operator_monitored_rejoin_policy',
]
