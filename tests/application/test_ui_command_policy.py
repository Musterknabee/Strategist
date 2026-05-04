from __future__ import annotations

from strategy_validator.application.ui_command_actions import execute_ui_operator_command
from strategy_validator.contracts.ui_command_mutation import UiMutationAuthContext, UiOperatorCommandRequest


def test_execute_ui_operator_command_exposes_policy_and_authorization(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv('STRATEGY_VALIDATOR_LEDGER_DB_PATH', str(tmp_path / 'ledger.sqlite3'))
    payload = execute_ui_operator_command(
        action='claim-item',
        request=UiOperatorCommandRequest(operator_id='jp', work_item_key='w1', review_target='alpha'),
        auth_context=UiMutationAuthContext(
            runtime_mode='TEST',
            authorization_mode='TOKEN',
            token_configured=True,
            token_source='authorization',
        ),
    )
    assert payload['accepted'] is True
    assert payload['policy']['schema_version'] == 'ui_operator_command_policy/v2'
    assert payload['policy']['is_allowed'] is True
    assert payload['policy']['authorization_mode'] == 'TOKEN'
    assert payload['policy']['target_fields_present'] == ['review_target', 'work_item_key']
    assert payload['authorization']['runtime_mode'] == 'TEST'
    assert payload['authorization']['token_source'] == 'authorization'
