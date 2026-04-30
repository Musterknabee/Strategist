from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from strategy_validator.control_plane.operator_reopen_lineage import (
    OracleOperatorReopenLineage,
    build_operator_reopen_lineage_request,
    materialize_operator_reopen_lineage,
)


@dataclass(frozen=True)
class OracleOperatorReopenRecurrencePolicyRequest:
    policy_root: Path
    board_label: str = 'default'
    evaluator_label: str = 'reopen-recurrence-policy'
    evaluated_at_utc: datetime | None = None
    escalation_after_reopen_count: int = 2
    chronic_after_reopen_count: int = 3
    drift_signal_mode: str = 'AUTO'


@dataclass(frozen=True)
class OracleOperatorReopenRecurrencePolicyItem:
    policy_key: str
    lineage_key: str
    work_item_key: str
    remediation_class: str
    current_reopen_count: int
    recurrence_class: str
    recurrence_policy_state: str
    escalation_required: bool
    recommended_queue_lane: str
    policy_reason_code: str
    evaluator_label: str
    evaluated_at_utc: str

    def to_payload(self) -> dict[str, Any]:
        return self.__dict__.copy()


@dataclass(frozen=True)
class OracleOperatorReopenRecurrencePolicy:
    schema_version: str
    board_label: str
    policy_root: str
    evaluator_label: str
    evaluated_at_utc: str
    item_count: int
    escalation_required_count: int
    chronic_reopen_count: int
    summary_output_path: str
    markdown_output_path: str
    items: tuple[OracleOperatorReopenRecurrencePolicyItem, ...]

    def to_payload(self) -> dict[str, Any]:
        return {
            'schema_version': self.schema_version,
            'board_label': self.board_label,
            'policy_root': self.policy_root,
            'evaluator_label': self.evaluator_label,
            'evaluated_at_utc': self.evaluated_at_utc,
            'item_count': self.item_count,
            'escalation_required_count': self.escalation_required_count,
            'chronic_reopen_count': self.chronic_reopen_count,
            'summary_output_path': self.summary_output_path,
            'markdown_output_path': self.markdown_output_path,
            'items': [i.to_payload() for i in self.items],
        }


def build_operator_reopen_recurrence_policy_request(**kwargs: Any) -> OracleOperatorReopenRecurrencePolicyRequest:
    kwargs['policy_root'] = Path(kwargs['policy_root']).resolve()
    return OracleOperatorReopenRecurrencePolicyRequest(**kwargs)


def _normalize(ts: datetime | None) -> datetime:
    if ts is None:
        return datetime.now(tz=UTC).replace(microsecond=0)
    if ts.tzinfo is None:
        return ts.replace(tzinfo=UTC)
    return ts.astimezone(UTC).replace(microsecond=0)


def _recurrence_class(count: int, chronic_after: int) -> str:
    if count <= 0:
        return 'NON_RECURRENT'
    if count >= chronic_after:
        return 'CHRONIC_REOPEN'
    if count == 1:
        return 'FIRST_REOPEN'
    return 'REPEAT_REOPEN'


def _derive_policy_item(item: Any, request: OracleOperatorReopenRecurrencePolicyRequest, evaluated_at_utc: datetime) -> OracleOperatorReopenRecurrencePolicyItem:
    recurrence_class = _recurrence_class(item.current_reopen_count, request.chronic_after_reopen_count)
    state = 'NO_REOPEN_ACTIVE'
    escalation_required = False
    queue_lane = 'OPERATOR_NORMAL_QUEUE'
    reason = 'NO_ACTIVE_REOPEN_POLICY_ACTION'
    if item.current_reopen_count >= request.chronic_after_reopen_count:
        state = 'CHRONIC_REOPEN_ESCALATION_REQUIRED'
        escalation_required = True
        queue_lane = 'SUPERVISOR_ESCALATION_QUEUE'
        reason = 'CHRONIC_REOPEN_EXCEEDED_POLICY_LIMIT'
    elif item.current_reopen_count >= request.escalation_after_reopen_count:
        state = 'RECURRENT_REOPEN_ESCALATION_REQUIRED'
        escalation_required = True
        queue_lane = 'SUPERVISOR_ESCALATION_QUEUE'
        reason = 'RECURRENT_REOPEN_REQUIRES_SUPERVISOR_ATTENTION'
    elif item.current_reopen_count == 1 and item.lineage_state == 'REOPEN_LINEAGE_ADVANCED':
        state = 'FIRST_REOPEN_MONITOR_AND_REMEDIATE'
        queue_lane = 'REENTRY_QUEUE'
        reason = 'FIRST_REOPEN_REQUIRES_TARGETED_REMEDIATION'
    elif item.lineage_state == 'REOPEN_LINEAGE_WATCH_ONLY':
        state = 'WATCH_REOPEN_CONTEXT'
        queue_lane = 'OPERATOR_MONITORING_QUEUE'
        reason = 'REOPEN_CONTEXT_REMAINS_UNDER_POST_RETURN_WATCH'
    return OracleOperatorReopenRecurrencePolicyItem(
        policy_key=f'reopen_recurrence_policy:{item.lineage_key}',
        lineage_key=item.lineage_key,
        work_item_key=item.work_item_key,
        remediation_class=item.remediation_class,
        current_reopen_count=item.current_reopen_count,
        recurrence_class=recurrence_class,
        recurrence_policy_state=state,
        escalation_required=escalation_required,
        recommended_queue_lane=queue_lane,
        policy_reason_code=reason,
        evaluator_label=request.evaluator_label,
        evaluated_at_utc=evaluated_at_utc.isoformat(),
    )


def materialize_operator_reopen_recurrence_policy(
    request: OracleOperatorReopenRecurrencePolicyRequest,
    *,
    reopen_lineage: OracleOperatorReopenLineage | None = None,
    operator_queue_query_result=None,
    board_label: str = 'default',
) -> OracleOperatorReopenRecurrencePolicy:
    if reopen_lineage is None:
        reopen_lineage = materialize_operator_reopen_lineage(
            build_operator_reopen_lineage_request(
                lineage_root=request.policy_root / 'reopen_lineage',
                board_label=board_label,
                lineage_label=request.evaluator_label,
                analyzed_at_utc=request.evaluated_at_utc,
                drift_signal_mode=request.drift_signal_mode,
            ),
            operator_queue_query_result=operator_queue_query_result,
            board_label=board_label,
        )
    evaluated_at_utc = _normalize(request.evaluated_at_utc)
    items = tuple(_derive_policy_item(i, request, evaluated_at_utc) for i in reopen_lineage.items)
    request.policy_root.mkdir(parents=True, exist_ok=True)
    summary_output_path = request.policy_root / 'ORACLE_OPERATOR_REOPEN_RECURRENCE_POLICY.json'
    markdown_output_path = request.policy_root / 'ORACLE_OPERATOR_REOPEN_RECURRENCE_POLICY.md'
    report = OracleOperatorReopenRecurrencePolicy(
        schema_version='oracle_operator_reopen_recurrence_policy/v1',
        board_label=reopen_lineage.board_label,
        policy_root=str(request.policy_root),
        evaluator_label=request.evaluator_label,
        evaluated_at_utc=evaluated_at_utc.isoformat(),
        item_count=len(items),
        escalation_required_count=len([i for i in items if i.escalation_required]),
        chronic_reopen_count=len([i for i in items if i.recurrence_class == 'CHRONIC_REOPEN']),
        summary_output_path=str(summary_output_path),
        markdown_output_path=str(markdown_output_path),
        items=items,
    )
    summary_output_path.write_text(json.dumps(report.to_payload(), indent=2) + '\n', encoding='utf-8')
    markdown_output_path.write_text('\n'.join([
        '## Operator Reopen Recurrence Policy',
        f"- Board label: `{report.board_label}`",
        f"- Evaluator label: `{report.evaluator_label}`",
        f"- Escalation required: `{report.escalation_required_count}`",
        f"- Chronic reopen count: `{report.chronic_reopen_count}`",
        *[f"- {i.work_item_key}: {i.recurrence_class} -> {i.recurrence_policy_state}" for i in report.items],
        '',
    ]), encoding='utf-8')
    return report


__all__ = [
    'OracleOperatorReopenRecurrencePolicy',
    'OracleOperatorReopenRecurrencePolicyItem',
    'OracleOperatorReopenRecurrencePolicyRequest',
    'build_operator_reopen_recurrence_policy_request',
    'materialize_operator_reopen_recurrence_policy',
]
