from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from strategy_validator.control_plane.operator_monitored_rejoin_policy import (
    OracleOperatorMonitoredRejoinPolicy,
    build_operator_monitored_rejoin_policy_request,
    materialize_operator_monitored_rejoin_policy,
)


@dataclass(frozen=True)
class OracleOperatorMonitoredRejoinActivationRequest:
    activation_root: Path
    board_label: str = 'default'
    activator_label: str = 'chronic-rejoin-activator'
    activated_at_utc: datetime | None = None


@dataclass(frozen=True)
class OracleOperatorMonitoredRejoinActivationItem:
    activation_key: str
    policy_key: str
    bridge_key: str
    certification_key: str
    work_item_key: str
    rejoin_policy_state: str
    monitoring_window_minutes: int
    supervisor_monitoring_required: bool
    activation_state: str
    activation_reason_code: str
    activated_queue_lane: str
    return_monitoring_bridge_state: str
    activator_label: str
    activated_at_utc: str

    def to_payload(self) -> dict[str, Any]:
        return self.__dict__.copy()


@dataclass(frozen=True)
class OracleOperatorMonitoredRejoinActivation:
    schema_version: str
    board_label: str
    activation_root: str
    activator_label: str
    activated_at_utc: str
    activation_count: int
    activated_count: int
    monitored_activation_count: int
    blocked_activation_count: int
    summary_output_path: str
    markdown_output_path: str
    items: tuple[OracleOperatorMonitoredRejoinActivationItem, ...]

    def to_payload(self) -> dict[str, Any]:
        return {
            'schema_version': self.schema_version,
            'board_label': self.board_label,
            'activation_root': self.activation_root,
            'activator_label': self.activator_label,
            'activated_at_utc': self.activated_at_utc,
            'activation_count': self.activation_count,
            'activated_count': self.activated_count,
            'monitored_activation_count': self.monitored_activation_count,
            'blocked_activation_count': self.blocked_activation_count,
            'summary_output_path': self.summary_output_path,
            'markdown_output_path': self.markdown_output_path,
            'items': [i.to_payload() for i in self.items],
        }


def build_operator_monitored_rejoin_activation_request(**kwargs: Any) -> OracleOperatorMonitoredRejoinActivationRequest:
    kwargs['activation_root'] = Path(kwargs['activation_root']).resolve()
    return OracleOperatorMonitoredRejoinActivationRequest(**kwargs)


def _normalize(ts: datetime | None) -> datetime:
    if ts is None:
        return datetime.now(tz=UTC).replace(microsecond=0)
    if ts.tzinfo is None:
        return ts.replace(tzinfo=UTC)
    return ts.astimezone(UTC).replace(microsecond=0)


def _derive_item(item: Any, request: OracleOperatorMonitoredRejoinActivationRequest, activated_at_utc: datetime) -> OracleOperatorMonitoredRejoinActivationItem:
    if item.rejoin_policy_state == 'CHRONIC_REJOIN_MONITORED':
        activation_state = 'MONITORED_REJOIN_ACTIVATED'
        reason = 'CERTIFIED_CHRONIC_REJOIN_ACTIVATED_WITH_HEIGHTENED_MONITORING'
        lane = 'SUPERVISOR_MONITORED_RETURN_QUEUE'
        bridge_state = 'BRIDGED_TO_RETURN_MONITORING'
    elif item.rejoin_policy_state == 'CHRONIC_REJOIN_STANDARD_GUARDRAILS':
        activation_state = 'STANDARD_REJOIN_ACTIVATED'
        reason = 'CERTIFIED_CHRONIC_REJOIN_ACTIVATED_UNDER_STANDARD_GUARDRAILS'
        lane = 'RETURN_AUTHORIZATION_REENTRY_QUEUE'
        bridge_state = 'BRIDGED_TO_STANDARD_RETURN_FLOW'
    else:
        activation_state = 'REJOIN_ACTIVATION_BLOCKED'
        reason = 'CHRONIC_REJOIN_POLICY_DID_NOT_AUTHORIZE_ACTIVATION'
        lane = 'CHRONIC_REMEDIATION_QUEUE'
        bridge_state = 'REJOIN_REMAINED_BLOCKED'
    return OracleOperatorMonitoredRejoinActivationItem(
        activation_key=f'monitored_rejoin_activation:{item.policy_key}',
        policy_key=item.policy_key,
        bridge_key=item.bridge_key,
        certification_key=item.certification_key,
        work_item_key=item.work_item_key,
        rejoin_policy_state=item.rejoin_policy_state,
        monitoring_window_minutes=item.monitoring_window_minutes,
        supervisor_monitoring_required=item.supervisor_monitoring_required,
        activation_state=activation_state,
        activation_reason_code=reason,
        activated_queue_lane=lane,
        return_monitoring_bridge_state=bridge_state,
        activator_label=request.activator_label,
        activated_at_utc=activated_at_utc.isoformat(),
    )


def materialize_operator_monitored_rejoin_activation(
    request: OracleOperatorMonitoredRejoinActivationRequest,
    *,
    monitored_rejoin_policy: OracleOperatorMonitoredRejoinPolicy | None = None,
    operator_queue_query_result=None,
    board_label: str = 'default',
) -> OracleOperatorMonitoredRejoinActivation:
    if monitored_rejoin_policy is None:
        monitored_rejoin_policy = materialize_operator_monitored_rejoin_policy(
            build_operator_monitored_rejoin_policy_request(
                policy_root=request.activation_root / 'monitored_rejoin_policy',
                board_label=board_label,
                evaluated_at_utc=request.activated_at_utc,
            ),
            operator_queue_query_result=operator_queue_query_result,
            board_label=board_label,
        )
    activated_at_utc = _normalize(request.activated_at_utc)
    items = tuple(_derive_item(i, request, activated_at_utc) for i in monitored_rejoin_policy.items)
    request.activation_root.mkdir(parents=True, exist_ok=True)
    summary_output_path = request.activation_root / 'ORACLE_OPERATOR_MONITORED_REJOIN_ACTIVATION.json'
    markdown_output_path = request.activation_root / 'ORACLE_OPERATOR_MONITORED_REJOIN_ACTIVATION.md'
    report = OracleOperatorMonitoredRejoinActivation(
        schema_version='oracle_operator_monitored_rejoin_activation/v1',
        board_label=monitored_rejoin_policy.board_label,
        activation_root=str(request.activation_root),
        activator_label=request.activator_label,
        activated_at_utc=activated_at_utc.isoformat(),
        activation_count=len(items),
        activated_count=len([i for i in items if i.activation_state != 'REJOIN_ACTIVATION_BLOCKED']),
        monitored_activation_count=len([i for i in items if i.activation_state == 'MONITORED_REJOIN_ACTIVATED']),
        blocked_activation_count=len([i for i in items if i.activation_state == 'REJOIN_ACTIVATION_BLOCKED']),
        summary_output_path=str(summary_output_path),
        markdown_output_path=str(markdown_output_path),
        items=items,
    )
    summary_output_path.write_text(json.dumps(report.to_payload(), indent=2) + '\n', encoding='utf-8')
    markdown_output_path.write_text(
        '\n'.join([
            '## Operator Monitored Rejoin Activation',
            f"- Board label: `{report.board_label}`",
            f"- Activator label: `{report.activator_label}`",
            f"- Activated count: `{report.activated_count}`",
            f"- Monitored activation count: `{report.monitored_activation_count}`",
            f"- Blocked activation count: `{report.blocked_activation_count}`",
            *[f"- {i.work_item_key}: {i.activation_state} -> {i.activated_queue_lane}" for i in report.items],
            '',
        ]),
        encoding='utf-8',
    )
    return report


__all__ = [
    'OracleOperatorMonitoredRejoinActivation',
    'OracleOperatorMonitoredRejoinActivationItem',
    'OracleOperatorMonitoredRejoinActivationRequest',
    'build_operator_monitored_rejoin_activation_request',
    'materialize_operator_monitored_rejoin_activation',
]
