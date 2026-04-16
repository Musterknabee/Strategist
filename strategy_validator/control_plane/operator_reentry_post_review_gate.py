from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from strategy_validator.control_plane.operator_reentry_completion_attestation import (
    OracleOperatorReentryCompletionAttestation,
    build_operator_reentry_completion_attestation_request,
    materialize_operator_reentry_completion_attestation,
)


@dataclass(frozen=True)
class OracleOperatorReentryPostReviewGateRequest:
    review_root: Path
    board_label: str = 'default'
    reviewer_label: str = 'post-remediation-gate'
    reviewed_at_utc: datetime | None = None


@dataclass(frozen=True)
class OracleOperatorReentryPostReviewGateItem:
    review_gate_key: str
    attestation_key: str
    completion_key: str
    work_item_key: str
    remediation_class: str
    attestation_state: str
    review_required: bool
    review_scope: str
    review_gate_state: str
    review_gate_reason_code: str
    return_authorization: str
    next_queue_lane: str
    reviewer_label: str
    reviewed_at_utc: str

    def to_payload(self) -> dict[str, Any]:
        return self.__dict__.copy()


@dataclass(frozen=True)
class OracleOperatorReentryPostReviewGate:
    schema_version: str
    board_label: str
    review_root: str
    reviewer_label: str
    reviewed_at_utc: str
    total_item_count: int
    return_authorized_count: int
    review_pending_count: int
    blocked_count: int
    continuing_reentry_count: int
    summary_output_path: str
    markdown_output_path: str
    items: tuple[OracleOperatorReentryPostReviewGateItem, ...]

    def to_payload(self) -> dict[str, Any]:
        return {
            'schema_version': self.schema_version,
            'board_label': self.board_label,
            'review_root': self.review_root,
            'reviewer_label': self.reviewer_label,
            'reviewed_at_utc': self.reviewed_at_utc,
            'total_item_count': self.total_item_count,
            'return_authorized_count': self.return_authorized_count,
            'review_pending_count': self.review_pending_count,
            'blocked_count': self.blocked_count,
            'continuing_reentry_count': self.continuing_reentry_count,
            'summary_output_path': self.summary_output_path,
            'markdown_output_path': self.markdown_output_path,
            'items': [item.to_payload() for item in self.items],
        }


def build_operator_reentry_post_review_gate_request(**kwargs: Any) -> OracleOperatorReentryPostReviewGateRequest:
    kwargs['review_root'] = Path(kwargs['review_root']).resolve()
    return OracleOperatorReentryPostReviewGateRequest(**kwargs)


def _normalize(ts: datetime | None) -> datetime:
    if ts is None:
        return datetime.now(tz=UTC).replace(microsecond=0)
    if ts.tzinfo is None:
        return ts.replace(tzinfo=UTC)
    return ts.astimezone(UTC).replace(microsecond=0)


def _derive_review_gate_item(item: Any, request: OracleOperatorReentryPostReviewGateRequest, reviewed_at_utc: datetime) -> OracleOperatorReentryPostReviewGateItem:
    review_gate_state = 'COMPLETION_NOT_YET_ATTESTED'
    reason_code = 'RETURN_NOT_ELIGIBLE'
    return_authorization = 'RETURN_NOT_AUTHORIZED'
    next_queue_lane = 'REENTRY_QUEUE'

    if item.attestation_state == 'ATTESTED_RETURN_READY' and item.attested_safe_to_return:
        review_gate_state = 'RETURN_AUTHORIZED'
        reason_code = 'ATTESTED_SAFE_TO_RETURN'
        return_authorization = 'SAFE_TO_RETURN_TO_NORMAL_FLOW'
        next_queue_lane = 'OPERATOR_NORMAL_QUEUE'
    elif item.attestation_state in {'ATTESTED_WITH_HEIGHTENED_REVIEW', 'ATTESTED_PENDING_TARGETED_REVIEW'}:
        review_gate_state = 'POST_REMEDIATION_REVIEW_REQUIRED'
        reason_code = 'REVIEW_REQUIRED_BEFORE_RETURN'
        return_authorization = 'RETURN_PENDING_REVIEW'
        next_queue_lane = 'POST_REMEDIATION_REVIEW_QUEUE'
    elif item.attestation_state == 'ATTESTATION_BLOCKED_ESCALATED':
        review_gate_state = 'SUPERVISOR_INTERVENTION_REQUIRED'
        reason_code = 'ESCALATION_BLOCKS_RETURN'
        return_authorization = 'RETURN_BLOCKED'
        next_queue_lane = 'SUPERVISOR_REVIEW_QUEUE'
    elif item.attestation_state.startswith('ATTESTATION_DEFERRED'):
        review_gate_state = 'REENTRY_REMEDIATION_CONTINUES'
        reason_code = 'REMEDIATION_CYCLE_NOT_CLOSED'
        return_authorization = 'RETURN_DEFERRED'
        next_queue_lane = 'REENTRY_QUEUE'
    elif item.attestation_state.startswith('ATTESTATION_PENDING'):
        review_gate_state = 'ATTESTATION_PENDING'
        reason_code = 'ATTESTATION_NOT_READY'
        return_authorization = 'RETURN_NOT_AUTHORIZED'
        next_queue_lane = 'REENTRY_QUEUE'

    return OracleOperatorReentryPostReviewGateItem(
        review_gate_key=f'review_gate:{item.attestation_key}',
        attestation_key=item.attestation_key,
        completion_key=item.completion_key,
        work_item_key=item.work_item_key,
        remediation_class=item.remediation_class,
        attestation_state=item.attestation_state,
        review_required=item.review_required,
        review_scope=item.review_scope,
        review_gate_state=review_gate_state,
        review_gate_reason_code=reason_code,
        return_authorization=return_authorization,
        next_queue_lane=next_queue_lane,
        reviewer_label=request.reviewer_label,
        reviewed_at_utc=reviewed_at_utc.isoformat(),
    )


def materialize_operator_reentry_post_review_gate(
    request: OracleOperatorReentryPostReviewGateRequest,
    *,
    reentry_completion_attestation: OracleOperatorReentryCompletionAttestation | None = None,
    operator_queue_query_result=None,
    board_label: str = 'default',
) -> OracleOperatorReentryPostReviewGate:
    if reentry_completion_attestation is None:
        reentry_completion_attestation = materialize_operator_reentry_completion_attestation(
            build_operator_reentry_completion_attestation_request(
                attestation_root=request.review_root / 'completion_attestation',
                board_label=board_label,
                attested_at_utc=request.reviewed_at_utc,
            ),
            operator_queue_query_result=operator_queue_query_result,
            board_label=board_label,
        )

    reviewed_at_utc = _normalize(request.reviewed_at_utc)
    items = tuple(_derive_review_gate_item(item, request, reviewed_at_utc) for item in reentry_completion_attestation.items)
    request.review_root.mkdir(parents=True, exist_ok=True)
    summary_output_path = request.review_root / 'ORACLE_OPERATOR_REENTRY_POST_REVIEW_GATE.json'
    markdown_output_path = request.review_root / 'ORACLE_OPERATOR_REENTRY_POST_REVIEW_GATE.md'
    report = OracleOperatorReentryPostReviewGate(
        schema_version='oracle_operator_reentry_post_review_gate/v1',
        board_label=reentry_completion_attestation.board_label,
        review_root=str(request.review_root),
        reviewer_label=request.reviewer_label,
        reviewed_at_utc=reviewed_at_utc.isoformat(),
        total_item_count=len(items),
        return_authorized_count=len([item for item in items if item.review_gate_state == 'RETURN_AUTHORIZED']),
        review_pending_count=len([item for item in items if item.review_gate_state == 'POST_REMEDIATION_REVIEW_REQUIRED']),
        blocked_count=len([item for item in items if item.review_gate_state == 'SUPERVISOR_INTERVENTION_REQUIRED']),
        continuing_reentry_count=len([item for item in items if item.review_gate_state == 'REENTRY_REMEDIATION_CONTINUES']),
        summary_output_path=str(summary_output_path),
        markdown_output_path=str(markdown_output_path),
        items=items,
    )
    summary_output_path.write_text(json.dumps(report.to_payload(), indent=2) + '\n', encoding='utf-8')
    markdown_output_path.write_text(
        '\n'.join([
            '## Operator Reentry Post-Remediation Review Gate',
            f"- Board label: `{report.board_label}`",
            f"- Reviewer label: `{report.reviewer_label}`",
            f"- Return authorized: `{report.return_authorized_count}`",
            f"- Review pending: `{report.review_pending_count}`",
            f"- Blocked: `{report.blocked_count}`",
            *[
                f"- {item.work_item_key}: {item.review_gate_state} -> {item.return_authorization}"
                for item in report.items
            ],
            '',
        ]),
        encoding='utf-8',
    )
    return report


__all__ = [
    'OracleOperatorReentryPostReviewGate',
    'OracleOperatorReentryPostReviewGateItem',
    'OracleOperatorReentryPostReviewGateRequest',
    'build_operator_reentry_post_review_gate_request',
    'materialize_operator_reentry_post_review_gate',
]
