from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from strategy_validator.control_plane.operator_post_review_disposition import (
    OracleOperatorPostReviewDisposition,
    build_operator_post_review_disposition_request,
    materialize_operator_post_review_disposition,
)


@dataclass(frozen=True)
class OracleOperatorReturnAuthorizationLedgerRequest:
    ledger_root: Path
    board_label: str = 'default'
    reviewer_label: str = 'return-authorizer'
    authorized_at_utc: datetime | None = None


@dataclass(frozen=True)
class OracleOperatorReturnAuthorizationLedgerItem:
    ledger_entry_key: str
    disposition_key: str
    review_gate_key: str
    work_item_key: str
    remediation_class: str
    reviewer_label: str
    disposition_state: str
    authorization_state: str
    authorization_reason_code: str
    authorized_return: bool
    authorization_history_state: str
    next_queue_lane: str
    authorized_at_utc: str

    def to_payload(self) -> dict[str, Any]:
        return self.__dict__.copy()


@dataclass(frozen=True)
class OracleOperatorReturnAuthorizationLedger:
    schema_version: str
    board_label: str
    ledger_root: str
    reviewer_label: str
    authorized_at_utc: str
    entry_count: int
    authorized_count: int
    denied_count: int
    rework_count: int
    escalated_count: int
    summary_output_path: str
    markdown_output_path: str
    items: tuple[OracleOperatorReturnAuthorizationLedgerItem, ...]

    def to_payload(self) -> dict[str, Any]:
        return {
            'schema_version': self.schema_version,
            'board_label': self.board_label,
            'ledger_root': self.ledger_root,
            'reviewer_label': self.reviewer_label,
            'authorized_at_utc': self.authorized_at_utc,
            'entry_count': self.entry_count,
            'authorized_count': self.authorized_count,
            'denied_count': self.denied_count,
            'rework_count': self.rework_count,
            'escalated_count': self.escalated_count,
            'summary_output_path': self.summary_output_path,
            'markdown_output_path': self.markdown_output_path,
            'items': [item.to_payload() for item in self.items],
        }


def build_operator_return_authorization_ledger_request(**kwargs: Any) -> OracleOperatorReturnAuthorizationLedgerRequest:
    kwargs['ledger_root'] = Path(kwargs['ledger_root']).resolve()
    return OracleOperatorReturnAuthorizationLedgerRequest(**kwargs)


def _normalize(ts: datetime | None) -> datetime:
    if ts is None:
        return datetime.now(tz=UTC).replace(microsecond=0)
    if ts.tzinfo is None:
        return ts.replace(tzinfo=UTC)
    return ts.astimezone(UTC).replace(microsecond=0)


def _derive_ledger_item(
    item: Any,
    request: OracleOperatorReturnAuthorizationLedgerRequest,
    authorized_at_utc: datetime,
) -> OracleOperatorReturnAuthorizationLedgerItem:
    authorization_state = 'RETURN_DENIED'
    reason_code = 'REVIEW_DID_NOT_AUTHORIZE_RETURN'
    authorized_return = False
    history_state = 'AUTHORIZATION_RECORDED_DENIAL'
    next_queue_lane = item.next_queue_lane

    if item.disposition_state == 'REVIEW_APPROVED' and item.return_certified:
        authorization_state = 'RETURN_AUTHORIZED'
        reason_code = 'POST_REMEDIATION_REVIEW_APPROVED_RETURN'
        authorized_return = True
        history_state = 'AUTHORIZATION_RECORDED_APPROVAL'
        next_queue_lane = 'OPERATOR_NORMAL_QUEUE'
    elif item.disposition_state == 'REWORK_REQUIRED':
        authorization_state = 'RETURN_REWORK_REQUIRED'
        reason_code = 'REMEDIATION_REWORK_REQUIRED_BEFORE_RETURN'
        history_state = 'AUTHORIZATION_RECORDED_REWORK'
        next_queue_lane = 'REENTRY_QUEUE'
    elif item.disposition_state == 'REVIEW_ESCALATED':
        authorization_state = 'RETURN_ESCALATED'
        reason_code = 'SUPERVISOR_AUTHORIZATION_REQUIRED'
        history_state = 'AUTHORIZATION_RECORDED_ESCALATION'
        next_queue_lane = 'SUPERVISOR_REVIEW_QUEUE'

    return OracleOperatorReturnAuthorizationLedgerItem(
        ledger_entry_key=f'return_auth:{item.disposition_key}',
        disposition_key=item.disposition_key,
        review_gate_key=item.review_gate_key,
        work_item_key=item.work_item_key,
        remediation_class=item.remediation_class,
        reviewer_label=request.reviewer_label,
        disposition_state=item.disposition_state,
        authorization_state=authorization_state,
        authorization_reason_code=reason_code,
        authorized_return=authorized_return,
        authorization_history_state=history_state,
        next_queue_lane=next_queue_lane,
        authorized_at_utc=authorized_at_utc.isoformat(),
    )


def materialize_operator_return_authorization_ledger(
    request: OracleOperatorReturnAuthorizationLedgerRequest,
    *,
    post_review_disposition: OracleOperatorPostReviewDisposition | None = None,
    operator_queue_query_result=None,
    board_label: str = 'default',
) -> OracleOperatorReturnAuthorizationLedger:
    if post_review_disposition is None:
        post_review_disposition = materialize_operator_post_review_disposition(
            build_operator_post_review_disposition_request(
                disposition_root=request.ledger_root / 'post_review_disposition',
                board_label=board_label,
                reviewer_label=request.reviewer_label,
                reviewed_at_utc=request.authorized_at_utc,
            ),
            operator_queue_query_result=operator_queue_query_result,
            board_label=board_label,
        )

    authorized_at_utc = _normalize(request.authorized_at_utc)
    items = tuple(_derive_ledger_item(item, request, authorized_at_utc) for item in post_review_disposition.items)
    request.ledger_root.mkdir(parents=True, exist_ok=True)
    summary_output_path = request.ledger_root / 'ORACLE_OPERATOR_RETURN_AUTHORIZATION_LEDGER.json'
    markdown_output_path = request.ledger_root / 'ORACLE_OPERATOR_RETURN_AUTHORIZATION_LEDGER.md'
    report = OracleOperatorReturnAuthorizationLedger(
        schema_version='oracle_operator_return_authorization_ledger/v1',
        board_label=post_review_disposition.board_label,
        ledger_root=str(request.ledger_root),
        reviewer_label=request.reviewer_label,
        authorized_at_utc=authorized_at_utc.isoformat(),
        entry_count=len(items),
        authorized_count=len([item for item in items if item.authorization_state == 'RETURN_AUTHORIZED']),
        denied_count=len([item for item in items if item.authorization_state == 'RETURN_DENIED']),
        rework_count=len([item for item in items if item.authorization_state == 'RETURN_REWORK_REQUIRED']),
        escalated_count=len([item for item in items if item.authorization_state == 'RETURN_ESCALATED']),
        summary_output_path=str(summary_output_path),
        markdown_output_path=str(markdown_output_path),
        items=items,
    )
    summary_output_path.write_text(json.dumps(report.to_payload(), indent=2) + '\n', encoding='utf-8')
    markdown_output_path.write_text(
        '\n'.join([
            '## Operator Return Authorization Ledger',
            f"- Board label: `{report.board_label}`",
            f"- Reviewer label: `{report.reviewer_label}`",
            f"- Authorized: `{report.authorized_count}`",
            f"- Rework required: `{report.rework_count}`",
            f"- Escalated: `{report.escalated_count}`",
            *[f"- {item.work_item_key}: {item.authorization_state} [{item.authorization_history_state}]" for item in report.items],
            '',
        ]),
        encoding='utf-8',
    )
    return report


__all__ = [
    'OracleOperatorReturnAuthorizationLedger',
    'OracleOperatorReturnAuthorizationLedgerItem',
    'OracleOperatorReturnAuthorizationLedgerRequest',
    'build_operator_return_authorization_ledger_request',
    'materialize_operator_return_authorization_ledger',
]
