from __future__ import annotations

import pytest
from fastapi import HTTPException

from strategy_validator.api.auth import _normalize_principal_id, _scopes_from_env
from strategy_validator.application.ui_command_policy import build_ui_operator_command_policy
from strategy_validator.contracts.ui_command_mutation import UiMutationAuthContext, UiOperatorCommandRequest


def test_mutation_auth_scopes_default_to_operator_write(monkeypatch):
    monkeypatch.delenv('STRATEGY_VALIDATOR_API_TOKEN_SCOPES', raising=False)
    assert 'operator:command:write' in _scopes_from_env()


def test_mutation_auth_scopes_parse_comma_and_space(monkeypatch):
    monkeypatch.setenv('STRATEGY_VALIDATOR_API_TOKEN_SCOPES', 'operator:projection:read, operator:command:write')
    assert _scopes_from_env() == ('operator:command:write', 'operator:projection:read')


def test_ui_command_policy_requires_write_scope():
    policy = build_ui_operator_command_policy(
        action='claim-item',
        request=UiOperatorCommandRequest(operator_id='operator', work_item_key='item-1'),
        auth_context=UiMutationAuthContext(
            runtime_mode='PRODUCTION',
            authorization_mode='TOKEN',
            token_configured=True,
            token_source='authorization',
            principal_id='operator',
            principal_source='token',
            role='operator',
            scopes=('operator:projection:read',),
        ),
    )
    assert policy['is_allowed'] is False
    assert 'operator:command:write' in ';'.join(policy['blocking_reasons'])


def test_operator_principal_validation_rejects_control_characters():
    with pytest.raises(HTTPException):
        _normalize_principal_id('operator\nadmin')
