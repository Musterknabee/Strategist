from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from strategy_validator.control_plane.operator_reentry_completion import (
    OracleOperatorReentryCompletion,
    build_operator_reentry_completion_request,
    materialize_operator_reentry_completion,
)


@dataclass(frozen=True)
class OracleOperatorReentryCompletionAttestationRequest:
    attestation_root: Path
    board_label: str = 'default'
    attestor_label: str = 'post-remediation-attestor'
    review_policy: str = 'AUTO_INFERRED'
    attested_at_utc: datetime | None = None


@dataclass(frozen=True)
class OracleOperatorReentryCompletionAttestationItem:
    attestation_key: str
    completion_key: str
    reassignment_key: str
    work_item_key: str
    assignee_label: str
    remediation_class: str
    completion_state: str
    evidence_posture: str
    attestation_state: str
    attestation_reason_code: str
    attested_safe_to_return: bool
    review_required: bool
    review_scope: str
    attestor_label: str
    attested_at_utc: str

    def to_payload(self) -> dict[str, Any]:
        return self.__dict__.copy()


@dataclass(frozen=True)
class OracleOperatorReentryCompletionAttestation:
    schema_version: str
    board_label: str
    attestation_root: str
    attestor_label: str
    review_policy: str
    attested_at_utc: str
    attestation_count: int
    attested_return_ready_count: int
    review_required_count: int
    blocked_count: int
    deferred_count: int
    summary_output_path: str
    markdown_output_path: str
    items: tuple[OracleOperatorReentryCompletionAttestationItem, ...]

    def to_payload(self) -> dict[str, Any]:
        return {
            'schema_version': self.schema_version,
            'board_label': self.board_label,
            'attestation_root': self.attestation_root,
            'attestor_label': self.attestor_label,
            'review_policy': self.review_policy,
            'attested_at_utc': self.attested_at_utc,
            'attestation_count': self.attestation_count,
            'attested_return_ready_count': self.attested_return_ready_count,
            'review_required_count': self.review_required_count,
            'blocked_count': self.blocked_count,
            'deferred_count': self.deferred_count,
            'summary_output_path': self.summary_output_path,
            'markdown_output_path': self.markdown_output_path,
            'items': [item.to_payload() for item in self.items],
        }


def build_operator_reentry_completion_attestation_request(**kwargs: Any) -> OracleOperatorReentryCompletionAttestationRequest:
    kwargs['attestation_root'] = Path(kwargs['attestation_root']).resolve()
    return OracleOperatorReentryCompletionAttestationRequest(**kwargs)


def _normalize(ts: datetime | None) -> datetime:
    if ts is None:
        return datetime.now(tz=UTC).replace(microsecond=0)
    if ts.tzinfo is None:
        return ts.replace(tzinfo=UTC)
    return ts.astimezone(UTC).replace(microsecond=0)


def _derive_attestation_item(item: Any, request: OracleOperatorReentryCompletionAttestationRequest, attested_at_utc: datetime) -> OracleOperatorReentryCompletionAttestationItem:
    attestation_state = 'ATTESTATION_PENDING_COMPLETION'
    reason_code = 'REMEDIATION_COMPLETION_NOT_YET_VERIFIED'
    attested_safe_to_return = False
    review_required = False
    review_scope = 'NO_REVIEW_AVAILABLE'

    if item.completion_state == 'REMEDIATION_COMPLETED_VERIFIED':
        if item.remediation_class == 'BREACH_REMEDIATION':
            attestation_state = 'ATTESTED_WITH_HEIGHTENED_REVIEW'
            reason_code = 'BREACH_REMEDIATION_REQUIRES_POST_REVIEW'
            review_required = True
            review_scope = 'POST_REMEDIATION_SUPERVISOR_REVIEW'
        elif item.remediation_class in {'CLAIM_REPAIR', 'DISPATCH_REPAIR'}:
            attestation_state = 'ATTESTED_PENDING_TARGETED_REVIEW'
            reason_code = 'SPECIALIST_REPAIR_REQUIRES_TARGETED_REVIEW'
            review_required = True
            review_scope = 'POST_REMEDIATION_TARGETED_REVIEW'
        else:
            attestation_state = 'ATTESTED_RETURN_READY'
            reason_code = 'GENERAL_REMEDIATION_COMPLETE_AND_SAFE'
            attested_safe_to_return = True
            review_required = False
            review_scope = 'NO_REVIEW_REQUIRED'
    elif item.completion_state == 'REMEDIATION_CYCLE_CLOSED_REASSIGNED':
        attestation_state = 'ATTESTATION_DEFERRED_REASSIGNED'
        reason_code = 'OWNERSHIP_MOVED_TO_NEW_REMEDIATION_CYCLE'
        review_scope = 'REENTRY_REMEDIATION_CONTINUES'
    elif item.completion_state == 'REMEDIATION_CYCLE_ESCALATED':
        attestation_state = 'ATTESTATION_BLOCKED_ESCALATED'
        reason_code = 'SUPERVISOR_INTERVENTION_REQUIRED'
        review_required = True
        review_scope = 'SUPERVISOR_INTERVENTION_QUEUE'
    elif item.completion_state == 'REMEDIATION_OPEN_PENDING_ACKNOWLEDGEMENT':
        attestation_state = 'ATTESTATION_PENDING_OWNER_ACKNOWLEDGEMENT'
        reason_code = 'OWNER_ACKNOWLEDGEMENT_NOT_YET_RECORDED'
        review_scope = 'ACKNOWLEDGEMENT_PENDING'
    elif item.completion_state == 'REMEDIATION_CYCLE_PREPARED_FOR_REASSIGNMENT':
        attestation_state = 'ATTESTATION_DEFERRED_REASSIGNMENT_PREPARED'
        reason_code = 'REASSIGNMENT_PREPARATION_NOT_YET_CLOSED'
        review_scope = 'REASSIGNMENT_PREPARATION'

    return OracleOperatorReentryCompletionAttestationItem(
        attestation_key=f'attestation:{item.completion_key}',
        completion_key=item.completion_key,
        reassignment_key=item.reassignment_key,
        work_item_key=item.work_item_key,
        assignee_label=item.assignee_label,
        remediation_class=item.remediation_class,
        completion_state=item.completion_state,
        evidence_posture=item.evidence_posture,
        attestation_state=attestation_state,
        attestation_reason_code=reason_code,
        attested_safe_to_return=attested_safe_to_return,
        review_required=review_required,
        review_scope=review_scope,
        attestor_label=request.attestor_label,
        attested_at_utc=attested_at_utc.isoformat(),
    )


def materialize_operator_reentry_completion_attestation(
    request: OracleOperatorReentryCompletionAttestationRequest,
    *,
    reentry_completion: OracleOperatorReentryCompletion | None = None,
    operator_queue_query_result=None,
    board_label: str = 'default',
) -> OracleOperatorReentryCompletionAttestation:
    if reentry_completion is None:
        reentry_completion = materialize_operator_reentry_completion(
            build_operator_reentry_completion_request(
                completion_root=request.attestation_root / 'reentry_completion',
                board_label=board_label,
                completed_at_utc=request.attested_at_utc,
            ),
            operator_queue_query_result=operator_queue_query_result,
            board_label=board_label,
        )

    attested_at_utc = _normalize(request.attested_at_utc)
    items = tuple(_derive_attestation_item(item, request, attested_at_utc) for item in reentry_completion.items)
    request.attestation_root.mkdir(parents=True, exist_ok=True)
    summary_output_path = request.attestation_root / 'ORACLE_OPERATOR_REENTRY_COMPLETION_ATTESTATION.json'
    markdown_output_path = request.attestation_root / 'ORACLE_OPERATOR_REENTRY_COMPLETION_ATTESTATION.md'
    report = OracleOperatorReentryCompletionAttestation(
        schema_version='oracle_operator_reentry_completion_attestation/v1',
        board_label=reentry_completion.board_label,
        attestation_root=str(request.attestation_root),
        attestor_label=request.attestor_label,
        review_policy=request.review_policy,
        attested_at_utc=attested_at_utc.isoformat(),
        attestation_count=len(items),
        attested_return_ready_count=len([item for item in items if item.attested_safe_to_return]),
        review_required_count=len([item for item in items if item.review_required]),
        blocked_count=len([item for item in items if item.attestation_state == 'ATTESTATION_BLOCKED_ESCALATED']),
        deferred_count=len([item for item in items if item.attestation_state.startswith('ATTESTATION_DEFERRED')]),
        summary_output_path=str(summary_output_path),
        markdown_output_path=str(markdown_output_path),
        items=items,
    )
    summary_output_path.write_text(json.dumps(report.to_payload(), indent=2) + '\n', encoding='utf-8')
    markdown_output_path.write_text(
        '\n'.join([
            '## Operator Reentry Completion Attestation',
            f"- Board label: `{report.board_label}`",
            f"- Attestor label: `{report.attestor_label}`",
            f"- Review policy: `{report.review_policy}`",
            f"- Return-ready attestations: `{report.attested_return_ready_count}`",
            f"- Review-required attestations: `{report.review_required_count}`",
            f"- Blocked attestations: `{report.blocked_count}`",
            *[
                f"- {item.work_item_key}: {item.attestation_state} [{item.review_scope}]"
                for item in report.items
            ],
            '',
        ]),
        encoding='utf-8',
    )
    return report


__all__ = [
    'OracleOperatorReentryCompletionAttestation',
    'OracleOperatorReentryCompletionAttestationItem',
    'OracleOperatorReentryCompletionAttestationRequest',
    'build_operator_reentry_completion_attestation_request',
    'materialize_operator_reentry_completion_attestation',
]
