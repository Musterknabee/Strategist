from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from strategy_validator.control_plane.operator_escalation_packet import (
    OracleOperatorEscalationPacket,
    build_operator_escalation_packet_request,
    materialize_operator_escalation_packet,
)
from strategy_validator.control_plane.operator_escalation_sla import (
    OracleOperatorEscalationSLA,
    build_operator_escalation_sla_request,
    materialize_operator_escalation_sla,
)


@dataclass(frozen=True)
class OracleOperatorSupervisorReviewRequest:
    review_root: Path
    board_label: str = 'default'
    supervisor_actor_label: str = 'supervisor'
    note: str = ''
    reviewed_at_utc: datetime | None = None


@dataclass(frozen=True)
class OracleOperatorSupervisorReviewItem:
    review_key: str
    packet_key: str
    work_item_key: str
    escalation_lane: str
    escalation_class: str
    review_urgency: str
    aging_status: str
    supervisor_disposition: str
    disposition_reason_code: str
    review_status: str
    closure_recommendation: str
    supervisor_actor_label: str
    note: str
    reviewed_at_utc: str

    def to_payload(self) -> dict[str, Any]:
        return self.__dict__.copy()


@dataclass(frozen=True)
class OracleOperatorSupervisorReview:
    schema_version: str
    board_label: str
    review_root: str
    total_review_count: int
    resolved_count: int
    requeue_count: int
    open_count: int
    summary_output_path: str
    markdown_output_path: str
    items: tuple[OracleOperatorSupervisorReviewItem, ...]

    def to_payload(self) -> dict[str, Any]:
        return {
            'schema_version': self.schema_version,
            'board_label': self.board_label,
            'review_root': self.review_root,
            'total_review_count': self.total_review_count,
            'resolved_count': self.resolved_count,
            'requeue_count': self.requeue_count,
            'open_count': self.open_count,
            'summary_output_path': self.summary_output_path,
            'markdown_output_path': self.markdown_output_path,
            'items': [item.to_payload() for item in self.items],
        }


def build_operator_supervisor_review_request(**kwargs: Any) -> OracleOperatorSupervisorReviewRequest:
    kwargs['review_root'] = Path(kwargs['review_root']).resolve()
    return OracleOperatorSupervisorReviewRequest(**kwargs)


def _normalize(ts: datetime | None) -> datetime:
    if ts is None:
        return datetime.now(tz=UTC).replace(microsecond=0)
    if ts.tzinfo is None:
        return ts.replace(tzinfo=UTC)
    return ts.astimezone(UTC).replace(microsecond=0)


def _review_item(packet, sla_item, request: OracleOperatorSupervisorReviewRequest, reviewed_at_utc: datetime) -> OracleOperatorSupervisorReviewItem:
    if sla_item.breach_posture == 'BREACH_ACTIVE' or sla_item.review_urgency == 'IMMEDIATE':
        disposition = 'REQUEUE_WITH_REMEDIATION'
        reason_code = 'ESCALATION_SLA_BREACH'
        review_status = 'SUPERVISOR_ACTIONED'
        closure_recommendation = 'RETURN_TO_OPERATOR'
    elif packet.escalation_class == 'CLAIM_OPERABILITY_ESCALATION':
        disposition = 'REQUEUE_WITH_REMEDIATION'
        reason_code = 'CLAIM_REPAIR_REQUIRED'
        review_status = 'SUPERVISOR_ACTIONED'
        closure_recommendation = 'RETURN_TO_OPERATOR'
    elif packet.escalation_class == 'DISPATCH_BLOCK_ESCALATION':
        disposition = 'REQUEUE_WITH_REMEDIATION'
        reason_code = 'DISPATCH_REMEDIATION_REQUIRED'
        review_status = 'SUPERVISOR_ACTIONED'
        closure_recommendation = 'RETURN_TO_OPERATOR'
    elif sla_item.aging_status == 'DUE_SOON':
        disposition = 'HOLD_OPEN'
        reason_code = 'SUPERVISOR_REVIEW_PENDING'
        review_status = 'SUPERVISOR_PENDING'
        closure_recommendation = 'KEEP_ESCALATED'
    else:
        disposition = 'APPROVE_EXCEPTION_PATH'
        reason_code = 'SUPERVISOR_OVERRIDE_APPROVED'
        review_status = 'SUPERVISOR_ACTIONED'
        closure_recommendation = 'RESOLVE_ESCALATION'

    return OracleOperatorSupervisorReviewItem(
        review_key=f'review:{packet.packet_key}',
        packet_key=packet.packet_key,
        work_item_key=packet.work_item_key,
        escalation_lane=packet.escalation_lane,
        escalation_class=packet.escalation_class,
        review_urgency=sla_item.review_urgency,
        aging_status=sla_item.aging_status,
        supervisor_disposition=disposition,
        disposition_reason_code=reason_code,
        review_status=review_status,
        closure_recommendation=closure_recommendation,
        supervisor_actor_label=request.supervisor_actor_label,
        note=request.note,
        reviewed_at_utc=reviewed_at_utc.isoformat(),
    )


def materialize_operator_supervisor_review(
    request: OracleOperatorSupervisorReviewRequest,
    *,
    escalation_packet: OracleOperatorEscalationPacket | None = None,
    escalation_sla: OracleOperatorEscalationSLA | None = None,
    operator_queue_query_result=None,
    board_label: str = 'default',
) -> OracleOperatorSupervisorReview:
    if escalation_packet is None:
        escalation_packet = materialize_operator_escalation_packet(
            build_operator_escalation_packet_request(packet_root=request.review_root / 'escalation_packet', board_label=board_label),
            operator_queue_query_result=operator_queue_query_result,
            board_label=board_label,
        )
    if escalation_sla is None:
        escalation_sla = materialize_operator_escalation_sla(
            build_operator_escalation_sla_request(sla_root=request.review_root / 'escalation_sla', board_label=board_label),
            escalation_packet=escalation_packet,
            board_label=board_label,
        )
    reviewed_at_utc = _normalize(request.reviewed_at_utc)
    sla_by_work_item = {item.work_item_key: item for item in escalation_sla.items}
    items = tuple(_review_item(packet, sla_by_work_item[packet.work_item_key], request, reviewed_at_utc) for packet in escalation_packet.items)

    request.review_root.mkdir(parents=True, exist_ok=True)
    summary_output_path = request.review_root / 'ORACLE_OPERATOR_SUPERVISOR_REVIEW.json'
    markdown_output_path = request.review_root / 'ORACLE_OPERATOR_SUPERVISOR_REVIEW.md'
    report = OracleOperatorSupervisorReview(
        schema_version='oracle_operator_supervisor_review/v1',
        board_label=escalation_packet.board_label,
        review_root=str(request.review_root),
        total_review_count=len(items),
        resolved_count=len([item for item in items if item.closure_recommendation == 'RESOLVE_ESCALATION']),
        requeue_count=len([item for item in items if item.closure_recommendation == 'RETURN_TO_OPERATOR']),
        open_count=len([item for item in items if item.closure_recommendation == 'KEEP_ESCALATED']),
        summary_output_path=str(summary_output_path),
        markdown_output_path=str(markdown_output_path),
        items=items,
    )
    summary_output_path.write_text(json.dumps(report.to_payload(), indent=2) + '\n', encoding='utf-8')
    markdown_output_path.write_text(
        '\n'.join([
            '## Operator Supervisor Review',
            f"- Board label: `{report.board_label}`",
            f"- Review count: `{report.total_review_count}`",
            f"- Resolved: `{report.resolved_count}`",
            f"- Requeued: `{report.requeue_count}`",
            f"- Open: `{report.open_count}`",
            *[
                f"- {item.work_item_key}: {item.supervisor_disposition} -> {item.closure_recommendation}"
                for item in report.items
            ],
            '',
        ]),
        encoding='utf-8',
    )
    return report


__all__ = [
    'OracleOperatorSupervisorReview',
    'OracleOperatorSupervisorReviewItem',
    'OracleOperatorSupervisorReviewRequest',
    'build_operator_supervisor_review_request',
    'materialize_operator_supervisor_review',
]
