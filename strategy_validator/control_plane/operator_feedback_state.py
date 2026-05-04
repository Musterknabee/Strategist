from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from strategy_validator.control_plane.materialization import write_json_markdown_artifacts

from strategy_validator.control_plane.operator_action_outcome_ledger import (
    OracleOperatorActionOutcomeLedger,
    build_operator_action_outcome_ledger_request,
    materialize_operator_action_outcome_ledger,
)
from strategy_validator.control_plane.operator_workboard_actions import (
    OracleOperatorWorkboardActionContract,
    materialize_operator_workboard_action_contract,
)


@dataclass(frozen=True)
class OracleOperatorFeedbackStateRequest:
    state_root: Path
    board_label: str = 'default'
    emitted_at_utc: datetime | None = None


@dataclass(frozen=True)
class OracleOperatorFeedbackStateItem:
    work_item_key: str
    current_state: str
    actor_label: str
    action_contract_key: str
    outcome_key: str
    execution_status: str | None = None

    def to_payload(self) -> dict[str, Any]:
        return self.__dict__.copy()


@dataclass(frozen=True)
class OracleOperatorFeedbackState:
    schema_version: str
    board_label: str
    state_root: str
    work_item_count: int
    summary_output_path: str
    markdown_output_path: str
    items: tuple[OracleOperatorFeedbackStateItem, ...]

    def to_payload(self) -> dict[str, Any]:
        return {
            'schema_version': self.schema_version,
            'board_label': self.board_label,
            'state_root': self.state_root,
            'work_item_count': self.work_item_count,
            'summary_output_path': self.summary_output_path,
            'markdown_output_path': self.markdown_output_path,
            'items': [i.to_payload() for i in self.items],
        }


def build_operator_feedback_state_request(**kwargs: Any) -> OracleOperatorFeedbackStateRequest:
    kwargs['state_root'] = Path(kwargs['state_root']).resolve()
    return OracleOperatorFeedbackStateRequest(**kwargs)


def materialize_operator_feedback_state(
    request: OracleOperatorFeedbackStateRequest,
    action_contract: OracleOperatorWorkboardActionContract | None = None,
    action_outcome_ledger: OracleOperatorActionOutcomeLedger | None = None,
    operator_queue_query_result=None,
    board_label: str = 'default',
    terminal_record_publication=None,
) -> OracleOperatorFeedbackState:
    if action_contract is None:
        action_contract = materialize_operator_workboard_action_contract(
            operator_queue_query_result=operator_queue_query_result,
            board_label=board_label,
        )
    if action_outcome_ledger is None:
        action_outcome_ledger = materialize_operator_action_outcome_ledger(
            build_operator_action_outcome_ledger_request(
                ledger_root=request.state_root / 'outcomes',
                board_label=action_contract.board_label,
                emitted_at_utc=request.emitted_at_utc,
            ),
            action_contract=action_contract,
        )
    by_contract = {e.action_contract_key: e for e in action_outcome_ledger.entries}
    items = []
    for contract in action_contract.items:
        outcome = by_contract[contract.action_contract_key]
        items.append(OracleOperatorFeedbackStateItem(
            work_item_key=contract.work_item_key,
            current_state=outcome.outcome_state,
            actor_label=outcome.actor_label,
            action_contract_key=contract.action_contract_key,
            outcome_key=outcome.outcome_key,
            execution_status=outcome.execution_status,
        ))
    request.state_root.mkdir(parents=True, exist_ok=True)
    summary_output_path = request.state_root / 'ORACLE_OPERATOR_FEEDBACK_STATE.json'
    markdown_output_path = request.state_root / 'ORACLE_OPERATOR_FEEDBACK_STATE.md'
    state = OracleOperatorFeedbackState(
        schema_version='oracle_operator_feedback_state/v1',
        board_label=action_contract.board_label,
        state_root=str(request.state_root),
        work_item_count=len(items),
        summary_output_path=str(summary_output_path),
        markdown_output_path=str(markdown_output_path),
        items=tuple(items),
    )
    write_json_markdown_artifacts(
        summary_output_path=summary_output_path,
        markdown_output_path=markdown_output_path,
        payload=state.to_payload(),
        markdown=[
            '## Operator Feedback State',
            f"- Board label: `{state.board_label}`",
            f"- Work item count: `{state.work_item_count}`",
            *[f"- {i.work_item_key}: {i.current_state} ({i.actor_label})" for i in state.items],
            '',
        ],
    )
    return state


__all__ = [
    'OracleOperatorFeedbackStateRequest',
    'OracleOperatorFeedbackStateItem',
    'OracleOperatorFeedbackState',
    'build_operator_feedback_state_request',
    'materialize_operator_feedback_state',
]
