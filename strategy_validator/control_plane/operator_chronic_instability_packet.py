from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from strategy_validator.control_plane.materialization import write_json_markdown_artifacts

from strategy_validator.control_plane.operator_reopen_recurrence_policy import (
    OracleOperatorReopenRecurrencePolicy,
    build_operator_reopen_recurrence_policy_request,
    materialize_operator_reopen_recurrence_policy,
)


@dataclass(frozen=True)
class OracleOperatorChronicInstabilityPacketRequest:
    packet_root: Path
    board_label: str = 'default'
    evaluator_label: str = 'chronic-instability-packet'
    emitted_at_utc: datetime | None = None


@dataclass(frozen=True)
class OracleOperatorChronicInstabilityPacketItem:
    packet_key: str
    policy_key: str
    lineage_key: str
    work_item_key: str
    recurrence_class: str
    recurrence_policy_state: str
    chronic_instability_class: str
    tribunal_lane: str
    escalation_destination: str
    remediation_obligation: str
    recurrence_reason_code: str
    review_checklist: tuple[str, ...]
    packet_status: str
    evaluator_label: str
    emitted_at_utc: str

    def to_payload(self) -> dict[str, Any]:
        payload = self.__dict__.copy()
        payload['review_checklist'] = list(self.review_checklist)
        return payload


@dataclass(frozen=True)
class OracleOperatorChronicInstabilityPacket:
    schema_version: str
    board_label: str
    packet_root: str
    evaluator_label: str
    emitted_at_utc: str
    packet_count: int
    escalation_required_count: int
    chronic_packet_count: int
    summary_output_path: str
    markdown_output_path: str
    items: tuple[OracleOperatorChronicInstabilityPacketItem, ...]

    def to_payload(self) -> dict[str, Any]:
        return {
            'schema_version': self.schema_version,
            'board_label': self.board_label,
            'packet_root': self.packet_root,
            'evaluator_label': self.evaluator_label,
            'emitted_at_utc': self.emitted_at_utc,
            'packet_count': self.packet_count,
            'escalation_required_count': self.escalation_required_count,
            'chronic_packet_count': self.chronic_packet_count,
            'summary_output_path': self.summary_output_path,
            'markdown_output_path': self.markdown_output_path,
            'items': [item.to_payload() for item in self.items],
        }


def build_operator_chronic_instability_packet_request(**kwargs: Any) -> OracleOperatorChronicInstabilityPacketRequest:
    kwargs['packet_root'] = Path(kwargs['packet_root']).resolve()
    return OracleOperatorChronicInstabilityPacketRequest(**kwargs)


def _normalize(ts: datetime | None) -> datetime:
    if ts is None:
        return datetime.now(tz=UTC).replace(microsecond=0)
    if ts.tzinfo is None:
        return ts.replace(tzinfo=UTC)
    return ts.astimezone(UTC).replace(microsecond=0)


def _checklist(item: Any, instability_class: str) -> tuple[str, ...]:
    steps = [
        f'Validate recurrence policy state `{item.recurrence_policy_state}` against reopen lineage before disposition.',
        f'Confirm escalation destination `{item.recommended_queue_lane}` is staffed for recurrence handling.',
    ]
    if instability_class == 'CHRONIC_INSTABILITY':
        steps.append('Produce a recurrence tribunal memo with root-cause, prior reopen history, and exit criteria.')
    else:
        steps.append('Attach a targeted remediation directive and explicit recurrence watch window before return.')
    return tuple(steps)


def _derive_item(item: Any, request: OracleOperatorChronicInstabilityPacketRequest, emitted_at_utc: datetime) -> OracleOperatorChronicInstabilityPacketItem:
    instability_class = 'CHRONIC_INSTABILITY' if item.recurrence_class == 'CHRONIC_REOPEN' else 'RECURRENT_INSTABILITY'
    tribunal_lane = 'RECURRENCE_TRIBUNAL_LANE' if instability_class == 'CHRONIC_INSTABILITY' else 'SUPERVISOR_RECURRENCE_LANE'
    destination = 'RECURRENCE_TRIBUNAL_QUEUE' if instability_class == 'CHRONIC_INSTABILITY' else 'SUPERVISOR_REVIEW_QUEUE'
    obligation = 'Record tribunal-grade recurrence remediation plan before any return activation.'
    if instability_class != 'CHRONIC_INSTABILITY':
        obligation = 'Record supervisor recurrence directive and strengthened post-return watch before release.'
    return OracleOperatorChronicInstabilityPacketItem(
        packet_key=f'chronic_packet:{item.policy_key}',
        policy_key=item.policy_key,
        lineage_key=item.lineage_key,
        work_item_key=item.work_item_key,
        recurrence_class=item.recurrence_class,
        recurrence_policy_state=item.recurrence_policy_state,
        chronic_instability_class=instability_class,
        tribunal_lane=tribunal_lane,
        escalation_destination=destination,
        remediation_obligation=obligation,
        recurrence_reason_code=item.policy_reason_code,
        review_checklist=_checklist(item, instability_class),
        packet_status='RECURRENCE_REVIEW_REQUIRED',
        evaluator_label=request.evaluator_label,
        emitted_at_utc=emitted_at_utc.isoformat(),
    )


def materialize_operator_chronic_instability_packet(
    request: OracleOperatorChronicInstabilityPacketRequest,
    *,
    reopen_recurrence_policy: OracleOperatorReopenRecurrencePolicy | None = None,
    operator_queue_query_result=None,
    board_label: str = 'default',
) -> OracleOperatorChronicInstabilityPacket:
    if reopen_recurrence_policy is None:
        reopen_recurrence_policy = materialize_operator_reopen_recurrence_policy(
            build_operator_reopen_recurrence_policy_request(
                policy_root=request.packet_root / 'reopen_recurrence_policy',
                board_label=board_label,
                evaluator_label=request.evaluator_label,
                evaluated_at_utc=request.emitted_at_utc,
            ),
            operator_queue_query_result=operator_queue_query_result,
            board_label=board_label,
        )
    emitted_at_utc = _normalize(request.emitted_at_utc)
    items = tuple(
        _derive_item(item, request, emitted_at_utc)
        for item in reopen_recurrence_policy.items
        if item.escalation_required
    )
    request.packet_root.mkdir(parents=True, exist_ok=True)
    summary_output_path = request.packet_root / 'ORACLE_OPERATOR_CHRONIC_INSTABILITY_PACKET.json'
    markdown_output_path = request.packet_root / 'ORACLE_OPERATOR_CHRONIC_INSTABILITY_PACKET.md'
    report = OracleOperatorChronicInstabilityPacket(
        schema_version='oracle_operator_chronic_instability_packet/v1',
        board_label=reopen_recurrence_policy.board_label,
        packet_root=str(request.packet_root),
        evaluator_label=request.evaluator_label,
        emitted_at_utc=emitted_at_utc.isoformat(),
        packet_count=len(items),
        escalation_required_count=len(items),
        chronic_packet_count=len([item for item in items if item.chronic_instability_class == 'CHRONIC_INSTABILITY']),
        summary_output_path=str(summary_output_path),
        markdown_output_path=str(markdown_output_path),
        items=items,
    )
    write_json_markdown_artifacts(
        summary_output_path=summary_output_path,
        markdown_output_path=markdown_output_path,
        payload=report.to_payload(),
        markdown=[
        '## Operator Chronic Instability Packet',
        f"- Board label: `{report.board_label}`",
        f"- Escalation-required packets: `{report.escalation_required_count}`",
        f"- Chronic packets: `{report.chronic_packet_count}`",
        *[f"- {item.work_item_key}: {item.chronic_instability_class} -> {item.escalation_destination}" for item in report.items],
        '',
    ],
    )
    return report


__all__ = [
    'OracleOperatorChronicInstabilityPacket',
    'OracleOperatorChronicInstabilityPacketItem',
    'OracleOperatorChronicInstabilityPacketRequest',
    'build_operator_chronic_instability_packet_request',
    'materialize_operator_chronic_instability_packet',
]
