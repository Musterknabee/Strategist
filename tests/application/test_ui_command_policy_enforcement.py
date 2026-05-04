from __future__ import annotations

import pytest

from strategy_validator.application.ui_command_actions import execute_ui_operator_command
from strategy_validator.contracts.ui_command_mutation import UiMutationAuthContext, UiOperatorCommandRequest


def _auth() -> UiMutationAuthContext:
    return UiMutationAuthContext(
        runtime_mode='TEST',
        authorization_mode='TOKEN',
        token_configured=True,
        token_source='authorization',
    )


def test_ui_operator_command_policy_blocks_targetless_command(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv('STRATEGY_VALIDATOR_LEDGER_DB_PATH', str(tmp_path / 'ledger.sqlite3'))
    with pytest.raises(ValueError, match='governed target field'):
        execute_ui_operator_command(
            action='claim-item',
            request=UiOperatorCommandRequest(operator_id='jp'),
            auth_context=_auth(),
        )


def test_ui_operator_command_policy_allows_governed_target(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv('STRATEGY_VALIDATOR_LEDGER_DB_PATH', str(tmp_path / 'ledger.sqlite3'))
    payload = execute_ui_operator_command(
        action='claim-item',
        request=UiOperatorCommandRequest(operator_id='jp', work_item_key='wk-1'),
        auth_context=_auth(),
    )
    assert payload['policy']['schema_version'] == 'ui_operator_command_policy/v3'
    assert payload['policy']['is_allowed'] is True
    assert payload['policy']['lifecycle_state'] == 'ALLOWED'


def test_ui_operator_command_policy_blocks_production_without_token_authorization(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv('STRATEGY_VALIDATOR_LEDGER_DB_PATH', str(tmp_path / 'ledger.sqlite3'))
    with pytest.raises(ValueError, match='production operator commands require token authorization'):
        execute_ui_operator_command(
            action='claim-item',
            request=UiOperatorCommandRequest(operator_id='jp', work_item_key='wk-1'),
            auth_context=UiMutationAuthContext(
                runtime_mode='PRODUCTION',
                authorization_mode='NON_PRODUCTION_BYPASS',
                token_configured=False,
                token_source='none',
            ),
        )


def test_ui_operator_command_policy_blocks_token_mode_without_recorded_token_source(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv('STRATEGY_VALIDATOR_LEDGER_DB_PATH', str(tmp_path / 'ledger.sqlite3'))
    with pytest.raises(ValueError, match='no token source'):
        execute_ui_operator_command(
            action='claim-item',
            request=UiOperatorCommandRequest(operator_id='jp', work_item_key='wk-1'),
            auth_context=UiMutationAuthContext(
                runtime_mode='PRODUCTION',
                authorization_mode='TOKEN',
                token_configured=True,
                token_source='none',
            ),
        )
