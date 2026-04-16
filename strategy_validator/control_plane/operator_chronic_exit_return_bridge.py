from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from strategy_validator.control_plane.operator_chronic_exit_certification import (
    OracleOperatorChronicExitCertification,
    build_operator_chronic_exit_certification_request,
    materialize_operator_chronic_exit_certification,
)


@dataclass(frozen=True)
class OracleOperatorChronicExitReturnBridgeRequest:
    bridge_root: Path
    board_label: str = 'default'
    bridge_label: str = 'chronic-exit-return-bridge'
    bridged_at_utc: datetime | None = None


@dataclass(frozen=True)
class OracleOperatorChronicExitReturnBridgeItem:
    bridge_key: str
    certification_key: str
    attestation_key: str
    work_item_key: str
    recurrence_class: str
    chronic_instability_class: str
    certification_state: str
    return_path_state: str
    bridge_state: str
    bridge_reason_code: str
    bridge_authorized: bool
    target_return_lane: str
    monitoring_profile: str
    bridge_label: str
    bridged_at_utc: str

    def to_payload(self) -> dict[str, Any]:
        return self.__dict__.copy()


@dataclass(frozen=True)
class OracleOperatorChronicExitReturnBridge:
    schema_version: str
    board_label: str
    bridge_root: str
    bridge_label: str
    bridged_at_utc: str
    bridge_count: int
    authorized_bridge_count: int
    monitored_bridge_count: int
    held_bridge_count: int
    summary_output_path: str
    markdown_output_path: str
    items: tuple[OracleOperatorChronicExitReturnBridgeItem, ...]

    def to_payload(self) -> dict[str, Any]:
        return {
            'schema_version': self.schema_version,
            'board_label': self.board_label,
            'bridge_root': self.bridge_root,
            'bridge_label': self.bridge_label,
            'bridged_at_utc': self.bridged_at_utc,
            'bridge_count': self.bridge_count,
            'authorized_bridge_count': self.authorized_bridge_count,
            'monitored_bridge_count': self.monitored_bridge_count,
            'held_bridge_count': self.held_bridge_count,
            'summary_output_path': self.summary_output_path,
            'markdown_output_path': self.markdown_output_path,
            'items': [i.to_payload() for i in self.items],
        }


def build_operator_chronic_exit_return_bridge_request(**kwargs: Any) -> OracleOperatorChronicExitReturnBridgeRequest:
    kwargs['bridge_root'] = Path(kwargs['bridge_root']).resolve()
    return OracleOperatorChronicExitReturnBridgeRequest(**kwargs)


def _normalize(ts: datetime | None) -> datetime:
    if ts is None:
        return datetime.now(tz=UTC).replace(microsecond=0)
    if ts.tzinfo is None:
        return ts.replace(tzinfo=UTC)
    return ts.astimezone(UTC).replace(microsecond=0)


def _derive_item(item: Any, request: OracleOperatorChronicExitReturnBridgeRequest, bridged_at_utc: datetime) -> OracleOperatorChronicExitReturnBridgeItem:
    bridge_state = 'CHRONIC_EXIT_BRIDGE_HELD'
    reason = 'CHRONIC_EXIT_NOT_CERTIFIED_FOR_RETURN_PATH'
    bridge_authorized = False
    target_lane = 'CHRONIC_REMEDIATION_QUEUE'
    monitoring_profile = 'REJOIN_BLOCKED'
    if item.chronic_exit_certified and 'WITH_MONITORING' in item.certification_state:
        bridge_state = 'CHRONIC_EXIT_BRIDGED_WITH_MONITORED_REJOIN'
        reason = 'CHRONIC_EXIT_CERTIFIED_WITH_MONITORED_REJOIN'
        bridge_authorized = True
        target_lane = 'SUPERVISOR_MONITORED_RETURN_QUEUE'
        monitoring_profile = 'HEIGHTENED_MONITORED_REJOIN'
    elif item.chronic_exit_certified:
        bridge_state = 'CHRONIC_EXIT_BRIDGED_TO_RETURN_AUTHORIZATION'
        reason = 'CHRONIC_EXIT_CERTIFIED_FOR_STANDARD_REJOIN'
        bridge_authorized = True
        target_lane = 'RETURN_AUTHORIZATION_REENTRY_QUEUE'
        monitoring_profile = 'STANDARD_REJOIN_GUARDRAILS'
    return OracleOperatorChronicExitReturnBridgeItem(
        bridge_key=f'chronic_exit_return_bridge:{item.certification_key}',
        certification_key=item.certification_key,
        attestation_key=item.attestation_key,
        work_item_key=item.work_item_key,
        recurrence_class=item.recurrence_class,
        chronic_instability_class=item.chronic_instability_class,
        certification_state=item.certification_state,
        return_path_state=item.return_path_state,
        bridge_state=bridge_state,
        bridge_reason_code=reason,
        bridge_authorized=bridge_authorized,
        target_return_lane=target_lane,
        monitoring_profile=monitoring_profile,
        bridge_label=request.bridge_label,
        bridged_at_utc=bridged_at_utc.isoformat(),
    )


def materialize_operator_chronic_exit_return_bridge(
    request: OracleOperatorChronicExitReturnBridgeRequest,
    *,
    chronic_exit_certification: OracleOperatorChronicExitCertification | None = None,
    operator_queue_query_result=None,
    board_label: str = 'default',
) -> OracleOperatorChronicExitReturnBridge:
    if chronic_exit_certification is None:
        chronic_exit_certification = materialize_operator_chronic_exit_certification(
            build_operator_chronic_exit_certification_request(
                certification_root=request.bridge_root / 'chronic_exit_certification',
                board_label=board_label,
                certified_at_utc=request.bridged_at_utc,
            ),
            operator_queue_query_result=operator_queue_query_result,
            board_label=board_label,
        )
    bridged_at_utc = _normalize(request.bridged_at_utc)
    items = tuple(_derive_item(item, request, bridged_at_utc) for item in chronic_exit_certification.items)
    request.bridge_root.mkdir(parents=True, exist_ok=True)
    summary_output_path = request.bridge_root / 'ORACLE_OPERATOR_CHRONIC_EXIT_RETURN_BRIDGE.json'
    markdown_output_path = request.bridge_root / 'ORACLE_OPERATOR_CHRONIC_EXIT_RETURN_BRIDGE.md'
    report = OracleOperatorChronicExitReturnBridge(
        schema_version='oracle_operator_chronic_exit_return_bridge/v1',
        board_label=chronic_exit_certification.board_label,
        bridge_root=str(request.bridge_root),
        bridge_label=request.bridge_label,
        bridged_at_utc=bridged_at_utc.isoformat(),
        bridge_count=len(items),
        authorized_bridge_count=len([i for i in items if i.bridge_authorized]),
        monitored_bridge_count=len([i for i in items if 'MONITORED' in i.bridge_state]),
        held_bridge_count=len([i for i in items if not i.bridge_authorized]),
        summary_output_path=str(summary_output_path),
        markdown_output_path=str(markdown_output_path),
        items=items,
    )
    summary_output_path.write_text(json.dumps(report.to_payload(), indent=2) + "\n", encoding='utf-8')
    markdown_output_path.write_text("\n".join([
        '## Operator Chronic Exit Return Bridge',
        f"- Board label: `{report.board_label}`",
        f"- Bridge label: `{report.bridge_label}`",
        f"- Authorized bridges: `{report.authorized_bridge_count}`",
        f"- Monitored bridges: `{report.monitored_bridge_count}`",
        f"- Held bridges: `{report.held_bridge_count}`",
        *[f"- {item.work_item_key}: {item.bridge_state} -> {item.target_return_lane}" for item in report.items],
        '',
    ]), encoding='utf-8')
    return report


__all__ = [
    'OracleOperatorChronicExitReturnBridge',
    'OracleOperatorChronicExitReturnBridgeItem',
    'OracleOperatorChronicExitReturnBridgeRequest',
    'build_operator_chronic_exit_return_bridge_request',
    'materialize_operator_chronic_exit_return_bridge',
]
