from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from strategy_validator.control_plane.materialization import write_json_markdown_artifacts

from strategy_validator.control_plane.operator_decision_execution import (
    OracleOperatorDecisionExecution,
    build_operator_decision_execution_request,
    materialize_operator_decision_execution,
)
from strategy_validator.control_plane.operator_workboard_actions import (
    OracleOperatorWorkboardActionContract,
    materialize_operator_workboard_action_contract,
)


@dataclass(frozen=True)
class OracleOperatorActionOutcomeLedgerRequest:
    ledger_root: Path
    board_label: str = 'default'
    outcome_state: str = 'ACKNOWLEDGED'
    actor_label: str = 'operator'
    note: str = ''
    emitted_at_utc: datetime | None = None


@dataclass(frozen=True)
class OracleOperatorActionOutcomeLedgerEntry:
    outcome_key: str
    action_contract_key: str
    work_item_key: str
    outcome_state: str
    actor_label: str
    note: str
    emitted_at_utc: str
    execution_status: str | None = None

    def to_payload(self) -> dict[str, Any]:
        return self.__dict__.copy()


@dataclass(frozen=True)
class OracleOperatorActionOutcomeLedger:
    schema_version: str
    board_label: str
    ledger_root: str
    outcome_count: int
    summary_output_path: str
    markdown_output_path: str
    entries: tuple[OracleOperatorActionOutcomeLedgerEntry, ...]

    def to_payload(self) -> dict[str, Any]:
        return {
            'schema_version': self.schema_version,
            'board_label': self.board_label,
            'ledger_root': self.ledger_root,
            'outcome_count': self.outcome_count,
            'summary_output_path': self.summary_output_path,
            'markdown_output_path': self.markdown_output_path,
            'entries': [e.to_payload() for e in self.entries],
        }


def build_operator_action_outcome_ledger_request(**kwargs: Any) -> OracleOperatorActionOutcomeLedgerRequest:
    kwargs['ledger_root'] = Path(kwargs['ledger_root']).resolve()
    return OracleOperatorActionOutcomeLedgerRequest(**kwargs)


def materialize_operator_action_outcome_ledger(
    request: OracleOperatorActionOutcomeLedgerRequest,
    action_contract: OracleOperatorWorkboardActionContract | None = None,
    decision_execution: OracleOperatorDecisionExecution | None = None,
    operator_queue_query_result=None,
    board_label: str = 'default',
) -> OracleOperatorActionOutcomeLedger:
    if action_contract is None:
        action_contract = materialize_operator_workboard_action_contract(
            operator_queue_query_result=operator_queue_query_result,
            board_label=board_label,
        )
    if decision_execution is None:
        decision_execution = materialize_operator_decision_execution(
            request=build_operator_decision_execution_request(
                execution_root=request.ledger_root / 'execution',
                board_label=action_contract.board_label,
                desired_transition=request.outcome_state,
                actor_label=request.actor_label,
                note=request.note,
                emitted_at_utc=request.emitted_at_utc,
            ),
            action_contract=action_contract,
        )

    entries = tuple(
        OracleOperatorActionOutcomeLedgerEntry(
            outcome_key=f'outcome:{item.action_contract_key}',
            action_contract_key=item.action_contract_key,
            work_item_key=item.work_item_key,
            outcome_state=item.effective_transition,
            actor_label=item.actor_label,
            note=item.note,
            emitted_at_utc=item.emitted_at_utc,
            execution_status=item.execution_status,
        )
        for item in decision_execution.items
    )
    request.ledger_root.mkdir(parents=True, exist_ok=True)
    summary_output_path = request.ledger_root / 'ORACLE_OPERATOR_ACTION_OUTCOME_LEDGER.json'
    markdown_output_path = request.ledger_root / 'ORACLE_OPERATOR_ACTION_OUTCOME_LEDGER.md'
    ledger = OracleOperatorActionOutcomeLedger(
        schema_version='oracle_operator_action_outcome_ledger/v1',
        board_label=action_contract.board_label,
        ledger_root=str(request.ledger_root),
        outcome_count=len(entries),
        summary_output_path=str(summary_output_path),
        markdown_output_path=str(markdown_output_path),
        entries=entries,
    )
    write_json_markdown_artifacts(
        summary_output_path=summary_output_path,
        markdown_output_path=markdown_output_path,
        payload=ledger.to_payload(),
        markdown=[
            '## Operator Action Outcome Ledger',
            f"- Board label: `{ledger.board_label}`",
            f"- Outcome count: `{ledger.outcome_count}`",
            *[f"- {e.work_item_key}: {e.outcome_state} by {e.actor_label} [{e.execution_status}]" for e in ledger.entries],
            '',
        ],
    )
    return ledger


__all__ = [
    'OracleOperatorActionOutcomeLedgerRequest',
    'OracleOperatorActionOutcomeLedgerEntry',
    'OracleOperatorActionOutcomeLedger',
    'build_operator_action_outcome_ledger_request',
    'materialize_operator_action_outcome_ledger',
]
