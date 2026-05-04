from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from strategy_validator.control_plane.materialization import write_json_markdown_artifacts

from strategy_validator.control_plane.operator_recurrence_tribunal_disposition import (
    OracleOperatorRecurrenceTribunalDisposition,
    build_operator_recurrence_tribunal_disposition_request,
    materialize_operator_recurrence_tribunal_disposition,
)


@dataclass(frozen=True)
class OracleOperatorChronicRemediationMandateLedgerRequest:
    ledger_root: Path
    board_label: str = 'default'
    reviewer_label: str = 'recurrence-tribunal'
    mandated_at_utc: datetime | None = None


@dataclass(frozen=True)
class OracleOperatorChronicRemediationMandateLedgerItem:
    ledger_entry_key: str
    disposition_key: str
    tribunal_key: str
    work_item_key: str
    recurrence_class: str
    chronic_instability_class: str
    disposition_state: str
    mandate_state: str
    remediation_directive: str
    freeze_return_activation: bool
    allow_return_posture: str
    mandate_reason_code: str
    mandate_history_state: str
    next_queue_lane: str
    reviewer_label: str
    mandated_at_utc: str

    def to_payload(self) -> dict[str, Any]:
        return self.__dict__.copy()


@dataclass(frozen=True)
class OracleOperatorChronicRemediationMandateLedger:
    schema_version: str
    board_label: str
    ledger_root: str
    reviewer_label: str
    mandated_at_utc: str
    entry_count: int
    mandate_required_count: int
    return_frozen_count: int
    chronic_mandate_count: int
    summary_output_path: str
    markdown_output_path: str
    items: tuple[OracleOperatorChronicRemediationMandateLedgerItem, ...]

    def to_payload(self) -> dict[str, Any]:
        return {
            'schema_version': self.schema_version,
            'board_label': self.board_label,
            'ledger_root': self.ledger_root,
            'reviewer_label': self.reviewer_label,
            'mandated_at_utc': self.mandated_at_utc,
            'entry_count': self.entry_count,
            'mandate_required_count': self.mandate_required_count,
            'return_frozen_count': self.return_frozen_count,
            'chronic_mandate_count': self.chronic_mandate_count,
            'summary_output_path': self.summary_output_path,
            'markdown_output_path': self.markdown_output_path,
            'items': [i.to_payload() for i in self.items],
        }


def build_operator_chronic_remediation_mandate_ledger_request(**kwargs: Any) -> OracleOperatorChronicRemediationMandateLedgerRequest:
    kwargs['ledger_root'] = Path(kwargs['ledger_root']).resolve()
    return OracleOperatorChronicRemediationMandateLedgerRequest(**kwargs)


def _normalize(ts: datetime | None) -> datetime:
    if ts is None:
        return datetime.now(tz=UTC).replace(microsecond=0)
    if ts.tzinfo is None:
        return ts.replace(tzinfo=UTC)
    return ts.astimezone(UTC).replace(microsecond=0)


def _derive_item(item: Any, request: OracleOperatorChronicRemediationMandateLedgerRequest, mandated_at_utc: datetime) -> OracleOperatorChronicRemediationMandateLedgerItem:
    directive = 'Strengthen remediation plan, add recurrence-specific checkpoints, and require certified review before return.'
    mandate_state = 'CHRONIC_REMEDIATION_MANDATED'
    allow_return_posture = 'RETURN_FROZEN_UNTIL_MANDATE_SATISFIED'
    reason = 'CHRONIC_REOPEN_MANDATE_RECORDED'
    history = 'MANDATE_HISTORY_RECORDED'
    if item.review_authority == 'SUPERVISOR':
        directive = 'Supervisor-mandated recurrence remediation with strengthened checkpoints and approval before return.'
        mandate_state = 'SUPERVISOR_REMEDIATION_MANDATED'
        allow_return_posture = 'RETURN_FROZEN_PENDING_SUPERVISOR_CLEARANCE'
        reason = 'SUPERVISOR_RECURRENCE_MANDATE_RECORDED'
    return OracleOperatorChronicRemediationMandateLedgerItem(
        ledger_entry_key=f'chronic_mandate:{item.disposition_key}',
        disposition_key=item.disposition_key,
        tribunal_key=item.tribunal_key,
        work_item_key=item.work_item_key,
        recurrence_class=item.recurrence_class,
        chronic_instability_class=item.chronic_instability_class,
        disposition_state=item.disposition_state,
        mandate_state=mandate_state,
        remediation_directive=directive,
        freeze_return_activation=item.freeze_return_activation,
        allow_return_posture=allow_return_posture,
        mandate_reason_code=reason,
        mandate_history_state=history,
        next_queue_lane=item.next_queue_lane,
        reviewer_label=request.reviewer_label,
        mandated_at_utc=mandated_at_utc.isoformat(),
    )


def materialize_operator_chronic_remediation_mandate_ledger(
    request: OracleOperatorChronicRemediationMandateLedgerRequest,
    *,
    recurrence_tribunal_disposition: OracleOperatorRecurrenceTribunalDisposition | None = None,
    operator_queue_query_result=None,
    board_label: str = 'default',
) -> OracleOperatorChronicRemediationMandateLedger:
    if recurrence_tribunal_disposition is None:
        recurrence_tribunal_disposition = materialize_operator_recurrence_tribunal_disposition(
            build_operator_recurrence_tribunal_disposition_request(
                disposition_root=request.ledger_root / 'recurrence_tribunal_disposition',
                board_label=board_label,
                reviewer_label=request.reviewer_label,
                reviewed_at_utc=request.mandated_at_utc,
            ),
            operator_queue_query_result=operator_queue_query_result,
            board_label=board_label,
        )
    mandated_at_utc = _normalize(request.mandated_at_utc)
    items = tuple(_derive_item(item, request, mandated_at_utc) for item in recurrence_tribunal_disposition.items)
    request.ledger_root.mkdir(parents=True, exist_ok=True)
    summary_output_path = request.ledger_root / 'ORACLE_OPERATOR_CHRONIC_REMEDIATION_MANDATE_LEDGER.json'
    markdown_output_path = request.ledger_root / 'ORACLE_OPERATOR_CHRONIC_REMEDIATION_MANDATE_LEDGER.md'
    report = OracleOperatorChronicRemediationMandateLedger(
        schema_version='oracle_operator_chronic_remediation_mandate_ledger/v1',
        board_label=recurrence_tribunal_disposition.board_label,
        ledger_root=str(request.ledger_root),
        reviewer_label=request.reviewer_label,
        mandated_at_utc=mandated_at_utc.isoformat(),
        entry_count=len(items),
        mandate_required_count=len([i for i in items if 'MANDATED' in i.mandate_state]),
        return_frozen_count=len([i for i in items if i.freeze_return_activation]),
        chronic_mandate_count=len([i for i in items if i.chronic_instability_class == 'CHRONIC_INSTABILITY']),
        summary_output_path=str(summary_output_path),
        markdown_output_path=str(markdown_output_path),
        items=items,
    )
    write_json_markdown_artifacts(
        summary_output_path=summary_output_path,
        markdown_output_path=markdown_output_path,
        payload=report.to_payload(),
        markdown=[
        '## Operator Chronic Remediation Mandate Ledger',
        f"- Board label: `{report.board_label}`",
        f"- Reviewer label: `{report.reviewer_label}`",
        f"- Mandate required: `{report.mandate_required_count}`",
        f"- Return frozen count: `{report.return_frozen_count}`",
        *[f"- {item.work_item_key}: {item.mandate_state} -> {item.next_queue_lane}" for item in report.items],
        '',
    ],
    )
    return report


__all__ = [
    'OracleOperatorChronicRemediationMandateLedger',
    'OracleOperatorChronicRemediationMandateLedgerItem',
    'OracleOperatorChronicRemediationMandateLedgerRequest',
    'build_operator_chronic_remediation_mandate_ledger_request',
    'materialize_operator_chronic_remediation_mandate_ledger',
]
