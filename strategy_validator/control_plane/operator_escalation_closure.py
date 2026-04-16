from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from strategy_validator.control_plane.operator_supervisor_review import (
    OracleOperatorSupervisorReview,
    build_operator_supervisor_review_request,
    materialize_operator_supervisor_review,
)


@dataclass(frozen=True)
class OracleOperatorEscalationClosureRequest:
    closure_root: Path
    board_label: str = 'default'
    closed_at_utc: datetime | None = None


@dataclass(frozen=True)
class OracleOperatorEscalationClosureItem:
    closure_key: str
    review_key: str
    packet_key: str
    work_item_key: str
    supervisor_disposition: str
    closure_status: str
    next_queue_lane: str
    next_state: str
    closure_reason_code: str
    remediation_required: bool
    closed_at_utc: str

    def to_payload(self) -> dict[str, Any]:
        return self.__dict__.copy()


@dataclass(frozen=True)
class OracleOperatorEscalationClosure:
    schema_version: str
    board_label: str
    closure_root: str
    total_item_count: int
    resolved_count: int
    requeued_count: int
    open_count: int
    summary_output_path: str
    markdown_output_path: str
    items: tuple[OracleOperatorEscalationClosureItem, ...]

    def to_payload(self) -> dict[str, Any]:
        return {
            'schema_version': self.schema_version,
            'board_label': self.board_label,
            'closure_root': self.closure_root,
            'total_item_count': self.total_item_count,
            'resolved_count': self.resolved_count,
            'requeued_count': self.requeued_count,
            'open_count': self.open_count,
            'summary_output_path': self.summary_output_path,
            'markdown_output_path': self.markdown_output_path,
            'items': [item.to_payload() for item in self.items],
        }


def build_operator_escalation_closure_request(**kwargs: Any) -> OracleOperatorEscalationClosureRequest:
    kwargs['closure_root'] = Path(kwargs['closure_root']).resolve()
    return OracleOperatorEscalationClosureRequest(**kwargs)


def _normalize(ts: datetime | None) -> datetime:
    if ts is None:
        return datetime.now(tz=UTC).replace(microsecond=0)
    if ts.tzinfo is None:
        return ts.replace(tzinfo=UTC)
    return ts.astimezone(UTC).replace(microsecond=0)


def _closure_item(review, closed_at_utc: datetime) -> OracleOperatorEscalationClosureItem:
    if review.closure_recommendation == 'RESOLVE_ESCALATION':
        closure_status = 'ESCALATION_CLOSED_RESOLVED'
        next_queue_lane = 'STANDARD_OPERATOR_FLOW'
        next_state = 'EXECUTION_AUTHORIZED'
        closure_reason_code = 'SUPERVISOR_APPROVED_EXCEPTION'
        remediation_required = False
    elif review.closure_recommendation == 'RETURN_TO_OPERATOR':
        closure_status = 'ESCALATION_CLOSED_REQUEUED'
        next_queue_lane = 'OPERATOR_REMEDIATION_QUEUE'
        next_state = 'REMEDIATION_REQUIRED'
        closure_reason_code = review.disposition_reason_code
        remediation_required = True
    else:
        closure_status = 'ESCALATION_REMAINS_OPEN'
        next_queue_lane = 'SUPERVISOR_REVIEW_QUEUE'
        next_state = 'SUPERVISOR_PENDING'
        closure_reason_code = review.disposition_reason_code
        remediation_required = False
    return OracleOperatorEscalationClosureItem(
        closure_key=f'closure:{review.review_key}',
        review_key=review.review_key,
        packet_key=review.packet_key,
        work_item_key=review.work_item_key,
        supervisor_disposition=review.supervisor_disposition,
        closure_status=closure_status,
        next_queue_lane=next_queue_lane,
        next_state=next_state,
        closure_reason_code=closure_reason_code,
        remediation_required=remediation_required,
        closed_at_utc=closed_at_utc.isoformat(),
    )


def materialize_operator_escalation_closure(
    request: OracleOperatorEscalationClosureRequest,
    *,
    supervisor_review: OracleOperatorSupervisorReview | None = None,
    operator_queue_query_result=None,
    board_label: str = 'default',
) -> OracleOperatorEscalationClosure:
    if supervisor_review is None:
        supervisor_review = materialize_operator_supervisor_review(
            build_operator_supervisor_review_request(review_root=request.closure_root / 'supervisor_review', board_label=board_label),
            operator_queue_query_result=operator_queue_query_result,
            board_label=board_label,
        )
    closed_at_utc = _normalize(request.closed_at_utc)
    items = tuple(_closure_item(item, closed_at_utc) for item in supervisor_review.items)

    request.closure_root.mkdir(parents=True, exist_ok=True)
    summary_output_path = request.closure_root / 'ORACLE_OPERATOR_ESCALATION_CLOSURE.json'
    markdown_output_path = request.closure_root / 'ORACLE_OPERATOR_ESCALATION_CLOSURE.md'
    report = OracleOperatorEscalationClosure(
        schema_version='oracle_operator_escalation_closure/v1',
        board_label=supervisor_review.board_label,
        closure_root=str(request.closure_root),
        total_item_count=len(items),
        resolved_count=len([item for item in items if item.closure_status == 'ESCALATION_CLOSED_RESOLVED']),
        requeued_count=len([item for item in items if item.closure_status == 'ESCALATION_CLOSED_REQUEUED']),
        open_count=len([item for item in items if item.closure_status == 'ESCALATION_REMAINS_OPEN']),
        summary_output_path=str(summary_output_path),
        markdown_output_path=str(markdown_output_path),
        items=items,
    )
    summary_output_path.write_text(json.dumps(report.to_payload(), indent=2) + '\n', encoding='utf-8')
    markdown_output_path.write_text(
        '\n'.join([
            '## Operator Escalation Closure',
            f"- Board label: `{report.board_label}`",
            f"- Resolved: `{report.resolved_count}`",
            f"- Requeued: `{report.requeued_count}`",
            f"- Open: `{report.open_count}`",
            *[
                f"- {item.work_item_key}: {item.closure_status} -> {item.next_state}"
                for item in report.items
            ],
            '',
        ]),
        encoding='utf-8',
    )
    return report


__all__ = [
    'OracleOperatorEscalationClosure',
    'OracleOperatorEscalationClosureItem',
    'OracleOperatorEscalationClosureRequest',
    'build_operator_escalation_closure_request',
    'materialize_operator_escalation_closure',
]
