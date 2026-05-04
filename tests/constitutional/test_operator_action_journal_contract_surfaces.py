from __future__ import annotations

import inspect
from pathlib import Path

from strategy_validator.contracts import (
    AppendOperatorActionEventRequest,
    OperatorActionEvent,
    ReadOperatorActionEventsRequest,
)


def test_operator_action_journal_contracts_resolve_from_bounded_contract_module() -> None:
    contract_module = 'strategy_validator.contracts.operator_action_journal'
    for symbol in (
        AppendOperatorActionEventRequest,
        OperatorActionEvent,
        ReadOperatorActionEventsRequest,
    ):
        assert inspect.getmodule(symbol).__name__ == contract_module


def test_ledger_operator_actions_module_does_not_define_contract_dataclasses_inline() -> None:
    source = Path('strategy_validator/ledger/operator_actions.py').read_text(encoding='utf-8')
    for class_name in (
        'class AppendOperatorActionEventRequest',
        'class OperatorActionEvent',
        'class ReadOperatorActionEventsRequest',
    ):
        assert class_name not in source
