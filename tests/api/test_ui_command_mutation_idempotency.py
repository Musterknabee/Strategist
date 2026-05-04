from __future__ import annotations

from fastapi.testclient import TestClient

from strategy_validator.api.app import app
from strategy_validator.ledger.operator_actions import read_operator_action_events, verify_operator_action_event_chain


def test_ui_command_route_replays_idempotent_command(monkeypatch, tmp_path) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv('STRATEGY_VALIDATOR_MODE', 'DEV')
    monkeypatch.delenv('STRATEGY_VALIDATOR_API_TOKEN', raising=False)
    monkeypatch.setenv('STRATEGY_VALIDATOR_LEDGER_DB_PATH', str(tmp_path / 'ledger.sqlite3'))
    client = TestClient(app)

    request_payload = {
        'operator_id': 'ops',
        'work_item_key': 'wk-1',
        'review_target': 'governance-main',
        'idempotency_key': 'ui-command-idempotency-1',
    }

    first = client.post('/ui/commands/claim-item', json=request_payload)
    second = client.post('/ui/commands/claim-item', json=request_payload)

    assert first.status_code == 200
    assert second.status_code == 200
    first_payload = first.json()
    second_payload = second.json()
    assert first_payload['idempotency_status'] == 'RECORDED'
    assert second_payload['idempotency_status'] == 'REPLAYED'
    assert second_payload['command_id'] == first_payload['command_id']
    assert second_payload['duplicate_of_command_id'] == first_payload['command_id']
    assert first_payload['sequence_number'] == 1
    assert first_payload['previous_event_hash'] is None

    events = read_operator_action_events(idempotency_key='ui-command-idempotency-1')
    assert len(events) == 1
    assert events[0].action_event_id == first_payload['command_id']
    assert verify_operator_action_event_chain().ok is True


def test_ui_command_route_rejects_idempotency_key_reuse_for_different_command(monkeypatch, tmp_path) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv('STRATEGY_VALIDATOR_MODE', 'DEV')
    monkeypatch.delenv('STRATEGY_VALIDATOR_API_TOKEN', raising=False)
    monkeypatch.setenv('STRATEGY_VALIDATOR_LEDGER_DB_PATH', str(tmp_path / 'ledger.sqlite3'))
    client = TestClient(app)

    first = client.post(
        '/ui/commands/claim-item',
        json={
            'operator_id': 'ops',
            'work_item_key': 'wk-1',
            'review_target': 'governance-main',
            'idempotency_key': 'ui-command-conflict-1',
        },
    )
    conflict = client.post(
        '/ui/commands/renew-lease',
        json={
            'operator_id': 'ops',
            'work_item_key': 'wk-1',
            'review_target': 'governance-main',
            'idempotency_key': 'ui-command-conflict-1',
        },
    )

    assert first.status_code == 200
    assert conflict.status_code == 400
    assert 'idempotency key' in conflict.json()['detail']
    assert len(read_operator_action_events(idempotency_key='ui-command-conflict-1')) == 1
    assert verify_operator_action_event_chain().ok is True
