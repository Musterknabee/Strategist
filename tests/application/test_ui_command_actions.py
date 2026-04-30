from __future__ import annotations

from strategy_validator.application.ui_command_actions import build_ui_operator_command_receipt_payload
from strategy_validator.ledger.operator_actions import read_operator_action_events


def test_ui_command_receipt_is_journaled(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv('STRATEGY_VALIDATOR_LEDGER_DB_PATH', str(tmp_path / 'ledger.sqlite3'))

    payload = build_ui_operator_command_receipt_payload(
        action='claim-item',
        operator_id='jp',
        work_item_key='wk-1',
        review_target='incident_pack_review',
    )

    assert payload['execution_mode'] == 'JOURNALED_RECEIPT'
    assert payload['journal_family'] == 'operator_action_events'
    assert payload['accepted'] is True
    rows = read_operator_action_events(operator_id='jp')
    assert len(rows) == 1
    assert rows[0].target_payload['review_target'] == 'incident_pack_review'
    assert rows[0].action == 'claim-item'


def test_ui_command_idempotency_replays_original_receipt(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv('STRATEGY_VALIDATOR_LEDGER_DB_PATH', str(tmp_path / 'ledger.sqlite3'))

    first = build_ui_operator_command_receipt_payload(
        action='claim-item',
        operator_id='jp',
        work_item_key='wk-1',
        idempotency_key='cmd-1',
    )
    second = build_ui_operator_command_receipt_payload(
        action='claim-item',
        operator_id='jp',
        work_item_key='wk-1',
        idempotency_key='cmd-1',
    )

    assert first['idempotency_status'] == 'RECORDED'
    assert second['idempotency_status'] == 'REPLAYED'
    assert second['command_id'] == first['command_id']
    assert second['duplicate_of_command_id'] == first['command_id']
    assert len(read_operator_action_events(operator_id='jp')) == 1


def test_ui_command_receipt_records_operator_chain_fields(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv('STRATEGY_VALIDATOR_LEDGER_DB_PATH', str(tmp_path / 'ledger.sqlite3'))

    first = build_ui_operator_command_receipt_payload(
        action='claim-item',
        operator_id='jp',
        work_item_key='wk-1',
    )
    second = build_ui_operator_command_receipt_payload(
        action='renew-lease',
        operator_id='jp',
        work_item_key='wk-1',
    )

    assert first['sequence_number'] == 1
    assert first['previous_event_hash'] is None
    assert second['sequence_number'] == 2
    assert second['previous_event_hash'] == first['event_hash']


def test_legacy_ui_command_receipt_builder_uses_policy_for_target_shape(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv('STRATEGY_VALIDATOR_LEDGER_DB_PATH', str(tmp_path / 'ledger.sqlite3'))

    import pytest

    with pytest.raises(ValueError, match='governed target field'):
        build_ui_operator_command_receipt_payload(action='claim-item', operator_id='jp')


def test_ui_command_idempotency_rejects_same_key_for_different_payload(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv('STRATEGY_VALIDATOR_LEDGER_DB_PATH', str(tmp_path / 'ledger.sqlite3'))

    import pytest

    first = build_ui_operator_command_receipt_payload(
        action='claim-item',
        operator_id='jp',
        work_item_key='wk-1',
        idempotency_key='cmd-conflict',
    )

    with pytest.raises(ValueError, match='different operator command payload'):
        build_ui_operator_command_receipt_payload(
            action='claim-item',
            operator_id='jp',
            work_item_key='wk-2',
            idempotency_key='cmd-conflict',
        )

    assert first['idempotency_status'] == 'RECORDED'
