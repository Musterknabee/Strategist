from __future__ import annotations

import pytest

from strategy_validator.ledger.operator_actions import append_operator_action_event, read_operator_action_events


def test_operator_action_journal_enforces_global_idempotency_key(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv('STRATEGY_VALIDATOR_LEDGER_DB_PATH', str(tmp_path / 'ledger.sqlite3'))
    first = append_operator_action_event(
        action='claim-item',
        operator_id='ops',
        target={'work_item_key': 'wk-1', 'idempotency_key': 'idem-1'},
        summary_line='first',
    )
    replay = append_operator_action_event(
        action='claim-item',
        operator_id='ops',
        target={'work_item_key': 'wk-1', 'idempotency_key': 'idem-1'},
        summary_line='first',
    )
    assert replay.action_event_id == first.action_event_id
    assert len(read_operator_action_events(idempotency_key='idem-1')) == 1

    with pytest.raises(ValueError, match='idempotency_key already used'):
        append_operator_action_event(
            action='renew-lease',
            operator_id='ops',
            target={'work_item_key': 'wk-1', 'idempotency_key': 'idem-1'},
            summary_line='conflict',
        )
