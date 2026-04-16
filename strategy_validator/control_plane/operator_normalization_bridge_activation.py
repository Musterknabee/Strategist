from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from strategy_validator.control_plane.operator_monitored_rejoin_normalization_bridge import (
    OracleOperatorMonitoredRejoinNormalizationBridge,
    build_operator_monitored_rejoin_normalization_bridge_request,
    materialize_operator_monitored_rejoin_normalization_bridge,
)


@dataclass(frozen=True)
class OracleOperatorNormalizationBridgeActivationRequest:
    activation_root: Path
    board_label: str = 'default'
    activator_label: str = 'normalization-bridge-activator'
    activated_at_utc: datetime | None = None
    monitoring_started_at_utc: datetime | None = None


@dataclass(frozen=True)
class OracleOperatorNormalizationBridgeActivationItem:
    bridge_activation_key: str
    bridge_key: str
    outcome_key: str
    work_item_key: str
    bridge_state: str
    normalization_eligible: bool
    reopen_required: bool
    activation_state: str
    activation_reason_code: str
    convergence_origin: str
    monitoring_started_at_utc: str
    activated_return_monitoring_target: str
    activated_restoration_audit_target: str
    next_queue_lane: str
    activator_label: str
    activated_at_utc: str

    def to_payload(self) -> dict[str, Any]:
        return self.__dict__.copy()


@dataclass(frozen=True)
class OracleOperatorNormalizationBridgeActivation:
    schema_version: str
    board_label: str
    activation_root: str
    activator_label: str
    activated_at_utc: str
    activation_count: int
    activated_count: int
    normalization_activation_count: int
    watch_continuation_count: int
    reopen_activation_count: int
    blocked_count: int
    summary_output_path: str
    markdown_output_path: str
    items: tuple[OracleOperatorNormalizationBridgeActivationItem, ...]

    def to_payload(self) -> dict[str, Any]:
        return {
            'schema_version': self.schema_version,
            'board_label': self.board_label,
            'activation_root': self.activation_root,
            'activator_label': self.activator_label,
            'activated_at_utc': self.activated_at_utc,
            'activation_count': self.activation_count,
            'activated_count': self.activated_count,
            'normalization_activation_count': self.normalization_activation_count,
            'watch_continuation_count': self.watch_continuation_count,
            'reopen_activation_count': self.reopen_activation_count,
            'blocked_count': self.blocked_count,
            'summary_output_path': self.summary_output_path,
            'markdown_output_path': self.markdown_output_path,
            'items': [item.to_payload() for item in self.items],
        }


def build_operator_normalization_bridge_activation_request(**kwargs: Any) -> OracleOperatorNormalizationBridgeActivationRequest:
    kwargs['activation_root'] = Path(kwargs['activation_root']).resolve()
    return OracleOperatorNormalizationBridgeActivationRequest(**kwargs)


def _normalize(ts: datetime | None) -> datetime:
    if ts is None:
        return datetime.now(tz=UTC).replace(microsecond=0)
    if ts.tzinfo is None:
        return ts.replace(tzinfo=UTC)
    return ts.astimezone(UTC).replace(microsecond=0)


def _derive_item(item: Any, request: OracleOperatorNormalizationBridgeActivationRequest, activated_at_utc: datetime, monitoring_started_at_utc: datetime) -> OracleOperatorNormalizationBridgeActivationItem:
    if item.bridge_state == 'MONITORED_REJOIN_BRIDGED_TO_NORMALIZATION':
        state = 'NORMALIZATION_BRIDGE_ACTIVATED'
        reason = 'CHRONIC_MONITORED_REJOIN_NORMALIZATION_BRIDGE_ACTIVATED_INTO_STANDARD_RESTORATION_LOOP'
        origin = 'CHRONIC_WATCH_NORMALIZATION'
        return_target = 'operator_return_monitoring'
        audit_target = 'operator_restoration_audit'
        lane = 'RETURN_NORMALIZATION_BRIDGE'
    elif item.bridge_state == 'MONITORED_REJOIN_WATCH_CONTINUES':
        state = 'NORMALIZATION_BRIDGE_CONTINUES_WATCH'
        reason = 'CHRONIC_MONITORED_REJOIN_REMAINS_UNDER_WATCH_BEFORE_FULL_NORMALIZATION_ACTIVATION'
        origin = 'CHRONIC_WATCH_CONTINUED_OBSERVATION'
        return_target = 'operator_return_monitoring'
        audit_target = 'operator_restoration_audit'
        lane = 'SUPERVISOR_MONITORED_RETURN_QUEUE'
    elif item.bridge_state == 'MONITORED_REJOIN_REOPEN_REQUIRED':
        state = 'NORMALIZATION_BRIDGE_REOPEN_REQUIRED'
        reason = 'CHRONIC_MONITORED_REJOIN_BREACHED_AND_CANNOT_ACTIVATE_NORMALIZATION_LOOP'
        origin = 'CHRONIC_WATCH_REOPEN'
        return_target = 'operator_return_reopen_loop'
        audit_target = 'operator_reentry_queue_state'
        lane = 'REENTRY_QUEUE'
    else:
        state = 'NORMALIZATION_BRIDGE_ACTIVATION_BLOCKED'
        reason = 'CHRONIC_MONITORED_REJOIN_DID_NOT_AUTHORIZE_NORMALIZATION_ACTIVATION'
        origin = 'CHRONIC_WATCH_BLOCKED'
        return_target = 'blocked'
        audit_target = 'blocked'
        lane = 'CHRONIC_REMEDIATION_QUEUE'

    return OracleOperatorNormalizationBridgeActivationItem(
        bridge_activation_key=f'normalization_bridge_activation:{item.bridge_key}',
        bridge_key=item.bridge_key,
        outcome_key=item.outcome_key,
        work_item_key=item.work_item_key,
        bridge_state=item.bridge_state,
        normalization_eligible=item.normalization_eligible,
        reopen_required=item.reopen_required,
        activation_state=state,
        activation_reason_code=reason,
        convergence_origin=origin,
        monitoring_started_at_utc=monitoring_started_at_utc.isoformat(),
        activated_return_monitoring_target=return_target,
        activated_restoration_audit_target=audit_target,
        next_queue_lane=lane,
        activator_label=request.activator_label,
        activated_at_utc=activated_at_utc.isoformat(),
    )


def materialize_operator_normalization_bridge_activation(
    request: OracleOperatorNormalizationBridgeActivationRequest,
    *,
    monitored_rejoin_normalization_bridge: OracleOperatorMonitoredRejoinNormalizationBridge | None = None,
    operator_queue_query_result=None,
    board_label: str = 'default',
) -> OracleOperatorNormalizationBridgeActivation:
    if monitored_rejoin_normalization_bridge is None:
        monitored_rejoin_normalization_bridge = materialize_operator_monitored_rejoin_normalization_bridge(
            build_operator_monitored_rejoin_normalization_bridge_request(
                bridge_root=request.activation_root / 'monitored_rejoin_normalization_bridge',
                board_label=board_label,
                bridged_at_utc=request.activated_at_utc,
            ),
            operator_queue_query_result=operator_queue_query_result,
            board_label=board_label,
        )
    activated_at_utc = _normalize(request.activated_at_utc)
    monitoring_started_at_utc = _normalize(request.monitoring_started_at_utc or request.activated_at_utc)
    items = tuple(_derive_item(item, request, activated_at_utc, monitoring_started_at_utc) for item in monitored_rejoin_normalization_bridge.items)
    request.activation_root.mkdir(parents=True, exist_ok=True)
    summary_output_path = request.activation_root / 'ORACLE_OPERATOR_NORMALIZATION_BRIDGE_ACTIVATION.json'
    markdown_output_path = request.activation_root / 'ORACLE_OPERATOR_NORMALIZATION_BRIDGE_ACTIVATION.md'
    report = OracleOperatorNormalizationBridgeActivation(
        schema_version='oracle_operator_normalization_bridge_activation/v1',
        board_label=monitored_rejoin_normalization_bridge.board_label,
        activation_root=str(request.activation_root),
        activator_label=request.activator_label,
        activated_at_utc=activated_at_utc.isoformat(),
        activation_count=len(items),
        activated_count=len([i for i in items if i.activation_state != 'NORMALIZATION_BRIDGE_ACTIVATION_BLOCKED']),
        normalization_activation_count=len([i for i in items if i.activation_state == 'NORMALIZATION_BRIDGE_ACTIVATED']),
        watch_continuation_count=len([i for i in items if i.activation_state == 'NORMALIZATION_BRIDGE_CONTINUES_WATCH']),
        reopen_activation_count=len([i for i in items if i.activation_state == 'NORMALIZATION_BRIDGE_REOPEN_REQUIRED']),
        blocked_count=len([i for i in items if i.activation_state == 'NORMALIZATION_BRIDGE_ACTIVATION_BLOCKED']),
        summary_output_path=str(summary_output_path),
        markdown_output_path=str(markdown_output_path),
        items=items,
    )
    summary_output_path.write_text(json.dumps(report.to_payload(), indent=2) + '\n', encoding='utf-8')
    markdown_output_path.write_text(
        '\n'.join([
            '## Operator Normalization Bridge Activation',
            f"- Board label: `{report.board_label}`",
            f"- Activator label: `{report.activator_label}`",
            f"- Activated count: `{report.activated_count}`",
            f"- Normalization activation count: `{report.normalization_activation_count}`",
            f"- Watch continuation count: `{report.watch_continuation_count}`",
            *[f"- {i.work_item_key}: {i.activation_state} -> {i.next_queue_lane}" for i in report.items],
            '',
        ]),
        encoding='utf-8',
    )
    return report


__all__ = [
    'OracleOperatorNormalizationBridgeActivation',
    'OracleOperatorNormalizationBridgeActivationItem',
    'OracleOperatorNormalizationBridgeActivationRequest',
    'build_operator_normalization_bridge_activation_request',
    'materialize_operator_normalization_bridge_activation',
]
