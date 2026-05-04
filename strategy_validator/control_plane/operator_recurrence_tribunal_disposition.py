from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from strategy_validator.control_plane.operator_recurrence_tribunal_lane import (
    OracleOperatorRecurrenceTribunalLane,
    build_operator_recurrence_tribunal_lane_request,
    materialize_operator_recurrence_tribunal_lane,
)


@dataclass(frozen=True)
class OracleOperatorRecurrenceTribunalDispositionRequest:
    disposition_root: Path
    board_label: str = 'default'
    reviewer_label: str = 'recurrence-tribunal'
    reviewed_at_utc: datetime | None = None


@dataclass(frozen=True)
class OracleOperatorRecurrenceTribunalDispositionItem:
    disposition_key: str
    tribunal_key: str
    packet_key: str
    work_item_key: str
    recurrence_class: str
    chronic_instability_class: str
    tribunal_state: str
    review_authority: str
    disposition_state: str
    freeze_return_activation: bool
    mandate_required: bool
    next_queue_lane: str
    disposition_reason_code: str
    reviewer_label: str
    reviewed_at_utc: str

    def to_payload(self) -> dict[str, Any]:
        return self.__dict__.copy()


@dataclass(frozen=True)
class OracleOperatorRecurrenceTribunalDisposition:
    schema_version: str
    board_label: str
    disposition_root: str
    reviewer_label: str
    reviewed_at_utc: str
    disposition_count: int
    mandate_required_count: int
    freeze_return_count: int
    chronic_disposition_count: int
    summary_output_path: str
    markdown_output_path: str
    items: tuple[OracleOperatorRecurrenceTribunalDispositionItem, ...]

    def to_payload(self) -> dict[str, Any]:
        return {
            'schema_version': self.schema_version,
            'board_label': self.board_label,
            'disposition_root': self.disposition_root,
            'reviewer_label': self.reviewer_label,
            'reviewed_at_utc': self.reviewed_at_utc,
            'disposition_count': self.disposition_count,
            'mandate_required_count': self.mandate_required_count,
            'freeze_return_count': self.freeze_return_count,
            'chronic_disposition_count': self.chronic_disposition_count,
            'summary_output_path': self.summary_output_path,
            'markdown_output_path': self.markdown_output_path,
            'items': [i.to_payload() for i in self.items],
        }


def build_operator_recurrence_tribunal_disposition_request(**kwargs: Any) -> OracleOperatorRecurrenceTribunalDispositionRequest:
    kwargs['disposition_root'] = Path(kwargs['disposition_root']).resolve()
    return OracleOperatorRecurrenceTribunalDispositionRequest(**kwargs)


def _normalize(ts: datetime | None) -> datetime:
    if ts is None:
        return datetime.now(tz=UTC).replace(microsecond=0)
    if ts.tzinfo is None:
        return ts.replace(tzinfo=UTC)
    return ts.astimezone(UTC).replace(microsecond=0)


def _derive_item(item: Any, request: OracleOperatorRecurrenceTribunalDispositionRequest, reviewed_at_utc: datetime) -> OracleOperatorRecurrenceTribunalDispositionItem:
    disposition_state = 'RECURRENCE_REMEDIATION_MANDATE_REQUIRED'
    freeze = True
    mandate_required = True
    next_lane = 'CHRONIC_REMEDIATION_QUEUE'
    reason = 'RECURRENCE_TRIBUNAL_MANDATE_REQUIRED'
    if item.review_authority == 'SUPERVISOR':
        disposition_state = 'SUPERVISOR_RECURRENCE_MANDATE_REQUIRED'
        next_lane = 'SUPERVISOR_REMEDIATION_QUEUE'
        reason = 'SUPERVISOR_RECURRENCE_MANDATE_REQUIRED'
    return OracleOperatorRecurrenceTribunalDispositionItem(
        disposition_key=f'recurrence_disposition:{item.tribunal_key}',
        tribunal_key=item.tribunal_key,
        packet_key=item.packet_key,
        work_item_key=item.work_item_key,
        recurrence_class=item.recurrence_class,
        chronic_instability_class=item.chronic_instability_class,
        tribunal_state=item.tribunal_state,
        review_authority=item.review_authority,
        disposition_state=disposition_state,
        freeze_return_activation=freeze,
        mandate_required=mandate_required,
        next_queue_lane=next_lane,
        disposition_reason_code=reason,
        reviewer_label=request.reviewer_label,
        reviewed_at_utc=reviewed_at_utc.isoformat(),
    )


def materialize_operator_recurrence_tribunal_disposition(
    request: OracleOperatorRecurrenceTribunalDispositionRequest,
    *,
    recurrence_tribunal_lane: OracleOperatorRecurrenceTribunalLane | None = None,
    operator_queue_query_result=None,
    board_label: str = 'default',
) -> OracleOperatorRecurrenceTribunalDisposition:
    if recurrence_tribunal_lane is None:
        recurrence_tribunal_lane = materialize_operator_recurrence_tribunal_lane(
            build_operator_recurrence_tribunal_lane_request(
                tribunal_root=request.disposition_root / 'recurrence_tribunal_lane',
                board_label=board_label,
                reviewer_label=request.reviewer_label,
                reviewed_at_utc=request.reviewed_at_utc,
            ),
            operator_queue_query_result=operator_queue_query_result,
            board_label=board_label,
        )
    reviewed_at_utc = _normalize(request.reviewed_at_utc)
    items = tuple(_derive_item(item, request, reviewed_at_utc) for item in recurrence_tribunal_lane.items)
    request.disposition_root.mkdir(parents=True, exist_ok=True)
    summary_output_path = request.disposition_root / 'ORACLE_OPERATOR_RECURRENCE_TRIBUNAL_DISPOSITION.json'
    markdown_output_path = request.disposition_root / 'ORACLE_OPERATOR_RECURRENCE_TRIBUNAL_DISPOSITION.md'
    report = OracleOperatorRecurrenceTribunalDisposition(
        schema_version='oracle_operator_recurrence_tribunal_disposition/v1',
        board_label=recurrence_tribunal_lane.board_label,
        disposition_root=str(request.disposition_root),
        reviewer_label=request.reviewer_label,
        reviewed_at_utc=reviewed_at_utc.isoformat(),
        disposition_count=len(items),
        mandate_required_count=len([i for i in items if i.mandate_required]),
        freeze_return_count=len([i for i in items if i.freeze_return_activation]),
        chronic_disposition_count=len([i for i in items if i.review_authority == 'TRIBUNAL']),
        summary_output_path=str(summary_output_path),
        markdown_output_path=str(markdown_output_path),
        items=items,
    )
    summary_output_path.write_text(json.dumps(report.to_payload(), indent=2) + '\n', encoding='utf-8')
    markdown_output_path.write_text('\n'.join([
        '## Operator Recurrence Tribunal Disposition',
        f"- Board label: `{report.board_label}`",
        f"- Reviewer label: `{report.reviewer_label}`",
        f"- Mandate required: `{report.mandate_required_count}`",
        f"- Freeze return count: `{report.freeze_return_count}`",
        *[f"- {item.work_item_key}: {item.disposition_state} -> {item.next_queue_lane}" for item in report.items],
        '',
    ]), encoding='utf-8')
    return report


__all__ = [
    'OracleOperatorRecurrenceTribunalDisposition',
    'OracleOperatorRecurrenceTribunalDispositionItem',
    'OracleOperatorRecurrenceTribunalDispositionRequest',
    'build_operator_recurrence_tribunal_disposition_request',
    'materialize_operator_recurrence_tribunal_disposition',
]
