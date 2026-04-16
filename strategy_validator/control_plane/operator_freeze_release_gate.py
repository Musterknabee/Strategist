from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from strategy_validator.control_plane.operator_chronic_remediation_satisfaction import (
    OracleOperatorChronicRemediationSatisfaction,
    build_operator_chronic_remediation_satisfaction_request,
    materialize_operator_chronic_remediation_satisfaction,
)


@dataclass(frozen=True)
class OracleOperatorFreezeReleaseGateRequest:
    gate_root: Path
    board_label: str = 'default'
    reviewer_label: str = 'freeze-release-review'
    reviewed_at_utc: datetime | None = None


@dataclass(frozen=True)
class OracleOperatorFreezeReleaseGateItem:
    gate_key: str
    satisfaction_key: str
    ledger_entry_key: str
    work_item_key: str
    recurrence_class: str
    chronic_instability_class: str
    satisfaction_state: str
    exit_criteria_state: str
    gate_state: str
    release_authorized: bool
    freeze_release_posture: str
    gate_reason_code: str
    next_queue_lane: str
    reviewer_label: str
    reviewed_at_utc: str

    def to_payload(self) -> dict[str, Any]:
        return self.__dict__.copy()


@dataclass(frozen=True)
class OracleOperatorFreezeReleaseGate:
    schema_version: str
    board_label: str
    gate_root: str
    reviewer_label: str
    reviewed_at_utc: str
    gate_count: int
    release_authorized_count: int
    hold_count: int
    supervisor_release_count: int
    summary_output_path: str
    markdown_output_path: str
    items: tuple[OracleOperatorFreezeReleaseGateItem, ...]

    def to_payload(self) -> dict[str, Any]:
        return {
            'schema_version': self.schema_version,
            'board_label': self.board_label,
            'gate_root': self.gate_root,
            'reviewer_label': self.reviewer_label,
            'reviewed_at_utc': self.reviewed_at_utc,
            'gate_count': self.gate_count,
            'release_authorized_count': self.release_authorized_count,
            'hold_count': self.hold_count,
            'supervisor_release_count': self.supervisor_release_count,
            'summary_output_path': self.summary_output_path,
            'markdown_output_path': self.markdown_output_path,
            'items': [i.to_payload() for i in self.items],
        }


def build_operator_freeze_release_gate_request(**kwargs: Any) -> OracleOperatorFreezeReleaseGateRequest:
    kwargs['gate_root'] = Path(kwargs['gate_root']).resolve()
    return OracleOperatorFreezeReleaseGateRequest(**kwargs)


def _normalize(ts: datetime | None) -> datetime:
    if ts is None:
        return datetime.now(tz=UTC).replace(microsecond=0)
    if ts.tzinfo is None:
        return ts.replace(tzinfo=UTC)
    return ts.astimezone(UTC).replace(microsecond=0)


def _derive_item(item: Any, request: OracleOperatorFreezeReleaseGateRequest, reviewed_at_utc: datetime) -> OracleOperatorFreezeReleaseGateItem:
    gate_state = 'FREEZE_RELEASE_AUTHORIZED'
    release_authorized = True
    posture = 'RETURN_RELEASED_AFTER_CHRONIC_REMEDIATION'
    reason = 'FREEZE_RELEASE_AUTHORIZED_AFTER_SATISFACTION'
    next_lane = 'RETURN_AUTHORIZATION_REENTRY_QUEUE'
    if 'SUPERVISOR' in item.exit_criteria_state:
        gate_state = 'SUPERVISOR_FREEZE_RELEASE_AUTHORIZED'
        posture = 'RETURN_RELEASED_WITH_SUPERVISOR_MONITORING'
        reason = 'SUPERVISOR_FREEZE_RELEASE_AUTHORIZED'
        next_lane = 'SUPERVISOR_RETURN_AUTHORIZATION_QUEUE'
    if not item.freeze_release_eligible:
        gate_state = 'FREEZE_RELEASE_HELD'
        release_authorized = False
        posture = 'RETURN_REMAINS_FROZEN'
        reason = 'FREEZE_RELEASE_NOT_ELIGIBLE'
        next_lane = 'CHRONIC_REMEDIATION_QUEUE'
    return OracleOperatorFreezeReleaseGateItem(
        gate_key=f'freeze_release_gate:{item.satisfaction_key}',
        satisfaction_key=item.satisfaction_key,
        ledger_entry_key=item.ledger_entry_key,
        work_item_key=item.work_item_key,
        recurrence_class=item.recurrence_class,
        chronic_instability_class=item.chronic_instability_class,
        satisfaction_state=item.satisfaction_state,
        exit_criteria_state=item.exit_criteria_state,
        gate_state=gate_state,
        release_authorized=release_authorized,
        freeze_release_posture=posture,
        gate_reason_code=reason,
        next_queue_lane=next_lane,
        reviewer_label=request.reviewer_label,
        reviewed_at_utc=reviewed_at_utc.isoformat(),
    )


def materialize_operator_freeze_release_gate(
    request: OracleOperatorFreezeReleaseGateRequest,
    *,
    chronic_remediation_satisfaction: OracleOperatorChronicRemediationSatisfaction | None = None,
    operator_queue_query_result=None,
    board_label: str = 'default',
) -> OracleOperatorFreezeReleaseGate:
    if chronic_remediation_satisfaction is None:
        chronic_remediation_satisfaction = materialize_operator_chronic_remediation_satisfaction(
            build_operator_chronic_remediation_satisfaction_request(
                satisfaction_root=request.gate_root / 'chronic_remediation_satisfaction',
                board_label=board_label,
                reviewer_label=request.reviewer_label,
                evaluated_at_utc=request.reviewed_at_utc,
            ),
            operator_queue_query_result=operator_queue_query_result,
            board_label=board_label,
        )
    reviewed_at_utc = _normalize(request.reviewed_at_utc)
    items = tuple(_derive_item(item, request, reviewed_at_utc) for item in chronic_remediation_satisfaction.items)
    request.gate_root.mkdir(parents=True, exist_ok=True)
    summary_output_path = request.gate_root / 'ORACLE_OPERATOR_FREEZE_RELEASE_GATE.json'
    markdown_output_path = request.gate_root / 'ORACLE_OPERATOR_FREEZE_RELEASE_GATE.md'
    report = OracleOperatorFreezeReleaseGate(
        schema_version='oracle_operator_freeze_release_gate/v1',
        board_label=chronic_remediation_satisfaction.board_label,
        gate_root=str(request.gate_root),
        reviewer_label=request.reviewer_label,
        reviewed_at_utc=reviewed_at_utc.isoformat(),
        gate_count=len(items),
        release_authorized_count=len([i for i in items if i.release_authorized]),
        hold_count=len([i for i in items if not i.release_authorized]),
        supervisor_release_count=len([i for i in items if 'SUPERVISOR' in i.gate_state]),
        summary_output_path=str(summary_output_path),
        markdown_output_path=str(markdown_output_path),
        items=items,
    )
    summary_output_path.write_text(json.dumps(report.to_payload(), indent=2) + '\n', encoding='utf-8')
    markdown_output_path.write_text('\n'.join([
        '## Operator Freeze Release Gate',
        f"- Board label: `{report.board_label}`",
        f"- Reviewer label: `{report.reviewer_label}`",
        f"- Release authorized count: `{report.release_authorized_count}`",
        f"- Hold count: `{report.hold_count}`",
        *[f"- {item.work_item_key}: {item.gate_state} -> {item.next_queue_lane}" for item in report.items],
        '',
    ]), encoding='utf-8')
    return report


__all__ = [
    'OracleOperatorFreezeReleaseGate',
    'OracleOperatorFreezeReleaseGateItem',
    'OracleOperatorFreezeReleaseGateRequest',
    'build_operator_freeze_release_gate_request',
    'materialize_operator_freeze_release_gate',
]
