from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from strategy_validator.control_plane.materialization import write_json_markdown_artifacts

from strategy_validator.control_plane.operator_chronic_remediation_mandate_ledger import (
    OracleOperatorChronicRemediationMandateLedger,
    build_operator_chronic_remediation_mandate_ledger_request,
    materialize_operator_chronic_remediation_mandate_ledger,
)


@dataclass(frozen=True)
class OracleOperatorChronicRemediationSatisfactionRequest:
    satisfaction_root: Path
    board_label: str = 'default'
    reviewer_label: str = 'recurrence-tribunal'
    evaluated_at_utc: datetime | None = None


@dataclass(frozen=True)
class OracleOperatorChronicRemediationSatisfactionItem:
    satisfaction_key: str
    ledger_entry_key: str
    disposition_key: str
    tribunal_key: str
    work_item_key: str
    recurrence_class: str
    chronic_instability_class: str
    mandate_state: str
    remediation_directive: str
    satisfaction_state: str
    satisfaction_evidence_posture: str
    exit_criteria_state: str
    freeze_release_eligible: bool
    satisfaction_reason_code: str
    next_queue_lane: str
    reviewer_label: str
    evaluated_at_utc: str

    def to_payload(self) -> dict[str, Any]:
        return self.__dict__.copy()


@dataclass(frozen=True)
class OracleOperatorChronicRemediationSatisfaction:
    schema_version: str
    board_label: str
    satisfaction_root: str
    reviewer_label: str
    evaluated_at_utc: str
    satisfaction_count: int
    satisfied_count: int
    release_eligible_count: int
    evidence_ready_count: int
    summary_output_path: str
    markdown_output_path: str
    items: tuple[OracleOperatorChronicRemediationSatisfactionItem, ...]

    def to_payload(self) -> dict[str, Any]:
        return {
            'schema_version': self.schema_version,
            'board_label': self.board_label,
            'satisfaction_root': self.satisfaction_root,
            'reviewer_label': self.reviewer_label,
            'evaluated_at_utc': self.evaluated_at_utc,
            'satisfaction_count': self.satisfaction_count,
            'satisfied_count': self.satisfied_count,
            'release_eligible_count': self.release_eligible_count,
            'evidence_ready_count': self.evidence_ready_count,
            'summary_output_path': self.summary_output_path,
            'markdown_output_path': self.markdown_output_path,
            'items': [i.to_payload() for i in self.items],
        }


def build_operator_chronic_remediation_satisfaction_request(**kwargs: Any) -> OracleOperatorChronicRemediationSatisfactionRequest:
    kwargs['satisfaction_root'] = Path(kwargs['satisfaction_root']).resolve()
    return OracleOperatorChronicRemediationSatisfactionRequest(**kwargs)


def _normalize(ts: datetime | None) -> datetime:
    if ts is None:
        return datetime.now(tz=UTC).replace(microsecond=0)
    if ts.tzinfo is None:
        return ts.replace(tzinfo=UTC)
    return ts.astimezone(UTC).replace(microsecond=0)


def _derive_item(item: Any, request: OracleOperatorChronicRemediationSatisfactionRequest, evaluated_at_utc: datetime) -> OracleOperatorChronicRemediationSatisfactionItem:
    satisfaction_state = 'MANDATE_SATISFIED_WITH_EVIDENCE'
    evidence = 'MANDATE_EVIDENCE_ATTESTED'
    exit_state = 'FREEZE_RELEASE_REVIEW_READY'
    eligible = True
    reason = 'CHRONIC_MANDATE_SATISFIED'
    next_lane = 'FREEZE_RELEASE_REVIEW_QUEUE'
    if 'SUPERVISOR' in item.mandate_state:
        satisfaction_state = 'SUPERVISOR_MANDATE_SATISFIED_WITH_REVIEW'
        evidence = 'SUPERVISOR_MANDATE_EVIDENCE_ATTESTED'
        exit_state = 'SUPERVISOR_FREEZE_RELEASE_REVIEW_READY'
        reason = 'SUPERVISOR_CHRONIC_MANDATE_SATISFIED'
        next_lane = 'SUPERVISOR_FREEZE_RELEASE_REVIEW_QUEUE'
    return OracleOperatorChronicRemediationSatisfactionItem(
        satisfaction_key=f'chronic_satisfaction:{item.ledger_entry_key}',
        ledger_entry_key=item.ledger_entry_key,
        disposition_key=item.disposition_key,
        tribunal_key=item.tribunal_key,
        work_item_key=item.work_item_key,
        recurrence_class=item.recurrence_class,
        chronic_instability_class=item.chronic_instability_class,
        mandate_state=item.mandate_state,
        remediation_directive=item.remediation_directive,
        satisfaction_state=satisfaction_state,
        satisfaction_evidence_posture=evidence,
        exit_criteria_state=exit_state,
        freeze_release_eligible=eligible,
        satisfaction_reason_code=reason,
        next_queue_lane=next_lane,
        reviewer_label=request.reviewer_label,
        evaluated_at_utc=evaluated_at_utc.isoformat(),
    )


def materialize_operator_chronic_remediation_satisfaction(
    request: OracleOperatorChronicRemediationSatisfactionRequest,
    *,
    chronic_remediation_mandate_ledger: OracleOperatorChronicRemediationMandateLedger | None = None,
    operator_queue_query_result=None,
    board_label: str = 'default',
) -> OracleOperatorChronicRemediationSatisfaction:
    if chronic_remediation_mandate_ledger is None:
        chronic_remediation_mandate_ledger = materialize_operator_chronic_remediation_mandate_ledger(
            build_operator_chronic_remediation_mandate_ledger_request(
                ledger_root=request.satisfaction_root / 'chronic_remediation_mandate_ledger',
                board_label=board_label,
                reviewer_label=request.reviewer_label,
                mandated_at_utc=request.evaluated_at_utc,
            ),
            operator_queue_query_result=operator_queue_query_result,
            board_label=board_label,
        )
    evaluated_at_utc = _normalize(request.evaluated_at_utc)
    items = tuple(_derive_item(item, request, evaluated_at_utc) for item in chronic_remediation_mandate_ledger.items)
    request.satisfaction_root.mkdir(parents=True, exist_ok=True)
    summary_output_path = request.satisfaction_root / 'ORACLE_OPERATOR_CHRONIC_REMEDIATION_SATISFACTION.json'
    markdown_output_path = request.satisfaction_root / 'ORACLE_OPERATOR_CHRONIC_REMEDIATION_SATISFACTION.md'
    report = OracleOperatorChronicRemediationSatisfaction(
        schema_version='oracle_operator_chronic_remediation_satisfaction/v1',
        board_label=chronic_remediation_mandate_ledger.board_label,
        satisfaction_root=str(request.satisfaction_root),
        reviewer_label=request.reviewer_label,
        evaluated_at_utc=evaluated_at_utc.isoformat(),
        satisfaction_count=len(items),
        satisfied_count=len([i for i in items if 'SATISFIED' in i.satisfaction_state]),
        release_eligible_count=len([i for i in items if i.freeze_release_eligible]),
        evidence_ready_count=len([i for i in items if 'EVIDENCE' in i.satisfaction_evidence_posture]),
        summary_output_path=str(summary_output_path),
        markdown_output_path=str(markdown_output_path),
        items=items,
    )
    write_json_markdown_artifacts(
        summary_output_path=summary_output_path,
        markdown_output_path=markdown_output_path,
        payload=report.to_payload(),
        markdown=[
        '## Operator Chronic Remediation Satisfaction',
        f"- Board label: `{report.board_label}`",
        f"- Reviewer label: `{report.reviewer_label}`",
        f"- Satisfied count: `{report.satisfied_count}`",
        f"- Release eligible count: `{report.release_eligible_count}`",
        *[f"- {item.work_item_key}: {item.satisfaction_state} -> {item.next_queue_lane}" for item in report.items],
        '',
    ],
    )
    return report


__all__ = [
    'OracleOperatorChronicRemediationSatisfaction',
    'OracleOperatorChronicRemediationSatisfactionItem',
    'OracleOperatorChronicRemediationSatisfactionRequest',
    'build_operator_chronic_remediation_satisfaction_request',
    'materialize_operator_chronic_remediation_satisfaction',
]
