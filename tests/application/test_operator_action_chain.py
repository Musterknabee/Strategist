from __future__ import annotations

from strategy_validator.application.ui_command_actions import build_ui_operator_command_receipt_payload
from strategy_validator.ledger.operator_actions import verify_operator_action_event_chain


def test_operator_action_event_chain_verifies_clean_journal(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv('STRATEGY_VALIDATOR_LEDGER_DB_PATH', str(tmp_path / 'ledger.sqlite3'))

    build_ui_operator_command_receipt_payload(action='claim-item', operator_id='jp', work_item_key='wk-1')
    build_ui_operator_command_receipt_payload(action='renew-lease', operator_id='jp', work_item_key='wk-1')

    report = verify_operator_action_event_chain()

    assert report.ok is True
    assert report.event_count == 2
    assert report.issue_count == 0
    assert report.issues == ()
