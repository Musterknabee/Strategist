from __future__ import annotations

import pytest
from fastapi import HTTPException
from starlette.requests import Request
from fastapi.testclient import TestClient

from strategy_validator.api.app import app
from strategy_validator.api.auth import (
    _normalize_principal_id,
    get_mutation_auth_runtime_status,
    require_mutation_auth,
)


def test_ui_command_requires_token_when_configured(monkeypatch) -> None:
    monkeypatch.setenv('STRATEGY_VALIDATOR_API_TOKEN', 'secret-token')
    monkeypatch.setattr(
        'strategy_validator.api.routes.ui.execute_ui_operator_command',
        lambda **_: {'schema_version': 'ui_operator_command_receipt/v1', 'accepted': True, 'action': 'claim-item'},
    )
    client = TestClient(app)

    unauthorized = client.post('/ui/commands/claim-item', json={'operator_id': 'jp', 'work_item_key': 'w1'})
    assert unauthorized.status_code == 401

    authorized = client.post(
        '/ui/commands/claim-item',
        headers={'Authorization': 'Bearer secret-token'},
        json={'operator_id': 'jp', 'work_item_key': 'w1'},
    )
    assert authorized.status_code == 200
    assert authorized.json()['accepted'] is True


def test_rebuild_route_is_authenticated_post(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv('STRATEGY_VALIDATOR_API_TOKEN', 'secret-token')
    monkeypatch.setattr(
        'strategy_validator.api.routes.rebuild.backfill_all_registered_projections',
        lambda **_: {'ok': True, 'rebuilt': 3},
    )
    client = TestClient(app)

    response = client.post('/rebuild/projection-backfill', json={'search_root': str(tmp_path)})
    assert response.status_code == 401

    response = client.post(
        '/rebuild/projection-backfill',
        headers={'X-Strategy-Validator-Token': 'secret-token'},
        json={'search_root': str(tmp_path)},
    )
    assert response.status_code == 200
    assert response.json()['rebuilt'] == 3


def test_readiness_publish_route_is_authenticated_post(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv('STRATEGY_VALIDATOR_API_TOKEN', 'secret-token')
    monkeypatch.setattr(
        'strategy_validator.api.routes.readiness.publish_release_bundle_from_paths',
        lambda **_: {'ok': True, 'published': True},
    )
    client = TestClient(app)

    payload = {
        'artifact_root': str(tmp_path),
        'policy_path': str(tmp_path / 'policy.json'),
        'keyed_host_fingerprint_path': str(tmp_path / 'fingerprint.json'),
        'publication_path': str(tmp_path / 'publication'),
        'scope': 'FULL',
        'burnin_artifact_paths': [],
    }

    response = client.post('/readiness/publish-release-bundle', json=payload)
    assert response.status_code == 401

    response = client.post(
        '/readiness/publish-release-bundle',
        headers={'Authorization': 'Bearer secret-token'},
        json=payload,
    )
    assert response.status_code == 200
    assert response.json()['published'] is True


def test_non_production_bypass_allows_mutation_routes_without_token(monkeypatch, tmp_path) -> None:
    monkeypatch.delenv('STRATEGY_VALIDATOR_API_TOKEN', raising=False)
    monkeypatch.setenv('STRATEGY_VALIDATOR_MODE', 'DEV')
    monkeypatch.setattr(
        'strategy_validator.api.routes.rebuild.backfill_all_registered_projections',
        lambda **_: {'ok': True, 'rebuilt': 1},
    )
    client = TestClient(app)

    response = client.post('/rebuild/projection-backfill', json={'search_root': str(tmp_path)})
    assert response.status_code == 200
    assert response.json()['rebuilt'] == 1


def test_ui_command_receipt_records_auth_principal(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv('STRATEGY_VALIDATOR_API_TOKEN', 'secret-token')
    monkeypatch.setenv('STRATEGY_VALIDATOR_LEDGER_DB_PATH', str(tmp_path / 'ledger.sqlite3'))
    client = TestClient(app)

    response = client.post(
        '/ui/commands/claim-item',
        headers={
            'Authorization': 'Bearer secret-token',
            'X-Strategy-Validator-Operator': 'operator-jp',
        },
        json={'operator_id': 'jp', 'work_item_key': 'w1', 'idempotency_key': 'auth-principal-smoke'},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload['authorization']['principal_id'] == 'operator-jp'
    assert payload['authorization']['principal_source'] == 'operator_header'
    assert payload['policy']['principal_id'] == 'operator-jp'


def test_mutation_auth_rejects_invalid_operator_principal_header(monkeypatch) -> None:
    monkeypatch.setenv('STRATEGY_VALIDATOR_API_TOKEN', 'secret-token')
    client = TestClient(app)

    response = client.post(
        '/ui/commands/claim-item',
        headers={
            'Authorization': 'Bearer secret-token',
            'X-Strategy-Validator-Operator': 'operator with spaces',
        },
        json={'operator_id': 'jp', 'work_item_key': 'w1'},
    )

    assert response.status_code == 400
    assert response.json()['detail'] == 'INVALID_OPERATOR_PRINCIPAL'


def test_ui_command_requires_configured_token_in_production(monkeypatch) -> None:
    monkeypatch.delenv('STRATEGY_VALIDATOR_API_TOKEN', raising=False)
    monkeypatch.delenv('STRATEGY_VALIDATOR_API_TOKEN_SCOPES', raising=False)
    monkeypatch.setenv('STRATEGY_VALIDATOR_MODE', 'PRODUCTION')
    client = TestClient(app)

    response = client.post('/ui/commands/claim-item', json={'operator_id': 'jp', 'work_item_key': 'w1'})
    assert response.status_code == 503
    assert response.json()['detail'] == 'MUTATION_AUTH_NOT_CONFIGURED'


def test_ui_command_rejects_placeholder_token_in_production(monkeypatch) -> None:
    monkeypatch.setenv('STRATEGY_VALIDATOR_MODE', 'PRODUCTION')
    monkeypatch.setenv('STRATEGY_VALIDATOR_API_TOKEN', 'secret-token')
    monkeypatch.setenv('STRATEGY_VALIDATOR_API_TOKEN_SCOPES', 'operator:command:write,operator:projection:read')
    client = TestClient(app)

    response = client.post(
        '/ui/commands/claim-item',
        headers={'Authorization': 'Bearer secret-token'},
        json={'operator_id': 'jp', 'work_item_key': 'w1'},
    )
    assert response.status_code == 503
    assert response.json()['detail'] == 'MUTATION_TOKEN_PLACEHOLDER'


def test_ui_command_rejects_missing_scopes_in_production(monkeypatch) -> None:
    monkeypatch.setenv('STRATEGY_VALIDATOR_MODE', 'PRODUCTION')
    token = 'abcdefghijklmnopqrstuvwxyz1234567890'
    monkeypatch.setenv('STRATEGY_VALIDATOR_API_TOKEN', token)
    monkeypatch.setenv('STRATEGY_VALIDATOR_API_TOKEN_SCOPES', 'operator:projection:read')
    client = TestClient(app)

    response = client.post(
        '/ui/commands/claim-item',
        headers={'Authorization': f'Bearer {token}'},
        json={'operator_id': 'jp', 'work_item_key': 'w1'},
    )
    assert response.status_code == 503
    assert response.json()['detail'] == 'MUTATION_TOKEN_SCOPES_MISSING'


def test_ui_command_accepts_valid_token_and_scopes_in_production(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv('STRATEGY_VALIDATOR_MODE', 'PRODUCTION')
    token = 'abcdefghijklmnopqrstuvwxyz1234567890'
    monkeypatch.setenv('STRATEGY_VALIDATOR_API_TOKEN', token)
    monkeypatch.setenv('STRATEGY_VALIDATOR_API_TOKEN_SCOPES', 'operator:command:write,operator:projection:read')
    monkeypatch.setenv('STRATEGY_VALIDATOR_LEDGER_DB_PATH', str(tmp_path / 'ledger.sqlite3'))
    client = TestClient(app)

    response = client.post(
        '/ui/commands/claim-item',
        headers={'Authorization': f'Bearer {token}'},
        json={'operator_id': 'jp', 'work_item_key': 'w1', 'idempotency_key': 'production-valid-token'},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload['authorization']['authorization_mode'] == 'TOKEN'


def test_ui_command_rejects_invalid_bearer_token(monkeypatch) -> None:
    monkeypatch.setenv('STRATEGY_VALIDATOR_MODE', 'PRODUCTION')
    monkeypatch.setenv('STRATEGY_VALIDATOR_API_TOKEN', 'abcdefghijklmnopqrstuvwxyz1234567890')
    monkeypatch.setenv('STRATEGY_VALIDATOR_API_TOKEN_SCOPES', 'operator:command:write,operator:projection:read')
    client = TestClient(app)

    response = client.post(
        '/ui/commands/claim-item',
        headers={'Authorization': 'Bearer wrong-token-value'},
        json={'operator_id': 'jp', 'work_item_key': 'w1'},
    )
    assert response.status_code == 401
    assert response.json()['detail'] == 'INVALID_MUTATION_TOKEN'


def test_ui_command_accepts_x_strategy_validator_token_header(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv('STRATEGY_VALIDATOR_MODE', 'PRODUCTION')
    token = 'abcdefghijklmnopqrstuvwxyz1234567890'
    monkeypatch.setenv('STRATEGY_VALIDATOR_API_TOKEN', token)
    monkeypatch.setenv('STRATEGY_VALIDATOR_API_TOKEN_SCOPES', 'operator:command:write,operator:projection:read')
    monkeypatch.setenv('STRATEGY_VALIDATOR_LEDGER_DB_PATH', str(tmp_path / 'ledger.sqlite3'))
    client = TestClient(app)

    response = client.post(
        '/ui/commands/claim-item',
        headers={'X-Strategy-Validator-Token': token},
        json={'operator_id': 'jp', 'work_item_key': 'w1', 'idempotency_key': 'x-token-valid'},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload['authorization']['token_source'] == 'x_strategy_validator_token'


def test_non_production_remote_bypass_forbidden_without_explicit_env(monkeypatch) -> None:
    monkeypatch.delenv('STRATEGY_VALIDATOR_API_TOKEN', raising=False)
    monkeypatch.setenv('STRATEGY_VALIDATOR_MODE', 'DEV')
    monkeypatch.delenv('STRATEGY_VALIDATOR_ALLOW_REMOTE_NON_PRODUCTION_MUTATION_BYPASS', raising=False)
    scope = {'type': 'http', 'method': 'POST', 'path': '/ui/commands/claim-item', 'headers': [], 'client': ('203.0.113.10', 4321)}
    request = Request(scope)

    with pytest.raises(HTTPException) as exc:
        require_mutation_auth(request, authorization=None, x_strategy_validator_token=None, x_strategy_validator_operator=None)
    assert exc.value.status_code == 403
    assert exc.value.detail == 'REMOTE_NON_PRODUCTION_MUTATION_BYPASS_FORBIDDEN'


def test_non_production_remote_bypass_allowed_only_with_explicit_env(monkeypatch) -> None:
    monkeypatch.delenv('STRATEGY_VALIDATOR_API_TOKEN', raising=False)
    monkeypatch.setenv('STRATEGY_VALIDATOR_MODE', 'DEV')
    monkeypatch.setenv('STRATEGY_VALIDATOR_ALLOW_REMOTE_NON_PRODUCTION_MUTATION_BYPASS', 'true')
    scope = {'type': 'http', 'method': 'POST', 'path': '/ui/commands/claim-item', 'headers': [], 'client': ('203.0.113.10', 4321)}
    request = Request(scope)

    context = require_mutation_auth(request, authorization=None, x_strategy_validator_token=None, x_strategy_validator_operator=None)
    assert context.authorization_mode == 'NON_PRODUCTION_BYPASS'
    assert context.principal_source == 'local_bypass'


def test_operator_principal_normalization_rejects_unsafe_values() -> None:
    for value in ('../etc/passwd', 'operator with spaces', 'operator\nname', 'x' * 129):
        with pytest.raises(HTTPException) as exc:
            _normalize_principal_id(value)
        assert exc.value.status_code == 400
        assert exc.value.detail == 'INVALID_OPERATOR_PRINCIPAL'


def test_mutation_runtime_status_reports_safe_and_unsafe_posture(monkeypatch) -> None:
    monkeypatch.setenv('STRATEGY_VALIDATOR_MODE', 'PRODUCTION')
    monkeypatch.delenv('STRATEGY_VALIDATOR_API_TOKEN', raising=False)
    missing = get_mutation_auth_runtime_status()
    assert missing.authorization_mode == 'MISCONFIGURED'
    assert missing.mutation_routes_safe is False
    assert missing.detail_code == 'MUTATION_AUTH_NOT_CONFIGURED'

    monkeypatch.setenv('STRATEGY_VALIDATOR_API_TOKEN', 'secret-token')
    monkeypatch.setenv('STRATEGY_VALIDATOR_API_TOKEN_SCOPES', 'operator:command:write,operator:projection:read')
    placeholder = get_mutation_auth_runtime_status()
    assert placeholder.authorization_mode == 'MISCONFIGURED'
    assert placeholder.detail_code == 'MUTATION_TOKEN_PLACEHOLDER'

    monkeypatch.setenv('STRATEGY_VALIDATOR_API_TOKEN', 'abcdefghijklmnopqrstuvwxyz1234567890')
    monkeypatch.setenv('STRATEGY_VALIDATOR_API_TOKEN_SCOPES', 'operator:command:write,operator:projection:read')
    safe = get_mutation_auth_runtime_status()
    assert safe.authorization_mode == 'TOKEN_PROTECTED'
    assert safe.mutation_routes_safe is True
    assert safe.detail_code == 'MUTATION_TOKEN_CONFIGURED'
