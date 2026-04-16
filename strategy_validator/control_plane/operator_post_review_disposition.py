from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from strategy_validator.control_plane.operator_reentry_post_review_gate import (
    OracleOperatorReentryPostReviewGate,
    build_operator_reentry_post_review_gate_request,
    materialize_operator_reentry_post_review_gate,
)


@dataclass(frozen=True)
class OracleOperatorPostReviewDispositionRequest:
    disposition_root: Path
    board_label: str = 'default'
    reviewer_label: str = 'post-remediation-reviewer'
    reviewed_at_utc: datetime | None = None


@dataclass(frozen=True)
class OracleOperatorPostReviewDispositionItem:
    disposition_key: str
    review_gate_key: str
    attestation_key: str
    completion_key: str
    work_item_key: str
    remediation_class: str
    review_gate_state: str
    return_authorization: str
    reviewer_label: str
    disposition_state: str
    disposition_reason_code: str
    return_certified: bool
    rework_required: bool
    next_queue_lane: str
    reviewed_at_utc: str

    def to_payload(self) -> dict[str, Any]:
        return self.__dict__.copy()


@dataclass(frozen=True)
class OracleOperatorPostReviewDisposition:
    schema_version: str
    board_label: str
    disposition_root: str
    reviewer_label: str
    reviewed_at_utc: str
    disposition_count: int
    approved_count: int
    denied_count: int
    rework_count: int
    escalated_count: int
    summary_output_path: str
    markdown_output_path: str
    items: tuple[OracleOperatorPostReviewDispositionItem, ...]

    def to_payload(self) -> dict[str, Any]:
        return {
            'schema_version': self.schema_version,
            'board_label': self.board_label,
            'disposition_root': self.disposition_root,
            'reviewer_label': self.reviewer_label,
            'reviewed_at_utc': self.reviewed_at_utc,
            'disposition_count': self.disposition_count,
            'approved_count': self.approved_count,
            'denied_count': self.denied_count,
            'rework_count': self.rework_count,
            'escalated_count': self.escalated_count,
            'summary_output_path': self.summary_output_path,
            'markdown_output_path': self.markdown_output_path,
            'items': [item.to_payload() for item in self.items],
        }


def build_operator_post_review_disposition_request(**kwargs: Any) -> OracleOperatorPostReviewDispositionRequest:
    kwargs['disposition_root'] = Path(kwargs['disposition_root']).resolve()
    return OracleOperatorPostReviewDispositionRequest(**kwargs)


def _normalize(ts: datetime | None) -> datetime:
    if ts is None:
        return datetime.now(tz=UTC).replace(microsecond=0)
    if ts.tzinfo is None:
        return ts.replace(tzinfo=UTC)
    return ts.astimezone(UTC).replace(microsecond=0)


def _derive_disposition_item(
    item: Any,
    request: OracleOperatorPostReviewDispositionRequest,
    reviewed_at_utc: datetime,
) -> OracleOperatorPostReviewDispositionItem:
    disposition_state = 'REVIEW_DENIED'
    reason_code = 'RETURN_NOT_CERTIFIED'
    return_certified = False
    rework_required = False
    next_queue_lane = 'REENTRY_QUEUE'

    if item.review_gate_state == 'RETURN_AUTHORIZED':
        disposition_state = 'REVIEW_APPROVED'
        reason_code = 'POST_REMEDIATION_REVIEW_APPROVED'
        return_certified = True
        next_queue_lane = 'OPERATOR_NORMAL_QUEUE'
    elif item.review_gate_state == 'POST_REMEDIATION_REVIEW_REQUIRED':
        disposition_state = 'REWORK_REQUIRED'
        reason_code = 'TARGETED_REVIEW_REQUIRES_REWORK'
        rework_required = True
        next_queue_lane = 'REENTRY_QUEUE'
    elif item.review_gate_state == 'SUPERVISOR_INTERVENTION_REQUIRED':
        disposition_state = 'REVIEW_ESCALATED'
        reason_code = 'SUPERVISOR_REVIEW_REQUIRED'
        next_queue_lane = 'SUPERVISOR_REVIEW_QUEUE'
    elif item.review_gate_state == 'REENTRY_REMEDIATION_CONTINUES':
        disposition_state = 'REWORK_REQUIRED'
        reason_code = 'REMEDIATION_STILL_IN_PROGRESS'
        rework_required = True
        next_queue_lane = 'REENTRY_QUEUE'
    elif item.review_gate_state == 'ATTESTATION_PENDING':
        disposition_state = 'REVIEW_DENIED'
        reason_code = 'ATTESTATION_PENDING_NO_RETURN'
        next_queue_lane = 'REENTRY_QUEUE'

    return OracleOperatorPostReviewDispositionItem(
        disposition_key=f'disposition:{item.review_gate_key}',
        review_gate_key=item.review_gate_key,
        attestation_key=item.attestation_key,
        completion_key=item.completion_key,
        work_item_key=item.work_item_key,
        remediation_class=item.remediation_class,
        review_gate_state=item.review_gate_state,
        return_authorization=item.return_authorization,
        reviewer_label=request.reviewer_label,
        disposition_state=disposition_state,
        disposition_reason_code=reason_code,
        return_certified=return_certified,
        rework_required=rework_required,
        next_queue_lane=next_queue_lane,
        reviewed_at_utc=reviewed_at_utc.isoformat(),
    )


def materialize_operator_post_review_disposition(
    request: OracleOperatorPostReviewDispositionRequest,
    *,
    reentry_post_review_gate: OracleOperatorReentryPostReviewGate | None = None,
    operator_queue_query_result=None,
    board_label: str = 'default',
) -> OracleOperatorPostReviewDisposition:
    if reentry_post_review_gate is None:
        reentry_post_review_gate = materialize_operator_reentry_post_review_gate(
            build_operator_reentry_post_review_gate_request(
                review_root=request.disposition_root / 'post_review_gate',
                board_label=board_label,
                reviewer_label=request.reviewer_label,
                reviewed_at_utc=request.reviewed_at_utc,
            ),
            operator_queue_query_result=operator_queue_query_result,
            board_label=board_label,
        )

    reviewed_at_utc = _normalize(request.reviewed_at_utc)
    items = tuple(_derive_disposition_item(item, request, reviewed_at_utc) for item in reentry_post_review_gate.items)
    request.disposition_root.mkdir(parents=True, exist_ok=True)
    summary_output_path = request.disposition_root / 'ORACLE_OPERATOR_POST_REVIEW_DISPOSITION.json'
    markdown_output_path = request.disposition_root / 'ORACLE_OPERATOR_POST_REVIEW_DISPOSITION.md'
    report = OracleOperatorPostReviewDisposition(
        schema_version='oracle_operator_post_review_disposition/v1',
        board_label=reentry_post_review_gate.board_label,
        disposition_root=str(request.disposition_root),
        reviewer_label=request.reviewer_label,
        reviewed_at_utc=reviewed_at_utc.isoformat(),
        disposition_count=len(items),
        approved_count=len([item for item in items if item.disposition_state == 'REVIEW_APPROVED']),
        denied_count=len([item for item in items if item.disposition_state == 'REVIEW_DENIED']),
        rework_count=len([item for item in items if item.disposition_state == 'REWORK_REQUIRED']),
        escalated_count=len([item for item in items if item.disposition_state == 'REVIEW_ESCALATED']),
        summary_output_path=str(summary_output_path),
        markdown_output_path=str(markdown_output_path),
        items=items,
    )
    summary_output_path.write_text(json.dumps(report.to_payload(), indent=2) + '\n', encoding='utf-8')
    markdown_output_path.write_text(
        '\n'.join([
            '## Operator Post-Remediation Review Disposition',
            f"- Board label: `{report.board_label}`",
            f"- Reviewer label: `{report.reviewer_label}`",
            f"- Approved: `{report.approved_count}`",
            f"- Rework required: `{report.rework_count}`",
            f"- Escalated: `{report.escalated_count}`",
            *[f"- {item.work_item_key}: {item.disposition_state} -> {item.next_queue_lane}" for item in report.items],
            '',
        ]),
        encoding='utf-8',
    )
    return report


__all__ = [
    'OracleOperatorPostReviewDisposition',
    'OracleOperatorPostReviewDispositionItem',
    'OracleOperatorPostReviewDispositionRequest',
    'build_operator_post_review_disposition_request',
    'materialize_operator_post_review_disposition',
]
