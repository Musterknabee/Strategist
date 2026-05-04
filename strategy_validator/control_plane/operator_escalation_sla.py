from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from strategy_validator.control_plane.operator_escalation_packet import (
    OracleOperatorEscalationPacket,
    build_operator_escalation_packet_request,
    materialize_operator_escalation_packet,
)


@dataclass(frozen=True)
class OracleOperatorEscalationSLARequest:
    sla_root: Path
    board_label: str = 'default'
    evaluated_at_utc: datetime | None = None
    escalation_started_at_utc: datetime | None = None


@dataclass(frozen=True)
class OracleOperatorEscalationSLAItem:
    sla_key: str
    packet_key: str
    work_item_key: str
    escalation_lane: str
    escalation_class: str
    priority_band: str
    packet_status: str
    sla_policy: str
    sla_window_minutes: int
    sla_due_by_utc: str | None
    aging_status: str
    breach_posture: str
    review_urgency: str
    review_summary_line: str

    def to_payload(self) -> dict[str, Any]:
        return self.__dict__.copy()


@dataclass(frozen=True)
class OracleOperatorEscalationSLA:
    schema_version: str
    board_label: str
    sla_root: str
    evaluated_at_utc: str
    total_item_count: int
    escalated_item_count: int
    breached_item_count: int
    urgent_item_count: int
    summary_output_path: str
    markdown_output_path: str
    items: tuple[OracleOperatorEscalationSLAItem, ...]

    def to_payload(self) -> dict[str, Any]:
        return {
            'schema_version': self.schema_version,
            'board_label': self.board_label,
            'sla_root': self.sla_root,
            'evaluated_at_utc': self.evaluated_at_utc,
            'total_item_count': self.total_item_count,
            'escalated_item_count': self.escalated_item_count,
            'breached_item_count': self.breached_item_count,
            'urgent_item_count': self.urgent_item_count,
            'summary_output_path': self.summary_output_path,
            'markdown_output_path': self.markdown_output_path,
            'items': [item.to_payload() for item in self.items],
        }


def build_operator_escalation_sla_request(**kwargs: Any) -> OracleOperatorEscalationSLARequest:
    kwargs['sla_root'] = Path(kwargs['sla_root']).resolve()
    return OracleOperatorEscalationSLARequest(**kwargs)


def _normalize(dt: datetime | None) -> datetime:
    value = dt or datetime.now(tz=UTC).replace(microsecond=0)
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.astimezone(UTC).replace(microsecond=0)


def _sla_window_minutes(priority_band: str, escalation_class: str) -> int:
    if priority_band == 'CRITICAL_PRIORITY':
        base = 15
    elif priority_band == 'ELEVATED_PRIORITY':
        base = 60
    else:
        base = 240
    if escalation_class == 'CLAIM_OPERABILITY_ESCALATION':
        return min(base, 30)
    if escalation_class == 'DISPATCH_BLOCK_ESCALATION':
        return min(base, 45)
    return base


def _age_item(packet, evaluated_at_utc: datetime, escalation_started_at_utc: datetime) -> OracleOperatorEscalationSLAItem:
    if packet.packet_status != 'SUPERVISOR_REVIEW_REQUIRED':
        return OracleOperatorEscalationSLAItem(
            sla_key=f'sla:{packet.packet_key}',
            packet_key=packet.packet_key,
            work_item_key=packet.work_item_key,
            escalation_lane=packet.escalation_lane,
            escalation_class=packet.escalation_class,
            priority_band=packet.priority_band,
            packet_status=packet.packet_status,
            sla_policy='NO_ESCALATION_SLA',
            sla_window_minutes=0,
            sla_due_by_utc=None,
            aging_status='NO_SLA_REQUIRED',
            breach_posture='NO_BREACH',
            review_urgency='NONE',
            review_summary_line='No escalation SLA applies because supervisor review is not required.',
        )

    window_minutes = _sla_window_minutes(packet.priority_band, packet.escalation_class)
    due_by = escalation_started_at_utc + timedelta(minutes=window_minutes)
    remaining_minutes = int((due_by - evaluated_at_utc).total_seconds() // 60)
    aging_status = 'WITHIN_SLA'
    breach_posture = 'BREACH_NONE'
    review_urgency = 'ROUTINE'
    if remaining_minutes < 0:
        aging_status = 'BREACHED'
        breach_posture = 'BREACH_ACTIVE'
        review_urgency = 'IMMEDIATE'
    elif remaining_minutes <= 15:
        aging_status = 'DUE_SOON'
        breach_posture = 'BREACH_IMMINENT'
        review_urgency = 'URGENT'
    if packet.priority_band == 'CRITICAL_PRIORITY' or packet.escalation_class == 'CLAIM_OPERABILITY_ESCALATION':
        review_urgency = 'IMMEDIATE'
        if aging_status == 'WITHIN_SLA':
            aging_status = 'DUE_SOON'
            breach_posture = 'BREACH_IMMINENT'

    return OracleOperatorEscalationSLAItem(
        sla_key=f'sla:{packet.packet_key}',
        packet_key=packet.packet_key,
        work_item_key=packet.work_item_key,
        escalation_lane=packet.escalation_lane,
        escalation_class=packet.escalation_class,
        priority_band=packet.priority_band,
        packet_status=packet.packet_status,
        sla_policy='SUPERVISOR_ESCALATION_SLA',
        sla_window_minutes=window_minutes,
        sla_due_by_utc=due_by.isoformat(),
        aging_status=aging_status,
        breach_posture=breach_posture,
        review_urgency=review_urgency,
        review_summary_line=(
            f"Escalation packet {packet.packet_key} requires {review_urgency.lower()} supervisor review "
            f"via {packet.escalation_lane} before {due_by.isoformat()}."
        ),
    )


def materialize_operator_escalation_sla(
    request: OracleOperatorEscalationSLARequest,
    *,
    escalation_packet: OracleOperatorEscalationPacket | None = None,
    operator_queue_query_result=None,
    board_label: str = 'default',
) -> OracleOperatorEscalationSLA:
    if escalation_packet is None:
        escalation_packet = materialize_operator_escalation_packet(
            build_operator_escalation_packet_request(packet_root=request.sla_root / 'escalation_packet', board_label=board_label),
            operator_queue_query_result=operator_queue_query_result,
            board_label=board_label,
        )
    evaluated_at_utc = _normalize(request.evaluated_at_utc)
    escalation_started_at_utc = _normalize(request.escalation_started_at_utc or request.evaluated_at_utc)
    items = tuple(_age_item(item, evaluated_at_utc, escalation_started_at_utc) for item in escalation_packet.items)

    request.sla_root.mkdir(parents=True, exist_ok=True)
    summary_output_path = request.sla_root / 'ORACLE_OPERATOR_ESCALATION_SLA.json'
    markdown_output_path = request.sla_root / 'ORACLE_OPERATOR_ESCALATION_SLA.md'
    report = OracleOperatorEscalationSLA(
        schema_version='oracle_operator_escalation_sla/v1',
        board_label=escalation_packet.board_label,
        sla_root=str(request.sla_root),
        evaluated_at_utc=evaluated_at_utc.isoformat(),
        total_item_count=len(items),
        escalated_item_count=len([item for item in items if item.sla_policy == 'SUPERVISOR_ESCALATION_SLA']),
        breached_item_count=len([item for item in items if item.breach_posture == 'BREACH_ACTIVE']),
        urgent_item_count=len([item for item in items if item.review_urgency in {'URGENT', 'IMMEDIATE'}]),
        summary_output_path=str(summary_output_path),
        markdown_output_path=str(markdown_output_path),
        items=items,
    )
    summary_output_path.write_text(json.dumps(report.to_payload(), indent=2) + '\n', encoding='utf-8')
    markdown_output_path.write_text(
        '\n'.join([
            '## Operator Escalation SLA',
            f"- Board label: `{report.board_label}`",
            f"- Evaluated at: `{report.evaluated_at_utc}`",
            f"- Escalated items: `{report.escalated_item_count}` / `{report.total_item_count}`",
            f"- Urgent items: `{report.urgent_item_count}`",
            *[
                f"- {item.work_item_key}: {item.review_urgency} / {item.aging_status} (due `{item.sla_due_by_utc}`)"
                for item in report.items
            ],
            '',
        ]),
        encoding='utf-8',
    )
    return report


__all__ = [
    'OracleOperatorEscalationSLA',
    'OracleOperatorEscalationSLAItem',
    'OracleOperatorEscalationSLARequest',
    'build_operator_escalation_sla_request',
    'materialize_operator_escalation_sla',
]
