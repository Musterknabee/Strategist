from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from strategy_validator.control_plane.operator_chronic_instability_packet import (
    OracleOperatorChronicInstabilityPacket,
    build_operator_chronic_instability_packet_request,
    materialize_operator_chronic_instability_packet,
)


@dataclass(frozen=True)
class OracleOperatorRecurrenceTribunalLaneRequest:
    tribunal_root: Path
    board_label: str = 'default'
    reviewer_label: str = 'recurrence-tribunal'
    reviewed_at_utc: datetime | None = None


@dataclass(frozen=True)
class OracleOperatorRecurrenceTribunalLaneItem:
    tribunal_key: str
    packet_key: str
    policy_key: str
    work_item_key: str
    recurrence_class: str
    chronic_instability_class: str
    tribunal_lane: str
    tribunal_destination: str
    tribunal_state: str
    review_authority: str
    remediation_directive: str
    tribunal_reason_code: str
    reviewed_at_utc: str

    def to_payload(self) -> dict[str, Any]:
        return self.__dict__.copy()


@dataclass(frozen=True)
class OracleOperatorRecurrenceTribunalLane:
    schema_version: str
    board_label: str
    tribunal_root: str
    reviewer_label: str
    reviewed_at_utc: str
    item_count: int
    tribunal_review_required_count: int
    chronic_lane_count: int
    summary_output_path: str
    markdown_output_path: str
    items: tuple[OracleOperatorRecurrenceTribunalLaneItem, ...]

    def to_payload(self) -> dict[str, Any]:
        return {
            'schema_version': self.schema_version,
            'board_label': self.board_label,
            'tribunal_root': self.tribunal_root,
            'reviewer_label': self.reviewer_label,
            'reviewed_at_utc': self.reviewed_at_utc,
            'item_count': self.item_count,
            'tribunal_review_required_count': self.tribunal_review_required_count,
            'chronic_lane_count': self.chronic_lane_count,
            'summary_output_path': self.summary_output_path,
            'markdown_output_path': self.markdown_output_path,
            'items': [i.to_payload() for i in self.items],
        }


def build_operator_recurrence_tribunal_lane_request(**kwargs: Any) -> OracleOperatorRecurrenceTribunalLaneRequest:
    kwargs['tribunal_root'] = Path(kwargs['tribunal_root']).resolve()
    return OracleOperatorRecurrenceTribunalLaneRequest(**kwargs)


def _normalize(ts: datetime | None) -> datetime:
    if ts is None:
        return datetime.now(tz=UTC).replace(microsecond=0)
    if ts.tzinfo is None:
        return ts.replace(tzinfo=UTC)
    return ts.astimezone(UTC).replace(microsecond=0)


def _derive_item(item: Any, request: OracleOperatorRecurrenceTribunalLaneRequest, reviewed_at_utc: datetime) -> OracleOperatorRecurrenceTribunalLaneItem:
    tribunal_state = 'SUPERVISOR_RECURRENCE_REVIEW_REQUIRED'
    review_authority = 'SUPERVISOR'
    directive = 'Capture supervisor recurrence disposition and strengthened remediation checkpoints.'
    destination = 'SUPERVISOR_REVIEW_QUEUE'
    reason = 'RECURRENT_REOPEN_REQUIRES_SUPERVISOR_REVIEW'
    if item.chronic_instability_class == 'CHRONIC_INSTABILITY':
        tribunal_state = 'RECURRENCE_TRIBUNAL_REVIEW_REQUIRED'
        review_authority = 'TRIBUNAL'
        directive = 'Conduct tribunal-grade recurrence review, freeze return activation, and define exit criteria.'
        destination = 'RECURRENCE_TRIBUNAL_QUEUE'
        reason = 'CHRONIC_REOPEN_REQUIRES_TRIBUNAL_REVIEW'
    return OracleOperatorRecurrenceTribunalLaneItem(
        tribunal_key=f'tribunal:{item.packet_key}',
        packet_key=item.packet_key,
        policy_key=item.policy_key,
        work_item_key=item.work_item_key,
        recurrence_class=item.recurrence_class,
        chronic_instability_class=item.chronic_instability_class,
        tribunal_lane=item.tribunal_lane,
        tribunal_destination=destination,
        tribunal_state=tribunal_state,
        review_authority=review_authority,
        remediation_directive=directive,
        tribunal_reason_code=reason,
        reviewed_at_utc=reviewed_at_utc.isoformat(),
    )


def materialize_operator_recurrence_tribunal_lane(
    request: OracleOperatorRecurrenceTribunalLaneRequest,
    *,
    chronic_instability_packet: OracleOperatorChronicInstabilityPacket | None = None,
    operator_queue_query_result=None,
    board_label: str = 'default',
) -> OracleOperatorRecurrenceTribunalLane:
    if chronic_instability_packet is None:
        chronic_instability_packet = materialize_operator_chronic_instability_packet(
            build_operator_chronic_instability_packet_request(
                packet_root=request.tribunal_root / 'chronic_instability_packet',
                board_label=board_label,
                evaluator_label=request.reviewer_label,
                emitted_at_utc=request.reviewed_at_utc,
            ),
            operator_queue_query_result=operator_queue_query_result,
            board_label=board_label,
        )
    reviewed_at_utc = _normalize(request.reviewed_at_utc)
    items = tuple(_derive_item(item, request, reviewed_at_utc) for item in chronic_instability_packet.items)
    request.tribunal_root.mkdir(parents=True, exist_ok=True)
    summary_output_path = request.tribunal_root / 'ORACLE_OPERATOR_RECURRENCE_TRIBUNAL_LANE.json'
    markdown_output_path = request.tribunal_root / 'ORACLE_OPERATOR_RECURRENCE_TRIBUNAL_LANE.md'
    report = OracleOperatorRecurrenceTribunalLane(
        schema_version='oracle_operator_recurrence_tribunal_lane/v1',
        board_label=chronic_instability_packet.board_label,
        tribunal_root=str(request.tribunal_root),
        reviewer_label=request.reviewer_label,
        reviewed_at_utc=reviewed_at_utc.isoformat(),
        item_count=len(items),
        tribunal_review_required_count=len(items),
        chronic_lane_count=len([i for i in items if i.review_authority == 'TRIBUNAL']),
        summary_output_path=str(summary_output_path),
        markdown_output_path=str(markdown_output_path),
        items=items,
    )
    summary_output_path.write_text(json.dumps(report.to_payload(), indent=2) + '\n', encoding='utf-8')
    markdown_output_path.write_text('\n'.join([
        '## Operator Recurrence Tribunal Lane',
        f"- Board label: `{report.board_label}`",
        f"- Tribunal review required: `{report.tribunal_review_required_count}`",
        f"- Chronic tribunal count: `{report.chronic_lane_count}`",
        *[f"- {item.work_item_key}: {item.tribunal_state} -> {item.tribunal_destination}" for item in report.items],
        '',
    ]), encoding='utf-8')
    return report


__all__ = [
    'OracleOperatorRecurrenceTribunalLane',
    'OracleOperatorRecurrenceTribunalLaneItem',
    'OracleOperatorRecurrenceTribunalLaneRequest',
    'build_operator_recurrence_tribunal_lane_request',
    'materialize_operator_recurrence_tribunal_lane',
]
