from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from strategy_validator.control_plane.operator_workboard_actions import (
    OracleOperatorWorkboardActionContract,
    OracleOperatorWorkboardActionContractRequest,
    materialize_operator_workboard_action_contract,
)


@dataclass(frozen=True)
class OracleOperatorDecisionJournalRequest:
    journal_root: Path
    board_label: str = 'default'
    emitted_at_utc: datetime | None = None


@dataclass(frozen=True)
class OracleOperatorDecisionJournalEvent:
    event_key: str
    action_contract_key: str
    work_item_key: str
    event_type: str
    emitted_at_utc: str
    summary_line: str

    def to_payload(self) -> dict[str, Any]:
        return self.__dict__.copy()


@dataclass(frozen=True)
class OracleOperatorDecisionJournal:
    schema_version: str
    board_label: str
    journal_root: str
    event_count: int
    summary_output_path: str
    markdown_output_path: str
    events: tuple[OracleOperatorDecisionJournalEvent, ...]

    def to_payload(self) -> dict[str, Any]:
        return {
            'schema_version': self.schema_version,
            'board_label': self.board_label,
            'journal_root': self.journal_root,
            'event_count': self.event_count,
            'summary_output_path': self.summary_output_path,
            'markdown_output_path': self.markdown_output_path,
            'events': [e.to_payload() for e in self.events],
        }


def build_operator_decision_journal_request(**kwargs: Any) -> OracleOperatorDecisionJournalRequest:
    kwargs['journal_root'] = Path(kwargs['journal_root']).resolve()
    return OracleOperatorDecisionJournalRequest(**kwargs)


def materialize_operator_decision_journal(
    request: OracleOperatorDecisionJournalRequest,
    action_contract: OracleOperatorWorkboardActionContract | None = None,
    operator_queue_query_result=None,
    board_label: str = 'default',
) -> OracleOperatorDecisionJournal:
    if action_contract is None:
        action_contract = materialize_operator_workboard_action_contract(
            operator_queue_query_result=operator_queue_query_result,
            board_label=board_label,
        )
    emitted = request.emitted_at_utc or datetime.now(UTC).replace(microsecond=0)
    if emitted.tzinfo is None:
        emitted = emitted.replace(tzinfo=UTC)
    events = tuple(
        OracleOperatorDecisionJournalEvent(
            event_key=f"journal:{item.action_contract_key}",
            action_contract_key=item.action_contract_key,
            work_item_key=item.work_item_key,
            event_type='ACTION_CONTRACT_EMITTED',
            emitted_at_utc=emitted.isoformat(),
            summary_line=f"Action contract emitted for {item.work_item_key} on board {action_contract.board_label}.",
        )
        for item in action_contract.items
    )
    request.journal_root.mkdir(parents=True, exist_ok=True)
    summary_output_path = request.journal_root / 'ORACLE_OPERATOR_DECISION_JOURNAL.json'
    markdown_output_path = request.journal_root / 'ORACLE_OPERATOR_DECISION_JOURNAL.md'
    journal = OracleOperatorDecisionJournal(
        schema_version='oracle_operator_decision_journal/v1',
        board_label=action_contract.board_label,
        journal_root=str(request.journal_root),
        event_count=len(events),
        summary_output_path=str(summary_output_path),
        markdown_output_path=str(markdown_output_path),
        events=events,
    )
    summary_output_path.write_text(json.dumps(journal.to_payload(), indent=2) + '\n', encoding='utf-8')
    markdown_output_path.write_text('\n'.join([
        '## Operator Decision Journal',
        f"- Board label: `{journal.board_label}`",
        f"- Event count: `{journal.event_count}`",
        *[f"- {e.summary_line}" for e in journal.events],
        '',
    ]), encoding='utf-8')
    return journal


__all__ = [
    'OracleOperatorDecisionJournalRequest',
    'OracleOperatorDecisionJournalEvent',
    'OracleOperatorDecisionJournal',
    'build_operator_decision_journal_request',
    'materialize_operator_decision_journal',
]
