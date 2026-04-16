from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from strategy_validator.control_plane.operator_escalation_closure import (
    OracleOperatorEscalationClosure,
    build_operator_escalation_closure_request,
    materialize_operator_escalation_closure,
)
from strategy_validator.control_plane.operator_workboard_actions import (
    OracleOperatorWorkboardActionContract,
    materialize_operator_workboard_action_contract,
)


@dataclass(frozen=True)
class OracleOperatorReentryQueueStateRequest:
    reentry_root: Path
    board_label: str = 'default'
    reopened_at_utc: datetime | None = None


@dataclass(frozen=True)
class OracleOperatorReentryQueueStateItem:
    reentry_key: str
    closure_key: str
    work_item_key: str
    action_contract_key: str
    action_name: str
    actor_lane: str
    reentry_queue_lane: str
    reentry_state: str
    remediation_required: bool
    remediation_reason_code: str
    remediation_class: str
    operator_action_required: str
    reopened_at_utc: str

    def to_payload(self) -> dict[str, Any]:
        return self.__dict__.copy()


@dataclass(frozen=True)
class OracleOperatorReentryQueueState:
    schema_version: str
    board_label: str
    reentry_root: str
    reentry_item_count: int
    remediation_item_count: int
    summary_output_path: str
    markdown_output_path: str
    items: tuple[OracleOperatorReentryQueueStateItem, ...]

    def to_payload(self) -> dict[str, Any]:
        return {
            'schema_version': self.schema_version,
            'board_label': self.board_label,
            'reentry_root': self.reentry_root,
            'reentry_item_count': self.reentry_item_count,
            'remediation_item_count': self.remediation_item_count,
            'summary_output_path': self.summary_output_path,
            'markdown_output_path': self.markdown_output_path,
            'items': [item.to_payload() for item in self.items],
        }


def build_operator_reentry_queue_state_request(**kwargs: Any) -> OracleOperatorReentryQueueStateRequest:
    kwargs['reentry_root'] = Path(kwargs['reentry_root']).resolve()
    return OracleOperatorReentryQueueStateRequest(**kwargs)


def _normalize(ts: datetime | None) -> datetime:
    if ts is None:
        return datetime.now(tz=UTC).replace(microsecond=0)
    if ts.tzinfo is None:
        return ts.replace(tzinfo=UTC)
    return ts.astimezone(UTC).replace(microsecond=0)


def _remediation_class(reason_code: str) -> str:
    if 'CLAIM' in reason_code:
        return 'CLAIM_REPAIR'
    if 'DISPATCH' in reason_code:
        return 'DISPATCH_REPAIR'
    if 'SLA' in reason_code:
        return 'BREACH_REMEDIATION'
    return 'GENERAL_REMEDIATION'


def _operator_action_required(reason_code: str) -> str:
    if 'CLAIM' in reason_code:
        return 'REPAIR_CLAIM_AND_RESUBMIT'
    if 'DISPATCH' in reason_code:
        return 'REPAIR_DISPATCH_GUARD_AND_REQUEUE'
    if 'SLA' in reason_code:
        return 'PRIORITIZE_AND_REMEDIATE_IMMEDIATELY'
    return 'REMEDIATE_AND_REQUEUE'


def materialize_operator_reentry_queue_state(
    request: OracleOperatorReentryQueueStateRequest,
    *,
    escalation_closure: OracleOperatorEscalationClosure | None = None,
    action_contract: OracleOperatorWorkboardActionContract | None = None,
    operator_queue_query_result=None,
    board_label: str = 'default',
) -> OracleOperatorReentryQueueState:
    if escalation_closure is None:
        escalation_closure = materialize_operator_escalation_closure(
            build_operator_escalation_closure_request(
                closure_root=request.reentry_root / 'escalation_closure',
                board_label=board_label,
                closed_at_utc=request.reopened_at_utc,
            ),
            operator_queue_query_result=operator_queue_query_result,
            board_label=board_label,
        )
    if action_contract is None:
        action_contract = materialize_operator_workboard_action_contract(
            operator_queue_query_result=operator_queue_query_result,
            board_label=board_label,
        )

    reopened_at_utc = _normalize(request.reopened_at_utc)
    contract_by_work_item = {item.work_item_key: item for item in action_contract.items}
    items = []
    for closure in escalation_closure.items:
        if closure.closure_status != 'ESCALATION_CLOSED_REQUEUED':
            continue
        contract = contract_by_work_item[closure.work_item_key]
        items.append(OracleOperatorReentryQueueStateItem(
            reentry_key=f'reentry:{closure.closure_key}',
            closure_key=closure.closure_key,
            work_item_key=closure.work_item_key,
            action_contract_key=contract.action_contract_key,
            action_name=contract.action_name,
            actor_lane=contract.actor_lane,
            reentry_queue_lane=closure.next_queue_lane,
            reentry_state=closure.next_state,
            remediation_required=closure.remediation_required,
            remediation_reason_code=closure.closure_reason_code,
            remediation_class=_remediation_class(closure.closure_reason_code),
            operator_action_required=_operator_action_required(closure.closure_reason_code),
            reopened_at_utc=reopened_at_utc.isoformat(),
        ))

    request.reentry_root.mkdir(parents=True, exist_ok=True)
    summary_output_path = request.reentry_root / 'ORACLE_OPERATOR_REENTRY_QUEUE_STATE.json'
    markdown_output_path = request.reentry_root / 'ORACLE_OPERATOR_REENTRY_QUEUE_STATE.md'
    report = OracleOperatorReentryQueueState(
        schema_version='oracle_operator_reentry_queue_state/v1',
        board_label=action_contract.board_label,
        reentry_root=str(request.reentry_root),
        reentry_item_count=len(items),
        remediation_item_count=len([item for item in items if item.remediation_required]),
        summary_output_path=str(summary_output_path),
        markdown_output_path=str(markdown_output_path),
        items=tuple(items),
    )
    summary_output_path.write_text(json.dumps(report.to_payload(), indent=2) + '\n', encoding='utf-8')
    markdown_output_path.write_text(
        '\n'.join([
            '## Operator Reentry Queue State',
            f"- Board label: `{report.board_label}`",
            f"- Reentry items: `{report.reentry_item_count}`",
            f"- Remediation items: `{report.remediation_item_count}`",
            *[
                f"- {item.work_item_key}: {item.reentry_state} via {item.reentry_queue_lane} [{item.operator_action_required}]"
                for item in report.items
            ],
            '',
        ]),
        encoding='utf-8',
    )
    return report


__all__ = [
    'OracleOperatorReentryQueueState',
    'OracleOperatorReentryQueueStateItem',
    'OracleOperatorReentryQueueStateRequest',
    'build_operator_reentry_queue_state_request',
    'materialize_operator_reentry_queue_state',
]
