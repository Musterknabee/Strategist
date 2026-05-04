from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor

from strategy_validator.ledger.operator_actions import (
    append_operator_action_event,
    read_operator_action_events,
    verify_operator_action_event_chain,
)


def _append(index: int):
    return append_operator_action_event(
        action='claim-item',
        operator_id='ops',
        target={'work_item_key': f'wk-{index}'},
        summary_line=f'append {index}',
    )


def test_operator_action_sequence_numbers_are_unique_under_concurrent_appends(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv('STRATEGY_VALIDATOR_LEDGER_DB_PATH', str(tmp_path / 'ledger.sqlite3'))

    with ThreadPoolExecutor(max_workers=6) as pool:
        events = list(pool.map(_append, range(12)))

    assert len({event.sequence_number for event in events}) == 12
    assert sorted(event.sequence_number for event in events) == list(range(1, 13))
    assert verify_operator_action_event_chain().ok is True
    assert len(read_operator_action_events()) == 12
