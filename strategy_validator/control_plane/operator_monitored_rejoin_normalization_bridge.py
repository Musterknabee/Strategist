from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from strategy_validator.control_plane.materialization import write_json_markdown_artifacts

from strategy_validator.control_plane.operator_chronic_watch_outcome import (
    OracleOperatorChronicWatchOutcome,
    build_operator_chronic_watch_outcome_request,
    materialize_operator_chronic_watch_outcome,
)


@dataclass(frozen=True)
class OracleOperatorMonitoredRejoinNormalizationBridgeRequest:
    bridge_root: Path
    board_label: str = 'default'
    bridge_label: str = 'monitored-rejoin-normalization-bridge'
    bridged_at_utc: datetime | None = None


@dataclass(frozen=True)
class OracleOperatorMonitoredRejoinNormalizationBridgeItem:
    bridge_key: str
    outcome_key: str
    handoff_key: str
    activation_key: str
    work_item_key: str
    outcome_state: str
    normalization_eligible: bool
    reopen_required: bool
    bridge_state: str
    bridge_reason_code: str
    return_monitoring_target: str
    restoration_audit_target: str
    next_queue_lane: str
    bridge_label: str
    bridged_at_utc: str

    def to_payload(self) -> dict[str, Any]:
        return self.__dict__.copy()


@dataclass(frozen=True)
class OracleOperatorMonitoredRejoinNormalizationBridge:
    schema_version: str
    board_label: str
    bridge_root: str
    bridge_label: str
    bridged_at_utc: str
    bridge_count: int
    normalization_bridge_count: int
    watch_continuation_count: int
    reopen_bridge_count: int
    blocked_bridge_count: int
    summary_output_path: str
    markdown_output_path: str
    items: tuple[OracleOperatorMonitoredRejoinNormalizationBridgeItem, ...]

    def to_payload(self) -> dict[str, Any]:
        return {
            'schema_version': self.schema_version,
            'board_label': self.board_label,
            'bridge_root': self.bridge_root,
            'bridge_label': self.bridge_label,
            'bridged_at_utc': self.bridged_at_utc,
            'bridge_count': self.bridge_count,
            'normalization_bridge_count': self.normalization_bridge_count,
            'watch_continuation_count': self.watch_continuation_count,
            'reopen_bridge_count': self.reopen_bridge_count,
            'blocked_bridge_count': self.blocked_bridge_count,
            'summary_output_path': self.summary_output_path,
            'markdown_output_path': self.markdown_output_path,
            'items': [item.to_payload() for item in self.items],
        }


def build_operator_monitored_rejoin_normalization_bridge_request(**kwargs: Any) -> OracleOperatorMonitoredRejoinNormalizationBridgeRequest:
    kwargs['bridge_root'] = Path(kwargs['bridge_root']).resolve()
    return OracleOperatorMonitoredRejoinNormalizationBridgeRequest(**kwargs)


def _normalize(ts: datetime | None) -> datetime:
    if ts is None:
        return datetime.now(tz=UTC).replace(microsecond=0)
    if ts.tzinfo is None:
        return ts.replace(tzinfo=UTC)
    return ts.astimezone(UTC).replace(microsecond=0)


def _derive_item(item: Any, request: OracleOperatorMonitoredRejoinNormalizationBridgeRequest, bridged_at_utc: datetime) -> OracleOperatorMonitoredRejoinNormalizationBridgeItem:
    if item.normalization_eligible:
        state = 'MONITORED_REJOIN_BRIDGED_TO_NORMALIZATION'
        reason = 'CHRONIC_MONITORED_REJOIN_STAYED_STABLE_AND_CAN_REJOIN_NORMALIZATION_PATH'
        return_target = 'operator_return_monitoring'
        restoration_target = 'operator_restoration_audit'
        next_lane = 'RETURN_NORMALIZATION_BRIDGE'
    elif item.reopen_required:
        state = 'MONITORED_REJOIN_REOPEN_REQUIRED'
        reason = 'CHRONIC_MONITORED_REJOIN_BREACHED_AND_MUST_REOPEN_REMEDIATION'
        return_target = 'operator_return_reopen_loop'
        restoration_target = 'operator_reentry_queue_state'
        next_lane = 'REENTRY_QUEUE'
    elif item.outcome_state == 'CHRONIC_WATCH_UNDER_OBSERVATION':
        state = 'MONITORED_REJOIN_WATCH_CONTINUES'
        reason = 'CHRONIC_MONITORED_REJOIN_STILL_WITHIN_OBSERVATION_WINDOW'
        return_target = 'operator_return_monitoring'
        restoration_target = 'operator_restoration_audit'
        next_lane = 'SUPERVISOR_MONITORED_RETURN_QUEUE'
    else:
        state = 'MONITORED_REJOIN_NORMALIZATION_BLOCKED'
        reason = 'CHRONIC_MONITORED_REJOIN_DID_NOT_REACH_NORMALIZATION_BRIDGE'
        return_target = 'blocked'
        restoration_target = 'blocked'
        next_lane = 'CHRONIC_REMEDIATION_QUEUE'

    return OracleOperatorMonitoredRejoinNormalizationBridgeItem(
        bridge_key=f'monitored_rejoin_normalization_bridge:{item.outcome_key}',
        outcome_key=item.outcome_key,
        handoff_key=item.handoff_key,
        activation_key=item.activation_key,
        work_item_key=item.work_item_key,
        outcome_state=item.outcome_state,
        normalization_eligible=item.normalization_eligible,
        reopen_required=item.reopen_required,
        bridge_state=state,
        bridge_reason_code=reason,
        return_monitoring_target=return_target,
        restoration_audit_target=restoration_target,
        next_queue_lane=next_lane,
        bridge_label=request.bridge_label,
        bridged_at_utc=bridged_at_utc.isoformat(),
    )


def materialize_operator_monitored_rejoin_normalization_bridge(
    request: OracleOperatorMonitoredRejoinNormalizationBridgeRequest,
    *,
    chronic_watch_outcome: OracleOperatorChronicWatchOutcome | None = None,
    operator_queue_query_result=None,
    board_label: str = 'default',
) -> OracleOperatorMonitoredRejoinNormalizationBridge:
    if chronic_watch_outcome is None:
        chronic_watch_outcome = materialize_operator_chronic_watch_outcome(
            build_operator_chronic_watch_outcome_request(
                outcome_root=request.bridge_root / 'chronic_watch_outcome',
                board_label=board_label,
                evaluator_label=request.bridge_label,
                evaluated_at_utc=request.bridged_at_utc,
            ),
            operator_queue_query_result=operator_queue_query_result,
            board_label=board_label,
        )
    bridged_at_utc = _normalize(request.bridged_at_utc)
    items = tuple(_derive_item(item, request, bridged_at_utc) for item in chronic_watch_outcome.items)
    request.bridge_root.mkdir(parents=True, exist_ok=True)
    summary_output_path = request.bridge_root / 'ORACLE_OPERATOR_MONITORED_REJOIN_NORMALIZATION_BRIDGE.json'
    markdown_output_path = request.bridge_root / 'ORACLE_OPERATOR_MONITORED_REJOIN_NORMALIZATION_BRIDGE.md'
    report = OracleOperatorMonitoredRejoinNormalizationBridge(
        schema_version='oracle_operator_monitored_rejoin_normalization_bridge/v1',
        board_label=chronic_watch_outcome.board_label,
        bridge_root=str(request.bridge_root),
        bridge_label=request.bridge_label,
        bridged_at_utc=bridged_at_utc.isoformat(),
        bridge_count=len(items),
        normalization_bridge_count=len([item for item in items if item.bridge_state == 'MONITORED_REJOIN_BRIDGED_TO_NORMALIZATION']),
        watch_continuation_count=len([item for item in items if item.bridge_state == 'MONITORED_REJOIN_WATCH_CONTINUES']),
        reopen_bridge_count=len([item for item in items if item.bridge_state == 'MONITORED_REJOIN_REOPEN_REQUIRED']),
        blocked_bridge_count=len([item for item in items if item.bridge_state == 'MONITORED_REJOIN_NORMALIZATION_BLOCKED']),
        summary_output_path=str(summary_output_path),
        markdown_output_path=str(markdown_output_path),
        items=items,
    )
    write_json_markdown_artifacts(
        summary_output_path=summary_output_path,
        markdown_output_path=markdown_output_path,
        payload=report.to_payload(),
        markdown=[
        '## Operator Monitored Rejoin Normalization Bridge',
        f"- Board label: `{report.board_label}`",
        f"- Bridge label: `{report.bridge_label}`",
        f"- Normalization bridge count: `{report.normalization_bridge_count}`",
        f"- Watch continuation count: `{report.watch_continuation_count}`",
        f"- Reopen bridge count: `{report.reopen_bridge_count}`",
        *[f"- {item.work_item_key}: {item.bridge_state} -> {item.next_queue_lane}" for item in report.items],
        '',
    ],
    )
    return report


__all__ = [
    'OracleOperatorMonitoredRejoinNormalizationBridge',
    'OracleOperatorMonitoredRejoinNormalizationBridgeItem',
    'OracleOperatorMonitoredRejoinNormalizationBridgeRequest',
    'build_operator_monitored_rejoin_normalization_bridge_request',
    'materialize_operator_monitored_rejoin_normalization_bridge',
]
