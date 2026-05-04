from __future__ import annotations

from strategy_validator.projections.operator_action_workboard import get_operator_action_projection_status


def test_operator_action_projection_status_is_disabled_without_ledger_path(monkeypatch) -> None:
    monkeypatch.delenv('STRATEGY_VALIDATOR_LEDGER_DB_PATH', raising=False)

    status = get_operator_action_projection_status()

    assert status.enabled is False
    assert status.state == 'DISABLED'
    assert status.trust_status == 'TRUST_RESTRICTED'
    assert status.ledger_db_path_configured is False
    assert 'STRATEGY_VALIDATOR_LEDGER_DB_PATH' in status.reason


def test_operator_action_projection_status_is_enabled_with_ledger_path(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv('STRATEGY_VALIDATOR_LEDGER_DB_PATH', str(tmp_path / 'ledger.sqlite3'))

    status = get_operator_action_projection_status()

    assert status.enabled is True
    assert status.state == 'ENABLED'
    assert status.trust_status == 'PROJECTION_ENABLED'
    assert status.ledger_db_path_configured is True
    assert status.source_label == 'operator_action_journal'
