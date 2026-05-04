from __future__ import annotations

from strategy_validator.application.operator_action_projection import build_operator_action_event_index_payload


def test_operator_action_projection_payload_is_read_model(monkeypatch, tmp_path):
    db_path = tmp_path / 'missing.sqlite3'
    monkeypatch.setenv('STRATEGY_VALIDATOR_LEDGER_DB_PATH', str(db_path))
    payload = build_operator_action_event_index_payload(database_path=str(db_path), readonly=True)
    assert payload['read_model'] == 'operator_action_event_projection_index'
    assert payload['readonly'] is True
    assert payload['event_count'] == 0
